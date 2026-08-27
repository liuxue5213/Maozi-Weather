import request from './request'

export function getMyCities() {
  return request({ url: '/cities/list' })
}

export function addCity(data) {
  return request({ url: '/cities/add', method: 'post', data })
}

export function deleteCity(id) {
  return request({ url: `/cities/delete/${id}`, method: 'delete' })
}

export function searchCities(keyword) {
  return request({ url: '/cities/search', params: { keyword } })
}

export function getAllCities(params) {
  return request({ url: '/cities/all', params })
}

// ===== 城市库管理（管理员） =====

export function createCityAdmin(data) {
  return request({ url: '/cities/manage/create', method: 'post', data })
}

export function updateCityAdmin(id, data) {
  return request({ url: `/cities/manage/${id}`, method: 'put', data })
}

export function deleteCityAdmin(id) {
  return request({ url: `/cities/manage/${id}`, method: 'delete' })
}
