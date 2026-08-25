<template>
  <div class="page-container">
    <div class="page-header">
      <h2>控制台</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <div class="stat-card">
          <el-icon size="32" color="#409EFF"><Location /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.cityCount }}</div>
            <div class="stat-label">关注城市</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <el-icon size="32" color="#67C23A"><Sunny /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.realtimeCount }}</div>
            <div class="stat-label">实况缓存</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <el-icon size="32" color="#E6A23C"><Download /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.syncTasks }}</div>
            <div class="stat-label">同步任务</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <el-icon size="32" color="#F56C6C"><DataAnalysis /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.historyRecords }}</div>
            <div class="stat-label">历史记录(万)</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <div class="card">
          <h3>最近同步任务</h3>
          <el-table :data="recentTasks" size="small">
            <el-table-column prop="station_id" label="站点" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">
                  {{ statusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="fetched_records" label="已拉取" />
          </el-table>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card">
          <h3>系统状态</h3>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="CMA API">正常</el-descriptions-item>
            <el-descriptions-item label="Redis 缓存">正常</el-descriptions-item>
            <el-descriptions-item label="MySQL">正常</el-descriptions-item>
            <el-descriptions-item label="定时任务">运行中</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>

    <div class="data-source-tag">数据来源：中国气象局</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const stats = ref({
  cityCount: 0,
  realtimeCount: 0,
  syncTasks: 0,
  historyRecords: 0,
})

const recentTasks = ref([])

function statusType(status) {
  const map = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    stopped: 'info',
  }
  return map[status] || 'info'
}

function statusText(status) {
  const map = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    stopped: '已停止',
  }
  return map[status] || status
}
</script>

<style lang="scss" scoped>
.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);

  .stat-info {
    .stat-value {
      font-size: 28px;
      font-weight: bold;
      color: #303133;
    }

    .stat-label {
      font-size: 14px;
      color: #909399;
      margin-top: 4px;
    }
  }
}

.card h3 {
  margin: 0 0 16px;
  font-size: 16px;
}
</style>
