<template>
  <div class="data-flow">
    <div class="data-flow-icon-wrap">
      <i class="el-icon-info data-flow-icon"></i>
    </div>
    <p class="data-flow-msg">未连接设备，请先连接设备开始采集数据</p>
  </div>
</template>

<script>
export default {
  name: 'EEGHomeRealtimeEmpty',
};
</script>

<style scoped>
.data-flow {
  text-align: center;
  padding: 48px 28px;
  color: #94a3b8;
  font-size: 0.9375rem;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
}
.data-flow-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, rgba(59, 130, 246, 0.15), rgba(15, 23, 42, 0.5));
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.25);
}
.data-flow-icon {
  font-size: 1.75rem;
  color: #7dd3fc;
  opacity: 0.95;
}
.data-flow-msg {
  margin: 0;
  max-width: 320px;
  line-height: 1.65;
  color: #cbd5e1;
}
</style>
