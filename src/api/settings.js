import request from '@/utils/request'

export function getPlatformSettings() {
  return request({
    url: '/api/v1/settings/platform',
    method: 'get'
  })
}

export function savePlatformSettings(data) {
  return request({
    url: '/api/v1/settings/platform',
    method: 'put',
    data
  })
}

export function testPlatformAiConnection(data) {
  return request({
    url: '/api/v1/settings/platform/test-ai',
    method: 'post',
    data
  })
}

export function getOrgData() {
  return request({
    url: '/api/v1/settings/org',
    method: 'get'
  })
}

export function createDepartment(data) {
  return request({
    url: '/api/v1/settings/org/departments',
    method: 'post',
    data
  })
}

export function updateDepartment(id, data) {
  return request({
    url: `/api/v1/settings/org/departments/${id}`,
    method: 'put',
    data
  })
}

export function deleteDepartment(id) {
  return request({
    url: `/api/v1/settings/org/departments/${id}`,
    method: 'delete'
  })
}

export function createOrgUser(data) {
  return request({
    url: '/api/v1/settings/org/users',
    method: 'post',
    data
  })
}

export function updateOrgUser(id, data) {
  return request({
    url: `/api/v1/settings/org/users/${id}`,
    method: 'put',
    data
  })
}

export function deleteOrgUser(id) {
  return request({
    url: `/api/v1/settings/org/users/${id}`,
    method: 'delete'
  })
}

export function getRoles() {
  return request({
    url: '/api/v1/settings/roles',
    method: 'get'
  })
}

export function createRole(data) {
  return request({
    url: '/api/v1/settings/roles',
    method: 'post',
    data
  })
}

export function updateRole(id, data) {
  return request({
    url: `/api/v1/settings/roles/${id}`,
    method: 'put',
    data
  })
}

export function deleteRole(id) {
  return request({
    url: `/api/v1/settings/roles/${id}`,
    method: 'delete'
  })
}

export function getCustomFields(entity) {
  return request({
    url: `/api/v1/settings/fields/${entity}`,
    method: 'get'
  })
}

export function createCustomField(entity, data) {
  return request({
    url: `/api/v1/settings/fields/${entity}`,
    method: 'post',
    data
  })
}

export function updateCustomField(id, data) {
  return request({
    url: `/api/v1/settings/fields/item/${id}`,
    method: 'put',
    data
  })
}

export function deleteCustomField(id) {
  return request({
    url: `/api/v1/settings/fields/item/${id}`,
    method: 'delete'
  })
}

export function getDictTypes() {
  return request({
    url: '/api/v1/settings/dict/types',
    method: 'get'
  })
}

export function getDictItemsManage(dictType) {
  return request({
    url: `/api/v1/settings/dict/${dictType}`,
    method: 'get'
  })
}

export function createDictItem(dictType, data) {
  return request({
    url: `/api/v1/settings/dict/${dictType}`,
    method: 'post',
    data
  })
}

export function updateDictItem(id, data) {
  return request({
    url: `/api/v1/settings/dict/item/${id}`,
    method: 'put',
    data
  })
}

export function deleteDictItem(id) {
  return request({
    url: `/api/v1/settings/dict/item/${id}`,
    method: 'delete'
  })
}

export function moveDictItem(id, direction) {
  return request({
    url: `/api/v1/settings/dict/item/${id}/move`,
    method: 'post',
    data: { direction }
  })
}

export function getRecycleRules() {
  return request({
    url: '/api/v1/settings/rules',
    method: 'get'
  })
}

export function saveRecycleRules(data) {
  return request({
    url: '/api/v1/settings/rules',
    method: 'put',
    data
  })
}
