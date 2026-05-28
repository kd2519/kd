import { ref, computed, onUnmounted } from 'vue'
import type { EEGDisplayMode, EEGExportFormat, EEGSample } from '@/types/eeg'
import { EMPTY_EEG_SAMPLE } from '@/types/eeg'
import { formatEEGDataForServer, parseEEGDataPayload } from '@/utils/eegParser'

const MAX_HISTORY = 60
const SAMPLE_INTERVAL_MS = 1000

function buildWsUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/eeg/`
}

function generateMockSample(tick: number): EEGSample {
  const wave = Math.sin(tick / 4) * 900 + Math.sin(tick / 1.7) * 400
  const noise = (Math.random() - 0.5) * 200
  const attention = Math.max(0, Math.min(100, 45 + Math.sin(tick / 6) * 35 + Math.random() * 10))
  const meditation = Math.max(0, Math.min(100, 40 + Math.cos(tick / 5) * 30 + Math.random() * 10))
  const base = 3000 + Math.sin(tick / 3) * 1500

  return {
    timestamp: new Date().toISOString(),
    raw: Math.round(wave + noise),
    signalQuality: Math.round(150 + Math.random() * 30),
    attention: Math.round(attention),
    meditation: Math.round(meditation),
    delta: Math.round(base * 0.9 + Math.random() * 400),
    theta: Math.round(base * 0.7 + Math.random() * 300),
    lowAlpha: Math.round(base * 0.55 + Math.random() * 250),
    highAlpha: Math.round(base * 0.5 + Math.random() * 200),
    lowBeta: Math.round(base * 0.85 + Math.random() * 350),
    highBeta: Math.round(base * 0.75 + Math.random() * 300),
    lowGamma: Math.round(base * 0.35 + Math.random() * 150),
    highGamma: Math.round(base * 0.3 + Math.random() * 120),
  }
}

export function useEEGMonitor() {
  const wsConnected = ref(false)
  const deviceConnected = ref(false)
  const isRecording = ref(false)
  const displayMode = ref<EEGDisplayMode>('raw')
  const exportFormat = ref<EEGExportFormat>('txt')
  const currentRecordingId = ref<string | null>(null)
  const currentSample = ref<EEGSample>(EMPTY_EEG_SAMPLE())
  const history = ref<EEGSample[]>([])
  const useMockDevice = ref(true)

  let socket: WebSocket | null = null
  let sampleTimer: ReturnType<typeof setInterval> | null = null
  let mockTick = 0

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
          // ignore malformed messages
        }
      }
    })
  }

  function disconnectWebSocket() {
    stopRecording()
    socket?.close()
    socket = null
    wsConnected.value = false
    deviceConnected.value = false
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
      data: formatEEGDataForServer(sample),
    })
  }

  function ingestSample(sample: EEGSample) {
    pushSample(sample)
    if (isRecording.value && wsConnected.value) {
      sendSampleToServer(sample)
    }
  }

  function startSampleLoop() {
    stopSampleLoop()
    sampleTimer = setInterval(() => {
      mockTick += 1
      ingestSample(generateMockSample(mockTick))
    }, SAMPLE_INTERVAL_MS)
  }

  function stopSampleLoop() {
    if (sampleTimer) {
      clearInterval(sampleTimer)
      sampleTimer = null
    }
  }

  async function scanDevice() {
    if (navigator.bluetooth) {
      try {
        const device = await navigator.bluetooth.requestDevice({
          acceptAllDevices: true,
          optionalServices: ['battery_service', 'generic_access', 'device_information'],
        })
        await device.gatt?.connect()
        useMockDevice.value = false
        deviceConnected.value = true
        return device.name || '蓝牙设备'
      } catch (err) {
        if ((err as Error).name !== 'NotFoundError') {
          throw err
        }
      }
    }

    useMockDevice.value = true
    deviceConnected.value = true
    return '模拟设备'
  }

  async function connectDevice() {
    await connectWebSocket()
    deviceConnected.value = true
  }

  function startRecording() {
    if (!deviceConnected.value) return false
    if (!wsConnected.value) return false

    isRecording.value = true
    history.value = []
    mockTick = 0
    currentSample.value = EMPTY_EEG_SAMPLE()

    sendWs({
      type: 'start_recording',
      name: `EEG_${new Date().toISOString().slice(0, 19).replace(/[T:]/g, '_')}`,
      description: '实时脑电监测记录',
    })

    startSampleLoop()
    return true
  }

  function stopRecording() {
    if (!isRecording.value) return
    isRecording.value = false
    stopSampleLoop()
    sendWs({ type: 'stop_recording' })
  }

  function ingestExternalSample(data: string | Record<string, number>) {
    const sample = parseEEGDataPayload(data)
    sample.timestamp = new Date().toISOString()
    ingestSample(sample)
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
      const content = [
        header.join('\t'),
        ...rows.map((row) => row.join('\t')),
      ].join('\n')
      return { blob: new Blob([content], { type: 'text/plain;charset=utf-8' }), ext: 'txt' }
    }

    const csv = [
      header.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n')
    return { blob: new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }), ext: 'csv' }
  }

  onUnmounted(() => {
    disconnectWebSocket()
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
    connectDevice,
    disconnectWebSocket,
    scanDevice,
    startRecording,
    stopRecording,
    ingestExternalSample,
    exportRecords,
  }
}
