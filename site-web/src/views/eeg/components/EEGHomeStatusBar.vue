<template>
  <div class="status-bar">
    <span class="status-item status-item--ok">
      <i class="el-icon-circle-check status-dot"></i>
      <span class="status-text">后端: 已连接</span>
    </span>
    <span class="status-item" :class="isConnected ? 'status-item--ok' : 'status-item--bad'">
      <i :class="isConnected ? 'el-icon-circle-check status-dot' : 'el-icon-circle-cross status-dot'"></i>
      <span class="status-text">设备: {{ deviceStatus }}</span>
    </span>
    <span class="status-item" :class="isRecording ? 'status-item--ok' : 'status-item--bad'">
      <i :class="isRecording ? 'el-icon-circle-check status-dot' : 'el-icon-circle-cross status-dot'"></i>
      <span class="status-text">数据: {{ isRecording ? '正在记录' : '未连接' }}</span>
    </span>
    <span class="status-item status-item--bad">
      <i class="el-icon-circle-cross status-dot"></i>
      <span class="status-text">API: 未连接</span>
    </span>
  </div>
</template>

<script>
export default {
  name: 'EEGHomeStatusBar',
  props: {
    isConnected: { type: Boolean, required: true },
    isRecording: { type: Boolean, required: true },
    deviceStatus: { type: String, required: true },
  },
};
</script>

<style scoped>
.status-bar {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 0.8125rem;
}
.status-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: #cbd5e1;
  font-size: 0.8125rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.2);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.status-item--ok {
  border-color: rgba(34, 197, 94, 0.28);
  box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.06), 0 4px 16px rgba(15, 23, 42, 0.25);
}
.status-item--bad {
  border-color: rgba(239, 68, 68, 0.22);
}
.status-item .status-dot {
  font-size: 1rem;
  flex-shrink: 0;
}
.status-item--ok .status-dot.el-icon-circle-check {
  color: #4ade80;
  animation: statusPulse 2.2s ease-in-out infinite;
  filter: drop-shadow(0 0 6px rgba(74, 222, 128, 0.35));
}
.status-item--bad .status-dot.el-icon-circle-cross {
  color: #f87171;
}
.status-text {
  letter-spacing: 0.02em;
}
@keyframes statusPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.72; }
}
</style>
