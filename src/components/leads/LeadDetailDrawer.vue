<template>
  <el-drawer
    v-model="visible"
    :title="lead ? `客户详情：${lead.name}` : '客户详情'"
    :size="drawerSize"
    destroy-on-close
    :show-close="false"
  >
    <template #header="{ close }">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <h2 class="text-xl font-bold text-gray-800">{{ lead?.name }}</h2>
          <el-tag :type="getStatusType(lead?.status)" effect="light" class="border-none font-medium">
            {{ getStatusText(lead?.status) }}
          </el-tag>
        </div>
        <div class="flex items-center space-x-2">
          <template v-if="!isEditing">
            <el-button type="primary" size="small" plain @click="startEdit"><el-icon class="mr-1"><Edit /></el-icon>编辑信息</el-button>
          </template>
          <template v-else>
            <el-button type="primary" size="small" @click="saveEdit"><el-icon class="mr-1"><Check /></el-icon>保存更改</el-button>
            <el-button size="small" @click="cancelEdit">取消</el-button>
          </template>
          <el-button circle size="small" @click="close"><el-icon><Close /></el-icon></el-button>
        </div>
      </div>
    </template>

    <div class="h-full flex flex-col md:flex-row gap-6 -mx-4 -mt-4 bg-gray-50 p-4">
      
      <!-- 左侧：状态流转与客户信息动态表单 -->
      <div class="flex-1 space-y-4">
        <!-- 业务操作按钮组 -->
        <div class="bg-white p-4 justify-between rounded-xl shadow-sm border border-gray-100 flex items-center space-x-2">
           <el-button type="success" class="flex-1 shadow-sm shadow-green-500/20" @click="addFollowUpVisible = true"><el-icon class="mr-1"><Phone /></el-icon> 添加跟进</el-button>
          <el-button type="primary" plain class="flex-1" :loading="aiSuggestLoading" @click="handleGenerateAiSuggestion">AI建议</el-button>
           <el-dropdown trigger="click" @command="handleStatusChange">
              <el-button class="flex-1"><el-icon class="mr-1"><Switch /></el-icon> 变更状态</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="communicating">流转至：初步沟通</el-dropdown-item>
                  <el-dropdown-item command="deep_following">流转至：深度跟进</el-dropdown-item>
                  <el-dropdown-item command="invited">流转至：已邀约</el-dropdown-item>
                  <el-dropdown-item command="visited">流转至：已到访</el-dropdown-item>
                  <el-dropdown-item command="deposit_paid">流转至：已交定金</el-dropdown-item>
                  <el-dropdown-item divided command="signed" class="text-green-600">标记为已签约</el-dropdown-item>
                  <el-dropdown-item command="lost" class="text-gray-500">标记战败流失</el-dropdown-item>
                  <el-dropdown-item command="invalid" class="text-gray-400">标记无效线索</el-dropdown-item>
                </el-dropdown-menu>
              </template>
           </el-dropdown>
        </div>

        <!-- 基础信息卡片 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="bg-slate-50 px-4 py-3 border-b border-gray-100 text-sm font-bold text-gray-700">基础资料</div>
          <div class="p-4 space-y-3">
            <div class="flex items-center h-8">
              <span class="w-20 text-gray-500 text-sm shrink-0">客户姓名：</span>
              <span v-if="!isEditing" class="text-gray-800 text-sm font-medium">{{ lead?.name || '暂无' }}</span>
              <el-input v-else v-model="editForm.name" size="small" class="w-48" />
            </div>
            <div class="flex items-center h-8">
              <span class="w-20 text-gray-500 text-sm shrink-0">联系电话：</span>
              <span v-if="!isEditing" class="text-gray-800 text-sm font-medium">{{ lead?.phone || '暂无' }}</span>
              <el-input v-else v-model="editForm.phone" size="small" class="w-48" />
            </div>
            <div class="flex items-center h-8">
              <span class="w-20 text-gray-500 text-sm shrink-0">来源渠道：</span>
              <span v-if="!isEditing" class="text-gray-800 text-sm">{{ getSourceLabel(lead?.source) }}</span>
              <el-select v-else v-model="editForm.source" size="small" class="w-48">
                <el-option
                  v-for="item in sourceOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </div>
            <div class="flex items-center h-8">
              <span class="w-20 text-gray-500 text-sm shrink-0">城市：</span>
              <span v-if="!isEditing" class="text-gray-800 text-sm">{{ dynamicData.city || '暂无' }}</span>
              <el-autocomplete
                v-else
                v-model="editForm.dynamicData.city"
                class="w-48"
                :fetch-suggestions="fetchCitySuggestions"
                placeholder="请输入城市"
                clearable
                @blur="normalizeCityField"
              />
            </div>
            <div class="flex items-center h-8">
              <span class="w-20 text-gray-500 text-sm shrink-0">负责销售：</span>
              <span v-if="!isEditing || !canAssignOwner" class="text-gray-800 text-sm">{{ getOwnerDisplay(lead?.owner) }}</span>
              <el-select v-else v-model="editForm.owner" size="small" class="w-48" filterable>
                <el-option
                  v-for="staff in assignableStaffOptions"
                  :key="staff.id"
                  :label="staff.label"
                  :value="staff.id"
                />
              </el-select>
            </div>
            <div class="flex items-center min-h-[32px]">
              <span class="w-20 text-gray-500 text-sm shrink-0">客户标签：</span>
              <span v-if="!isEditing" class="text-gray-800 text-sm flex flex-wrap gap-1">
                <el-tag v-for="tag in lead?.tags" :key="tag" size="small" type="info" class="border-gray-200">{{ getTagLabel(tag) }}</el-tag>
                <span v-if="!lead?.tags?.length" class="text-gray-400">暂无</span>
              </span>
              <el-select 
                v-else 
                v-model="editForm.tags" 
                multiple 
                filterable 
                clearable
                placeholder="请选择客户标签" 
                size="small" 
                class="flex-1"
              >
                <el-option
                  v-for="item in tagOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </div>
          </div>
        </div>

        <!-- 动态自定义字段 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="bg-slate-50 px-4 py-3 border-b border-gray-100 text-sm font-bold text-gray-700 flex justify-between items-center">
            加盟特写特征
            <el-icon class="text-gray-400 cursor-pointer hover:text-blue-500"><Setting /></el-icon>
          </div>
          <div class="p-4 space-y-3">
            <template v-if="businessCustomFields.length > 0">
              <div v-for="field in businessCustomFields" :key="field.id" class="flex items-center min-h-[32px]">
                <span class="w-24 text-gray-500 text-sm shrink-0">{{ field.name }}：</span>
                <span v-if="!isEditing" class="text-gray-800 text-sm">{{ formatFieldValue(field, dynamicData[field.code]) }}</span>
                <el-input
                  v-else-if="field.type === 'text'"
                  v-model="editForm.dynamicData[field.code]"
                  size="small"
                  class="w-48"
                />
                <el-input
                  v-else-if="field.type === 'textarea'"
                  v-model="editForm.dynamicData[field.code]"
                  type="textarea"
                  :rows="2"
                  class="w-64"
                />
                <el-input-number
                  v-else-if="field.type === 'number'"
                  v-model="editForm.dynamicData[field.code]"
                  :min="0"
                  size="small"
                  class="w-48"
                />
                <el-date-picker
                  v-else-if="field.type === 'date'"
                  v-model="editForm.dynamicData[field.code]"
                  type="date"
                  value-format="YYYY-MM-DD"
                  size="small"
                  class="w-48"
                />
                <el-select
                  v-else-if="field.type === 'select' && getFieldOptions(field.code).length > 0"
                  v-model="editForm.dynamicData[field.code]"
                  size="small"
                  class="w-48"
                >
                  <el-option
                    v-for="item in getFieldOptions(field.code)"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <el-input
                  v-else
                  v-model="editForm.dynamicData[field.code]"
                  size="small"
                  class="w-48"
                />
              </div>
            </template>
            <div v-else class="text-sm text-gray-400">暂无可展示的自定义字段</div>
            <div class="flex items-center min-h-[32px]">
              <span class="w-24 text-gray-500 text-sm shrink-0">备注：</span>
              <span v-if="!isEditing" class="text-gray-800 text-sm">{{ dynamicData.remarks || '--' }}</span>
              <el-input
                v-else
                v-model="editForm.dynamicData.remarks"
                type="textarea"
                :rows="2"
                class="w-64"
              />
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="bg-slate-50 px-4 py-3 border-b border-gray-100 text-sm font-bold text-gray-700">AI跟进助手</div>
          <div class="p-4 space-y-3">
            <div class="flex flex-wrap items-center gap-2">
              <el-tag size="small" type="info">场景：{{ aiSceneLabel }}</el-tag>
              <el-tag size="small" effect="plain">建议目标：{{ aiUserGoal || '推进下一次有效触达' }}</el-tag>
            </div>
            <el-input v-model="aiUserGoal" size="small" placeholder="可选：例如“推进本周到访”" />
            <div class="flex flex-wrap gap-2">
              <el-button
                v-for="preset in aiGoalPresets"
                :key="preset"
                size="small"
                text
                bg
                @click="aiUserGoal = preset"
              >
                {{ preset }}
              </el-button>
            </div>
            <div v-if="aiSuggestError" class="text-sm text-red-500">{{ aiSuggestError }}</div>
            <div v-else-if="aiSuggestLoading" class="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-sm text-blue-700">
              AI正在结合最近跟进记录生成建议，请稍候...
            </div>
            <template v-else-if="aiSuggestion">
              <div class="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm">
                <div class="text-xs text-gray-500 mb-1">下一句（可直接开口）</div>
                <div class="text-gray-800 leading-6">{{ aiSuggestion.nextSentence }}</div>
              </div>
              <div class="rounded-lg border border-gray-100 bg-white p-3 text-sm">
                <div class="text-xs text-gray-500 mb-1">下一步动作</div>
                <div class="text-gray-800 leading-6">{{ aiSuggestion.nextAction }}</div>
              </div>
              <div class="rounded-lg border border-amber-100 bg-amber-50 p-3 text-sm">
                <div class="text-xs text-amber-700 mb-1">风险点（优先规避）</div>
                <ul class="list-disc pl-5 space-y-1 text-amber-900">
                  <li v-for="(risk, index) in (aiSuggestion.riskPoints || [])" :key="`${risk}-${index}`">{{ risk }}</li>
                </ul>
              </div>
              <div class="rounded-lg border border-emerald-100 bg-emerald-50 p-3 text-sm">
                <div class="text-xs text-emerald-700 mb-1">推荐话术（可直接发送）</div>
                <div class="text-emerald-900 leading-6 whitespace-pre-wrap">{{ aiSuggestion.recommendedScript }}</div>
              </div>
              <div class="pt-1 flex items-center justify-between text-xs text-gray-400">
                <span>置信度：{{ Math.round((aiSuggestion.confidence || 0) * 100) }}%</span>
                <span>{{ aiSuggestion.model }}</span>
              </div>
              <div class="flex items-center gap-2">
                <el-button size="small" text @click="copyAiScript">复制推荐话术</el-button>
              </div>
            </template>
            <div v-else class="text-sm text-gray-400">点击“AI建议”可生成下一步话术与动作建议</div>
          </div>
        </div>
      </div>

      <!-- 右侧：全景视图的时间轴追踪 (类似朋友圈) -->
      <div class="w-full md:w-96 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
        <div class="bg-slate-50 px-4 py-3 border-b border-gray-100 text-sm font-bold text-gray-700 shrink-0">
          跟进时间轴 (Time-line)
        </div>
        <div class="p-4 flex-1 overflow-y-auto">
          <el-timeline>
            <el-timeline-item 
              v-for="activity in localActivities"
              :key="activity.id"
              :timestamp="activity.time" 
              placement="top"
              :type="activity.iconColor"
              :icon="activity.icon"
              :hollow="activity.hollow"
            >
              <div class="bg-gray-50 p-3 rounded-lg border border-gray-100 mt-1">
                <p class="text-sm text-gray-800" :class="{ 'mb-1': activity.content }">{{ activity.title }}</p>
                <p v-if="activity.content" class="text-xs text-gray-500">{{ activity.content }}</p>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>

    </div>

    <AddFollowUpDialog v-model:visible="addFollowUpVisible" :lead="lead" @success="onFollowUpSuccess" />
  </el-drawer>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { Edit, Close, Phone, Switch, Setting, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AddFollowUpDialog from '@/components/leads/AddFollowUpDialog.vue'
import { getLeadById, updateLead, getAssignableStaff, generateAiSuggestion } from '@/api/leads'
import { useLeadMeta } from '@/composables/useLeadMeta'
import { validateLeadName } from '@/utils/leadNameValidator'
import { normalizeCityInput, queryCitySuggestions } from '@/utils/chinaCity'
import { getCurrentRole, getCurrentStaffId, getCurrentUser } from '@/utils/auth'

const props = defineProps({
  visible: Boolean,
  lead: Object
})

const emit = defineEmits(['update:visible', 'updated'])

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

// 响应式抽屉宽度
const windowWidth = ref(window.innerWidth)
const drawerSize = computed(() => windowWidth.value < 768 ? '100%' : '800px')

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const addFollowUpVisible = ref(false)
const aiSuggestLoading = ref(false)
const aiSuggestError = ref('')
const aiSuggestion = ref(null)
const aiUserGoal = ref('')
const aiGoalPresets = ['推进本周到访', '确认加盟预算范围', '确认开店决策时间', '处理加盟政策异议']
const ownerNameMap = ref({})
const assignableStaffOptions = ref([])
const canAssignOwner = ref(false)
const currentRole = getCurrentRole()
const currentStaffId = getCurrentStaffId()
const currentUser = getCurrentUser()

const localActivities = ref([])

const aiSceneLabel = computed(() => {
  const status = props.lead?.status
  const map = {
    pending: '首次触达',
    communicating: '初步沟通',
    deep_following: '深度跟进',
    invited: '邀约到访',
    visited: '到访后推进',
    deposit_paid: '定金后推进',
    signed: '签约维护',
    invalid: '无效客户处理',
    lost: '流失挽回'
  }
  return map[status] || '通用跟进'
})

const {
  sourceOptions,
  tagOptions,
  businessCustomFields,
  getSourceLabel,
  normalizeTagValues,
  getTagLabel,
  loadLeadMeta,
  getFieldOptions
} = useLeadMeta()

// 行内编辑状态控制
const isEditing = ref(false)
const editForm = ref({
  dynamicData: {}
})
const dynamicData = computed(() => props.lead?.dynamicData || {})

const startEdit = () => {
  isEditing.value = true
  const nextDynamicData = { ...(props.lead?.dynamicData || {}) }
  for (const field of businessCustomFields.value) {
    if (!(field.code in nextDynamicData)) {
      nextDynamicData[field.code] = ''
    }
  }
  if (!("city" in nextDynamicData)) {
    nextDynamicData.city = ''
  }

  editForm.value = {
    name: props.lead?.name || '',
    phone: props.lead?.phone || '',
    source: props.lead?.source || '',
    owner: props.lead?.owner || '',
    tags: normalizeTagValues(props.lead?.tags ? [...props.lead.tags] : []),
    dynamicData: nextDynamicData
  }
}

const cancelEdit = () => {
  isEditing.value = false
}

const saveEdit = async () => {
  if (!props.lead) return
  const nameValidation = validateLeadName(editForm.value.name)
  if (!nameValidation.valid) {
    ElMessage.warning(nameValidation.message)
    return
  }
  
  try {
    const payload = {
      name: String(editForm.value.name).trim(),
      phone: editForm.value.phone,
      source: editForm.value.source,
      tags: editForm.value.tags,
      dynamicData: { ...(editForm.value.dynamicData || {}) }
    }
    payload.dynamicData.city = normalizeCityInput(payload.dynamicData.city)
    if (canAssignOwner.value) {
      payload.owner = editForm.value.owner || null
    }
    await updateLead(props.lead.id, payload)
    
    // 成功后同步更新前端数据展示
    props.lead.name = String(editForm.value.name).trim()
    props.lead.phone = editForm.value.phone
    props.lead.source = editForm.value.source
    if (canAssignOwner.value) {
      props.lead.owner = editForm.value.owner || null
    }
    props.lead.tags = editForm.value.tags
    props.lead.dynamicData = { ...(editForm.value.dynamicData || {}) }
    emit('updated')

    isEditing.value = false
    ElMessage.success('客户信息更新成功')
    
    localActivities.value.unshift({
      id: Date.now() + 10,
      title: '【系统】信息变更：更新了客户基础信息或扩展特征。',
      content: '',
      time: new Date().toLocaleString(),
      iconColor: 'info',
      hollow: true
    })
  } catch (error) {
    console.error('更新失败:', error)
    ElMessage.error(error?.response?.data?.message || '更新失败')
  }
}

const getAutoLevel = (status) => {
  const map = {
    'signed': 'A', 'deposit_paid': 'A', 'visited': 'A', 'invited': 'A',
    'deep_following': 'B',
    'communicating': 'C',
    'invalid': 'D', 'lost': 'D'
  }
  return map[status] || null
}

const getStatusText = (status) => {
  const map = {
    'pending': '待跟进',
    'communicating': '初步沟通',
    'deep_following': '深度跟进',
    'invited': '已邀约',
    'visited': '已到访',
    'deposit_paid': '已交定金',
    'signed': '已签约',
    'invalid': '无效线索',
    'lost': '战败流失'
  }
  return map[status] || '未知状态'
}

const handleStatusChange = async (status) => {
  if (!props.lead) return
  const oldStatusText = getStatusText(props.lead.status)
  
  // Auto map intention level
  const newLevel = getAutoLevel(status)
  let levelChangeText = ''
  
  try {
    const payload = { status }
    if (newLevel && newLevel !== props.lead.level) {
      payload.level = newLevel
    }
    
    await updateLead(props.lead.id, payload)
    
    props.lead.status = status
    
    if (newLevel && newLevel !== props.lead.level) {
      const oldLevel = props.lead.level || '暂无'
      props.lead.level = newLevel
      levelChangeText = `并触发自动评级机制，意向度从 [${oldLevel}] 更新为 [${newLevel} 级]。`
    }

    try {
      const latest = await getLeadById(props.lead.id)
      if (latest?.lead) {
        Object.assign(props.lead, latest.lead)
      }
    } catch (_error) {
      // fallback to optimistic local update when detail refresh fails
    }

    localActivities.value.unshift({
      id: Date.now(),
      title: `【系统】状态流转：由 ${oldStatusText} 变更为 ${getStatusText(status)}。${levelChangeText}`,
      content: '',
      time: new Date().toLocaleString(),
      iconColor: 'warning',
      hollow: true
    })
    ElMessage.success('状态变更成功')
    emit('updated')
  } catch (error) {
    console.error('状态变更失败:', error)
    ElMessage.error(error?.response?.data?.message || '状态变更失败')
  }
}

// 格式化时间戳避免乱码
const formatTs = (ts) => {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ts
    return d.toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
  } catch (e) {
    return ts
  }
}

// 监听 lead 数据变化，加载时间轴数据
watch(() => props.lead, async (newLead) => {
  aiSuggestError.value = ''
  aiSuggestion.value = null
  aiUserGoal.value = ''
  if (newLead && newLead.id) {
    try {
      const res = await getLeadById(newLead.id)
      localActivities.value = (res.timeline || []).map(item => ({
        id: item.id,
        title: `【${item.operator || '系统'}】跟进记录 (${item.type})`,
        content: item.content,
        time: formatTs(item.timestamp),
        iconColor: item.aiAnalysis ? 'success' : 'primary',
        hollow: false
      }))
    } catch (error) {
       console.error('获取跟进记录失败:', error)
       localActivities.value = []
    }
  } else {
    localActivities.value = []
  }
}, { immediate: true })

const handleGenerateAiSuggestion = async () => {
  if (!props.lead?.id) return
  aiSuggestLoading.value = true
  aiSuggestError.value = ''
  try {
    aiSuggestion.value = await generateAiSuggestion(props.lead.id, {
      userGoal: aiUserGoal.value || undefined
    })
  } catch (error) {
    aiSuggestion.value = null
    aiSuggestError.value = error?.response?.data?.message || error?.message || 'AI建议生成失败，请稍后重试'
  } finally {
    aiSuggestLoading.value = false
  }
}

const copyAiScript = async () => {
  const script = aiSuggestion.value?.recommendedScript || ''
  if (!script) {
    ElMessage.warning('暂无可复制的话术')
    return
  }
  try {
    await navigator.clipboard.writeText(script)
    ElMessage.success('推荐话术已复制')
  } catch (_error) {
    ElMessage.warning('复制失败，请手动复制')
  }
}

const onFollowUpSuccess = (data) => {
  const methodMap = {
    'phone': '电话沟通',
    'wechat': '微信沟通',
    'visit': '客户到访',
    'reject': '拒绝接听',
    'invalid': '空号/停机'
  }

  localActivities.value.unshift({
    id: Date.now(),
    title: `【我】新增了跟进记录 (${methodMap[data.method] || '其他'})`,
    content: data.content,
    time: new Date().toLocaleString(),
    iconColor: 'success',
    icon: Phone
  })

  if (data.status && data.status !== props.lead.status) {
    localActivities.value.unshift({
      id: Date.now() + 1,
      title: `【系统】状态流转：手动变更目标状态标识为 ${data.status}`,
      content: '',
      time: new Date().toLocaleString(),
      iconColor: 'warning',
      hollow: true
    })
    
    // 同步更新外部传入的 lead 对象状态以便立即反映在视图上
    props.lead.status = data.status
    const newLevel = getAutoLevel(data.status)
    if (newLevel) {
      props.lead.level = newLevel
    }
    emit('updated')
  }
}

const getStatusType = (status) => {
  const map = {
    'pending': 'info',
    'communicating': 'primary',
    'deep_following': 'primary',
    'invited': 'primary',
    'visited': 'primary',
    'deposit_paid': 'warning',
    'signed': 'success',
    'invalid': 'info',
    'lost': 'danger'
  }
  return status ? map[status] : 'info'
}

const getOwnerDisplay = (ownerId) => {
  if (!ownerId) return '暂无'
  return ownerNameMap.value[ownerId] || ownerId
}

const loadOwnerMap = async () => {
  if (currentRole === 'sales') {
    ownerNameMap.value = {
      [currentStaffId]: currentUser?.name || '我'
    }
    return
  }

  try {
    const data = await getAssignableStaff()
    const users = data.list || []
    ownerNameMap.value = users.reduce((acc, user) => {
      acc[user.id] = user.name
      return acc
    }, {})
  } catch (_error) {
    ownerNameMap.value = {}
  }
}

const loadAssignableStaff = async () => {
  if (currentRole === 'sales') {
    assignableStaffOptions.value = []
    canAssignOwner.value = false
    return
  }

  try {
    const data = await getAssignableStaff()
    const users = data.list || []
    assignableStaffOptions.value = users.map((user) => ({
      id: user.id,
      label: `${user.name}${user.deptName ? ` (${user.deptName})` : ''}`
    }))
    canAssignOwner.value = assignableStaffOptions.value.length > 0
  } catch (_error) {
    assignableStaffOptions.value = []
    canAssignOwner.value = false
  }
}

const formatFieldValue = (field, value) => {
  if (value === null || value === undefined || value === '') {
    return '--'
  }
  if (field.type === 'select') {
    const option = getFieldOptions(field.code).find((item) => item.value === value)
    return option?.label || String(value)
  }
  return String(value)
}

const fetchCitySuggestions = (queryString, callback) => {
  callback(queryCitySuggestions(queryString))
}

const normalizeCityField = () => {
  editForm.value.dynamicData.city = normalizeCityInput(editForm.value.dynamicData.city)
}

onMounted(async () => {
  await loadLeadMeta(true)
  await loadOwnerMap()
  await loadAssignableStaff()
})
</script>

<style scoped>
/* You can define overriding rules for el-drawer's padding here to make the gray background bleed to edges */
:deep(.el-drawer__body) {
  padding: 1rem;
  background-color: #f8fafc; /* match bg-gray-50 */
}
:deep(.el-drawer__header) {
  margin-bottom: 0px;
  padding: 1rem;
  border-bottom: 1px solid #f1f5f9;
}
</style>
