export interface EEGSample {
  timestamp: string
  raw: number
  signalQuality: number
  attention: number
  meditation: number
  delta: number
  theta: number
  lowAlpha: number
  highAlpha: number
  lowBeta: number
  highBeta: number
  lowGamma: number
  highGamma: number
}

export type EEGDisplayMode = 'raw' | 'eeg'
export type EEGExportFormat = 'xlsx' | 'txt'

export const EEG_BAND_LABELS = [
  { key: 'delta', label: 'Delta', color: '#5470c6' },
  { key: 'theta', label: 'Theta', color: '#8B4513' },
  { key: 'lowAlpha', label: 'LowAlpha', color: '#ee6666' },
  { key: 'highAlpha', label: 'HighAlpha', color: '#91cc75' },
  { key: 'lowBeta', label: 'LowBeta', color: '#73c0de' },
  { key: 'highBeta', label: 'HighBeta', color: '#fac858' },
  { key: 'lowGamma', label: 'LowGamma', color: '#9a60b4' },
  { key: 'highGamma', label: 'MiddleGamma', color: '#3ba272' },
] as const

export const EMPTY_EEG_SAMPLE = (): EEGSample => ({
  timestamp: '',
  raw: 0,
  signalQuality: 0,
  attention: 0,
  meditation: 0,
  delta: 0,
  theta: 0,
  lowAlpha: 0,
  highAlpha: 0,
  lowBeta: 0,
  highBeta: 0,
  lowGamma: 0,
  highGamma: 0,
})
