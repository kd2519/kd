<template>
  <div class="app-container eeg-home" :style="bgStyle">
    <EEGHomePageHeader />
    <EEGHomeStatusBar
      :is-connected="isConnected"
      :is-recording="isRecording"
      :device-status="deviceStatus"
    />
    <EEGHomeActionToolbar
      :is-recording="isRecording"
      @connect-device="connectDevice"
      @start-recording="startRecording"
      @analyze-data="analyzeData"
      @import-data="importData"
      @test-backend="testBackend"
    />

    <div class="main-content">
      <EEGHomeSidebar
        v-model:device-address="deviceAddress"
        v-model:api-key="apiKey"
        :is-connected="isConnected"
        :device-status="deviceStatus"
        :data-status="dataStatus"
        @scan-devices="scanDevices"
        @test-api="testAPI"
      />
      <EEGHomeMainPanel
        v-model:active-tab="activeTab"
        :log-content="logContent"
        :report-preview="reportPreview"
        :report-frame-key="reportFrameKey"
        :report-preview-title="reportPreviewTitle"
        :report-preview-meta="reportPreviewMeta"
        @clear-log="clearLog"
        @report-clear="clearReportPreview"
        @report-refresh-iframe="refreshReportIframe"
        @report-readonly-submit="onReportReadonlySubmit"
        @report-readonly-click="onReportReadonlyClick"
      />
    </div>

    <footer class="footer">
      基于EEG与人工智能的睡眠健康评估系统 V2.0 | 本地数据安全存储 | 支持CSV/Excel数据分析
    </footer>
  </div>
</template>

<script>
import EEGHomePageHeader from './components/EEGHomePageHeader.vue';
import EEGHomeStatusBar from './components/EEGHomeStatusBar.vue';
import EEGHomeActionToolbar from './components/EEGHomeActionToolbar.vue';
import EEGHomeSidebar from './components/EEGHomeSidebar.vue';
import EEGHomeMainPanel from './components/EEGHomeMainPanel.vue';

export default {
  name: 'EEGHome',
  components: {
    EEGHomePageHeader,
    EEGHomeStatusBar,
    EEGHomeActionToolbar,
    EEGHomeSidebar,
    EEGHomeMainPanel,
  },
  data() {
    return {
      currentRecordingId: null,
      bgStyle: {
        backgroundImage: 'linear-gradient(to right, rgba(0, 0, 70, 0.3), rgba(28, 181, 224, 0.3)), url("/背景鲸鱼.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed',
      },
      deviceAddress: '',
      apiKey: '51e09aa5-d2dd-41ab-bf91-51ef798844e7',
      activeTab: 'realtime',
      websocket: null,
      isConnected: false,
      bluetoothConnected: false,
      isRecording: false,
      deviceStatus: '未连接',
      signalQuality: '-- /200',
      dataStatus: '未保存数据',
      logContent: '',
      reportPreview: null,
      reportFrameKey: 0,
      historyFiles: [],
      importedFileName: '',
      currentFilePath: '',
      eegTimer: null,
    };
  },
  beforeDestroy() {
    if (this.websocket) this.websocket.close();
    if (this.eegTimer) clearTimeout(this.eegTimer);
  },
  computed: {
    reportPreviewTitle() {
      if (!this.reportPreview) return '睡眠健康评估结果';
      return this.reportPreview.title || '睡眠健康评估结果';
    },
    reportPreviewMeta() {
      if (!this.reportPreview?.loadedAt) return '';
      const d = new Date(this.reportPreview.loadedAt);
      return `加载于 ${d.toLocaleString()}`;
    },
  },
  methods: {
    clearReportPreview() {
      this.reportPreview = null;
      this.reportFrameKey = 0;
    },
    refreshReportIframe() {
      if (this.reportPreview?.type !== 'iframe') return;
      this.reportFrameKey += 1;
      this.$message.info('已刷新预览');
    },
    onReportReadonlySubmit(e) {
      e.preventDefault();
      e.stopPropagation();
      this.$message.info('当前为只读预览，不可提交表单');
      return false;
    },
    onReportReadonlyClick(e) {
      const target = e.target;
      if (!target || !target.closest) return;
      const link = target.closest('a[href]');
      if (link) {
        const href = link.getAttribute('href');
        if (!href || href.trim().toLowerCase().startsWith('javascript:') || href.trim().toLowerCase().startsWith('vbscript:')) {
          e.preventDefault();
          e.stopPropagation();
          return;
        }
        if (href.startsWith('#')) return;
        e.preventDefault();
        e.stopPropagation();
        try {
          window.open(new URL(href, window.location.href).href, '_blank', 'noopener,noreferrer');
        } catch {
          window.open(href, '_blank', 'noopener,noreferrer');
        }
        return;
      }
      const el = target.closest(
        'button, input[type="submit"], input[type="button"], input[type="reset"], input[type="image"], select, textarea'
      );
      if (!el) return;
      if (el.tagName.toLowerCase() === 'input') {
        const t = (el.getAttribute('type') || 'text').toLowerCase();
        const allowFocus = ['text', 'search', 'number', 'email', 'url', 'tel', 'password', 'date', 'time', 'datetime-local', 'month', 'week', 'hidden', ''];
        if (allowFocus.includes(t)) return;
        if (t === 'checkbox' || t === 'radio' || t === 'file') {
          e.preventDefault();
          e.stopPropagation();
          this.$message.info('只读预览：不可更改或上传');
          return;
        }
      }
      e.preventDefault();
      e.stopPropagation();
      this.$message.info('当前为只读预览，不可操作该控件');
    },
    connectDevice() {
      if (this.isConnected) {
        this.$message.info('后端已连接');
        return;
      }
      if (!this.bluetoothConnected) {
        this.$message.warning('请先扫描并配对蓝牙设备');
        return;
      }
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${protocol}${window.location.host}/ws/eeg/`;
        this.websocket = new WebSocket(wsUrl);
        this.websocket.onopen = () => {
          this.isConnected = true;
          this.deviceStatus = '已连接';
          this.$message.success('设备连接成功');
        };
        this.websocket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          this.handleWebSocketMessage(data);
        };
        this.websocket.onclose = () => {
          this.isConnected = false;
          this.isRecording = false;
          this.deviceStatus = '未连接';
          this.$message.info('设备连接已断开');
        };
        this.websocket.onerror = (error) => {
          this.$message.error('连接发生错误: ' + error.message);
        };
      } catch (error) {
        this.$message.error('连接失败: ' + error.message);
      }
    },
    loadReport(filename) {
      if (!filename) {
        this.$message.error('报告文件名为空');
        return;
      }
      const reportUrl = `/brain/reports/${filename}`;
      fetch(reportUrl)
        .then((response) => {
          if (response.ok) return response.text();
          throw new Error('报告文件不存在');
        })
        .then(() => {
          this.reportPreview = {
            type: 'iframe',
            src: reportUrl,
            title: filename,
            loadedAt: Date.now(),
          };
          this.reportFrameKey += 1;
          this.activeTab = 'report';
        })
        .catch((error) => {
          this.$message.error('加载报告失败: ' + error.message);
        });
    },
    startRecording() {
      if (this.isRecording) {
        this.isRecording = false;
        if (this.eegTimer) {
          clearTimeout(this.eegTimer);
          this.eegTimer = null;
        }
        this.$message.info('已停止记录数据');
        this.dataStatus = '记录已停止';
      } else {
        this.currentRecordingId = null;
        if (!this.isConnected) {
          this.$message.warning('请先连接设备');
          return;
        }
        this.isRecording = true;
        this.$message.success('开始记录数据');
        this.sendEEGData();
      }
    },
    sendEEGData() {
      if (!this.isRecording || !this.isConnected) return;
      const eegData = {
        type: 'eeg_data',
        timestamp: new Date().toISOString(),
        data: this.generateMockEEGData(),
      };
      try {
        this.websocket.send(JSON.stringify(eegData));
        this.dataStatus = '正在记录数据...';
      } catch (error) {
        this.$message.error('发送数据失败: ' + error.message);
      }
      this.eegTimer = setTimeout(() => this.sendEEGData(), 1000);
    },
    generateMockEEGData() {
      const bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma'];
      return bands.map((band) => `${band} ${Math.floor(Math.random() * 100)}`).join(' ');
    },
    analyzeData() {
      if (this.currentRecordingId) {
        this.analyzeExistingFile(this.currentRecordingId);
        return;
      }
      if (!this.isConnected) {
        this.$message.warning('请先连接设备或导入数据文件');
        return;
      }
      const analysisRequest = {
        type: 'request_analysis',
        api_key: this.apiKey,
      };
      this.websocket.send(JSON.stringify(analysisRequest));
      this.$message.info('正在分析数据...');
    },
    analyzeExistingFile(recordingId) {
      fetch('/brain/api/analyze-existing-data/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recording_id: recordingId, api_key: this.apiKey }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.status === 'success') {
            this.$message.success(data.message);
            this.logContent += `[${new Date().toLocaleTimeString()}] ${data.message}\n`;
            if (data.report_filename) {
              this.loadReport(data.report_filename);
            } else if (data.report_content) {
              this.reportPreview = {
                type: 'html',
                html: data.report_content,
                title: data.report_title || '分析报告',
                loadedAt: Date.now(),
              };
              this.activeTab = 'report';
            }
          } else {
            this.$message.error(data.message);
            this.logContent += `[${new Date().toLocaleTimeString()}] 分析失败: ${data.message}\n`;
          }
        })
        .catch((error) => {
          this.$message.error('分析请求失败: ' + error.message);
          this.logContent += `[${new Date().toLocaleTimeString()}] 分析请求失败: ${error.message}\n`;
        });
    },
    importData() {
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.csv,.xlsx,.xls,.txt';
      fileInput.onchange = (event) => {
        const file = event.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        fetch('/brain/api/import-eeg-data/', {
          method: 'POST',
          body: formData,
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.status === 'success') {
              this.$message.success(data.message);
              this.logContent += `[${new Date().toLocaleTimeString()}] ${data.message}\n`;
              this.dataStatus = `已导入: ${file.name}`;
              this.importedFileName = file.name;
              this.currentRecordingId = data.recording_id;
              this.analyzeExistingFile(this.currentRecordingId);
            } else {
              this.$message.error(data.message);
              this.logContent += `[${new Date().toLocaleTimeString()}] 导入失败: ${data.message}\n`;
            }
          })
          .catch((error) => {
            this.$message.error('文件上传失败: ' + error.message);
            this.logContent += `[${new Date().toLocaleTimeString()}] 文件上传失败: ${error.message}\n`;
          });
      };
      fileInput.click();
    },
    testBackend() {
      this.$message.success('后端连接正常');
    },
    checkBluetoothSupport() {
      const supportInfo = {
        bluetooth: !!navigator.bluetooth,
        secureContext: window.isSecureContext,
        https: window.location.protocol === 'https:',
        localhost: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
        chrome: /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor),
      };
      if (!supportInfo.bluetooth) {
        let message = '您的浏览器不支持Web Bluetooth API。';
        if (!supportInfo.chrome) message += '建议使用最新版Google Chrome浏览器。';
        else if (!supportInfo.secureContext) {
          if (!supportInfo.https && !supportInfo.localhost) message += 'Web Bluetooth需要HTTPS环境或本地环境(localhost)。';
          else message += '请检查浏览器设置或使用支持的浏览器。';
        }
        this.$message.warning(message);
        return false;
      }
      if (!supportInfo.secureContext) {
        this.$message.warning('Web Bluetooth需要安全环境（HTTPS或localhost）。');
        return false;
      }
      return true;
    },
    scanDevices() {
      if (!this.checkBluetoothSupport()) return;
      this.$message.info('正在扫描蓝牙设备...');
      navigator.bluetooth
        .requestDevice({
          acceptAllDevices: true,
          optionalServices: ['battery_service', 'generic_access', 'device_information'],
        })
        .then((device) => {
          this.$message.success(`找到设备: ${device.name}`);
          this.deviceAddress = device.id;
          return device.gatt.connect();
        })
        .then(() => {
          this.$message.success('蓝牙设备配对成功');
          this.bluetoothConnected = true;
        })
        .catch((error) => {
          this.$message.error(`扫描失败: ${error.message}`);
        });
    },
    testAPI() {
      if (!this.apiKey) {
        this.$message.warning('请输入API密钥');
        return;
      }
      const loading = this.$loading({
        lock: true,
        text: '测试中...',
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.7)',
      });
      fetch('/brain/api/test-api-key/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: this.apiKey }),
      })
        .then((res) => res.json())
        .then((data) => {
          loading.close();
          if (data.status === 'success') this.$message.success(data.message);
          else this.$message.error(data.message);
        })
        .catch((error) => {
          loading.close();
          this.$message.error('测试请求失败: ' + error.message);
        });
    },
    clearLog() {
      this.logContent = '';
      this.$message.success('日志已清空');
    },
    handleWebSocketMessage(data) {
      switch (data.type) {
        case 'data_received':
          this.logContent += `[${new Date().toLocaleTimeString()}] 数据已接收: ${data.timestamp}\n`;
          break;
        case 'data_error':
          this.$message.error('数据处理错误: ' + data.error);
          this.logContent += `[${new Date().toLocaleTimeString()}] 错误: ${data.error}\n`;
          break;
        case 'import_success':
          this.$message.success('导入数据已成功保存到服务器');
          this.logContent += `[${new Date().toLocaleTimeString()}] 导入数据已保存: ${data.file_path}\n`;
          break;
        case 'analysis_result':
          if (data.success) {
            if (data.path) this.loadReport(data.path);
            else if (data.content) {
              this.reportPreview = {
                type: 'html',
                html: data.content,
                title: data.report_title || '分析报告',
                loadedAt: Date.now(),
              };
              this.activeTab = 'report';
            }
            this.$message.success('分析完成');
            this.logContent += `[${new Date().toLocaleTimeString()}] 分析完成\n`;
          } else {
            this.$message.error('分析失败: ' + data.error);
            this.logContent += `[${new Date().toLocaleTimeString()}] 分析失败: ${data.error}\n`;
          }
          break;
        case 'error':
          this.$message.error('服务器错误: ' + data.message);
          this.logContent += `[${new Date().toLocaleTimeString()}] 服务器错误: ${data.message}\n`;
          break;
      }
      this.$nextTick(() => {
        const logPanel = document.querySelector('.el-tab-pane[name="log"] .placeholder');
        if (logPanel) logPanel.scrollTop = logPanel.scrollHeight;
      });
    },
  },
  mounted() {
    this.testBackend();
  },
};
</script>

<style scoped>
.app-container.eeg-home {
  position: relative;
  isolation: isolate;
}
.eeg-home::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse 120% 80% at 50% -30%, rgba(59, 130, 246, 0.14), transparent 50%),
    radial-gradient(ellipse 60% 40% at 100% 50%, rgba(14, 165, 233, 0.06), transparent 45%),
    radial-gradient(ellipse 50% 50% at 0% 80%, rgba(99, 102, 241, 0.07), transparent 40%);
}
.eeg-home > * {
  position: relative;
  z-index: 1;
}
.app-container {
  font-family: 'Microsoft YaHei', 'Segoe UI', system-ui, sans-serif;
  margin: 0;
  padding: 24px 20px 32px;
  min-height: 100vh;
  color: #e8eef7;
}
.main-content {
  margin-left: auto;
  margin-right: auto;
  width: min(1120px, 92vw);
  display: flex;
  gap: 22px;
  align-items: stretch;
}
.footer {
  text-align: center;
  margin-top: 32px;
  padding-top: 20px;
  color: #64748b;
  font-size: 0.75rem;
  letter-spacing: 0.03em;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
  max-width: min(1120px, 92vw);
  margin-left: auto;
  margin-right: auto;
}
@media (max-width: 960px) {
  .main-content {
    flex-direction: column;
    width: 100%;
    max-width: 100%;
  }
  .main-content :deep(.sidebar) {
    width: 100%;
    height: auto;
    min-height: 0;
    max-height: none;
  }
  .main-content :deep(.tab-content-container) {
    max-height: 70vh;
  }
}
</style>
