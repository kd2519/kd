import { ref, computed, onUnmounted } from 'vue'
import type { EEGDisplayMode, EEGExportFormat, EEGSample } from '@/types/eeg'
import { EMPTY_EEG_SAMPLE } from '@/types/eeg'
import { createBluetoothEEG } from '@/services/bluetoothEEG'
import { sampleToBackendDict } from '@/utils/tgamBluetoothParser'

const MAX_HISTORY = 60

function buildWsUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/eeg/`
}

export function useEEGMonitor() {
  const wsConnected = ref(false)
  const isRecording = ref(false)
  const displayMode = ref<EEGDisplayMode>('raw')
  const exportFormat = ref<EEGExportFormat>('txt')
  const currentRecordingId = ref<string | null>(null)
  const currentSample = ref<EEGSample>(EMPTY_EEG_SAMPLE())
  const history = ref<EEGSample[]>([])

  let socket: WebSocket | null = null

  const bluetooth = createBluetoothEEG()
  bluetooth.setHandlers({
    shouldEmit: () => true,
    onSample: (sample) => ingestSample(sample, true),
  })

  const deviceConnected = bluetooth.bluetoothConnected
  const useMockDevice = computed(() => !bluetooth.bluetoothConnected.value)

  const signalStrength = computed(() => {
    const q = currentSample.value.signalQuality
    if (q >= 180) return 4
    if (q >= 150) return 3
    if (q >= 100) return 2
    if (q > 0) return 1
    return 0
  })

  function pushSample(sample: EEGSample) {
    currentSample.value = sample
    history.value = [...history.value, sample].slice(-MAX_HISTORY)
  }

  function connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (socket?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      try {
        socket = new WebSocket(buildWsUrl())
      } catch (err) {
        reject(err)
        return
      }

      socket.onopen = () => {
        wsConnected.value = true
        resolve()
      }

      socket.onclose = () => {
        wsConnected.value = false
        if (isRecording.value) stopRecording()
      }

      socket.onerror = () => {
        reject(new Error('WebSocket 连接失败'))
      }

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'recording_status') {
            if (data.status === 'started') {
              currentRecordingId.value = data.recording_id ?? null
            } else if (data.status === 'stopped') {
              currentRecordingId.value = data.recording_id ?? currentRecordingId.value
            }
          }
        } catch {
          // ignore
        }
      }
    })
  }

  async function disconnectAll() {
    stopRecording()
    await bluetooth.disconnectBluetooth()
    socket?.close()
    socket = null
    wsConnected.value = false
  }

  function sendWs(payload: Record<string, unknown>) {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload))
    }
  }

  function sendSampleToServer(sample: EEGSample) {
    sendWs({
      type: 'eeg_data',
      timestamp: sample.timestamp,
      data: sampleToBackendDict(sample),
    })
  }

  function ingestSample(sample: EEGSample, updateChart = true) {
    if (updateChart) pushSample(sample)
    if (isRecording.value && wsConnected.value) {
      sendSampleToServer(sample)
    }
  }

  async function scanDevice() {
    return bluetooth.scanDevices()
  }

  async function connectBluetoothDevice() {
    await bluetooth.connectBluetooth()
  }

  async function connectDevice() {
    await connectWebSocket()
  }

  function startRecording() {
    if (!bluetooth.bluetoothConnected.value) return false
    if (!wsConnected.value) return false

    isRecording.value = true
    history.value = []
    currentSample.value = EMPTY_EEG_SAMPLE()

    sendWs({
      type: 'start_recording',
      name: `EEG_${new Date().toISOString().slice(0, 19).replace(/[T:]/g, '_')}`,
      description: '实时脑电监测记录',
    })

    return true
  }

  function stopRecording() {
    if (!isRecording.value) return
    isRecording.value = false
    sendWs({ type: 'stop_recording' })
  }

  function exportRecords() {
    if (history.value.length === 0) return null

    const header = [
      '时间',
      'Raw',
      'SignalQuality',
      'Attention',
      'Meditation',
      'Delta',
      'Theta',
      'LowAlpha',
      'HighAlpha',
      'LowBeta',
      'HighBeta',
      'LowGamma',
      'HighGamma',
    ]

    const rows = history.value.map((s) => [
      s.timestamp,
      s.raw,
      s.signalQuality,
      s.attention,
      s.meditation,
      s.delta,
      s.theta,
      s.lowAlpha,
      s.highAlpha,
      s.lowBeta,
      s.highBeta,
      s.lowGamma,
      s.highGamma,
    ])

    if (exportFormat.value === 'txt') {
      const content = [header.join('\t'), ...rows.map((row) => row.join('\t'))].join('\n')
      return { blob: new Blob([content], { type: 'text/plain;charset=utf-8' }), ext: 'txt' }
    }

    const csv = [header.join(','), ...rows.map((row) => row.join(','))].join('\n')
    return { blob: new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }), ext: 'csv' }
  }

  onUnmounted(() => {
    disconnectAll()
  })

  return {
    wsConnected,
    deviceConnected,
    isRecording,
    displayMode,
    exportFormat,
    currentRecordingId,
    currentSample,
    history,
    signalStrength,
    useMockDevice,
    deviceAddress: bluetooth.deviceAddress,
    scanDevice,
    connectBluetoothDevice,
    connectDevice,
    disconnectWebSocket: disconnectAll,
    startRecording,
    stopRecording,
    exportRecords,
  }
}
