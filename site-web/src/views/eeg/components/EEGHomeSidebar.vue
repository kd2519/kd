<template>
  <aside class="sidebar">
    <div class="card sidebar-card">
      <h3><span class="card-icon"><i class="el-icon-mobile-phone"></i></span> 设备连接</h3>
      <div class="form-group">
        <label>蓝牙设备地址</label>
        <el-input
          class="custom-input"
          :model-value="deviceAddress"
          placeholder="例如: JDY-18"
          @update:model-value="$emit('update:deviceAddress', $event)"
        />
        <el-button id="scann_button" type="primary" size="small" @click="$emit('scan-devices')">扫描</el-button>
      </div>
      <div class="status-info">
        <p>
          连接状态:
          <span :class="isConnected ? 'status-value status-value--ok' : 'status-value status-value--bad'">{{ deviceStatus }}</span>
        </p>
        <p>信号质量: <span class="status-value">-- /200</span></p>
      </div>
    </div>

    <div class="card sidebar-card">
      <h3><span class="card-icon"><i class="el-icon-document"></i></span> 数据保存</h3>
      <div class="data-status">
        <p>{{ dataStatus }}</p>
      </div>
    </div>

    <div class="card sidebar-card">
      <h3><span class="card-icon"><i class="el-icon-setting"></i></span> 分析配置</h3>
      <div class="form-group">
        <label>API密钥</label>
        <el-input
          class="custom-input"
          :model-value="apiKey"
          placeholder="请输入API密钥"
          @update:model-value="$emit('update:apiKey', $event)"
        />
      </div>
      <el-button type="primary" size="small" @click="$emit('test-api')">测试API</el-button>
      <div class="history-file">
        <p>历史数据文件</p>
        <p class="history-file-empty">暂无历史数据</p>
      </div>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'EEGHomeSidebar',
  props: {
    deviceAddress: { type: String, required: true },
    apiKey: { type: String, required: true },
    isConnected: { type: Boolean, required: true },
    deviceStatus: { type: String, required: true },
    dataStatus: { type: String, required: true },
  },
  emits: ['update:deviceAddress', 'update:apiKey', 'scan-devices', 'test-api'],
};
</script>

<style scoped>
.custom-input {
  margin-top: 5px;
}
.custom-input :deep(.el-input__wrapper) {
  background-color: #ffffff !important;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.45) inset !important;
  border-radius: 8px !important;
  transition: box-shadow 0.2s ease;
}
.custom-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(100, 116, 139, 0.55) inset !important;
}
.custom-input :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px rgba(59, 130, 246, 0.65) inset,
    0 0 0 3px rgba(59, 130, 246, 0.12) !important;
}
.custom-input :deep(.el-input__inner) {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #1e293b !important;
}
.custom-input :deep(.el-input__inner::placeholder) {
  color: #94a3b8;
}
.el-button {
  border-radius: 6px;
  padding: 10px 18px;
  transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  font-size: 0.9375rem;
  font-weight: 500;
}
.el-button:hover {
  transform: none;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.35);
}
#scann_button {
  margin-top: 8px;
  font-size: 0.875rem;
}
.sidebar {
  width: 340px;
  flex-shrink: 0;
  min-height: 700px;
  height: 700px;
  background: rgba(15, 23, 42, 0.38);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 14px;
  padding: 16px 14px;
  box-shadow:
    0 4px 24px rgba(15, 23, 42, 0.32),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(16px);
  overflow-y: auto;
}
.sidebar::-webkit-scrollbar {
  width: 6px;
}
.sidebar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.25);
  border-radius: 999px;
}
.card {
  margin-bottom: 0;
  border-bottom: none;
  padding-bottom: 0;
}
.sidebar-card {
  margin-bottom: 14px;
  padding: 14px 14px 16px;
  border-radius: 12px;
  background: rgba(30, 41, 59, 0.42);
  border: 1px solid rgba(148, 163, 184, 0.12);
  box-shadow: 0 2px 14px rgba(15, 23, 42, 0.2);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.sidebar-card:hover {
  border-color: rgba(148, 163, 184, 0.22);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.28);
}
.sidebar-card:last-child {
  margin-bottom: 0;
}
.card h3 {
  margin: 0 0 12px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #e2e8f0;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 10px;
}
.card-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(145deg, rgba(59, 130, 246, 0.25), rgba(15, 23, 42, 0.5));
  border: 1px solid rgba(148, 163, 184, 0.15);
  color: #93c5fd;
  font-size: 0.875rem;
}
.form-group {
  margin: 10px 0;
}
.form-group label {
  font-size: 0.8125rem;
  color: #94a3b8;
}
.status-info {
  margin-top: 10px;
  font-size: 0.8125rem;
  color: #94a3b8;
}
.data-status {
  padding: 10px 12px;
  background: rgba(30, 41, 59, 0.6);
  border-radius: 6px;
  margin-top: 10px;
  color: #cbd5e1;
  font-size: 0.8125rem;
  border: 1px solid rgba(148, 163, 184, 0.15);
}
.history-file {
  margin-top: 10px;
  font-size: 0.8125rem;
  color: #94a3b8;
}
.status-value {
  font-weight: 500;
  color: #94a3b8;
}
.status-value--ok {
  color: #4ade80;
}
.status-value--bad {
  color: #f87171;
}
.history-file-empty {
  color: #7dd3fc;
  margin-top: 4px;
}
</style>
