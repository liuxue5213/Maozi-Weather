<template>
  <div class="page-container">
    <div class="page-header">
      <h2>城市站点管理</h2>
    </div>

    <div class="card">
      <div class="toolbar">
        <el-input
          v-model="searchKey"
          placeholder="搜索城市名称"
          style="width: 240px"
          :prefix-icon="Search"
          clearable
        />
        <el-button type="primary" :icon="Plus" @click="showAddDialog = true">
          添加城市
        </el-button>
        <el-button :icon="Upload">批量导入</el-button>
      </div>

      <el-table :data="cities" stripe>
        <el-table-column prop="city_name" label="城市名称" />
        <el-table-column prop="city_code" label="城市编码" width="120" />
        <el-table-column prop="station_id" label="站点ID" width="120" />
        <el-table-column prop="province" label="所属省份" width="120" />
        <el-table-column prop="longitude" label="经度" width="100" />
        <el-table-column prop="latitude" label="纬度" width="100" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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

    <!-- 添加城市对话框 -->
    <el-dialog v-model="showAddDialog" title="添加城市" width="500px">
      <el-form :model="cityForm" label-width="100px">
        <el-form-item label="城市名称">
          <el-input v-model="cityForm.city_name" />
        </el-form-item>
        <el-form-item label="站点ID">
          <el-input v-model="cityForm.station_id" placeholder="气象站点ID" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number v-model="cityForm.longitude" :precision="4" />
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number v-model="cityForm.latitude" :precision="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAllCities } from '@/api/city'

const cities = ref([])
const searchKey = ref('')
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const showAddDialog = ref(false)
const cityForm = ref({
  city_name: '',
  station_id: '',
  longitude: 0,
  latitude: 0,
})

async function fetchCities() {
  const res = await getAllCities({ page: page.value, page_size: pageSize.value })
  cities.value = res
}

function handleEdit(row) {
  // TODO: 编辑城市
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除城市「${row.city_name}」？`, '提示', { type: 'warning' })
  // TODO: 调用删除接口
  ElMessage.success('删除成功')
}

function handleAdd() {
  // TODO: 调用添加接口
  showAddDialog.value = false
  ElMessage.success('添加成功')
}

onMounted(() => {
  fetchCities()
})
</script>

<style lang="scss" scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
