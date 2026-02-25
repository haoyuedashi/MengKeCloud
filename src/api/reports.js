import request from '@/utils/request'

export function getReportsOverview(params = {}) {
  const {
    trendWindow = '7days',
    startDate,
    endDate,
    deptName,
    ownerId
  } = params

  return request({
    url: '/api/v1/reports/overview',
    method: 'get',
    params: {
      trend_window: trendWindow,
      start_date: startDate,
      end_date: endDate,
      dept_name: deptName,
      owner_id: ownerId
    }
  })
}
