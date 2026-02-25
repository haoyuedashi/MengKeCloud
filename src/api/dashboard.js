import request from '@/utils/request'

export function getDashboardOverview() {
  return request({
    url: '/api/v1/dashboard/overview',
    method: 'get'
  })
}
