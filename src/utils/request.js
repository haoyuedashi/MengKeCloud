import axios from 'axios'
import { ElMessage } from 'element-plus'
import { clearSession, getAccessToken, getRefreshToken, updateAccessToken } from '@/utils/auth'

const request = axios.create({
  baseURL: '',
  timeout: 10000
})

let refreshingPromise = null

async function refreshAccessTokenOnce() {
  if (!refreshingPromise) {
    const refresh = getRefreshToken()
    if (!refresh) {
      throw new Error('missing refresh token')
    }
    refreshingPromise = axios
      .post('/api/v1/auth/refresh', { refreshToken: refresh })
      .then((resp) => {
        const data = resp?.data?.data || {}
        if (!data.accessToken) {
          throw new Error('refresh failed')
        }
        updateAccessToken(data.accessToken)
        return data.accessToken
      })
      .finally(() => {
        refreshingPromise = null
      })
  }
  return refreshingPromise
}

request.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && typeof res.code === 'number') {
      if (res.code !== 200) {
        ElMessage.error(res.message || '请求失败')
        return Promise.reject(new Error(res.message || 'request failed'))
      }
      return res.data
    }
    return res
  },
  async (error) => {
    const status = error?.response?.status
    const originalConfig = error?.config || {}

    if (status === 401 && !originalConfig._retry && !originalConfig.skipAuthRetry) {
      originalConfig._retry = true
      try {
        const newToken = await refreshAccessTokenOnce()
        originalConfig.headers = originalConfig.headers || {}
        originalConfig.headers.Authorization = `Bearer ${newToken}`
        return request(originalConfig)
      } catch (_refreshError) {
        clearSession()
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }

    const isTimeout = error?.code === 'ECONNABORTED' || String(error?.message || '').toLowerCase().includes('timeout')
    const msg = isTimeout
      ? '请求超时，请稍后重试（AI模型响应较慢时可在系统设置提高超时秒数）'
      : (error?.response?.data?.message || error.message || '网络或服务器错误')
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
