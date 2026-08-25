<template>
  <el-container class="layout">
    <el-aside width="200px" class="aside">
      <div class="logo">
        <span class="logo-icon">🎩</span>
        <span class="logo-text">帽子天气</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        class="menu"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="`/${item.path}`"
        >
          <span class="menu-icon">{{ item.icon }}</span>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span>{{ route.meta.title }}</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <span class="user-avatar">管</span>
              {{ userStore.userInfo?.username || '管理员' }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const menuItems = [
  { path: 'dashboard', title: '首页', icon: '🏠' },
  { path: 'weather', title: '实时天气', icon: '🌤️' },
  { path: 'cities', title: '城市管理', icon: '🏙️' },
  { path: 'history', title: '历史同步', icon: '📥' },
  { path: 'history-query', title: '数据查询', icon: '🔍' },
  { path: 'analysis', title: '数据分析', icon: '📈' },
  { path: 'settings', title: '系统配置', icon: '⚙️' },
  { path: 'logs', title: '监控日志', icon: '📋' },
]

async function handleCommand(command) {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style lang="scss" scoped>
.layout {
  height: 100vh;
}

.aside {
  background: #fff;
  border-right: 1px solid #e8e8e8;

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border-bottom: 1px solid #e8e8e8;

    .logo-icon {
      font-size: 24px;
    }

    .logo-text {
      font-size: 18px;
      font-weight: 700;
      color: #333;
    }
  }

  .menu {
    border-right: none;
    padding-top: 8px;

    .menu-icon {
      margin-right: 8px;
      font-size: 16px;
    }

    .el-menu-item {
      height: 44px;
      line-height: 44px;
      margin: 4px 8px;
      border-radius: 8px;

      &.is-active {
        background: #f0f7ff;
        color: #409eff;
      }

      &:hover {
        background: #f5f7fa;
      }
    }
  }
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #e8e8e8;

  .header-left {
    font-size: 16px;
    font-weight: 500;
    color: #333;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    color: #555;
    font-size: 14px;

    .user-avatar {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: #e8f4fd;
      color: #409eff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 600;
    }
  }
}
</style>
