<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统配置</h2>
    </div>

    <el-tabs tab-position="left" class="settings-tabs">
      <el-tab-pane label="CMA 接口配置">
        <div class="card">
          <h3>中国气象数据网 API 配置</h3>
          <el-alert
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 20px"
          >
            <template #title>
              安全提示：CMA 密钥仅保存在后端，前端仅用于修改配置，不会明文展示
            </template>
          </el-alert>
          <el-form :model="cmaConfig" label-width="120px" style="max-width: 500px">
            <el-form-item label="AppID">
              <el-input v-model="cmaConfig.appid" placeholder="CMA AppID" />
            </el-form-item>
            <el-form-item label="AppSecret">
              <el-input
                v-model="cmaConfig.appsecret"
                type="password"
                placeholder="留空表示不修改"
                show-password
              />
            </el-form-item>
            <el-form-item label="QPS 限制">
              <el-input-number v-model="cmaConfig.qps_limit" :min="1" :max="20" />
              <span class="form-tip">每秒请求数（建议 ≤10）</span>
            </el-form-item>
            <el-form-item label="重试次数">
              <el-input-number v-model="cmaConfig.max_retries" :min="1" :max="10" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveCmaConfig">保存配置</el-button>
              <el-button @click="testConnection">测试连接</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="用户管理">
        <div class="card">
          <h3>系统用户</h3>
          <el-table :data="users" stripe>
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="real_name" label="姓名" />
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
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button link type="primary">编辑</el-button>
                <el-button link type="danger">禁用</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="缓存配置">
        <div class="card">
          <h3>Redis 缓存配置</h3>
          <el-descriptions :column="1" border style="max-width: 500px">
            <el-descriptions-item label="实况缓存">10 分钟</el-descriptions-item>
            <el-descriptions-item label="预报缓存">1 小时</el-descriptions-item>
            <el-descriptions-item label="预警缓存">5 分钟</el-descriptions-item>
          </el-descriptions>
          <el-button type="warning" style="margin-top: 16px" @click="clearCache">
            清空所有缓存
          </el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const cmaConfig = reactive({
  appid: '',
  appsecret: '',
  qps_limit: 10,
  max_retries: 3,
})

const users = ref([])

function saveCmaConfig() {
  ElMessage.success('配置已保存')
}

function testConnection() {
  ElMessage.info('正在测试 CMA 连接...')
}

async function clearCache() {
  await ElMessageBox.confirm('确定清空所有缓存？', '提示', { type: 'warning' })
  ElMessage.success('缓存已清空')
}
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

.form-tip {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}
</style>
