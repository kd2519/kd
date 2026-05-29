import type { EEGSample } from '@/types/eeg'
import { EMPTY_EEG_SAMPLE } from '@/types/eeg'

const KEY_MAP: Record<string, keyof EEGSample> = {
  raw: 'raw',
  rawwave: 'raw',
  signal: 'signalQuality',
  signalquality: 'signalQuality',
  attention: 'attention',
  meditation: 'meditation',
  delta: 'delta',
  theta: 'theta',
  lowalpha: 'lowAlpha',
  highalpha: 'highAlpha',
  alpha: 'lowAlpha',
  lowbeta: 'lowBeta',
  highbeta: 'highBeta',
  beta: 'lowBeta',
  lowgamma: 'lowGamma',
  highgamma: 'highGamma',
  middlegamma: 'highGamma',
  gamma: 'lowGamma',
}

function setSampleValue(sample: EEGSample, key: keyof EEGSample, value: number) {
  if (key === 'timestamp') return
  sample[key] = value
}

export function parseEEGDataPayload(data: string | Record<string, number | string>): EEGSample {
  const sample = EMPTY_EEG_SAMPLE()
  sample.timestamp = new Date().toISOString()

  if (typeof data === 'object' && data !== null) {
    Object.entries(data).forEach(([key, value]) => {
      if (key === 'timestamp') {
        sample.timestamp = String(value)
        return
      }
      const mapped = KEY_MAP[key.toLowerCase().replace(/\s+/g, '')]
      if (mapped) setSampleValue(sample, mapped, Number(value) || 0)
    })
    return sample
  }

  const pattern = /(\w+)\s+(-?\d+\.?\d*)/g
  let match: RegExpExecArray | null
  while ((match = pattern.exec(data)) !== null) {
    const mapped = KEY_MAP[match[1].toLowerCase()]
    if (mapped) setSampleValue(sample, mapped, Number(match[2]) || 0)
  }

  return sample
}

export function formatEEGDataForServer(sample: EEGSample): string {
  return [
    `Raw ${sample.raw}`,
    `SignalQuality ${sample.signalQuality}`,
    `Attention ${sample.attention}`,
    `Meditation ${sample.meditation}`,
    `Delta ${sample.delta}`,
    `Theta ${sample.theta}`,
    `LowAlpha ${sample.lowAlpha}`,
    `HighAlpha ${sample.highAlpha}`,
    `LowBeta ${sample.lowBeta}`,
    `HighBeta ${sample.highBeta}`,
    `LowGamma ${sample.lowGamma}`,
    `HighGamma ${sample.highGamma}`,
  ].join(' ')
}

export function formatTimeLabel(iso: string): string {
  const date = new Date(iso)
  return date.toLocaleTimeString('zh-CN', { hour12: false })
}
