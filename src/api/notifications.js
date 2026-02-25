import request from '@/utils/request'

export function getNotifications(params) {
  return request({
    url: '/api/v1/notifications',
    method: 'get',
    params
  })
}

export function markNotificationRead(notificationId) {
  return request({
    url: `/api/v1/notifications/${notificationId}/read`,
    method: 'put'
  })
}

export function markAllNotificationsRead(params) {
  return request({
    url: '/api/v1/notifications/read-all',
    method: 'put',
    params
  })
}

export function runRecycleNow() {
  return request({
    url: '/api/v1/notifications/recycle/run-now',
    method: 'post'
  })
}
