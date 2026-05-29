<template>
  <div class="eeg-charts">
    <div class="chart-panel">
      <div class="chart-title">RawWave</div>
      <div ref="rawChartRef" class="chart-box" />
    </div>
    <div class="chart-panel">
      <div class="chart-title">频段分布</div>
      <div ref="bandChartRef" class="chart-box chart-box--sm" />
    </div>
    <div class="chart-panel">
      <div class="chart-title">心理状态趋势</div>
      <div ref="mentalChartRef" class="chart-box chart-box--sm" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { EEGSample } from '@/types/eeg'
import { EEG_BAND_LABELS } from '@/types/eeg'
import { formatTimeLabel } from '@/utils/eegParser'

const props = defineProps<{
  history: EEGSample[]
  current: EEGSample
  displayMode: 'raw' | 'eeg'
}>()

const rawChartRef = ref<HTMLDivElement>()
const bandChartRef = ref<HTMLDivElement>()
const mentalChartRef = ref<HTMLDivElement>()

let rawChart: echarts.ECharts | null = null
let bandChart: echarts.ECharts | null = null
let mentalChart: echarts.ECharts | null = null

const CHART_THEME = {
  backgroundColor: '#f1f5f9',
  axisLine: '#94a3b8',
  axisLabel: '#64748b',
  splitLine: '#dde4ee',
  legend: '#64748b',
  barLabel: '#475569',
}

function initCharts() {
  if (rawChartRef.value) rawChart = echarts.init(rawChartRef.value)
  if (bandChartRef.value) bandChart = echarts.init(bandChartRef.value)
  if (mentalChartRef.value) mentalChart = echarts.init(mentalChartRef.value)
  updateCharts()
}

function updateRawChart() {
  if (!rawChart) return
  const times = props.history.map((s) => formatTimeLabel(s.timestamp))
  const values = props.history.map((s) => s.raw)

  rawChart.setOption({
    backgroundColor: CHART_THEME.backgroundColor,
    animation: false,
    grid: { left: 56, right: 24, top: 36, bottom: 32 },
    tooltip: { trigger: 'axis' },
    legend: { data: ['RawWave'], top: 4, right: 16, textStyle: { color: CHART_THEME.legend, fontSize: 12 } },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: CHART_THEME.axisLine } },
      axisLabel: { color: CHART_THEME.axisLabel, fontSize: 11 },
      splitLine: { show: true, lineStyle: { color: CHART_THEME.splitLine, type: 'dashed' } },
    },
    yAxis: {
      type: 'value',
      min: -1500,
      max: 1500,
      axisLine: { show: true, lineStyle: { color: CHART_THEME.axisLine } },
      axisLabel: { color: CHART_THEME.axisLabel },
      splitLine: { lineStyle: { color: CHART_THEME.splitLine } },
    },
    series: [
      {
        name: 'RawWave',
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { color: '#dc2626', width: 1.5 },
        data: values,
      },
    ],
  })
}

function updateBandChart() {
  if (!bandChart) return
  const sample = props.current
  const labels = EEG_BAND_LABELS.map((b) => b.label)
  const values = EEG_BAND_LABELS.map((b) => sample[b.key as keyof EEGSample] as number)
  const colors = EEG_BAND_LABELS.map((b) => b.color)

  bandChart.setOption({
    backgroundColor: CHART_THEME.backgroundColor,
    animation: true,
    animationDuration: 300,
    grid: { left: 48, right: 24, top: 40, bottom: 36 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: CHART_THEME.axisLabel, fontSize: 11, rotate: 20 },
      axisLine: { lineStyle: { color: CHART_THEME.axisLine } },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: true, lineStyle: { color: CHART_THEME.axisLine } },
      axisLabel: { color: CHART_THEME.axisLabel },
      splitLine: { lineStyle: { color: CHART_THEME.splitLine } },
    },
    series: [
      {
        type: 'bar',
        barWidth: '52%',
        data: values.map((v, i) => ({
          value: v,
          itemStyle: { color: colors[i], borderRadius: [4, 4, 0, 0] },
        })),
        label: {
          show: true,
          position: 'top',
          color: CHART_THEME.barLabel,
          fontSize: 11,
        },
      },
    ],
  })
}

function updateMentalChart() {
  if (!mentalChart) return
  const times = props.history.map((s) => formatTimeLabel(s.timestamp))
  const attention = props.history.map((s) => s.attention)
  const meditation = props.history.map((s) => s.meditation)
  const none = props.history.map((s) => Math.max(0, 100 - s.attention - s.meditation))

  mentalChart.setOption({
    backgroundColor: CHART_THEME.backgroundColor,
    animation: false,
    grid: { left: 56, right: 24, top: 40, bottom: 32 },
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['None', 'Attention', 'Meditation'],
      top: 4,
      textStyle: { color: CHART_THEME.legend, fontSize: 12 },
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: CHART_THEME.axisLine } },
      axisLabel: { color: CHART_THEME.axisLabel, fontSize: 11 },
      splitLine: { show: true, lineStyle: { color: CHART_THEME.splitLine, type: 'dashed' } },
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLine: { show: true, lineStyle: { color: CHART_THEME.axisLine } },
      axisLabel: { color: CHART_THEME.axisLabel },
      splitLine: { lineStyle: { color: CHART_THEME.splitLine } },
    },
    series: [
      {
        name: 'None',
        type: 'line',
        stack: 'mental',
        areaStyle: { color: 'rgba(239, 68, 68, 0.35)' },
        lineStyle: { width: 0 },
        showSymbol: false,
        data: none,
        itemStyle: { color: '#ef4444' },
      },
      {
        name: 'Attention',
        type: 'line',
        stack: 'mental',
        areaStyle: { color: 'rgba(34, 197, 94, 0.35)' },
        lineStyle: { width: 0 },
        showSymbol: false,
        data: attention,
        itemStyle: { color: '#22c55e' },
      },
      {
        name: 'Meditation',
        type: 'line',
        stack: 'mental',
        areaStyle: { color: 'rgba(168, 85, 247, 0.35)' },
        lineStyle: { width: 0 },
        showSymbol: false,
        data: meditation,
        itemStyle: { color: '#a855f7' },
      },
    ],
  })
}

function updateCharts() {
  updateRawChart()
  updateBandChart()
  updateMentalChart()
}

function handleResize() {
  rawChart?.resize()
  bandChart?.resize()
  mentalChart?.resize()
}

watch(
  () => [props.history, props.current, props.displayMode],
  () => updateCharts(),
  { deep: true },
)

onMounted(async () => {
  await nextTick()
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  rawChart?.dispose()
  bandChart?.dispose()
  mentalChart?.dispose()
})
</script>

<style scoped>
.eeg-charts {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  min-height: 0;
}

.chart-panel {
  flex: 1;
  min-height: 0;
  background: #f8fafc;
  border: 1px solid #dde4ee;
  border-radius: 8px;
  padding: 8px 12px 4px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
}

.chart-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 4px;
  padding-left: 4px;
}

.chart-box {
  flex: 1;
  min-height: 160px;
  background: #f1f5f9;
  border-radius: 6px;
}

.chart-box--sm {
  min-height: 140px;
}
</style>
