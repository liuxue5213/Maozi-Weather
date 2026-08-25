import request from './request'

export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data,
  })
}

export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post',
  })
}

export function getMe() {
  return request({
    url: '/auth/me',
    method: 'get',
  })
}
