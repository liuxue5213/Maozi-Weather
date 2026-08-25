<template>
  <div class="page-container">
    <div class="page-header">
      <h2>历史数据查询</h2>
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
          <el-button type="primary" :icon="Search" @click="handleQuery">查询</el-button>
          <el-button :icon="Download" @click="handleExport" :disabled="!records.length">导出CSV</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card" style="margin-top: 20px">
      <el-table :data="records" stripe height="calc(100vh - 360px)">
        <el-table-column prop="observe_time" label="观测时间" width="180" />
        <el-table-column prop="temperature" label="温度(℃)" width="100" />
        <el-table-column prop="pressure" label="气压(hPa)" width="100" />
        <el-table-column prop="humidity" label="湿度(%)" width="100" />
        <el-table-column prop="wind_direction" label="风向(°)" width="100" />
        <el-table-column prop="wind_speed" label="风速(m/s)" width="100" />
        <el-table-column prop="precipitation" label="降水(mm)" width="100" />
        <el-table-column label="缺测" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_missing" type="warning" size="small">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </div>

    <div class="data-source-tag">数据来源：中国气象局</div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Search, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { queryHistory, exportHistory } from '@/api/history'

const queryForm = reactive({
  station_id: '',
})
const dateRange = ref([])
const records = ref([])
const page = ref(1)
const pageSize = ref(100)
const total = ref(0)

async function handleQuery() {
  if (!queryForm.station_id) {
    ElMessage.warning('请输入站点ID')
    return
  }
  const params = {
    station_id: queryForm.station_id,
    start_time: dateRange.value?.[0] || '',
    end_time: dateRange.value?.[1] || '',
    page: page.value,
    page_size: pageSize.value,
  }
  records.value = await queryHistory(params)
}

async function handleExport() {
  const params = {
    station_id: queryForm.station_id,
    start_time: dateRange.value?.[0] || '',
    end_time: dateRange.value?.[1] || '',
  }
  const blob = await exportHistory(params)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `history_${queryForm.station_id}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}
</script>
