<template>
  <div class="eeg-monitor" :style="bgStyle">
    <header class="monitor-header">
      <div class="header-left">
        <router-link to="/" class="back-link">
          <el-icon><ArrowLeft /></el-icon>
          返回首页
        </router-link>
        <h1 class="page-title">实时脑电监测</h1>
        <EEGPageNav current="monitor" />
      </div>
      <div class="header-status">
        <span class="status-item">
          <span class="status-dot" :class="{ online: deviceConnected }" />
          设备连接
        </span>
        <el-button size="small" @click="handleScan" :loading="scanning">
          扫描设备
        </el-button>
        <el-button
          size="small"
          :type="wsConnected ? 'success' : 'primary'"
          plain
          @click="handleToggleConnection"
        >
          {{ wsConnected ? '已连接服务' : '连接服务' }}
        </el-button>
        <div class="signal-indicator" title="信号强度">
          <span
            v-for="i in 4"
            :key="i"
            class="signal-bar"
            :class="{ active: i <= signalStrength }"
          />
        </div>
      </div>
    </header>

    <div class="monitor-body">
      <main class="monitor-main">
        <EEGMonitorCharts
          :history="history"
          :current="currentSample"
          :display-mode="displayMode"
        />
      </main>
      <EEGMonitorSidebar
        :sample="currentSample"
        v-model:display-mode="displayMode"
        v-model:export-format="exportFormat"
        :is-recording="isRecording"
        :device-connected="deviceConnected"
        :has-data="history.length > 0"
        @start="handleStart"
        @stop="handleStop"
        @export="handleExport"
      />
    </div>

    <footer class="monitor-footer">
      <span v-if="currentRecordingId">记录 ID: {{ currentRecordingId }}</span>
      <span v-if="useMockDevice" class="mock-tag">蓝牙未连接</span>
      <span>{{ statusText }}</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import EEGMonitorCharts from './components/EEGMonitorCharts.vue'
import EEGMonitorSidebar from './components/EEGMonitorSidebar.vue'
import EEGPageNav from '../components/EEGPageNav.vue'
import { useEEGMonitor } from '@/composables/useEEGMonitor'

const bgStyle = {
  backgroundImage:
    'linear-gradient(to right, rgba(0, 0, 40, 0.72), rgba(15, 23, 42, 0.68)), url("/background.jpg")',
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  backgroundRepeat: 'no-repeat',
  backgroundAttachment: 'fixed',
}

const scanning = ref(false)

const {
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
  connectBluetoothDevice,
  startRecording,
  stopRecording,
  exportRecords,
} = useEEGMonitor()

const statusText = computed(() => {
  if (isRecording.value) return '正在采集数据...'
  if (deviceConnected.value && wsConnected.value) return '就绪，点击开始记录'
  if (wsConnected.value) return '服务已连接，请扫描并连接蓝牙设备'
  return '请先连接服务，再扫描蓝牙设备'
})

async function handleScan() {
  scanning.value = true
  try {
    const name = await scanDevice()
    await connectBluetoothDevice()
    if (!wsConnected.value) {
      await connectDevice()
    }
    ElMessage.success(`蓝牙设备已连接: ${name}`)
  } catch (err) {
    ElMessage.error(`连接失败: ${(err as Error).message}`)
  } finally {
    scanning.value = false
  }
}

async function handleToggleConnection() {
  if (wsConnected.value) {
    disconnectWebSocket()
    ElMessage.info('已断开服务连接')
    return
  }
  try {
    await connectDevice()
    ElMessage.success('服务连接成功')
  } catch (err) {
    ElMessage.error(`连接失败: ${(err as Error).message}`)
  }
}

function handleStart() {
  if (!deviceConnected.value) {
    ElMessage.warning('请先扫描设备')
    return
  }
  if (!wsConnected.value) {
    ElMessage.warning('请先连接服务')
    return
  }
  if (startRecording()) {
    ElMessage.success('开始记录')
  }
}

function handleStop() {
  stopRecording()
  ElMessage.info('已停止记录')
}

function handleExport() {
  const result = exportRecords()
  if (!result) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const url = URL.createObjectURL(result.blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `eeg_record_${Date.now()}.${result.ext}`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}
</script>

<style scoped>
.eeg-monitor {
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  color: #e2e8f0;
  font-family: 'Microsoft YaHei', 'Segoe UI', system-ui, sans-serif;
}

.eeg-monitor::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% 0%, rgba(59, 130, 246, 0.12), transparent 55%),
    radial-gradient(ellipse 60% 40% at 100% 100%, rgba(14, 165, 233, 0.08), transparent 50%);
}

.eeg-monitor > * {
  position: relative;
  z-index: 1;
}

.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: rgba(15, 23, 42, 0.55);
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.35);
  backdrop-filter: blur(14px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #94a3b8;
  text-decoration: none;
  font-size: 13px;
}

.back-link:hover {
  color: #7dd3fc;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #f1f5f9;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.status-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #cbd5e1;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #64748b;
}

.status-dot.online {
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.25);
}

.signal-indicator {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 18px;
  margin-left: 8px;
}

.signal-bar {
  width: 4px;
  background: rgba(148, 163, 184, 0.45);
  border-radius: 1px;
}

.signal-bar:nth-child(1) { height: 5px; }
.signal-bar:nth-child(2) { height: 9px; }
.signal-bar:nth-child(3) { height: 13px; }
.signal-bar:nth-child(4) { height: 17px; }

.signal-bar.active {
  background: #4ade80;
}

.monitor-body {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px 20px;
  min-height: 0;
}

.monitor-main {
  flex: 1;
  min-width: 0;
  min-height: calc(100vh - 140px);
}

.monitor-footer {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 10px 20px;
  font-size: 12px;
  color: #94a3b8;
  background: rgba(15, 23, 42, 0.55);
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  backdrop-filter: blur(14px);
}

.mock-tag {
  color: #fbbf24;
  font-weight: 500;
}

@media (max-width: 960px) {
  .monitor-body {
    flex-direction: column;
  }

  .monitor-main {
    min-height: 520px;
  }

  .header-left {
    gap: 10px;
  }
}
</style>
