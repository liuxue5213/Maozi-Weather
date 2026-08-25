import request from './request'

export function analyzeStation(params) {
  return request({ url: '/analysis/station', params })
}

export function monthlyAnalysis(params) {
  return request({ url: '/analysis/monthly', params })
}
