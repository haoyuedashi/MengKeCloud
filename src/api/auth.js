import request from '@/utils/request'

export function loginByPhone(data) {
  return request({
    url: '/api/v1/auth/login',
    method: 'post',
    data
  })
}

export function refreshToken(refreshToken) {
  return request({
    url: '/api/v1/auth/refresh',
    method: 'post',
    data: { refreshToken },
    skipAuthRetry: true
  })
}

export function logout(refreshToken) {
  return request({
    url: '/api/v1/auth/logout',
    method: 'post',
    data: { refreshToken },
    skipAuthRetry: true
  })
}

export function getMe() {
  return request({
    url: '/api/v1/auth/me',
    method: 'get'
  })
}

export function changePassword(data) {
  return request({
    url: '/api/v1/auth/change-password',
    method: 'post',
    data
  })
}
