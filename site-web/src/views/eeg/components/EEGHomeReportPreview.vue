<template>
  <div class="tab-pane-content report-tab-pane">
    <div class="report-shell">
      <div v-if="preview" class="report-toolbar">
        <span class="report-toolbar-accent" aria-hidden="true"></span>
        <div class="report-toolbar-inner">
          <div class="report-toolbar-left">
            <span class="report-toolbar-label">分析报告</span>
            <span class="report-toolbar-title">{{ title }}</span>
            <span v-if="meta" class="report-toolbar-meta">{{ meta }}</span>
          </div>
          <div class="report-toolbar-right">
            <el-tooltip
              placement="bottom-end"
              content="嵌入区为只读沙箱。需更大版面查看时，请使用「弹窗查看」。"
            >
              <span class="report-toolbar-badge">
                只读预览
                <span class="report-toolbar-hint" aria-hidden="true">?</span>
              </span>
            </el-tooltip>
            <div class="report-toolbar-actions">
              <el-button
                v-if="preview.type === 'iframe' || preview.type === 'html'"
                type="primary"
                link
                size="small"
                @click="openReportDialog"
              >弹窗查看</el-button>
              <el-button
                v-if="preview.type === 'iframe'"
                type="primary"
                link
                size="small"
                @click="$emit('refresh-iframe')"
              >刷新</el-button>
              <el-button type="danger" link size="small" @click="$emit('clear')">关闭预览</el-button>
            </div>
          </div>
        </div>
      </div>
      <div class="report-viewport" :class="{ 'report-viewport--filled': !!preview }">
        <div v-if="!preview" class="report-empty-state">
          <span class="report-empty-icon el-icon-document"></span>
          <p class="report-empty-title">暂无报告</p>
          <p class="report-empty-desc">完成「分析数据」或导入文件并分析后，报告将在此处以标准版式展示。</p>
        </div>
        <div v-else-if="preview.type === 'iframe'" class="report-embed">
          <iframe
            :key="frameKey"
            class="report-frame"
            :src="preview.src"
            title="分析报告只读预览"
            sandbox="allow-same-origin allow-scripts allow-popups-to-escape-sandbox allow-downloads"
            referrerpolicy="strict-origin-when-cross-origin"
            loading="lazy"
          />
        </div>
        <div v-else class="report-html-scroll">
          <div
            class="report-content report-content--html"
            @submit.capture.prevent="$emit('readonly-submit', $event)"
            @click.capture="$emit('readonly-click', $event)"
            v-html="preview.html"
          />
        </div>
      </div>
    </div>

    <el-dialog
      v-model="reportDialogVisible"
      :title="title || '分析报告'"
      class="report-view-dialog"
      width="92%"
      align-center
      destroy-on-close
      append-to-body
      @closed="onReportDialogClosed"
    >
      <div class="report-dialog-body">
        <iframe
          v-if="preview && preview.type === 'iframe'"
          :key="'dlg-' + frameKey + '-' + dialogIframeKey"
          class="report-dialog-frame"
          :src="preview.src"
          title="分析报告弹窗预览"
          sandbox="allow-same-origin allow-scripts allow-popups-to-escape-sandbox allow-downloads"
          referrerpolicy="strict-origin-when-cross-origin"
        />
        <div
          v-else-if="preview && preview.type === 'html'"
          class="report-dialog-html"
          @submit.capture.prevent="$emit('readonly-submit', $event)"
          @click.capture="$emit('readonly-click', $event)"
          v-html="preview.html"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'EEGHomeReportPreview',
  props: {
    preview: { type: Object, default: null },
    frameKey: { type: Number, default: 0 },
    title: { type: String, default: '睡眠健康评估结果' },
    meta: { type: String, default: '' },
  },
  emits: ['clear', 'refresh-iframe', 'readonly-submit', 'readonly-click'],
  data() {
    return {
      reportDialogVisible: false,
      dialogIframeKey: 0,
    };
  },
  methods: {
    openReportDialog() {
      if (!this.preview) return;
      this.dialogIframeKey += 1;
      this.reportDialogVisible = true;
    },
    onReportDialogClosed() {
      this.dialogIframeKey = 0;
    },
  },
};
</script>

<style scoped>
.report-tab-pane {
  padding: 0 !important;
  display: flex;
  flex-direction: column;
  background: rgba(15, 23, 42, 0.35);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 10px;
  overflow: hidden;
}
.report-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  overflow: hidden;
}
.report-toolbar {
  position: relative;
  flex-shrink: 0;
  padding: 0;
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.98) 0%, rgba(15, 23, 42, 0.94) 100%);
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset;
}
.report-toolbar-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, #38bdf8, #3b82f6, #6366f1);
  border-radius: 0 2px 2px 0;
  opacity: 0.95;
}
.report-toolbar-inner {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px 16px;
  padding: 12px 16px 12px 18px;
}
.report-toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.report-toolbar-label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #64748b;
}
.report-toolbar-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f1f5f9;
  letter-spacing: 0.01em;
  line-height: 1.35;
  word-break: break-word;
  overflow-wrap: anywhere;
}
.report-toolbar-meta {
  font-size: 0.6875rem;
  color: #94a3b8;
  margin-top: 2px;
  letter-spacing: 0.02em;
  line-height: 1.4;
}
.report-toolbar-right {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px 12px;
  flex-shrink: 0;
}
.report-toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 4px 4px;
}
.report-toolbar-badge {
  flex-shrink: 0;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #64748b;
  padding: 5px 11px;
  border-radius: 6px;
  background: rgba(51, 65, 85, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.18);
  cursor: help;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.report-toolbar-hint {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  font-size: 0.625rem;
  font-weight: 700;
  line-height: 1;
  background: rgba(148, 163, 184, 0.25);
  color: #94a3b8;
}
.report-viewport {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #e8edf3 0%, #f1f5f9 40%, #f8fafc 100%);
  position: relative;
}
.report-viewport--filled {
  background: linear-gradient(180deg, #dce3ec 0%, #eef2f7 50%, #f8fafc 100%);
}
.report-empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 36px 24px;
  margin: 16px;
  max-width: 400px;
  align-self: center;
  width: calc(100% - 32px);
  border: 1px dashed rgba(100, 116, 139, 0.4);
  border-radius: 12px;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.92) 0%, rgba(241, 245, 249, 0.8) 100%);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
}
.report-empty-icon {
  font-size: 2.5rem;
  color: #cbd5e1;
  margin-bottom: 14px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(241, 245, 249, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.9);
}
.report-empty-title {
  margin: 0 0 8px;
  font-size: 1rem;
  font-weight: 600;
  color: #334155;
}
.report-empty-desc {
  margin: 0;
  max-width: 100%;
  font-size: 0.8125rem;
  line-height: 1.55;
  color: #64748b;
}
/* iframe：外圈留白 + 圆角纸张感 */
.report-embed {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 12px 14px 14px;
  box-sizing: border-box;
}
.report-frame {
  flex: 1;
  min-height: 0;
  width: 100%;
  border: none;
  background: #fff;
  display: block;
  border-radius: 10px;
  box-shadow:
    0 0 0 1px rgba(148, 163, 184, 0.25),
    0 8px 28px rgba(15, 23, 42, 0.12);
}
/* 直出 HTML：可滚动外层 + 居中版心 */
.report-html-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 12px 14px 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.report-content--html {
  flex: 0 1 auto;
  width: 100%;
  max-width: min(960px, 100%);
  box-sizing: border-box;
  background: #fff;
  color: #1e293b;
  font-size: 0.875rem;
  line-height: 1.65;
  padding: 20px 22px 28px;
  border-radius: 10px;
  box-shadow:
    0 0 0 1px rgba(148, 163, 184, 0.2),
    0 10px 36px rgba(15, 23, 42, 0.1);
}
/* 后端报告常见结构（不影响 iframe 内样式） */
.report-content--html :deep(.report-container) {
  max-width: 100%;
}
.report-content--html :deep(.section_compant) {
  margin-bottom: 1.25rem;
}
.report-content--html :deep(.section_compant:last-child) {
  margin-bottom: 0;
}
.report-content--html :deep(h1),
.report-content--html :deep(h2),
.report-content--html :deep(h3),
.report-content--html :deep(h4) {
  line-height: 1.35;
  margin-top: 0.75em;
  margin-bottom: 0.5em;
}
.report-content--html :deep(h1:first-child),
.report-content--html :deep(h2:first-child),
.report-content--html :deep(h3:first-child) {
  margin-top: 0;
}
.report-content--html :deep(p) {
  margin: 0.65em 0;
}
.report-content--html :deep(table) {
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
  margin: 1rem 0;
  table-layout: auto;
}
.report-content--html :deep(th),
.report-content--html :deep(td) {
  padding: 10px 12px;
  text-align: left;
  border: 1px solid #e2e8f0;
  vertical-align: top;
}
.report-content--html :deep(th) {
  background: #f1f5f9;
  font-weight: 600;
  color: #0f172a;
}
.report-content--html :deep(img),
.report-content--html :deep(svg) {
  max-width: 100%;
  height: auto;
}
.report-content--html :deep(pre),
.report-content--html :deep(code) {
  font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
  font-size: 0.8125rem;
}
.report-content--html :deep(pre) {
  overflow-x: auto;
  padding: 12px 14px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
@media (max-width: 520px) {
  .report-toolbar-inner {
    grid-template-columns: 1fr;
    align-items: stretch;
  }
  .report-toolbar-right {
    justify-content: space-between;
    border-top: 1px solid rgba(148, 163, 184, 0.15);
    padding-top: 10px;
    margin-top: 4px;
  }
  .report-toolbar-actions {
    justify-content: flex-start;
  }
  .report-content--html {
    padding: 14px 14px 20px;
  }
}
</style>

<!-- 弹窗 teleport 到 body，单独块保证样式命中 -->
<style lang="css">
.el-dialog.report-view-dialog {
  max-width: min(1120px, 96vw);
}
.el-dialog.report-view-dialog .el-dialog__body {
  padding: 10px 16px 18px;
  box-sizing: border-box;
}
.report-dialog-body {
  height: min(82vh, 900px);
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.report-dialog-frame {
  flex: 1;
  min-height: 0;
  width: 100%;
  border: none;
  border-radius: 8px;
  background: #f8fafc;
  box-shadow: inset 0 0 0 1px #e2e8f0;
}
.report-dialog-html {
  flex: 1;
  min-height: 0;
  width: 100%;
  overflow: auto;
  border-radius: 8px;
  background: #fff;
  padding: 12px;
  box-sizing: border-box;
  color: #1e293b;
  font-size: 0.875rem;
  line-height: 1.6;
}
</style>
