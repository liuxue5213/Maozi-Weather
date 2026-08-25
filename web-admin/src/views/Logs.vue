<template>
  <div class="page-container">
    <div class="page-header">
      <h2>监控日志</h2>
    </div>

    <el-tabs>
      <el-tab-pane label="API 调用日志">
        <div class="card">
          <el-table :data="apiLogs" stripe size="small">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="endpoint" label="接口" width="200" />
            <el-table-column prop="params" label="参数" width="200" show-overflow-tooltip />
            <el-table-column prop="status_code" label="状态码" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status_code === 200 ? 'success' : 'danger'" size="small">
                  {{ row.status_code }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="response_time" label="响应时间" width="100" />
            <el-table-column prop="created_at" label="时间" width="180" />
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="同步任务日志">
        <div class="card">
          <el-table :data="taskLogs" stripe size="small">
            <el-table-column prop="task_id" label="任务ID" width="80" />
            <el-table-column prop="station_id" label="站点" width="100" />
            <el-table-column prop="event" label="事件" width="120" />
            <el-table-column prop="message" label="详情" />
            <el-table-column prop="created_at" label="时间" width="180" />
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="缓存监控">
        <div class="card">
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="cache-stat">
                <div class="cache-value">{{ cacheStats.hitRate }}%</div>
                <div class="cache-label">缓存命中率</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="cache-stat">
                <div class="cache-value">{{ cacheStats.realtimeCount }}</div>
                <div class="cache-label">实况缓存数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="cache-stat">
                <div class="cache-value">{{ cacheStats.forecastCount }}</div>
                <div class="cache-label">预报缓存数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="cache-stat">
                <div class="cache-value">{{ cacheStats.warningCount }}</div>
                <div class="cache-label">预警缓存数</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const apiLogs = ref([])
const taskLogs = ref([])
const cacheStats = ref({
  hitRate: 0,
  realtimeCount: 0,
  forecastCount: 0,
  warningCount: 0,
})
</script>

<style lang="scss" scoped>
.cache-stat {
  text-align: center;
  padding: 20px;

  .cache-value {
    font-size: 32px;
    font-weight: bold;
    color: #409eff;
  }

  .cache-label {
    color: #909399;
    margin-top: 8px;
  }
}
</style>
