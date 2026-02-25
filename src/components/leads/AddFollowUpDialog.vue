<template>
  <el-dialog
    v-model="visible"
    title="添加跟进记录"
    width="550px"
    destroy-on-close
    class="rounded-xl overflow-hidden"
  >
    <div class="px-2">
      <el-form 
        ref="formRef" 
        :model="formData" 
        :rules="rules" 
        label-position="top" 
        class="space-y-4"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <el-form-item label="跟进方式" prop="method">
            <el-select v-model="formData.method" placeholder="选择跟进方式" size="large" class="w-full">
              <el-option label="电话打通" value="phone" />
              <el-option label="微信沟通" value="wechat" />
              <el-option label="客户到访" value="visit" />
              <el-option label="拒绝接听" value="reject" />
              <el-option label="空号/停机" value="invalid" />
            </el-select>
          </el-form-item>

        <el-form-item label="更新客户状态 (可选)" prop="status">
            <el-select v-model="formData.status" placeholder="不更改状态" size="large" class="w-full" clearable>
              <el-option
                v-for="item in statusOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="跟进内容" prop="content">
          <el-input 
            v-model="formData.content" 
            type="textarea" 
            :rows="4" 
            placeholder="请详细记录本次沟通的客户意向、关注点、异议等内容..."
            resize="none"
          />
        </el-form-item>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <el-form-item label="下次跟进时间" prop="nextTime">
            <el-date-picker
              v-model="formData.nextTime"
              type="datetime"
              placeholder="安排下次联系"
              size="large"
              class="!w-full"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>

          <el-form-item label="附件 (可选)">
             <el-upload
                action="#"
                :auto-upload="false"
                class="w-full"
                limit="3"
             >
                <el-button size="small" plain><el-icon class="mr-1"><Paperclip /></el-icon>上传截图/文件</el-button>
             </el-upload>
          </el-form-item>
        </div>

      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer bg-gray-50 -mx-5 -mb-5 px-5 py-4 border-t border-gray-100 flex justify-end gap-3 mt-4">
        <el-button @click="visible = false" size="large">取消</el-button>
        <el-button type="primary" size="large" class="shadow-md shadow-blue-500/30" :loading="loading" @click="handleSubmit">
          <el-icon class="mr-1"><Check /></el-icon>提交跟进
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue'
import { Phone, Check, Paperclip } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { addFollowUp, updateLead } from '@/api/leads'
import { useLeadMeta } from '@/composables/useLeadMeta'
import { getCurrentStaffId } from '@/utils/auth'

const props = defineProps({
  visible: Boolean,
  initialContent: {
    type: String,
    default: ''
  },
  lead: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'success'])

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const formRef = ref(null)
const loading = ref(false)
const { statusOptions, loadLeadMeta } = useLeadMeta()

const formData = reactive({
  method: 'phone',
  status: '', // allow empty, meaning no change
  content: '',
  nextTime: ''
})

// when dialog opens, we might prepopulate status if we want, but usually it's empty to signify "no change" unless explicitly selected
watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadLeadMeta(true)
    formData.method = 'phone'
    formData.status = ''
    formData.content = props.initialContent || ''
    formData.nextTime = ''
    // If we want to default the select to the lead's current status:
    // if (props.lead && props.lead.status) formData.status = props.lead.status
  }
})

const rules = {
  method: [{ required: true, message: '请选择跟进方式', trigger: 'change' }],
  content: [{ required: true, message: '请输入跟进内容', trigger: 'blur' }]
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

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        if (!props.lead?.id) {
          throw new Error('未获取到线索ID')
        }

        const payload = {
          type: formData.method,
          content: formData.content,
          operator: getCurrentStaffId() || 'UNKNOWN'
        }
        await addFollowUp(props.lead.id, payload)

        // 若用户附加了状态流转要求，则调用更新状态 API
        if (formData.status && formData.status !== props.lead.status) {
          const updatePayload = { status: formData.status }
          const newLevel = getAutoLevel(formData.status)
          if (newLevel && newLevel !== props.lead.level) {
            updatePayload.level = newLevel
          }
          await updateLead(props.lead.id, updatePayload)
        }

        ElMessage.success('跟进记录添加成功！')
        visible.value = false
        emit('success', { ...formData, leadId: props.lead.id })
      } catch (error) {
        console.error('添加跟进失败:', error)
        ElMessage.error(error?.response?.data?.message || '添加跟进失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}
:deep(.el-dialog__header) {
  margin-bottom: 0px;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 1rem;
}
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
}
</style>
