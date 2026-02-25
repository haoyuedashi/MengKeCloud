<template>
  <el-dialog
    v-model="visible"
    title="分配线索"
    :width="dialogWidth"
    destroy-on-close
    class="rounded-xl overflow-hidden"
  >
    <div class="px-2">
      <div class="bg-blue-50 text-blue-600 px-4 py-3 rounded-lg flex items-start mb-6">
        <el-icon class="mt-0.5 mr-2"><InfoFilled /></el-icon>
        <span class="text-sm">您正在将 <strong>{{ leads.length }}</strong> 条线索进行定向分配，分配后将直接进入目标销售的私海列表。</span>
      </div>

      <el-form label-position="top">
        <el-form-item label="选择目标部门/员工" required>
          <el-cascader
            v-model="selectedUser"
            :options="deptAndStaffOptions"
            :props="cascaderProps"
            placeholder="请选择员工"
            size="large"
            class="w-full"
            :loading="loadingStaff"
            filterable
            clearable
          >
            <template #default="{ node, data }">
              <div class="flex items-center">
                <el-icon v-if="!data.isUser" class="mr-2 text-gray-400"><Folder /></el-icon>
                <el-icon v-else class="mr-2 text-blue-500"><User /></el-icon>
                <span>{{ data.label }}</span>
              </div>
            </template>
          </el-cascader>
        </el-form-item>
        
        <el-form-item label="分配备注记录 (可选)" class="mt-4">
          <el-input 
            v-model="assignReason" 
            type="textarea" 
            :rows="3" 
            placeholder="填写分配备注，如：高净值客户请优先跟进..."
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="border-t border-gray-100 -mx-5 -mb-5 px-5 py-4 bg-gray-50 flex justify-end gap-3 mt-4">
        <el-button @click="visible = false" size="large">取消</el-button>
        <el-button type="primary" size="large" class="shadow-md shadow-blue-500/30 bg-teal-500 hover:bg-teal-600 border-none" :disabled="!selectedUser || loadingStaff" @click="handleConfirm">
          <el-icon class="mr-1"><Position /></el-icon> 确认分配
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { InfoFilled, User, Folder, Position } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getAssignableStaff } from '@/api/leads'

const windowWidth = ref(window.innerWidth)
const dialogWidth = computed(() => windowWidth.value < 768 ? '90%' : '500px')

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const props = defineProps({
  visible: Boolean,
  leads: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:visible', 'success'])

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const selectedUser = ref('')
const assignReason = ref('')
const loadingStaff = ref(false)

const cascaderProps = {
  expandTrigger: 'hover',
  emitPath: false,
  value: 'value',
  label: 'label',
  children: 'children',
  checkStrictly: false,
}

const deptAndStaffOptions = ref([])

const normalizeDeptName = (name) => {
  const text = String(name || '').trim()
  return text || '未分组'
}

const findUserById = (userId) => {
  for (const dept of deptAndStaffOptions.value) {
    const user = (dept.children || []).find((item) => item.value === userId)
    if (user) return user
  }
  return null
}

const loadAssignableStaffOptions = async () => {
  loadingStaff.value = true
  try {
    const data = await getAssignableStaff()
    const list = Array.isArray(data?.list) ? data.list : []
    const grouped = {}

    for (const staff of list) {
      if (!staff?.id) continue
      const deptName = normalizeDeptName(staff.deptName)
      if (!grouped[deptName]) {
        grouped[deptName] = []
      }
      grouped[deptName].push({
        value: staff.id,
        label: String(staff.name || staff.id),
        isUser: true,
      })
    }

    const deptNames = Object.keys(grouped).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'))
    deptAndStaffOptions.value = deptNames.map((deptName, index) => ({
      value: `dept_${index}_${deptName}`,
      label: deptName,
      isUser: false,
      children: grouped[deptName].sort((a, b) => a.label.localeCompare(b.label, 'zh-Hans-CN')),
    }))
  } catch (_error) {
    deptAndStaffOptions.value = []
    ElMessage.error('加载可分配员工失败')
  } finally {
    loadingStaff.value = false
  }
}

watch(
  () => visible.value,
  async (val) => {
    if (!val) {
      selectedUser.value = ''
      assignReason.value = ''
      return
    }
    await loadAssignableStaffOptions()
  }
)

const handleConfirm = () => {
  const targetUser = findUserById(selectedUser.value)
  if (!targetUser) {
    ElMessage.warning('请选择目标员工')
    return
  }

  emit('success', {
    id: selectedUser.value,
    name: targetUser.label,
    reason: assignReason.value
  })
  
  // reset
  selectedUser.value = ''
  assignReason.value = ''
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
</style>
