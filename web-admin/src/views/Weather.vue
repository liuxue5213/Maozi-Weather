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

    <!-- 预报 -->
    <div class="card" style="margin-top: 20px">
      <h3>未来7天预报</h3>
      <el-table :data="forecast" size="small" v-if="forecast.length">
        <el-table-column prop="forecast_time" label="日期" width="120" />
        <el-table-column prop="weather_desc" label="天气" />
        <el-table-column label="温度">
          <template #default="{ row }">{{ row.temp_min }}~{{ row.temp_max }}°C</template>
        </el-table-column>
        <el-table-column prop="precipitation_sum" label="降水" width="80" />
      </el-table>
      <el-empty v-else description="请选择城市" />
    </div>

    <div class="data-source-tag">数据来源：{{ dataSource || 'Open-Meteo（和风天气增强）' }} | 帽子天气</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Top, Bottom } from '@element-plus/icons-vue'
import { getRealtime, getForecast, getWarning } from '@/api/weather'
import { getAirQuality, getLifeIndex, getSunriseSunset } from '@/api/air'
import { getAllCities } from '@/api/city'

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

const aqiColor = computed(() => {
  if (!airQuality.value) return '#909399'
  const aqi = airQuality.value.aqi
  if (!aqi) return '#909399'
  if (aqi <= 50) return '#67C23A'
  if (aqi <= 100) return '#E6A23C'
  if (aqi <= 150) return '#F56C6C'
  if (aqi <= 200) return '#FF0000'
  return '#8B0000'
})

function indexColor(level) {
  if (level && (level.includes('适宜') || level.includes('舒适'))) return '#67C23A'
  if (level && (level.includes('较'))) return '#E6A23C'
  if (level && (level.includes('不宜') || level.includes('冷') || level.includes('热'))) return '#F56C6C'
  return '#409EFF'
}

// 加载城市列表
async function loadCities() {
  try {
    const res = await getAllCities({ page: 1, page_size: 1000 })
    cities.value = res?.items || []
    console.log('加载城市数量:', cities.value.length)
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
  } catch (error) {
    console.error('获取天气数据失败:', error)
    ElMessage.error('获取天气数据失败')
  } finally {
    loading.value = false
  }
}

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
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;

  .index-name {
    font-size: 14px;
    color: #606266;
    margin-bottom: 4px;
  }

  .index-level {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 8px;
  }

  .index-desc {
    font-size: 12px;
    color: #909399;
    line-height: 1.4;
  }
}

.card h3 {
  margin: 0 0 16px;
  font-size: 16px;
}
</style>
