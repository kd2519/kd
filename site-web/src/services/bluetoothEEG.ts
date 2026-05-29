import { ref } from 'vue'
import { EEG_BLE_NOTIFY_CHAR, EEG_BLE_SERVICE } from '@/constants/eegBluetooth'
import type { EEGSample } from '@/types/eeg'
import {
  appendBuffer,
  processBluetoothBuffer,
} from '@/utils/tgamBluetoothParser'

export type BluetoothEEGOptions = {
  onSample?: (sample: EEGSample) => void
  shouldEmit?: () => boolean
}

export function createBluetoothEEG(options: BluetoothEEGOptions = {}) {
  const bluetoothDevice = ref<BluetoothDevice | null>(null)
  const bluetoothConnected = ref(false)
  const deviceAddress = ref('')

  let server: BluetoothRemoteGATTServer | null = null
  let characteristic: BluetoothRemoteGATTCharacteristic | null = null
  let buffer = new Uint8Array()
  let lastRaw = 0
  let onSample = options.onSample
  let shouldEmit = options.shouldEmit ?? (() => true)

  function setHandlers(handlers: Partial<BluetoothEEGOptions>) {
    if (handlers.onSample) onSample = handlers.onSample
    if (handlers.shouldEmit) shouldEmit = handlers.shouldEmit
  }

  function checkSupport(): boolean {
    return !!navigator.bluetooth
  }

  async function scanDevices(): Promise<string> {
    if (!checkSupport()) {
      throw new Error('当前浏览器不支持 Web Bluetooth')
    }

    const device = await navigator.bluetooth.requestDevice({
      acceptAllDevices: true,
      optionalServices: [EEG_BLE_SERVICE],
    })

    bluetoothDevice.value = device
    deviceAddress.value = device.id
    return device.name || device.id || '蓝牙设备'
  }

  async function connectBluetooth(): Promise<void> {
    if (!bluetoothDevice.value) {
      throw new Error('请先扫描并选择蓝牙设备')
    }

    server = await bluetoothDevice.value.gatt!.connect()
    const service = await server.getPrimaryService(EEG_BLE_SERVICE)
    characteristic = await service.getCharacteristic(EEG_BLE_NOTIFY_CHAR)
    await characteristic.startNotifications()
    characteristic.addEventListener('characteristicvaluechanged', handleBluetoothData)
    bluetoothConnected.value = true
  }

  async function disconnectBluetooth(): Promise<void> {
    if (characteristic) {
      try {
        await characteristic.stopNotifications()
        characteristic.removeEventListener('characteristicvaluechanged', handleBluetoothData)
      } catch {
        // ignore
      }
      characteristic = null
    }

    if (server?.connected) {
      try {
        await server.disconnect()
      } catch {
        // ignore
      }
    }

    server = null
    buffer = new Uint8Array()
    lastRaw = 0
    bluetoothConnected.value = false
  }

  function handleBluetoothData(event: Event) {
    const target = event.target as BluetoothRemoteGATTCharacteristic
    const value = target.value
    if (!value) return

    const chunk = new Uint8Array(value.buffer, value.byteOffset, value.byteLength)
    buffer = new Uint8Array(appendBuffer(buffer, chunk))

    const result = processBluetoothBuffer(buffer, lastRaw)
    buffer = new Uint8Array(result.buffer)
    lastRaw = result.lastRaw

    if (!shouldEmit()) return

    for (const sample of result.samples) {
      onSample?.(sample)
    }
  }

  return {
    bluetoothDevice,
    bluetoothConnected,
    deviceAddress,
    checkSupport,
    scanDevices,
    connectBluetooth,
    disconnectBluetooth,
    setHandlers,
  }
}
