import request from '@/utils/request'

/**
 * 获取公海池列表
 * @param {Object} params - 分页与筛选参数 
 */
export function getPoolLeads(params) {
    return request({
        url: '/api/v1/pool/leads',
        method: 'get',
        params
    })
}

/**
 * 捞取单个线索到私海
 * @param {String|Number} id 
 */
export function claimLead(id) {
    return request({
        url: `/api/v1/pool/leads/${id}/claim`,
        method: 'post',
        data: {}
    })
}

/**
 * 批量捞取线索到私海
 * @param {Array} ids 
 */
export function batchClaimLeads(ids) {
    return request({
        url: `/api/v1/pool/batch-claim`,
        method: 'post',
        data: { ids }
    })
}

/**
 * 分配线索给指定销售
 * @param {String|Number} id 
 * @param {String|Number} userId 
 */
export function assignLead(id, userId) {
    return request({
        url: `/api/v1/pool/${id}/assign`,
        method: 'post',
        data: { userId }
    })
}

/**
 * 批量分配线索给指定销售
 * @param {Array} ids 
 * @param {String|Number} userId 
 */
export function batchAssignLeads(ids, userId) {
    return request({
        url: `/api/v1/pool/leads/assign`,
        method: 'post',
        data: { lead_ids: ids, staff_id: userId }
    })
}

/**
 * 获取公海池流转与审计记录
 * @param {Object} params - 筛选条件 (例如: action, lead_id)
 */
export function getPoolTransfers(params) {
    return request({
        url: '/api/v1/pool/transfers',
        method: 'get',
        params
    })
}

/**
 * 老板端彻底删除公海线索
 * @param {String|Number} id
 */
export function deletePoolLead(id) {
    return request({
        url: `/api/v1/pool/leads/${id}`,
        method: 'delete'
    })
}

/**
 * 老板端批量彻底删除公海线索
 * @param {Array<string>} leadIds
 */
export function deletePoolLeadsBatch(leadIds) {
    return request({
        url: '/api/v1/pool/leads/delete-batch',
        method: 'post',
        data: { lead_ids: leadIds }
    })
}
