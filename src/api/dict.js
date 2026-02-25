import request from '@/utils/request'

const DICT_TYPE_ALIASES = {
  status: 'lead_status',
  source: 'lead_source',
  level: 'lead_level',
  loss_reason: 'loss_reason'
}

function normalizeDictType(dictType) {
  return DICT_TYPE_ALIASES[dictType] || dictType
}

/**
 * 通用字典拉取接口
 * @param {string} dictType - 字典类型 (例如 source, status)
 * @returns {Promise<Array>} 字典项列表
 */
export function getDictItems(dictType) {
    return request({
        url: `/api/v1/dict/${normalizeDictType(dictType)}`,
        method: 'get'
    }).then((res) => {
        if (Array.isArray(res)) {
            return res
        }
        return res?.items || []
    })
}
