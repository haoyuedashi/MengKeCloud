const CITY_LIST = [
  '北京', '上海', '广州', '深圳', '天津', '重庆', '成都', '杭州', '南京', '武汉',
  '西安', '苏州', '郑州', '长沙', '青岛', '宁波', '东莞', '佛山', '合肥', '福州',
  '厦门', '济南', '沈阳', '大连', '昆明', '南宁', '南昌', '贵阳', '太原', '石家庄',
  '哈尔滨', '长春', '兰州', '乌鲁木齐', '呼和浩特', '海口', '三亚', '珠海', '无锡', '常州',
  '嘉兴', '金华', '绍兴', '温州', '台州', '湖州', '扬州', '徐州', '南通', '盐城',
  '烟台', '潍坊', '临沂', '洛阳', '开封', '泉州', '漳州', '惠州', '中山', '汕头'
]

const normalizeToken = (value) => String(value || '').trim().replace(/市$/u, '')

export const normalizeCityInput = (value) => {
  const token = normalizeToken(value)
  if (!token) return ''
  const exact = CITY_LIST.find((item) => item === token)
  if (exact) return exact
  const fuzzy = CITY_LIST.find((item) => item.startsWith(token) || token.startsWith(item))
  return fuzzy || token
}

export const queryCitySuggestions = (queryString) => {
  const token = normalizeToken(queryString)
  if (!token) {
    return CITY_LIST.slice(0, 20).map((item) => ({ value: item }))
  }
  return CITY_LIST
    .filter((item) => item.includes(token) || item.startsWith(token))
    .slice(0, 20)
    .map((item) => ({ value: item }))
}
