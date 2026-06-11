/**
 * Client-side audio extraction.
 * Decodes any audio/video blob, downmixes to mono, and encodes 16-bit PCM WAV.
 * Uses a lower sample rate for larger recordings to keep upload size within route memory limits.
 */

const DEFAULT_TARGET_SAMPLE_RATE = 16000;
const LARGE_FILE_THRESHOLD_BYTES = 24 * 1024 * 1024;
const VERY_LARGE_FILE_THRESHOLD_BYTES = 64 * 1024 * 1024;

export const TARGET_ANALYSIS_CHUNK_BYTES = 6 * 1024 * 1024;

export interface AudioWavChunk {
  blob: Blob;
  index: number;
  total: number;
  startSec: number;
  endSec: number;
}

export function chooseTargetSampleRate(blob: Blob): number {
  if (blob.size >= VERY_LARGE_FILE_THRESHOLD_BYTES) return 8000;
  if (blob.size >= LARGE_FILE_THRESHOLD_BYTES) return 12000;
  return DEFAULT_TARGET_SAMPLE_RATE;
}

export function estimateMonoWavBytes(durationSec: number, sampleRate: number): number {
  return Math.max(44, Math.ceil(durationSec * sampleRate) * 2 + 44);
}

export async function extractAudioWavBlob(
  blob: Blob,
  targetSampleRate = chooseTargetSampleRate(blob),
): Promise<Blob> {
  const rendered = await renderMonoAudio(blob, targetSampleRate);
  const wav = encodeWavMono(rendered.getChannelData(0), rendered.sampleRate);
  return new Blob([wav], { type: "audio/wav" });
}

export async function extractAudioWavChunks(
  blob: Blob,
  targetSampleRate = chooseTargetSampleRate(blob),
  maxChunkBytes = TARGET_ANALYSIS_CHUNK_BYTES,
): Promise<AudioWavChunk[]> {
  const rendered = await renderMonoAudio(blob, targetSampleRate);
  const channelData = rendered.getChannelData(0);
  const maxSamplesPerChunk = Math.max(1, Math.floor((maxChunkBytes - 44) / 2));
  const total = Math.max(1, Math.ceil(channelData.length / maxSamplesPerChunk));
  const chunks: AudioWavChunk[] = [];

  for (let start = 0, index = 0; start < channelData.length; start += maxSamplesPerChunk, index++) {
    const end = Math.min(channelData.length, start + maxSamplesPerChunk);
    const wav = encodeWavMono(channelData.slice(start, end), rendered.sampleRate);
    chunks.push({
      blob: new Blob([wav], { type: "audio/wav" }),
      index,
      total,
      startSec: start / rendered.sampleRate,
      endSec: end / rendered.sampleRate,
    });
  }

  return chunks;
}

async function renderMonoAudio(blob: Blob, targetSampleRate: number): Promise<AudioBuffer> {
  const arrayBuffer = await blob.arrayBuffer();

  const AudioCtx: typeof OfflineAudioContext =
    (window as unknown as { OfflineAudioContext: typeof OfflineAudioContext })
      .OfflineAudioContext ||
    (window as unknown as { webkitOfflineAudioContext: typeof OfflineAudioContext })
      .webkitOfflineAudioContext;

  // Need a regular AudioContext just to decode.
  const TempCtx: typeof AudioContext =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  const tempCtx = new TempCtx();
  let decoded: AudioBuffer;
  try {
    decoded = await tempCtx.decodeAudioData(arrayBuffer.slice(0));
  } finally {
    await tempCtx.close().catch(() => {});
  }

  // Resample + downmix using OfflineAudioContext.
  const duration = decoded.duration;
  const offline = new AudioCtx(1, Math.ceil(duration * targetSampleRate), targetSampleRate);
  const src = offline.createBufferSource();
  src.buffer = decoded;
  src.connect(offline.destination);
  src.start(0);
  return offline.startRendering();
}

function encodeWavMono(samples: Float32Array, sampleRate: number): ArrayBuffer {
  const numChannels = 1;
  const bytesPerSample = 2;
  const blockAlign = numChannels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = samples.length * bytesPerSample;
  const bufferSize = 44 + dataSize;
  const ab = new ArrayBuffer(bufferSize);
  const view = new DataView(ab);

  let offset = 0;
  const writeStr = (s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(offset++, s.charCodeAt(i));
  };
  writeStr("RIFF");
  view.setUint32(offset, 36 + dataSize, true);
  offset += 4;
  writeStr("WAVE");
  writeStr("fmt ");
  view.setUint32(offset, 16, true);
  offset += 4;
  view.setUint16(offset, 1, true);
  offset += 2;
  view.setUint16(offset, numChannels, true);
  offset += 2;
  view.setUint32(offset, sampleRate, true);
  offset += 4;
  view.setUint32(offset, byteRate, true);
  offset += 4;
  view.setUint16(offset, blockAlign, true);
  offset += 2;
  view.setUint16(offset, 16, true);
  offset += 2;
  writeStr("data");
  view.setUint32(offset, dataSize, true);
  offset += 4;

  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }
  return ab;
}
