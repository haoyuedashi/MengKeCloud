import request from '@/utils/request'

/**
 * 获取线索列表
 * @param {Object} params - 分页与筛选参数 {page, pageSize, keyword, status, source, level}
 */
export function getLeads(params) {
    return request({
        url: '/api/v1/leads',
        method: 'get',
        params
    })
}

/**
 * 获取单条线索详情
 * @param {String} id 
 */
export function getLeadById(id) {
    return request({
        url: `/api/v1/leads/${id}`,
        method: 'get'
    })
}

/**
 * 创建新线索
 * @param {Object} data 
 */
export function createLead(data) {
    return request({
        url: '/api/v1/leads',
        method: 'post',
        data
    })
}

/**
 * 更新线索 (支持增量更新)
 * @param {String} id 
 * @param {Object} data 
 */
export function updateLead(id, data) {
    return request({
        url: `/api/v1/leads/${id}`,
        method: 'put',
        data
    })
}

/**
 * 删除线索
 * @param {String} id 
 */
export function deleteLead(id) {
    return request({
        url: `/api/v1/leads/${id}`,
        method: 'delete'
    })
}

/**
 * 新增一条跟进记录
 * @param {String} leadId 
 * @param {Object} data - { content, type }
 */
export function addFollowUp(leadId, data) {
    return request({
        url: `/api/v1/leads/${leadId}/follow-up`,
        method: 'post',
        data
    })
}

/**
 * 生成 AI 跟进建议
 * @param {String} leadId
 * @param {Object} data - { userGoal? }
 */
export function generateAiSuggestion(leadId, data = {}) {
    return request({
        url: `/api/v1/leads/${leadId}/ai-suggestion`,
        method: 'post',
        data,
        timeout: 30000
    })
}

/**
 * 单个/批量分配线索给指定员工
 * @param {Array<string>} leadIds
 * @param {string} staffId
 */
export function assignLeads(leadIds, staffId) {
    return request({
        url: '/api/v1/leads/assign',
        method: 'post',
        data: { leadIds, staffId }
    })
}

/**
 * 批量手动转入公海
 * @param {Array<string>} leadIds
 */
export function transferLeadsToPool(leadIds) {
    return request({
        url: '/api/v1/leads/to-pool',
        method: 'post',
        data: { leadIds }
    })
}

/**
 * 导出线索 CSV（仅老板）
 * @param {Object} params
 */
export function exportLeads(params) {
    return request({
        url: '/api/v1/leads/export',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

/**
 * 导入线索 CSV（三角色）
 * @param {File} file
 */
export function importLeads(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
        url: '/api/v1/leads/import',
        method: 'post',
        data: formData,
        headers: { 'Content-Type': 'multipart/form-data' }
    })
}

/**
 * 获取当前账号可分配员工列表
 */
export function getAssignableStaff() {
    return request({
        url: '/api/v1/leads/assignable-staff',
        method: 'get'
    })
}

/**
 * 获取线索跟进动态时间轴
 * @param {String} leadId 
 */
export function getLeadActivities(leadId) {
    return request({
        url: `/api/v1/leads/${leadId}/activities`,
        method: 'get'
    })
}
