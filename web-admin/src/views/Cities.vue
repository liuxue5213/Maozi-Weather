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
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-button type="primary" :icon="Plus" @click="openAddDialog">
          添加城市
        </el-button>
      </div>

      <el-table v-loading="loading" :data="cities" stripe>
        <el-table-column prop="city_name" label="城市名称" />
        <el-table-column prop="city_code" label="城市编码" width="120">
          <template #default="{ row }">{{ row.city_code || '-' }}</template>
        </el-table-column>
        <el-table-column prop="station_id" label="站点ID" width="120">
          <template #default="{ row }">{{ row.station_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="province" label="所属省份" width="120">
          <template #default="{ row }">{{ row.province || '-' }}</template>
        </el-table-column>
        <el-table-column prop="longitude" label="经度" width="110" />
        <el-table-column prop="latitude" label="纬度" width="110" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @current-change="fetchCities"
        @size-change="handleSizeChange"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </div>

    <!-- 新增/编辑城市对话框 -->
    <el-dialog v-model="showEditDialog" :title="editingId ? '编辑城市' : '添加城市'" width="500px">
      <el-form ref="formRef" :model="cityForm" :rules="rules" label-width="100px">
        <el-form-item label="城市名称" prop="city_name">
          <el-input v-model="cityForm.city_name" placeholder="如：北京" />
        </el-form-item>
        <el-form-item label="站点ID">
          <el-input v-model="cityForm.station_id" placeholder="气象站点ID，如 54511" />
        </el-form-item>
        <el-form-item label="省份">
          <el-input v-model="cityForm.province" placeholder="如：北京市" />
        </el-form-item>
        <el-form-item label="经度" prop="longitude">
          <el-input-number v-model="cityForm.longitude" :precision="4" :min="-180" :max="180" />
        </el-form-item>
        <el-form-item label="纬度" prop="latitude">
          <el-input-number v-model="cityForm.latitude" :precision="4" :min="-90" :max="90" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAllCities, createCityAdmin, updateCityAdmin, deleteCityAdmin } from '@/api/city'

const cities = ref([])
const searchKey = ref('')
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const showEditDialog = ref(false)
const editingId = ref(null)

const emptyForm = {
  city_name: '',
  station_id: '',
  province: '',
  longitude: null,
  latitude: null,
}
const cityForm = reactive({ ...emptyForm })
const rules = {
  city_name: [{ required: true, message: '请输入城市名称', trigger: 'blur' }],
}

async function fetchCities() {
  loading.value = true
  try {
    const res = await getAllCities({
      page: page.value,
      page_size: pageSize.value,
      keyword: searchKey.value || undefined,
    })
    cities.value = res?.items || []
    total.value = res?.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchCities()
}

function handleSizeChange() {
  page.value = 1
  fetchCities()
}

function openAddDialog() {
  editingId.value = null
  Object.assign(cityForm, emptyForm)
  showEditDialog.value = true
}

function openEditDialog(row) {
  editingId.value = row.id
  Object.assign(cityForm, {
    city_name: row.city_name,
    station_id: row.station_id || '',
    province: row.province || '',
    longitude: row.longitude ?? null,
    latitude: row.latitude ?? null,
  })
  showEditDialog.value = true
}

async function handleSubmit() {
  // 过滤空字符串字段，避免把可空列覆盖为无效值
  const payload = {}
  for (const [k, v] of Object.entries(cityForm)) {
    if (v !== '' && v !== null && v !== undefined) payload[k] = v
  }
  if (!payload.city_name) return

  saving.value = true
  try {
    if (editingId.value) {
      await updateCityAdmin(editingId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await createCityAdmin(payload)
      ElMessage.success('添加成功')
    }
    showEditDialog.value = false
    fetchCities()
  } catch (error) {
    // 错误提示已在拦截器统一弹出
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(
    `确定删除城市「${row.city_name}」？该用户的关注记录将一并移除。`,
    '提示',
    { type: 'warning' }
  )
  await deleteCityAdmin(row.id)
  ElMessage.success('删除成功')
  fetchCities()
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
