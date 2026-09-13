<template>
  <div class="page-container">
    <div class="page-header">
      <h2>实时天气</h2>
    </div>

    <div class="card">
      <el-select
        v-model="selectedCity"
        placeholder="选择城市"
        style="width: 240px"
        filterable
        @change="fetchWeather"
      >
        <el-option
          v-for="city in cities"
          :key="city.id"
          :label="city.city_name"
          :value="city.id"
        />
      </el-select>
      <span v-if="loading" class="source-tag">加载中...</span>
      <span v-else-if="dataSource" class="source-tag">数据来源: {{ dataSource }}</span>
    </div>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 实况 -->
      <el-col :span="8">
        <div class="card">
          <h3>实时实况</h3>
          <div v-if="realtime" class="realtime-box">
            <div class="temp">{{ realtime.temperature }}°C</div>
            <div class="desc">{{ realtime.weather_desc }}</div>
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="体感">{{ realtime.feels_like }}°C</el-descriptions-item>
              <el-descriptions-item label="湿度">{{ realtime.humidity }}%</el-descriptions-item>
              <el-descriptions-item label="气压">{{ realtime.pressure }}hPa</el-descriptions-item>
              <el-descriptions-item label="风速">{{ realtime.wind_speed }}m/s</el-descriptions-item>
              <el-descriptions-item label="降水">{{ realtime.precipitation }}mm</el-descriptions-item>
            </el-descriptions>

            <!-- 日出日落 -->
            <div v-if="sunInfo" class="sun-info">
              <el-divider>日出日落</el-divider>
              <el-descriptions :column="2" size="small">
                <el-descriptions-item label="日出">{{ formatTime(sunInfo.sunrise) }}</el-descriptions-item>
                <el-descriptions-item label="日落">{{ formatTime(sunInfo.sunset) }}</el-descriptions-item>
                <el-descriptions-item label="昼长" :span="2">{{ sunInfo.daylight_hours }} 小时</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          <el-empty v-else description="请选择城市" />
        </div>
      </el-col>

      <!-- 空气质量 -->
      <el-col :span="8">
        <div class="card">
          <h3>空气质量</h3>
          <div v-if="airQuality" class="air-box">
            <div class="aqi-value" :style="{ color: aqiColor }">
              {{ airQuality.aqi }}
              <span class="aqi-level">{{ airQuality.aqi_level }}</span>
            </div>
            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="PM2.5">{{ airQuality.pm25 }}</el-descriptions-item>
              <el-descriptions-item label="PM10">{{ airQuality.pm10 }}</el-descriptions-item>
              <el-descriptions-item label="SO₂">{{ airQuality.so2 }}</el-descriptions-item>
              <el-descriptions-item label="NO₂">{{ airQuality.no2 }}</el-descriptions-item>
              <el-descriptions-item label="CO">{{ airQuality.co }}</el-descriptions-item>
              <el-descriptions-item label="O₃">{{ airQuality.o3 }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else description="请选择城市" />
        </div>
      </el-col>

      <!-- 预警 -->
      <el-col :span="8">
        <div class="card">
          <h3>气象预警</h3>
          <div v-if="warnings.length" class="warning-list">
            <el-alert
              v-for="w in warnings"
              :key="w.warning_id"
              :title="w.title"
              :type="warningType(w.warning_level)"
              :closable="false"
              show-icon
            >
              <template #default>
                <p>{{ w.content }}</p>
                <small>{{ w.publish_time }}</small>
              </template>
            </el-alert>
          </div>
          <el-empty v-else description="当前无预警" />
        </div>
      </el-col>
    </el-row>

    <!-- 生活指数 -->
    <div class="card" style="margin-top: 20px">
      <h3>生活指数</h3>
      <el-row :gutter="20" v-if="lifeIndices.length">
        <el-col :span="4" v-for="item in lifeIndices" :key="item.index_type">
          <div class="index-card">
            <div class="index-name">{{ item.index_name }}</div>
            <div class="index-level" :style="{ color: indexColor(item.index_level) }">{{ item.index_level }}</div>
            <div class="index-desc">{{ item.index_desc }}</div>
          </div>
        </el-col>
      </el-row>
      <el-empty v-else description="请选择城市" />
    </div>

    <!-- 未来7天预报图表 -->
    <div class="card" style="margin-top: 20px">
      <h3>未来7天预报</h3>
      <div v-show="forecast.length" ref="forecastChartRef" class="forecast-chart"></div>
      <el-empty v-if="!forecast.length" description="请选择城市" />
    </div>

    <div class="data-source-tag">数据来源：{{ dataSource || 'Open-Meteo（和风天气增强）' }} | 帽子天气</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getRealtime, getForecast, getWarning } from '@/api/weather'
import { getAirQuality, getLifeIndex, getSunriseSunset } from '@/api/air'
import { getAllCities } from '@/api/city'
import { isDark } from '@/store/theme'

const cities = ref([])
const selectedCity = ref(null)
const currentCityInfo = ref(null)
const realtime = ref(null)
const forecast = ref([])
const warnings = ref([])
const airQuality = ref(null)
const lifeIndices = ref([])
const sunInfo = ref(null)
const dataSource = ref('')
const loading = ref(false)
const forecastChartRef = ref(null)
let forecastChart = null

const aqiColor = computed(() => aqiLevelColor(airQuality.value?.aqi))

// 国标 AQI 分级配色：优绿/良黄/轻度橙/中度红/重度紫/严重褐红
function aqiLevelColor(aqi) {
  if (!aqi) return '#909399'
  if (aqi <= 50) return '#4CAF50'
  if (aqi <= 100) return '#FFC107'
  if (aqi <= 150) return '#FF9800'
  if (aqi <= 200) return '#F44336'
  if (aqi <= 300) return '#9C27B0'
  return '#8D2E2E'
}

function indexColor(level) {
  if (level && (level.includes('适宜') || level.includes('舒适'))) return '#67C23A'
  if (level && (level.includes('较'))) return '#E6A23C'
  if (level && (level.includes('不宜') || level.includes('冷') || level.includes('热'))) return '#F56C6C'
  return '#409EFF'
}

// 渲染 7 天温度/降水混合图
function renderForecastChart() {
  if (!forecastChartRef.value || !forecast.value.length) return
  if (!forecastChart) {
    forecastChart = echarts.init(forecastChartRef.value)
  }
  const dark = isDark.value
  const axisColor = dark ? '#A3A6AD' : '#606266'
  const splitColor = dark ? 'rgba(255,255,255,0.12)' : '#EBEEF5'
  const days = forecast.value.map(d => (d.forecast_time || '').slice(5))
  const maxTemps = forecast.value.map(d => d.temp_max ?? null)
  const minTemps = forecast.value.map(d => d.temp_min ?? null)
  const precip = forecast.value.map(d => d.precipitation_sum ?? 0)

  forecastChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['最高温', '最低温', '降水量'],
      textStyle: { color: axisColor },
      top: 0,
    },
    grid: { left: 48, right: 48, top: 36, bottom: 28 },
    xAxis: {
      type: 'category',
      data: days,
      axisLabel: { color: axisColor },
      axisLine: { lineStyle: { color: splitColor } },
    },
    yAxis: [
      {
        type: 'value',
        name: '°C',
        nameTextStyle: { color: axisColor },
        axisLabel: { color: axisColor },
        splitLine: { lineStyle: { color: splitColor } },
      },
      {
        type: 'value',
        name: 'mm',
        nameTextStyle: { color: axisColor },
        axisLabel: { color: axisColor },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '最高温',
        type: 'line',
        smooth: true,
        data: maxTemps,
        itemStyle: { color: '#F56C6C' },
        label: { show: true, position: 'top', color: axisColor, formatter: '{c}°' },
      },
      {
        name: '最低温',
        type: 'line',
        smooth: true,
        data: minTemps,
        itemStyle: { color: '#409EFF' },
        label: { show: true, position: 'bottom', color: axisColor, formatter: '{c}°' },
      },
      {
        name: '降水量',
        type: 'bar',
        yAxisIndex: 1,
        data: precip,
        itemStyle: { color: 'rgba(64,158,255,0.35)', borderRadius: [4, 4, 0, 0] },
        barWidth: '30%',
      },
    ],
  })
}

function handleResize() {
  forecastChart?.resize()
}

// 加载城市列表
async function loadCities() {
  try {
    const res = await getAllCities({ page: 1, page_size: 1000 })
    cities.value = res?.items || []
  } catch (error) {
    console.error('加载城市列表失败:', error)
    ElMessage.error('加载城市列表失败')
  }
}

async function fetchWeather() {
  if (!selectedCity.value) return

  // 获取城市信息
  const city = cities.value.find(c => c.id === selectedCity.value)
  if (!city) {
    ElMessage.warning('未找到城市信息')
    return
  }

  currentCityInfo.value = city
  const lat = city.latitude
  const lon = city.longitude

  if (!lat || !lon) {
    ElMessage.warning('该城市缺少经纬度信息')
    return
  }

  loading.value = true

  try {
    // 先获取实时天气
    const realtimeRes = await getRealtime(city.id, lat, lon)
    realtime.value = realtimeRes
    dataSource.value = realtimeRes?.data_source || ''

    // 获取其他数据
    const [forecastRes, warningRes, airRes, lifeRes, sunRes] = await Promise.all([
      getForecast(city.id, lat, lon, 7),
      getWarning(city.id),
      getAirQuality(city.id, lat, lon),
      getLifeIndex(city.id, {
        temperature: realtimeRes?.temperature || 20,
        humidity: realtimeRes?.humidity || 50,
        precipitation: realtimeRes?.precipitation || 0,
        wind_speed: realtimeRes?.wind_speed || 0,
        uv: realtimeRes?.uv_index || 5,
      }),
      getSunriseSunset(city.id, { latitude: lat, longitude: lon }),
    ])

    forecast.value = forecastRes.daily || []
    warnings.value = warningRes
    airQuality.value = airRes
    lifeIndices.value = lifeRes
    sunInfo.value = sunRes
    await nextTick()
    renderForecastChart()
  } catch (error) {
    console.error('获取天气数据失败:', error)
    ElMessage.error('获取天气数据失败')
  } finally {
    loading.value = false
  }
}

// 暗色模式切换后重绘图表配色
watch(isDark, () => {
  nextTick(renderForecastChart)
})

function warningType(level) {
  const map = { '红色': 'error', '橙色': 'warning', '黄色': 'info', '蓝色': 'info' }
  return map[level] || 'info'
}

// 格式化时间
function formatTime(timeStr) {
  if (!timeStr) return '-'
  if (timeStr.includes('T')) {
    return timeStr.split('T')[1]?.substring(0, 5) || timeStr
  }
  return timeStr
}

onMounted(() => {
  loadCities()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  forecastChart?.dispose()
  forecastChart = null
})
</script>

<style lang="scss" scoped>
.source-tag {
  font-size: 12px;
  color: #409eff;
  margin-left: 12px;
}

.realtime-box {
  .temp {
    font-size: 48px;
    font-weight: bold;
    color: #409eff;
    text-align: center;
  }
  .desc {
    text-align: center;
    color: #909399;
    margin-bottom: 16px;
  }
}

.sun-info {
  margin-top: 16px;
}

.air-box {
  .aqi-value {
    font-size: 48px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 16px;

    .aqi-level {
      font-size: 16px;
      margin-left: 8px;
    }
  }
}

.warning-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.index-card {
  text-align: center;
  padding: 16px 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-light);

  .index-name {
    font-size: 14px;
    color: var(--el-text-color-regular);
    margin-bottom: 4px;
  }

  .index-level {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 8px;
  }

  .index-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    line-height: 1.4;
  }
}

.forecast-chart {
  width: 100%;
  height: 320px;
}

.card h3 {
  margin: 0 0 16px;
  font-size: 16px;
}
</style>
