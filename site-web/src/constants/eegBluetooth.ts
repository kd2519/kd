/** JDY-18 蓝牙透传模块 + TGAM 脑电（与 git_Yunmengze 一致） */
export const EEG_BLE_SERVICE = '0000ffe0-0000-1000-8000-00805f9b34fb'
export const EEG_BLE_NOTIFY_CHAR = '0000ffe1-0000-1000-8000-00805f9b34fb'

export const TGAM_PACKET_SIZE = 32
export const TGAM_SYNC = [0xaa, 0xaa, 0x20] as const

export const EEG_BAND_KEYS = [
  'Delta',
  'Theta',
  'Low Alpha',
  'High Alpha',
  'Low Beta',
  'High Beta',
  'Low Gamma',
  'Middle Gamma',
] as const
