<template>
  <div class="page-container">
    <div class="page-header">
      <h2>历史数据同步</h2>
    </div>

    <div class="card">
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
          新建同步任务
        </el-button>
        <el-radio-group v-model="statusFilter" size="small">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="pending">待执行</el-radio-button>
          <el-radio-button label="running">执行中</el-radio-button>
          <el-radio-button label="completed">已完成</el-radio-button>
          <el-radio-button label="failed">失败</el-radio-button>
        </el-radio-group>
      </div>

      <el-table :data="tasks" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="station_id" label="站点ID" width="100" />
        <el-table-column prop="start_date" label="开始日期" width="120" />
        <el-table-column prop="end_date" label="结束日期" width="120" />
        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <el-progress
              :percentage="progressPercent(row)"
              :status="progressStatus(row.status)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="fetched_records" label="已拉取" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'failed'"
              link
              type="primary"
              @click="handleRetry(row)"
            >
              重试
            </el-button>
            <el-button
              v-if="row.status === 'running'"
              link
              type="danger"
              @click="handleStop(row)"
            >
              停止
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新建任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建同步任务" width="500px">
      <el-form :model="taskForm" label-width="100px">
        <el-form-item label="站点ID">
          <el-input v-model="taskForm.station_id" placeholder="如: 54511" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="taskForm.start_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="taskForm.end_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建任务</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSyncTasks, createSyncTask, retryTask, stopTask } from '@/api/history'

const tasks = ref([])
const statusFilter = ref('')
const showCreateDialog = ref(false)
const taskForm = ref({
  station_id: '',
  start_date: '',
  end_date: '',
})

async function fetchTasks() {
  const res = await getSyncTasks({ status: statusFilter.value })
  tasks.value = res.items || []
}

function progressPercent(row) {
  if (!row.total_records) return 0
  return Math.round((row.fetched_records / row.total_records) * 100)
}

function progressStatus(status) {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return ''
}

function statusType(status) {
  const map = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger', stopped: 'info' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { pending: '待执行', running: '执行中', completed: '已完成', failed: '失败', stopped: '已停止' }
  return map[status] || status
}

async function handleCreate() {
  await createSyncTask(taskForm.value)
  ElMessage.success('任务创建成功')
  showCreateDialog.value = false
  fetchTasks()
}

async function handleRetry(row) {
  await retryTask(row.id)
  ElMessage.success('任务已重新提交')
  fetchTasks()
}

async function handleStop(row) {
  await ElMessageBox.confirm('确定停止该任务？', '提示', { type: 'warning' })
  await stopTask(row.id)
  ElMessage.success('任务已停止')
  fetchTasks()
}

onMounted(() => {
  fetchTasks()
})
</script>

<style lang="scss" scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
