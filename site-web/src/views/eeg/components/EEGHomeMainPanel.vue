<template>
  <div class="main-panel">
    <el-tabs :model-value="activeTab" @update:model-value="$emit('update:activeTab', $event)">
      <el-tab-pane label="实时数据" name="realtime">
        <div class="tab-content-container">
          <div class="tab-pane-content">
            <EEGHomeRealtimeEmpty />
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="分析报告" name="report">
        <div class="tab-content-container">
          <EEGHomeReportPreview
            :preview="reportPreview"
            :frame-key="reportFrameKey"
            :title="reportPreviewTitle"
            :meta="reportPreviewMeta"
            @clear="$emit('report-clear')"
            @refresh-iframe="$emit('report-refresh-iframe')"
            @readonly-submit="$emit('report-readonly-submit', $event)"
            @readonly-click="$emit('report-readonly-click', $event)"
          />
        </div>
      </el-tab-pane>
      <el-tab-pane label="系统日志" name="log">
        <div class="tab-content-container">
          <div class="tab-pane-content">
            <div class="placeholder" v-text="logContent || '系统日志将显示在此处'"></div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
    <div class="clear-log-btn">
      <el-button type="text" @click="$emit('clear-log')">清空日志</el-button>
    </div>
  </div>
</template>

<script>
import EEGHomeRealtimeEmpty from './EEGHomeRealtimeEmpty.vue';
import EEGHomeReportPreview from './EEGHomeReportPreview.vue';

export default {
  name: 'EEGHomeMainPanel',
  components: {
    EEGHomeRealtimeEmpty,
    EEGHomeReportPreview,
  },
  props: {
    activeTab: { type: String, required: true },
    logContent: { type: String, required: true },
    reportPreview: { type: Object, default: null },
    reportFrameKey: { type: Number, default: 0 },
    reportPreviewTitle: { type: String, default: '' },
    reportPreviewMeta: { type: String, default: '' },
  },
  emits: [
    'update:activeTab',
    'clear-log',
    'report-clear',
    'report-refresh-iframe',
    'report-readonly-submit',
    'report-readonly-click',
  ],
};
</script>

<style scoped>
.main-panel {
  flex: 1;
  min-width: 0;
  background: rgba(15, 23, 42, 0.36);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 14px;
  padding: 14px 18px 12px;
  box-shadow:
    0 4px 28px rgba(15, 23, 42, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(14px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.main-panel :deep(.el-tabs__header) {
  margin-bottom: 12px;
}
.main-panel :deep(.el-tabs) {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.main-panel :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.main-panel :deep(.el-tab-pane) {
  flex: 1;
  overflow-y: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.main-panel :deep(.el-tabs__item) {
  color: #94a3b8 !important;
  font-weight: 500;
  font-size: 0.875rem;
}
.main-panel :deep(.el-tabs__item.is-active) {
  color: #e8eef7 !important;
}
.main-panel :deep(.el-tabs__active-bar) {
  background-color: #3b82f6;
  height: 2px;
}
.main-panel :deep(.el-tabs__nav-wrap::after) {
  background-color: rgba(148, 163, 184, 0.2);
}
.main-panel :deep(.el-tabs__nav) {
  border-bottom: none;
}
.tab-content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 400px;
  max-height: 600px;
  height: 500px;
}
.tab-pane-content {
  flex: 1;
  overflow: hidden;
  padding: 16px;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.25);
}
.placeholder {
  height: 100%;
  overflow-y: auto;
  text-align: left;
  white-space: pre-wrap;
  color: #cbd5e1;
  font-family: ui-monospace, 'Cascadia Code', 'Consolas', monospace;
  font-size: 0.8125rem;
  line-height: 1.55;
  background: rgba(30, 41, 59, 0.45);
  padding: 12px 14px;
  border-radius: 6px;
  flex: 1;
  border: 1px solid rgba(148, 163, 184, 0.12);
}
.clear-log-btn {
  text-align: right;
  margin-top: 8px;
}
.clear-log-btn :deep(.el-button--text) {
  color: #94a3b8;
}
.clear-log-btn :deep(.el-button--text:hover) {
  color: #e8eef7;
}
</style>
