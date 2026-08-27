import request from './request'

export function getApiLogs(params) {
  return request({ url: '/logs/api', params })
}

export function getTaskLogs(params) {
  return request({ url: '/logs/tasks', params })
}

export function getCacheStats() {
  return request({ url: '/logs/cache' })
}
