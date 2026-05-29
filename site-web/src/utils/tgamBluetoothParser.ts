import type { EEGSample } from '@/types/eeg'
import { EEG_BAND_KEYS, TGAM_PACKET_SIZE, TGAM_SYNC } from '@/constants/eegBluetooth'

export interface ParsedTGAMPacket {
  timestamp: string
  signalQuality: number
  attention: number
  meditation: number
  Delta: number
  Theta: number
  'Low Alpha': number
  'High Alpha': number
  'Low Beta': number
  'High Beta': number
  'Low Gamma': number
  'Middle Gamma': number
}

export function parseTGAMPacket(packet: Uint8Array): ParsedTGAMPacket | null {
  if (
    packet.length < TGAM_PACKET_SIZE ||
    packet[0] !== TGAM_SYNC[0] ||
    packet[1] !== TGAM_SYNC[1] ||
    packet[2] !== TGAM_SYNC[2]
  ) {
    return null
  }

  const signalQuality = packet[4]
  if (packet[5] !== 0x83) {
    return null
  }

  const eegPower: Record<string, number> = {}
  let index = 6
  for (const band of EEG_BAND_KEYS) {
    const value = (packet[index] << 16) | (packet[index + 1] << 8) | packet[index + 2]
    eegPower[band] = value
    index += 3
  }

  let attention = 0
  let meditation = 0
  while (index < 30) {
    const code = packet[index]
    if (code === 0x04) {
      attention = packet[index + 1]
      index += 2
    } else if (code === 0x05) {
      meditation = packet[index + 1]
      index += 2
    } else {
      index += 1
    }
  }

  return {
    timestamp: new Date().toISOString(),
    signalQuality,
    attention,
    meditation,
    Delta: eegPower.Delta ?? 0,
    Theta: eegPower.Theta ?? 0,
    'Low Alpha': eegPower['Low Alpha'] ?? 0,
    'High Alpha': eegPower['High Alpha'] ?? 0,
    'Low Beta': eegPower['Low Beta'] ?? 0,
    'High Beta': eegPower['High Beta'] ?? 0,
    'Low Gamma': eegPower['Low Gamma'] ?? 0,
    'Middle Gamma': eegPower['Middle Gamma'] ?? 0,
  }
}

/** 解析 TGAM Raw 小包 (AA AA 04 80 ...) */
export function tryParseRawWavePacket(buffer: Uint8Array): { raw: number; consumed: number } | null {
  if (buffer.length < 7) return null
  if (buffer[0] !== 0xaa || buffer[1] !== 0xaa || buffer[2] !== 0x04 || buffer[3] !== 0x80) {
    return null
  }
  const high = buffer[4]
  const low = buffer[5]
  let raw = (high << 8) | low
  if (raw > 32767) raw -= 65536
  return { raw, consumed: 7 }
}

export function parsedPacketToSample(parsed: ParsedTGAMPacket, raw = 0): EEGSample {
  return {
    timestamp: parsed.timestamp,
    raw,
    signalQuality: parsed.signalQuality,
    attention: parsed.attention,
    meditation: parsed.meditation,
    delta: parsed.Delta,
    theta: parsed.Theta,
    lowAlpha: parsed['Low Alpha'],
    highAlpha: parsed['High Alpha'],
    lowBeta: parsed['Low Beta'],
    highBeta: parsed['High Beta'],
    lowGamma: parsed['Low Gamma'],
    highGamma: parsed['Middle Gamma'],
  }
}

export function sampleToBackendDict(sample: EEGSample): Record<string, number | string> {
  return {
    timestamp: sample.timestamp,
    signalQuality: sample.signalQuality,
    attention: sample.attention,
    meditation: sample.meditation,
    Delta: sample.delta,
    Theta: sample.theta,
    'Low Alpha': sample.lowAlpha,
    'High Alpha': sample.highAlpha,
    'Low Beta': sample.lowBeta,
    'High Beta': sample.highBeta,
    'Low Gamma': sample.lowGamma,
    'Middle Gamma': sample.highGamma,
    Raw: sample.raw,
  }
}

export function processBluetoothBuffer(
  buffer: Uint8Array,
  lastRaw: number,
): { buffer: Uint8Array; samples: EEGSample[]; lastRaw: number } {
  let working = buffer
  const samples: EEGSample[] = []
  let raw = lastRaw

  try {
    while (working.length >= 4) {
      const rawPacket = tryParseRawWavePacket(working)
      if (rawPacket) {
        raw = rawPacket.raw
        working = working.slice(rawPacket.consumed)
        continue
      }

      if (working.length >= TGAM_PACKET_SIZE) {
        let syncPos = -1
        for (let i = 0; i <= working.length - 3; i++) {
          if (
            working[i] === TGAM_SYNC[0] &&
            working[i + 1] === TGAM_SYNC[1] &&
            working[i + 2] === TGAM_SYNC[2]
          ) {
            syncPos = i
            break
          }
        }

        if (syncPos === -1) {
          if (working.length > 100) working = new Uint8Array()
          break
        }

        if (syncPos > 0) {
          working = working.slice(syncPos)
          continue
        }

        if (working.length < TGAM_PACKET_SIZE) break

        const packet = working.slice(0, TGAM_PACKET_SIZE)
        working = working.slice(TGAM_PACKET_SIZE)
        const parsed = parseTGAMPacket(packet)
        if (parsed) {
          samples.push(parsedPacketToSample(parsed, raw))
        }
        continue
      }

      break
    }
  } catch {
    working = new Uint8Array()
  }

  return { buffer: working, samples, lastRaw: raw }
}

export function appendBuffer(current: Uint8Array, chunk: Uint8Array): Uint8Array {
  const merged = new Uint8Array(current.length + chunk.length)
  merged.set(current)
  merged.set(chunk, current.length)
  return merged
}
