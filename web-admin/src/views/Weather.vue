<template>
  <div class="page-container">
    <div class="page-header">
      <h2>实时天气</h2>
      <span class="data-source-tag">数据源：Open-Meteo / 和风天气</span>
    </div>

    <div class="card">
      <el-select v-model="selectedCity" placeholder="选择城市" style="width: 200px" @change="fetchWeather">
        <el-option
          v-for="city in cities"
          :key="city.id"
          :label="city.city_name"
          :value="city.id"
        />
      </el-select>
      <span v-if="dataSource" class="source-tag">当前来源: {{ dataSource }}</span>
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
              <el-descriptions-item label="风向风速">{{ realtime.wind_direction }} {{ realtime.wind_speed }}m/s</el-descriptions-item>
              <el-descriptions-item label="降水">{{ realtime.precipitation }}mm</el-descriptions-item>
            </el-descriptions>

            <!-- 日出日落 -->
            <div v-if="sunInfo" class="sun-info">
              <el-divider>日出日落</el-divider>
              <el-descriptions :column="2" size="small">
                <el-descriptions-item label="日出">
                  <el-icon><Top /></el-icon> {{ formatTime(sunInfo.sunrise) }}
                </el-descriptions-item>
                <el-descriptions-item label="日落">
                  <el-icon><Bottom /></el-icon> {{ formatTime(sunInfo.sunset) }}
                </el-descriptions-item>
                <el-descriptions-item label="昼长" :span="2">{{ sunInfo.daylight_hours }} 小时</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
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
              <el-descriptions-item label="首要污染物" :span="2">{{ airQuality.aqi_primary || '-' }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else description="暂无空气质量数据" />
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
            <div class="index-icon">
              <el-icon :size="24" :color="indexColor(item.index_level)">
                <component :is="indexIcon(item.index_type)" />
              </el-icon>
            </div>
            <div class="index-name">{{ item.index_name }}</div>
            <div class="index-level" :style="{ color: indexColor(item.index_level) }">{{ item.index_level }}</div>
            <div class="index-desc">{{ item.index_desc }}</div>
          </div>
        </el-col>
      </el-row>
      <el-empty v-else description="暂无生活指数数据" />
    </div>

    <!-- 预报 -->
    <div class="card" style="margin-top: 20px">
      <h3>未来16天预报</h3>
      <el-table :data="forecast" size="small" v-if="forecast.length">
        <el-table-column prop="forecast_time" label="日期" width="120" />
        <el-table-column prop="weather_desc" label="天气" />
        <el-table-column label="温度">
          <template #default="{ row }">{{ row.temp_min }}~{{ row.temp_max }}°C</template>
        </el-table-column>
        <el-table-column prop="precipitation_sum" label="降水" width="80" />
        <el-table-column prop="wind_speed_max" label="最大风速" width="100" />
      </el-table>
      <el-empty v-else description="暂无预报数据" />
    </div>

    <div class="data-source-tag">数据来源：Open-Meteo / 和风天气 / 中国气象局</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Top, Bottom, Umbrella, Van, Basketball, Sunny, Position } from '@element-plus/icons-vue'
import { getRealtime, getForecast, getWarning } from '@/api/weather'
import { getAirQuality, getLifeIndex, getSunriseSunset } from '@/api/air'

const cities = ref([])
const selectedCity = ref(null)
const realtime = ref(null)
const forecast = ref([])
const warnings = ref([])
const airQuality = ref(null)
const lifeIndices = ref([])
const sunInfo = ref(null)
const dataSource = ref('')

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

function indexIcon(type) {
  const icons = {
    clothing: Umbrella,
    car_wash: Van,
    sport: Basketball,
    uv: Sunny,
    travel: Position,
  }
  return icons[type] || Sunny
}

function indexColor(level) {
  if (level && (level.includes('适宜') || level.includes('舒适'))) return '#67C23A'
  if (level && (level.includes('较'))) return '#E6A23C'
  if (level && (level.includes('不宜') || level.includes('冷') || level.includes('热'))) return '#F56C6C'
  return '#409EFF'
}

async function fetchWeather() {
  if (!selectedCity.value) return

  // 获取城市经纬度（实际项目中从城市库获取）
  const cityInfo = cities.value.find(c => c.id === selectedCity.value)
  const lat = cityInfo?.latitude || 39.9042
  const lon = cityInfo?.longitude || 116.4074

  // 实时天气
  realtime.value = await getRealtime(selectedCity.value, lat, lon)
  dataSource.value = realtime.value?.data_source || ''

  // 预报
  const forecastData = await getForecast(selectedCity.value, lat, lon, 16)
  forecast.value = forecastData.daily || []

  // 预警
  warnings.value = await getWarning(selectedCity.value)

  // 空气质量
  airQuality.value = await getAirQuality(selectedCity.value)

  // 生活指数
  const temp = realtime.value?.temperature || 20
  const humidity = realtime.value?.humidity || 50
  const precip = realtime.value?.precipitation || 0
  const wind = realtime.value?.wind_speed || 0
  lifeIndices.value = await getLifeIndex(selectedCity.value, {
    temperature: temp,
    humidity,
    precipitation: precip,
    wind_speed: wind,
  })

  // 日出日落
  sunInfo.value = await getSunriseSunset(selectedCity.value, { latitude: lat, longitude: lon })
}

function warningType(level) {
  const map = { '红色': 'error', '橙色': 'warning', '黄色': 'info', '蓝色': 'info' }
  return map[level] || 'info'
}

// 格式化时间（Open-Meteo 返回 ISO 格式如 "2024-01-01T05:42"）
function formatTime(timeStr) {
  if (!timeStr) return '-'
  // 如果是 ISO 格式，提取时分部分
  if (timeStr.includes('T')) {
    return timeStr.split('T')[1]?.substring(0, 5) || timeStr
  }
  return timeStr
}

onMounted(async () => {
  // TODO: 获取关注城市列表
})
</script>

<style lang="scss" scoped>
.data-source-tag {
  font-size: 12px;
  color: #909399;
  margin-left: 16px;
}

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

  .index-icon {
    margin-bottom: 8px;
  }

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
