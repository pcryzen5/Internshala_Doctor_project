/**
 * Resilient WebSocket client for live audio streaming and transcription events.
 * Conforms to binary frame specification in docs/TRD.md & docs/API.md.
 */

import { floatTo16BitPCM } from './audio';

export interface TranscriptSegmentEvent {
  type: 'transcript.segment';
  seq: number;
  text: string;
  start_ms: number;
  end_ms: number;
  confidence: number;
}

export interface TranscriptErrorEvent {
  type: 'transcript.error';
  seq: number;
  code: string;
  message: string;
}

export interface SessionBusyEvent {
  type: 'session.busy';
  queue_depth: number;
}

export type WebSocketConnectionStatus = 'connecting' | 'connected' | 'disconnected';

export interface AudioWebSocketOptions {
  sessionId: string;
  onSegment: (event: TranscriptSegmentEvent) => void;
  onError?: (event: TranscriptErrorEvent) => void;
  onBusy?: (event: SessionBusyEvent) => void;
  onStatusChange?: (status: WebSocketConnectionStatus) => void;
}

export class AudioWebSocketClient {
  private socket: WebSocket | null = null;
  private sessionId: string;
  private options: AudioWebSocketOptions;
  private sendBuffer: { seq: number; buffer: ArrayBuffer }[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private isExplicitlyClosed = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(options: AudioWebSocketOptions) {
    this.options = options;
    this.sessionId = options.sessionId;
  }

  public connect(): void {
    this.isExplicitlyClosed = false;
    this.options.onStatusChange?.('connecting');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/sessions/${this.sessionId}/audio`;

    try {
      this.socket = new WebSocket(wsUrl);
      this.socket.binaryType = 'arraybuffer';

      this.socket.onopen = () => {
        this.reconnectAttempts = 0;
        this.options.onStatusChange?.('connected');
        this.flushBuffer();
      };

      this.socket.onmessage = (event) => {
        if (typeof event.data === 'string') {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'transcript.segment') {
              this.options.onSegment(data as TranscriptSegmentEvent);
            } else if (data.type === 'transcript.error') {
              this.options.onError?.(data as TranscriptErrorEvent);
            } else if (data.type === 'session.busy') {
              this.options.onBusy?.(data as SessionBusyEvent);
            }
          } catch {
            // Ignore parse errors on ping/pong or unstructured messages
          }
        }
      };

      this.socket.onerror = () => {
        this.options.onStatusChange?.('disconnected');
      };

      this.socket.onclose = () => {
        this.options.onStatusChange?.('disconnected');
        if (!this.isExplicitlyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 8000);
          this.reconnectAttempts++;
          this.reconnectTimer = setTimeout(() => {
            this.connect();
          }, delay);
        }
      };
    } catch {
      this.options.onStatusChange?.('disconnected');
    }
  }

  public sendAudioSegment(seq: number, floatSamples: Float32Array, sampleRate = 16000): void {
    const pcm16 = floatTo16BitPCM(floatSamples);
    const headerStr = JSON.stringify({ seq, sampleRate });
    const encoder = new TextEncoder();
    const headerBytes = encoder.encode(headerStr);
    const headerLen = headerBytes.byteLength;

    // Binary layout: 4 bytes big endian header length + JSON header + PCM16
    const totalLength = 4 + headerLen + pcm16.byteLength;
    const arrayBuffer = new ArrayBuffer(totalLength);
    const dataView = new DataView(arrayBuffer);

    // 4-byte big endian header length
    dataView.setUint32(0, headerLen, false);

    // Copy header bytes
    new Uint8Array(arrayBuffer, 4, headerLen).set(headerBytes);

    // Copy PCM16 bytes
    new Int16Array(arrayBuffer, 4 + headerLen, pcm16.length).set(pcm16);

    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(arrayBuffer);
    } else {
      // Buffer if disconnected or connecting, keep max 30 segments
      if (this.sendBuffer.length >= 30) {
        this.sendBuffer.shift();
      }
      this.sendBuffer.push({ seq, buffer: arrayBuffer });
    }
  }

  public stopSession(): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: 'session.stop' }));
    }
  }

  private flushBuffer(): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
    // Resend in strict seq order
    this.sendBuffer.sort((a, b) => a.seq - b.seq);
    while (this.sendBuffer.length > 0) {
      const item = this.sendBuffer.shift();
      if (item) {
        this.socket.send(item.buffer);
      }
    }
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}
