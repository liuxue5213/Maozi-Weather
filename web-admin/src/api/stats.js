import request from './request'

export function getStats() {
  return request({ url: '/system/stats' })
}

export function clearCache() {
  return request({ url: '/system/cache/clear', method: 'post' })
}

export function pingUpstream() {
  return request({ url: '/system/ping-upstream' })
}

export function getConfig() {
  return request({ url: '/system/config' })
}

export function listUsers() {
  return request({ url: '/system/users' })
}

export function toggleUserActive(userId) {
  return request({ url: `/system/users/${userId}/toggle-active`, method: 'post' })
}
