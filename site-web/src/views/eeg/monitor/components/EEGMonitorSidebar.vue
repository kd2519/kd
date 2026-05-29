<template>
  <aside class="monitor-sidebar">
    <div class="sidebar-section">
      <div class="section-title">实时数据</div>
      <el-table :data="tableRows" size="small" stripe class="data-table" max-height="320">
        <el-table-column prop="name" label="名称" width="110" />
        <el-table-column prop="value" label="数值" align="right" />
      </el-table>
    </div>

    <div class="sidebar-section">
      <div class="section-title">显示模式</div>
      <el-radio-group :model-value="displayMode" @update:model-value="$emit('update:displayMode', $event)">
        <el-radio value="raw">Raw原始脑电</el-radio>
        <el-radio value="eeg">EEG脑电</el-radio>
      </el-radio-group>
    </div>

    <div class="sidebar-section">
      <div class="section-title">导出格式</div>
      <el-radio-group :model-value="exportFormat" @update:model-value="$emit('update:exportFormat', $event)">
        <el-radio value="xlsx">Excel格式</el-radio>
        <el-radio value="txt">TXT</el-radio>
      </el-radio-group>
    </div>

    <div class="sidebar-actions">
      <el-button
        class="action-btn"
        :type="isRecording ? 'default' : 'primary'"
        :disabled="!deviceConnected || isRecording"
        @click="$emit('start')"
      >
        <el-icon><VideoPlay /></el-icon>
        开始
      </el-button>
      <el-button
        class="action-btn stop-btn"
        type="danger"
        :disabled="!isRecording"
        @click="$emit('stop')"
      >
        <el-icon><VideoPause /></el-icon>
        停止
      </el-button>
    </div>

    <el-button type="primary" class="export-btn" :disabled="!hasData" @click="$emit('export')">
      <el-icon><Download /></el-icon>
      导出记录
    </el-button>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { VideoPlay, VideoPause, Download } from '@element-plus/icons-vue'
import type { EEGExportFormat, EEGSample, EEGDisplayMode } from '@/types/eeg'

const props = defineProps<{
  sample: EEGSample
  displayMode: EEGDisplayMode
  exportFormat: EEGExportFormat
  isRecording: boolean
  deviceConnected: boolean
  hasData: boolean
}>()

defineEmits<{
  start: []
  stop: []
  export: []
  'update:displayMode': [value: EEGDisplayMode]
  'update:exportFormat': [value: EEGExportFormat]
}>()

const tableRows = computed(() => {
  const s = props.sample
  return [
    { name: 'Raw', value: s.raw },
    { name: 'Signal', value: s.signalQuality },
    { name: 'Attention', value: s.attention },
    { name: 'Meditation', value: s.meditation },
    { name: 'Delta', value: s.delta },
    { name: 'Theta', value: s.theta },
    { name: 'LowAlpha', value: s.lowAlpha },
    { name: 'HighAlpha', value: s.highAlpha },
    { name: 'LowBeta', value: s.lowBeta },
    { name: 'HighBeta', value: s.highBeta },
    { name: 'LowGamma', value: s.lowGamma },
    { name: 'MiddleGamma', value: s.highGamma },
  ]
})
</script>

<style scoped>
.monitor-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.35);
  backdrop-filter: blur(12px);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.data-table {
  width: 100%;
  font-size: 12px;
}

.data-table :deep(.el-table__header th) {
  background: #f1f5f9;
  color: #64748b;
  font-weight: 600;
}

.data-table :deep(.el-table__body tr) {
  background: #f8fafc;
}

.data-table :deep(.el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #f1f5f9;
}

.sidebar-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
}

.stop-btn {
  min-width: 88px;
}

.export-btn {
  width: 100%;
  height: 40px;
  margin-top: auto;
}

.monitor-sidebar :deep(.el-radio) {
  display: flex;
  margin-right: 0;
  margin-bottom: 6px;
  color: #475569;
  font-size: 13px;
}
</style>
