<template>
  <div class="dashboard">
    <!-- 顶部欢迎区 -->
    <div class="welcome-section">
      <div class="welcome-text">
        <h2>你好，{{ hourGreeting }}</h2>
        <p class="subtitle">今天想关注哪里的天气？</p>
      </div>
      <div class="weather-emoji">{{ weatherEmoji }}</div>
    </div>

    <!-- 快速统计 - 手绘风格 -->
    <div class="stats-row">
      <div class="stat-card stat-cities">
        <div class="stat-icon">📍</div>
        <div class="stat-info">
          <div class="stat-number">{{ formatCount(stats.cityCount) }}</div>
          <div class="stat-label">关注城市</div>
        </div>
      </div>
      <div class="stat-card stat-tasks">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-number">{{ stats.syncTasks }}</div>
          <div class="stat-label">同步任务</div>
        </div>
      </div>
      <div class="stat-card stat-records">
        <div class="stat-icon">📁</div>
        <div class="stat-info">
          <div class="stat-number">{{ formatCount(stats.historyRecords) }}</div>
          <div class="stat-label">历史记录</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h3 class="section-title">快捷操作</h3>
      <div class="actions-grid">
        <router-link to="/weather" class="action-card">
          <span class="action-icon">🌤️</span>
          <span class="action-name">查看天气</span>
        </router-link>
        <router-link to="/cities" class="action-card">
          <span class="action-icon">🏙️</span>
          <span class="action-name">城市管理</span>
        </router-link>
        <router-link to="/history" class="action-card">
          <span class="action-icon">📥</span>
          <span class="action-name">数据同步</span>
        </router-link>
        <router-link to="/analysis" class="action-card">
          <span class="action-icon">📈</span>
          <span class="action-name">数据分析</span>
        </router-link>
      </div>
    </div>

    <!-- 系统状态 -->
    <div class="system-status">
      <h3 class="section-title">系统状态</h3>
      <div class="status-list">
        <div class="status-item">
          <span class="status-dot ok"></span>
          <span class="label">CMA API</span>
          <span class="value">正常</span>
        </div>
        <div class="status-item">
          <span class="status-dot ok"></span>
          <span class="label">Redis 缓存</span>
          <span class="value">正常</span>
        </div>
        <div class="status-item">
          <span class="status-dot ok"></span>
          <span class="label">MySQL</span>
          <span class="value">正常</span>
        </div>
        <div class="status-item">
          <span class="status-dot ok"></span>
          <span class="label">定时任务</span>
          <span class="value">运行中</span>
        </div>
      </div>
    </div>

    <div class="footer-note">
      帽子天气 · 数据来源：中国气象局
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStats } from '@/api/stats'

const stats = ref({
  cityCount: 0,
  followCount: 0,
  syncTasks: 0,
  historyRecords: 0,
})

// 超过一万显示 x.x万，避免长数字撑爆卡片
function formatCount(n) {
  if (n == null) return '—'
  return n >= 10000 ? `${(n / 10000).toFixed(1)}万` : String(n)
}

onMounted(async () => {
  try {
    const res = await getStats()
    if (res) stats.value = { ...stats.value, ...res }
  } catch (error) {
    // 统计加载失败保持 0 展示，错误已由拦截器提示
  }
})

const hourGreeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了，注意休息'
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  if (h < 22) return '晚上好'
  return '夜深了，注意休息'
})

const weatherEmoji = computed(() => {
  const h = new Date().getHours()
  if (h >= 6 && h < 18) return '☀️'
  return '🌙'
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.welcome-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding: 24px 28px;
  background: linear-gradient(135deg, #fff8f0 0%, #f0f7ff 100%);
  border-radius: 16px;
  border: 1px solid #e8e8e8;

  .welcome-text {
    h2 {
      margin: 0;
      font-size: 22px;
      font-weight: 600;
      color: #333;
    }
    .subtitle {
      margin: 6px 0 0;
      color: #888;
      font-size: 14px;
    }
  }

  .weather-emoji {
    font-size: 48px;
    line-height: 1;
  }
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e8e8e8;
  transition: transform 0.2s, box-shadow 0.2s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  .stat-icon {
    font-size: 32px;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f5f5f5;
    border-radius: 10px;
  }

  .stat-number {
    font-size: 24px;
    font-weight: 700;
    color: #333;
  }

  .stat-label {
    font-size: 13px;
    color: #888;
    margin-top: 2px;
  }
}

.stat-cities .stat-icon { background: #fff3e0; }
.stat-tasks .stat-icon { background: #e3f2fd; }
.stat-records .stat-icon { background: #f3e5f5; }

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #555;
  margin: 0 0 16px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 32px;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 12px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  text-decoration: none;
  color: #555;
  transition: all 0.2s;

  &:hover {
    border-color: #409eff;
    background: #f0f7ff;
    transform: translateY(-2px);
  }

  .action-icon {
    font-size: 28px;
  }

  .action-name {
    font-size: 13px;
    font-weight: 500;
  }
}

.system-status {
  margin-bottom: 24px;

  .status-list {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    padding: 16px 20px;
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;

      &.ok { background: #52c41a; }
      &.warn { background: #faad14; }
      &.error { background: #ff4d4f; }
    }

    .label {
      flex: 1;
      font-size: 14px;
      color: #555;
    }

    .value {
      font-size: 13px;
      color: #888;
    }
  }
}

.footer-note {
  text-align: center;
  color: #bbb;
  font-size: 12px;
  padding: 16px;
}
</style>
