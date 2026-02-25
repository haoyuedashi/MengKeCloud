const CHINESE_NAME_REGEX = /^[\u4e00-\u9fa5·]{1,3}$/
const ENGLISH_NAME_REGEX = /^[A-Za-z][A-Za-z\s'.-]{0,19}$/

export function validateLeadName(name) {
  const value = String(name || '').trim()
  if (!value) {
    return { valid: false, message: '客户姓名不能为空' }
  }

  if (CHINESE_NAME_REGEX.test(value)) {
    return { valid: true, message: '' }
  }

  if (ENGLISH_NAME_REGEX.test(value)) {
    return { valid: true, message: '' }
  }

  return {
    valid: false,
    message: '客户姓名仅支持中文(最多3字)或英文(最多20字符)'
  }
}
