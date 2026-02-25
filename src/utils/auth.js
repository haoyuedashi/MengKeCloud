const ACCESS_TOKEN_KEY = 'mengke_access_token'
const REFRESH_TOKEN_KEY = 'mengke_refresh_token'
const USER_KEY = 'mengke_user'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || ''
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY) || ''
}

export function getCurrentUser() {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (_error) {
    return null
  }
}

export function getCurrentRole() {
  return getCurrentUser()?.role || ''
}

export function getMustChangePassword() {
  return Boolean(getCurrentUser()?.mustChangePassword)
}

export function getCurrentStaffId() {
  return getCurrentUser()?.staffId || ''
}

export function saveSession(payload) {
  const user = {
    staffId: payload.staffId,
    name: payload.name,
    role: payload.role,
    phone: payload.phone,
    mustChangePassword: Boolean(payload.mustChangePassword)
  }
  localStorage.setItem(ACCESS_TOKEN_KEY, payload.accessToken || '')
  localStorage.setItem(REFRESH_TOKEN_KEY, payload.refreshToken || '')
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function updateAccessToken(accessToken) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken || '')
}

export function clearSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function isLoggedIn() {
  return Boolean(getAccessToken())
}
