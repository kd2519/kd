<template>
  <div class="action-toolbar">
    <div class="button-group">
      <el-button type="primary" @click="$emit('connect-device')">连接设备</el-button>
      <el-button type="success" @click="$emit('start-recording')">
        {{ isRecording ? '停止记录' : '开始记录' }}
      </el-button>
      <el-button type="warning" @click="$emit('analyze-data')">分析数据</el-button>
      <el-button type="info" @click="$emit('import-data')">导入数据</el-button>
      <el-button type="text" class="btn-link-ghost" @click="$emit('test-backend')">测试后端连接</el-button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EEGHomeActionToolbar',
  props: {
    isRecording: { type: Boolean, required: true },
  },
  emits: ['connect-device', 'start-recording', 'analyze-data', 'import-data', 'test-backend'],
};
</script>

<style scoped>
.action-toolbar {
  max-width: 920px;
  margin: 0 auto 24px;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.42);
  border: 1px solid rgba(148, 163, 184, 0.16);
  backdrop-filter: blur(14px);
  box-shadow: 0 8px 32px rgba(15, 23, 42, 0.28);
}
.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  align-items: center;
}
.button-group :deep(.el-button--text) {
  margin-left: 4px;
}
.btn-link-ghost {
  opacity: 0.92;
}
.btn-link-ghost:hover {
  opacity: 1;
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
</style>
