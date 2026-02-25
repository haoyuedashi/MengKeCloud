<template>
  <el-dialog
    v-model="visible"
    title="录入新客户"
    width="680px"
    destroy-on-close
    top="4vh"
    class="rounded-xl overflow-hidden create-lead-dialog"
  >
    <div class="px-1">
      <el-form 
        ref="formRef" 
        :model="formData" 
        :rules="rules" 
        label-position="top" 
        class="space-y-3"
      >
        <!-- 分区：基础信息 -->
        <h3 class="text-sm font-semibold text-gray-800 border-b border-gray-100 pb-1.5 mb-3">基础信息</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <el-form-item :label="nameLabel" prop="name" :required="isNameRequired">
            <el-input v-model="formData.name" placeholder="请输入姓名">
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </el-form-item>
          
          <el-form-item :label="phoneLabel" prop="phone" :required="isPhoneRequired">
            <el-input v-model="formData.phone" placeholder="请输入11位手机号">
              <template #prefix><el-icon><Phone /></el-icon></template>
            </el-input>
          </el-form-item>

          <el-form-item :label="statusLabel" prop="status" :required="isStatusRequired">
            <el-select v-model="formData.status" placeholder="请选择初始状态" class="w-full">
              <el-option
                v-for="item in dictOptions.status"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item :label="sourceLabel" prop="source" :required="isSourceRequired">
            <el-select v-model="formData.source" placeholder="请选择来源" class="w-full">
              <el-option
                v-for="item in dictOptions.source"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="客户标签">
            <el-select 
              v-model="formData.tags" 
              multiple 
              filterable 
              clearable
              placeholder="请选择客户标签" 
              class="w-full"
            >
              <el-option
                v-for="item in tagOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="城市" prop="city">
            <el-autocomplete
              v-model="formData.city"
              class="w-full"
              :fetch-suggestions="fetchCitySuggestions"
              placeholder="请输入城市，如：上海"
              clearable
              @blur="normalizeCityField"
            />
          </el-form-item>

          <el-form-item v-if="showAssignee" label="指派员工" class="md:col-span-2">
            <el-select v-model="formData.owner" placeholder="可选：直接分配给员工" class="w-full" clearable filterable>
              <el-option
                v-for="staff in assigneeOptions"
                :key="staff.id"
                :label="staff.label"
                :value="staff.id"
              />
            </el-select>
          </el-form-item>
        </div>

        <!-- 分区：动态扩展信息 -->
        <h3 class="text-sm font-semibold text-gray-800 border-b border-gray-100 pb-1.5 mt-4 mb-3 flex justify-between items-center">
          加盟意向特征
          <el-tag size="small" type="info" class="font-normal border-none bg-gray-50">可在此类目自定义字段</el-tag>
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <template v-for="field in businessCustomFields" :key="field.id">
            <el-form-item :label="field.name" :required="field.isRequired">
              <el-input
                v-if="field.type === 'text'"
                v-model="dynamicFieldValues[field.code]"
                :placeholder="field.placeholder || '请输入'"
              />
              <el-input
                v-else-if="field.type === 'textarea'"
                v-model="dynamicFieldValues[field.code]"
                type="textarea"
                :rows="3"
                :placeholder="field.placeholder || '请输入'"
              />
              <el-input-number
                v-else-if="field.type === 'number'"
                v-model="dynamicFieldValues[field.code]"
                :min="0"
                class="!w-full"
              />
              <el-date-picker
                v-else-if="field.type === 'date'"
                v-model="dynamicFieldValues[field.code]"
                type="date"
                value-format="YYYY-MM-DD"
                :placeholder="field.placeholder || '请选择日期'"
                class="!w-full"
              />
              <el-select
                v-else-if="field.type === 'select' && getFieldOptions(field.code).length > 0"
                v-model="dynamicFieldValues[field.code]"
                :placeholder="field.placeholder || '请选择'"
                class="w-full"
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
                v-model="dynamicFieldValues[field.code]"
                :placeholder="field.placeholder || '请输入'"
              />
            </el-form-item>
          </template>
        </div>

        <el-form-item label="备注信息" class="mt-2">
          <el-input 
            v-model="formData.remarks" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入首次沟通的内容或注意事项..."
          />
        </el-form-item>

      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer bg-gray-50 -mx-5 -mb-5 px-5 py-3 border-t border-gray-100 flex justify-end gap-2 mt-3">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" class="shadow-sm shadow-blue-500/20" :loading="loading" @click="handleSubmit">
          <el-icon class="mr-1"><Check /></el-icon>确认录入
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue'
import { User, Phone, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { createLead } from '@/api/leads'
import { useLeadMeta } from '@/composables/useLeadMeta'
import { validateLeadName } from '@/utils/leadNameValidator'
import { normalizeCityInput, queryCitySuggestions } from '@/utils/chinaCity'

const props = defineProps({
  visible: Boolean,
  assigneeOptions: {
    type: Array,
    default: () => []
  },
  showAssignee: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:visible', 'success'])

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const formRef = ref(null)
const loading = ref(false)

const formData = reactive({
  name: '',
  phone: '',
  status: 'pending',
  source: '',
  city: '',
  owner: '',
  remarks: '',
  tags: [],
  dynamic: {}
})

const dynamicFieldValues = reactive({})

const {
  statusOptions,
  sourceOptions,
  tagOptions,
  businessCustomFields,
  getBaseFieldLabel,
  isBaseFieldRequired,
  loadLeadMeta,
  getFieldOptions
} = useLeadMeta()

const nameLabel = computed(() => getBaseFieldLabel('name', '客户姓名'))
const phoneLabel = computed(() => getBaseFieldLabel('phone', '联系电话'))
const statusLabel = computed(() => getBaseFieldLabel('status', '客户状态'))
const sourceLabel = computed(() => getBaseFieldLabel('source', '来源渠道'))

const isNameRequired = computed(() => isBaseFieldRequired('name', true))
const isPhoneRequired = computed(() => isBaseFieldRequired('phone', true))
const isStatusRequired = computed(() => isBaseFieldRequired('status', true))
const isSourceRequired = computed(() => isBaseFieldRequired('source', false))

const rules = computed(() => ({
  name: [
    ...(isNameRequired.value ? [{ required: true, message: `请输入${nameLabel.value}`, trigger: 'blur' }] : []),
    {
      validator: (_rule, value, callback) => {
        const result = validateLeadName(value)
        if (!result.valid) {
          callback(new Error(result.message))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  phone: [
    ...(isPhoneRequired.value ? [{ required: true, message: `请输入${phoneLabel.value}`, trigger: 'blur' }] : []),
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  status: [
    ...(isStatusRequired.value ? [{ required: true, message: `请选择${statusLabel.value}`, trigger: 'change' }] : [])
  ],
  source: [
    ...(isSourceRequired.value ? [{ required: true, message: `请选择${sourceLabel.value}`, trigger: 'change' }] : [])
  ]
}))

const dictOptions = computed(() => ({
  source: sourceOptions.value,
  status: statusOptions.value
}))

const initializeDynamicFieldValues = () => {
  const nextValues = {}
  for (const field of businessCustomFields.value) {
    nextValues[field.code] = formData.dynamic[field.code] ?? ''
  }

  Object.keys(dynamicFieldValues).forEach((key) => {
    if (!(key in nextValues)) {
      delete dynamicFieldValues[key]
    }
  })
  Object.assign(dynamicFieldValues, nextValues)
}

watch(
  () => businessCustomFields.value,
  () => {
    initializeDynamicFieldValues()
  },
  { immediate: true }
)

watch(
  () => visible.value,
  async (isOpen) => {
    if (!isOpen) return
    await loadLeadMeta(true)
    initializeDynamicFieldValues()
  },
  { immediate: true }
)

watch(
  () => props.showAssignee,
  (val) => {
    if (!val) {
      formData.owner = ''
    }
  }
)

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        for (const field of businessCustomFields.value) {
          if (!field.isRequired) continue
          const value = dynamicFieldValues[field.code]
          if (value === null || value === undefined || value === '') {
            ElMessage.warning(`请填写必填字段：${field.name}`)
            loading.value = false
            return
          }
        }

        const dynamicPayload = { ...dynamicFieldValues }
        const normalizedCity = normalizeCityInput(formData.city)
        if (normalizedCity) {
          dynamicPayload.city = normalizedCity
        }
        if (formData.remarks) {
          dynamicPayload.remarks = formData.remarks
        }

        const payload = {
          name: formData.name,
          phone: formData.phone,
          project: '待确认项目', // Schema requires project
          source: formData.source,
          status: formData.status,
          level: 'C', // Schema requires level
          owner: formData.owner || null,
          tags: formData.tags || [],
          dynamicData: dynamicPayload
        }
        const res = await createLead(payload)
        ElMessage.success('线索录入成功！')
        visible.value = false
        emit('success', res || payload)
        
        // Reset form manually
        formData.name = ''
        formData.phone = ''
        formData.remarks = ''
        formData.source = ''
        formData.city = ''
        formData.owner = ''
        formData.status = 'pending'
        formData.tags = []
        Object.keys(dynamicFieldValues).forEach((key) => {
          dynamicFieldValues[key] = ''
        })
      } catch (error) {
        console.error('新建线索失败:', error)
      } finally {
         loading.value = false
      }
    }
  })
}

const fetchCitySuggestions = (queryString, callback) => {
  callback(queryCitySuggestions(queryString))
}

const normalizeCityField = () => {
  formData.city = normalizeCityInput(formData.city)
}
</script>

<style scoped>
/* 覆盖 El-Dialog 默认生硬的样式 */
:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

:deep(.create-lead-dialog .el-dialog) {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
:deep(.el-dialog__header) {
  margin-bottom: 0px;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 0.75rem;
}
:deep(.el-dialog__body) {
  padding-top: 14px;
  padding-bottom: 12px;
  overflow-y: auto;
}
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
  margin-bottom: 4px;
}
:deep(.el-form-item) {
  margin-bottom: 10px;
}
</style>
