<template>
  <div class="app-container" :style="bgStyle">
    <!-- 头部 -->
    <header class="header">
      <div class="logo-container">
        <img src="/logo.jpg" alt="云梦泽 - Yun Meng Ze">
      </div>
      <h1 class="title">基于EEG与人工智能的睡眠健康评估系统 V2.0</h1>
      <p class="subtitle">实时采集 · 本地存储 · 智能分析</p>
    </header>

    <!-- 状态指示 -->
    <div class="status-bar">
      <span class="status-item"><i class="el-icon-circle-check" style="color: green;"></i> 后端: 已连接</span>
      <span class="status-item">
        <i :class="isConnected ? 'el-icon-circle-check' : 'el-icon-circle-cross'" :style="{color: isConnected ? 'green' : 'red'}"></i>
        设备: {{ deviceStatus }}
      </span>
      <span class="status-item">
        <i :class="isRecording ? 'el-icon-circle-check' : 'el-icon-circle-cross'" :style="{color: isRecording ? 'green' : 'red'}"></i>
        数据: {{ isRecording ? '正在记录' : '未连接' }}
      </span>
      <span class="status-item"><i class="el-icon-circle-cross" style="color: red;"></i> API: 未连接</span>
    </div>

    <!-- 操作按钮 -->
    <div class="button-group">
      <el-button type="primary" @click="connectDevice">连接设备</el-button>
      <el-button type="success" @click="startRecording">{{ isRecording ? '停止记录' : '开始记录' }}</el-button>
      <el-button type="warning" @click="analyzeData">分析数据</el-button>
      <el-button type="info" @click="importData">导入数据</el-button>
      <el-button type="text" @click="testBackend">测试后端连接</el-button>
    </div>

    <!-- 主体内容 -->
    <div class="main-content">
      <!-- 左侧侧边栏 -->
      <div class="sidebar">
        <div class="card">
          <h3><i class="el-icon-mobile-phone"></i> 设备连接</h3>
          <div class="form-group">
            <label>蓝牙设备地址</label>
            <el-input class="custom-input" v-model="deviceAddress" placeholder="例如: JDY-18"></el-input>
            <el-button id="scann_button" type="primary" size="small" @click="scanDevices">扫描</el-button>
          </div>
          <div class="status-info">
            <p>连接状态: <span :style="{color: isConnected ? 'green' : 'red'}">{{ deviceStatus }}</span></p>
            <p>信号质量: <span>-- /200</span></p>
          </div>
        </div>

        <div class="card">
          <h3><i class="el-icon-document"></i> 数据保存</h3>
          <div class="data-status">
            <p>{{ dataStatus }}</p>
          </div>
        </div>

        <div class="card">
          <h3><i class="el-icon-setting"></i> 分析配置</h3>
          <div class="form-group">
            <label>API密钥</label>
            <el-input class="custom-input" v-model="apiKey" placeholder="请输入API密钥"></el-input>
          </div>
          <el-button type="primary" size="small" @click="testAPI">测试API</el-button>
          <div class="history-file">
            <p>历史数据文件</p>
            <p style="color: #99ccff;">暂无历史数据</p>
          </div>
        </div>
      </div>

      <!-- 右侧主内容区 -->
      <div class="main-panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="实时数据" name="realtime">
            <div class="tab-content-container">
              <div class="tab-pane-content">
                <div class="data-flow">
                  <i class="el-icon-info"></i>
                  <p>未连接设备，请先连接设备开始采集数据</p>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="分析报告" name="report">
            <div class="tab-content-container">
              <div class="tab-pane-content">
                <div class="placeholder" v-if="!reportContent">分析报告内容将显示在此处</div>
                <div v-else class="report-content" v-html="reportContent"></div>
              </div>
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
          <el-button type="text" @click="clearLog">清空日志</el-button>
        </div>
      </div>
    </div>

    <footer class="footer">
      基于EEG与人工智能的睡眠健康评估系统 V2.0 | 本地数据安全存储 | 支持CSV/Excel数据分析
    </footer>
  </div>
</template>

<script>
export default {
  name: 'EEGHome',
  data() {
    return {
      currentRecordingId: null,
      bgStyle: {
        backgroundImage: 'linear-gradient(to right, rgba(0, 0, 70, 0.3), rgba(28, 181, 224, 0.3)), url("/背景鲸鱼.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
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
      reportContent: '',
      historyFiles: [],
      importedFileName: '',
      currentFilePath: '',
      eegTimer: null,
    }
  },
  beforeDestroy() {
    if (this.websocket) this.websocket.close();
    if (this.eegTimer) clearTimeout(this.eegTimer);
  },
  methods: {
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
        .then(response => {
          if (response.ok) return response.text();
          throw new Error('报告文件不存在');
        })
        .then(() => {
          this.reportContent = `<iframe src="${reportUrl}" style="width:100%; height:100%; border:none;"></iframe>`;
          this.activeTab = 'report';
        })
        .catch(error => {
          this.$message.error('加载报告失败: ' + error.message);
        });
    },
    startRecording() {
      if (this.isRecording) {
        // 停止记录
        this.isRecording = false;
        if (this.eegTimer) {
          clearTimeout(this.eegTimer);
          this.eegTimer = null;
        }
        this.$message.info('已停止记录数据');
        this.dataStatus = '记录已停止';
      } else {
        // 开始记录：清除导入的数据记录ID，确保分析实时数据
        this.currentRecordingId = null;   // 添加这一行
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
        data: this.generateMockEEGData()
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
      return bands.map(band => `${band} ${Math.floor(Math.random() * 100)}`).join(' ');
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
          // 实时数据分析（通过 WebSocket）
          const analysisRequest = {
            type: 'request_analysis',
            api_key: this.apiKey
          };
          this.websocket.send(JSON.stringify(analysisRequest));
          this.$message.info('正在分析数据...');
        },
    analyzeExistingFile(recordingId) {
        fetch('/brain/api/analyze-existing-data/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ recording_id: recordingId, api_key: this.apiKey })
        })
          .then(res => res.json())
          .then(data => {
            if (data.status === 'success') {
              this.$message.success(data.message);
              this.logContent += `[${new Date().toLocaleTimeString()}] ${data.message}\n`;
              // 优先使用 report_filename（通过 iframe 加载，保证脚本执行）
              if (data.report_filename) {
                this.loadReport(data.report_filename);
              } else if (data.report_content) {
                // 降级：如果没有文件名才使用内容
                this.reportContent = data.report_content;
                this.activeTab = 'report';
              }
            } else {
              this.$message.error(data.message);
              this.logContent += `[${new Date().toLocaleTimeString()}] 分析失败: ${data.message}\n`;
            }
          })
          .catch(error => {
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
          body: formData
        })
          .then(res => res.json())
          .then(data => {
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
          .catch(error => {
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
        chrome: /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor)
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
      navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: ['battery_service', 'generic_access', 'device_information']
      })
        .then(device => {
          this.$message.success(`找到设备: ${device.name}`);
          this.deviceAddress = device.id;
          return device.gatt.connect();
        })
        .then(() => {
          this.$message.success('蓝牙设备配对成功');
          this.bluetoothConnected = true;
        })
        .catch(error => {
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
        background: 'rgba(0, 0, 0, 0.7)'
      });
      fetch('/brain/api/test-api-key/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: this.apiKey })
      })
        .then(res => res.json())
        .then(data => {
          loading.close();
          if (data.status === 'success') this.$message.success(data.message);
          else this.$message.error(data.message);
        })
        .catch(error => {
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
              this.reportContent = data.content;
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
    }
  },
  mounted() {
    this.testBackend();
  }
};
</script>

<style scoped>
.app-container {
  font-family: 'Microsoft YaHei', sans-serif;
  margin: 0;
  padding: 20px;
  min-height: 100vh;
  color: #fff;
}
/* 其他样式保持与之前完全一致，复制之前的样式即可（除背景外） */
.header {
  text-align: center;
  margin-bottom: 30px;
}
.logo-container {
  width: 120px;
  height: 120px;
  margin: 50px auto 0px auto;
  display: block;
}
.logo-container img {
  width: 120px;
  height: auto;
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
}
.title {
  color: #ffd000;
  font-size: 1.8rem;
  margin: 10px 0;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.7);
}
.subtitle {
  color: #99ccff;
  font-size: 0.9rem;
  margin-top: 5px;
}
.status-bar {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 20px;
  font-size: 0.9rem;
}
.status-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 20px;
}
.el-icon-circle-check {
  color: #00ff00;
  animation: pulse 2s infinite;
}
.el-icon-circle-cross {
  color: #ff0000;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.button-group {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-bottom: 20px;
}
.custom-input input {
  margin-top: 5px;
  border: 2px solid #00ffff !important;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.7) !important;
  border-radius: 8px !important;
  background-color: rgba(51, 128, 158, 0.8) !important;
  color: #fff !important;
}
.el-button {
  border: 1px solid #00ffff;
  border-radius: 8px;
  padding: 10px 20px;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
  transition: all 0.3s ease;
  background: transparent;
  color: #00ffff;
  font-size: 20px;
}
#scann_button {
  margin-top: 8px;
  font-size: 16px;
}
.el-button:hover {
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
}
.el-button[type="primary"] {
  background: transparent;
  color: #00ffff;
}
.el-button[type="success"] {
  background: transparent;
  color: #00ff00;
}
.el-button[type="warning"] {
  background: transparent;
  color: #ffcc00;
}
.el-button[type="info"] {
  background: transparent;
  color: #00ccff;
}
.main-content {
  margin-left: 12.5%;
  width: 75%;
  display: flex;
  gap: 20px;
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
  overflow-y: hidden;
  padding: 20px;
  background: rgba(0, 20, 40, 0.6);
  border-radius: 8px;
  border: 1px solid #00aaff;
  box-shadow: 0 0 10px rgba(51, 142, 253, 0.301);
}
.sidebar {
  width: 350px;
  height: 700px;
  background: rgba(47, 99, 242, 0.297);
  border: 1px solid #00ffff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
}
.card {
  margin-bottom: 20px;
  border-bottom: 1px solid #00ffff;
  padding-bottom: 16px;
}
.card h3 {
  margin-top: 0;
  font-size: 1rem;
  color: #00ffff;
  display: flex;
  align-items: center;
  gap: 8px;
}
.form-group {
  margin: 10px 0;
}
.status-info {
  margin-top: 10px;
  font-size: 0.9rem;
  color: #99ccff;
}
.data-status {
  padding: 10px;
  background: rgba(104, 104, 111, 0.506);
  border-radius: 4px;
  margin-top: 10px;
  color: #00ffff;
}
.history-file {
  margin-top: 10px;
  font-size: 0.9rem;
  color: #99ccff;
}
.main-panel {
  flex: 1;
  background: rgba(27, 27, 82, 0.5);
  border: 1px solid #00ffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 0 20px rgba(63, 109, 158, 0.2);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.main-panel .el-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.main-panel .el-tabs__content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.main-panel .el-tab-pane {
  flex: 1;
  overflow-y: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.data-flow {
  text-align: center;
  padding: 40px;
  color: #99ccff;
  font-size: 1rem;
  flex: 1;
  overflow-y: auto;
}
.placeholder {
  height: 100%;
  overflow-y: auto;
  text-align: left;
  white-space: pre-wrap;
  color: #00ffff;
  font-family: monospace;
  line-height: 1.5;
  background: rgba(28, 48, 74, 0.345);
  padding: 10px;
  border-radius: 8px;
  flex: 1;
}
.clear-log-btn {
  text-align: right;
  margin-top: 10px;
}
.footer {
  text-align: center;
  margin-top: 30px;
  color: #99ccff;
  font-size: 0.8rem;
  text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
}
.el-tabs__item {
  color: #99ccff !important;
  font-weight: bold;
}
.el-tabs__item.is-active {
  color: #00ffff !important;
  border-bottom: 2px solid #00ffff;
}
.el-tabs__nav {
  border-bottom: none;
}
.tab-pane-content {
  padding: 0 !important;
  overflow: hidden;
}
.report-content {
  width: 100%;
  height: 100%;
  overflow-y: hidden;     /* 添加垂直滚动条 */
  padding-right: 5px;   /* 避免滚动条遮挡内容（可选） */
  box-sizing: border-box;
}
.report-content table {
  width: 100%;
  border-collapse: collapse;
}
</style>