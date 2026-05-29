<template>
  <nav class="eeg-page-nav">
    <router-link
      to="/eeg/monitor"
      class="nav-item"
      :class="{ active: current === 'monitor' }"
    >
      <el-icon><TrendCharts /></el-icon>
      实时脑电监测
    </router-link>
    <span class="nav-divider" />
    <router-link
      to="/eeg"
      class="nav-item"
      :class="{ active: current === 'analysis' }"
    >
      <el-icon><DataAnalysis /></el-icon>
      睡眠健康分析
    </router-link>
  </nav>
</template>

<script setup lang="ts">
import { TrendCharts, DataAnalysis } from '@element-plus/icons-vue'

defineProps<{
  current: 'monitor' | 'analysis'
}>()
</script>

<style scoped>
.eeg-page-nav {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.45);
  border: 1px solid rgba(148, 163, 184, 0.2);
  backdrop-filter: blur(12px);
}

.nav-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #cbd5e1;
  text-decoration: none;
  transition: background 0.2s ease, color 0.2s ease;
}

.nav-item:hover {
  color: #f1f5f9;
  background: rgba(59, 130, 246, 0.15);
}

.nav-item.active {
  color: #fff;
  background: rgba(59, 130, 246, 0.35);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}

.nav-divider {
  width: 1px;
  height: 20px;
  background: rgba(148, 163, 184, 0.25);
  margin: 0 2px;
}
</style>
