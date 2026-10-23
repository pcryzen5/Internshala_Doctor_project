/**
 * Audio encoding and format conversion utilities.
 */

export function floatTo16BitPCM(samples: Float32Array): Int16Array {
  const output = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return output;
}

export function encodeWAV(samples: Float32Array, sampleRate = 16000): Blob {
  const pcm16 = floatTo16BitPCM(samples);
  const buffer = new ArrayBuffer(44 + pcm16.length * 2);
  const view = new DataView(buffer);

  function writeString(offset: number, str: string) {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  }

  // RIFF identifier
  writeString(0, 'RIFF');
  // file length minus RIFF identifier & file length
  view.setUint32(4, 36 + pcm16.length * 2, true);
  // RIFF type & format chunk
  writeString(8, 'WAVEfmt ');
  // format chunk length
  view.setUint32(16, 16, true);
  // sample format (raw 1 = PCM)
  view.setUint16(20, 1, true);
  // channel count (1 = mono)
  view.setUint16(22, 1, true);
  // sample rate
  view.setUint32(24, sampleRate, true);
  // byte rate (sampleRate * blockAlign)
  view.setUint32(28, sampleRate * 2, true);
  // block align (channel count * bytes per sample)
  view.setUint16(32, 2, true);
  // bits per sample
  view.setUint16(34, 16, true);
  // data chunk identifier
  writeString(36, 'data');
  // data chunk length
  view.setUint32(40, pcm16.length * 2, true);

  // Write PCM audio frames
  const offset = 44;
  for (let i = 0; i < pcm16.length; i++) {
    view.setInt16(offset + i * 2, pcm16[i], true);
  }

  return new Blob([view], { type: 'audio/wav' });
}
