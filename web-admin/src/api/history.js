import request from './request'

export function createSyncTask(data) {
  return request({ url: '/history/task/create', method: 'post', data })
}

export function getSyncTasks(params) {
  return request({ url: '/history/task/list', params })
}

export function retryTask(taskId) {
  return request({ url: `/history/task/${taskId}/retry`, method: 'post' })
}

export function stopTask(taskId) {
  return request({ url: `/history/task/${taskId}/stop`, method: 'post' })
}

export function queryHistory(params) {
  return request({ url: '/history/query', params })
}

export function exportHistory(params) {
  return request({ url: '/history/export', params, responseType: 'blob' })
}
