<template>
  <div class="page-container">
    <div class="page-header">
      <h2>数据分析</h2>
    </div>

    <div class="card">
      <el-form :inline="true" :model="queryForm">
        <el-form-item label="站点ID">
          <el-input v-model="queryForm.station_id" placeholder="如: 54511" style="width: 160px" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            value-format="YYYY-MM-DD HH:mm:ss"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleAnalyze">分析</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <div class="card">
          <h3>温度统计</h3>
          <el-descriptions :column="2" border v-if="stats">
            <el-descriptions-item label="最高温">{{ stats.temperature?.max }}°C</el-descriptions-item>
            <el-descriptions-item label="最低温">{{ stats.temperature?.min }}°C</el-descriptions-item>
            <el-descriptions-item label="平均温">{{ stats.temperature?.avg }}°C</el-descriptions-item>
            <el-descriptions-item label="有效记录">{{ stats.temperature?.count }}</el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="暂无数据" />
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card">
          <h3>降水统计</h3>
          <el-descriptions :column="2" border v-if="stats">
            <el-descriptions-item label="累计降水">{{ stats.precipitation?.total }}mm</el-descriptions-item>
            <el-descriptions-item label="降雨天数">{{ stats.precipitation?.rainy_days }}天</el-descriptions-item>
            <el-descriptions-item label="总记录">{{ stats.total_records }}</el-descriptions-item>
            <el-descriptions-item label="缺测记录">{{ stats.missing_records }}</el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="暂无数据" />
        </div>
      </el-col>
    </el-row>

    <div class="card" style="margin-top: 20px">
      <h3>月度趋势</h3>
      <div ref="chartRef" style="height: 350px"></div>
    </div>

    <div class="data-source-tag">数据来源：中国气象局</div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import * as echarts from 'echarts'
import { analyzeStation, monthlyAnalysis } from '@/api/analysis'

const queryForm = reactive({ station_id: '' })
const dateRange = ref([])
const stats = ref(null)
const chartRef = ref()

async function handleAnalyze() {
  if (!queryForm.station_id) return
  const params = {
    station_id: queryForm.station_id,
    start_time: dateRange.value?.[0] || '',
    end_time: dateRange.value?.[1] || '',
  }
  stats.value = await analyzeStation(params)
  renderChart()
}

async function renderChart() {
  if (!queryForm.station_id || !chartRef.value) return
  const chart = echarts.init(chartRef.value)
  // TODO: 获取月度数据渲染图表
  chart.setOption({
    xAxis: { type: 'category', data: [] },
    yAxis: { type: 'value' },
    series: [],
  })
}
</script>

<style lang="scss" scoped>
.card h3 {
  margin: 0 0 16px;
  font-size: 16px;
}
</style>
