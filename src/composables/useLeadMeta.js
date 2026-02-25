import { computed, reactive, toRefs } from 'vue'
import { getDictItems } from '@/api/dict'
import { getCustomFields } from '@/api/settings'

const BASE_LEAD_FIELD_CODES = new Set([
  'name',
  'customer_name',
  'phone',
  'project',
  'status',
  'source',
  'city',
  'level',
  'owner',
  'tags',
  'remarks'
])

const FIELD_CODE_ALIASES = {
  name: 'customer_name'
}

const state = reactive({
  loaded: false,
  dirty: false,
  loading: false,
  statusOptions: [],
  sourceOptions: [],
  levelOptions: [],
  tagOptions: [],
  customFields: []
})

const FALLBACK_STATUS_OPTIONS = [
  { value: 'pending', label: '待跟进' },
  { value: 'communicating', label: '初步沟通' },
  { value: 'deep_following', label: '深度跟进' },
  { value: 'invited', label: '已邀约' },
  { value: 'visited', label: '已到访' },
  { value: 'deposit_paid', label: '已交定金' },
  { value: 'signed', label: '已签约' },
      { value: 'invalid', label: '无效客户' },
  { value: 'lost', label: '战败流失' }
]

const FALLBACK_SOURCE_OPTIONS = [
  { value: 'douyin', label: '抖音广告' },
  { value: 'baidu', label: '百度搜索' },
  { value: 'expo', label: '线下展会' },
  { value: 'referral', label: '转介绍' }
]

const FALLBACK_LEVEL_OPTIONS = [
  { value: 'A', label: 'A级' },
  { value: 'B', label: 'B级' },
  { value: 'C', label: 'C级' },
  { value: 'D', label: 'D级' }
]

const FALLBACK_TAG_OPTIONS = [
  { value: 'high_value', label: '高净值' },
  { value: 'franchise_exp', label: '曾加盟过' },
  { value: 'mall_shop', label: '商场铺' },
  { value: 'competitor_convert', label: '竞品转出' },
  { value: 'signed', label: '已签约' }
]

function normalizeCustomFields(fields) {
  return (fields || [])
    .map((field) => ({
      ...field,
      fieldOptions: normalizeDictOptions(field?.fieldOptions || [], [])
    }))
    .slice()
    .sort((a, b) => (a.sort || 0) - (b.sort || 0))
}

function normalizeDictOptions(options, fallback) {
  const merged = Array.isArray(options) && options.length > 0 ? options : fallback
  const map = new Map()
  for (const option of merged) {
    if (!option?.value) continue
    if (!map.has(option.value)) {
      map.set(option.value, {
        value: option.value,
        label: option.label || option.value
      })
    }
  }
  return Array.from(map.values())
}

async function loadLeadMeta(force = false) {
  if (state.loading) {
    return
  }
  if (state.loaded && !state.dirty && !force) {
    return
  }

  state.loading = true
  try {
    const [statusRes, sourceRes, levelRes, tagRes, customFieldsRes] = await Promise.all([
      getDictItems('status'),
      getDictItems('source'),
      getDictItems('level'),
      getDictItems('tag'),
      getCustomFields('lead')
    ])

    state.statusOptions = normalizeDictOptions(statusRes, FALLBACK_STATUS_OPTIONS)
    state.sourceOptions = normalizeDictOptions(sourceRes, FALLBACK_SOURCE_OPTIONS)
    state.levelOptions = normalizeDictOptions(levelRes, FALLBACK_LEVEL_OPTIONS)
    state.tagOptions = normalizeDictOptions(tagRes, FALLBACK_TAG_OPTIONS)
    state.customFields = normalizeCustomFields(customFieldsRes?.list || [])
    state.loaded = true
    state.dirty = false
  } finally {
    state.loading = false
  }
}

function invalidateLeadMeta() {
  state.dirty = true
  state.loaded = false
}

const activeCustomFields = computed(() => state.customFields.filter((field) => field.active))

const businessCustomFields = computed(() => {
  return activeCustomFields.value.filter((field) => !BASE_LEAD_FIELD_CODES.has(field.code))
})

const baseFieldConfigMap = computed(() => {
  const map = {}
  for (const field of state.customFields) {
    if (!BASE_LEAD_FIELD_CODES.has(field.code)) {
      continue
    }
    map[field.code] = field
  }
  return map
})

function resolveFieldCode(fieldCode) {
  return FIELD_CODE_ALIASES[fieldCode] || fieldCode
}

function getBaseFieldConfig(fieldCode) {
  const code = resolveFieldCode(fieldCode)
  return baseFieldConfigMap.value[code] || null
}

function getBaseFieldLabel(fieldCode, fallbackLabel = '') {
  const config = getBaseFieldConfig(fieldCode)
  return config?.name || fallbackLabel
}

function isBaseFieldRequired(fieldCode, fallbackRequired = false) {
  const config = getBaseFieldConfig(fieldCode)
  if (!config) {
    return fallbackRequired
  }
  return !!config.isRequired
}

function getFieldOptions(fieldCode) {
  if (fieldCode === 'status') return state.statusOptions
  if (fieldCode === 'source') return state.sourceOptions
  if (fieldCode === 'level') return state.levelOptions
  const customSelectField = state.customFields.find((field) => field.code === fieldCode && field.type === 'select')
  if (customSelectField) {
    return customSelectField.fieldOptions || []
  }
  return []
}

function getSourceLabel(sourceValue) {
  if (!sourceValue) return '--'
  const normalized = sourceValue === 'douying' ? 'douyin' : sourceValue
  const option = state.sourceOptions.find((item) => item.value === normalized)
  return option?.label || sourceValue
}

function normalizeTagValues(tagValues = []) {
  const values = Array.isArray(tagValues) ? tagValues : []
  const knownTagByLabel = new Map(state.tagOptions.map((item) => [item.label, item.value]))
  return values.map((tag) => knownTagByLabel.get(tag) || tag)
}

function getTagLabel(tagValue) {
  const option = state.tagOptions.find((item) => item.value === tagValue)
  return option?.label || tagValue
}

export function useLeadMeta() {
  return {
    ...toRefs(state),
    activeCustomFields,
    businessCustomFields,
    baseFieldConfigMap,
    getBaseFieldConfig,
    getBaseFieldLabel,
    isBaseFieldRequired,
    getSourceLabel,
    normalizeTagValues,
    getTagLabel,
    loadLeadMeta,
    invalidateLeadMeta,
    getFieldOptions
  }
}
