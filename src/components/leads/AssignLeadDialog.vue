<template>
  <el-dialog
    v-model="visible"
    title="分配客户"
    width="520px"
    destroy-on-close
  >
    <div class="space-y-4">
      <div class="text-sm text-gray-600 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
        当前选中 <span class="font-semibold text-blue-600">{{ leads.length }}</span> 条客户，分配后将直接归属到目标员工私海。
      </div>

      <el-form label-position="top">
        <el-form-item label="目标员工" required>
          <el-select v-model="targetStaffId" placeholder="请选择员工" class="w-full" filterable clearable>
            <el-option
              v-for="staff in staffOptions"
              :key="staff.id"
              :label="staff.label"
              :value="staff.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :disabled="!targetStaffId" @click="handleConfirm">确认分配</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  visible: Boolean,
  leads: {
    type: Array,
    default: () => []
  },
  staffOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:visible', 'success'])

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const targetStaffId = ref('')

watch(
  () => visible.value,
  (val) => {
    if (!val) {
      targetStaffId.value = ''
    }
  }
)

const handleConfirm = () => {
  if (!targetStaffId.value) {
    return
  }
  emit('success', targetStaffId.value)
}
</script>
