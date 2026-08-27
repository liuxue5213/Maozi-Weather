<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统配置</h2>
    </div>

    <el-tabs tab-position="left" class="settings-tabs">
      <el-tab-pane label="数据源与接口">
        <div class="card">
          <h3>运行时配置</h3>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 20px"
            title="数据源密钥通过后端 .env 文件配置（CMA_APPID/CMA_APPSECRET、QWEATHER_* 等），修改后重启后端生效；密钥不在页面明文存储或回传"
          />
          <el-descriptions :column="1" border style="max-width: 560px" v-loading="configLoading">
            <el-descriptions-item label="运行环境">{{ runtimeConfig.app_env || '—' }}</el-descriptions-item>
            <el-descriptions-item label="主数据源">{{ runtimeConfig.primary_source || '—' }}</el-descriptions-item>
            <el-descriptions-item label="自动备用切换">
              {{ runtimeConfig.fallback_enabled ? '已启用' : '未启用' }}
            </el-descriptions-item>
            <el-descriptions-item label="CMA 密钥">
              <el-tag v-if="runtimeConfig.cma_configured" type="success" size="small">已配置</el-tag>
              <el-tag v-else type="info" size="small">未配置</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="和风天气">
              <el-tag v-if="runtimeConfig.qweather_configured" type="success" size="small">已配置</el-tag>
              <el-tag v-else type="info" size="small">未配置</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="CMA 限流">
              {{ runtimeConfig.qps_limit ?? '—' }} 次/秒
            </el-descriptions-item>
            <el-descriptions-item label="失败重试次数">
              {{ runtimeConfig.max_retries ?? '—' }}
            </el-descriptions-item>
          </el-descriptions>

          <div style="margin-top: 16px; display: flex; gap: 12px">
            <el-button @click="loadConfig">刷新配置</el-button>
            <el-button type="primary" :loading="pinging" @click="testConnection">测试上游连通性</el-button>
            <el-button
              v-if="pingResult"
              :type="pingResult.ok ? 'success' : 'danger'"
              plain
              disabled
            >
              {{ pingResult.ok ? `连通正常 · ${pingResult.latency_ms}ms` : `失败：${pingResult.error}` }}
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="用户管理">
        <div class="card">
          <h3>系统用户</h3>
          <el-table v-loading="usersLoading" :data="users" stripe>
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="real_name" label="姓名">
              <template #default="{ row }">{{ row.real_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="is_admin" label="角色">
              <template #default="{ row }">
                <el-tag v-if="row.is_admin" type="danger" size="small">管理员</el-tag>
                <el-tag v-else type="info" size="small">普通用户</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button
                  link
                  :type="row.is_active ? 'danger' : 'primary'"
                  :disabled="row.is_current"
                  @click="handleToggleUser(row)"
                >
                  {{ row.is_active ? '禁用' : '启用' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="缓存管理">
        <div class="card">
          <h3>Redis 缓存</h3>
          <el-descriptions :column="1" border style="max-width: 500px">
            <el-descriptions-item label="实况缓存 TTL">10 分钟</el-descriptions-item>
            <el-descriptions-item label="预报缓存 TTL">1 小时</el-descriptions-item>
            <el-descriptions-item label="预警缓存 TTL">5 分钟</el-descriptions-item>
            <el-descriptions-item label="生活指数缓存 TTL">1 小时</el-descriptions-item>
          </el-descriptions>
          <el-button
            type="warning"
            style="margin-top: 16px"
            :loading="clearing"
            @click="clearAllCache"
          >
            清空所有天气缓存
          </el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getConfig, listUsers, toggleUserActive, clearCache, pingUpstream } from '@/api/stats'

const runtimeConfig = reactive({})
const configLoading = ref(false)
const pinging = ref(false)
const pingResult = ref(null)

const users = ref([])
const usersLoading = ref(false)
const clearing = ref(false)

async function loadConfig() {
  configLoading.value = true
  try {
    const res = await getConfig()
    if (res) Object.assign(runtimeConfig, res)
  } finally {
    configLoading.value = false
  }
}

async function testConnection() {
  pinging.value = true
  try {
    pingResult.value = await pingUpstream()
  } catch (error) {
    pingResult.value = null
  } finally {
    pinging.value = false
  }
}

async function loadUsers() {
  usersLoading.value = true
  try {
    users.value = await listUsers()
  } catch (error) {
    users.value = []
  } finally {
    usersLoading.value = false
  }
}

async function handleToggleUser(row) {
  const action = row.is_active ? '禁用' : '启用'
  await ElMessageBox.confirm(`确定${action}用户「${row.username}」？`, '提示', { type: 'warning' })
  await toggleUserActive(row.id)
  ElMessage.success(`已${action}`)
  loadUsers()
}

async function clearAllCache() {
  await ElMessageBox.confirm('确定清空所有天气缓存？清空后首个请求会稍慢。', '提示', { type: 'warning' })
  clearing.value = true
  try {
    const res = await clearCache()
    ElMessage.success(res?.message || '缓存已清空')
  } finally {
    clearing.value = false
  }
}

onMounted(() => {
  loadConfig()
  loadUsers()
})
</script>

<style lang="scss" scoped>
.settings-tabs {
  background: #fff;
  border-radius: 8px;

  .card {
    margin: 0;
    box-shadow: none;
  }
}

.card h3 {
  margin: 0 0 16px;
  font-size: 16px;
}
</style>
