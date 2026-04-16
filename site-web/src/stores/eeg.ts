import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useEegStore = defineStore('eeg', () => {
  const isRecording = ref(false)
  const deviceStatus = ref('未连接')
  const signalQuality = ref('-- /200')
  const dataStatus = ref('未保存数据')
  const logContent = ref('')
  const reportContent = ref('')
  const activeTab = ref('realtime')
  const apiKey = ref('51e09aa5-d2dd-41ab-bf91-51ef798844e7')
  const deviceAddress = ref('')
  const isConnected = ref(false) // WebSocket 连接状态

  const addLog = (msg: string) => {
    logContent.value += `[${new Date().toLocaleTimeString()}] ${msg}\n`
  }

  const clearLog = () => {
    logContent.value = ''
  }

  const setReport = (contentOrUrl: string, isIframe = true) => {
    if (isIframe) {
      reportContent.value = `<iframe src="${contentOrUrl}" style="width:100%; height:100%; border:none;"></iframe>`
    } else {
      reportContent.value = contentOrUrl
    }
    activeTab.value = 'report'
  }

  return {
    isRecording, deviceStatus, signalQuality, dataStatus, logContent, reportContent, activeTab, apiKey, deviceAddress, isConnected,
    addLog, clearLog, setReport
  }
})