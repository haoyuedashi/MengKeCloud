<template>
  <el-drawer
    v-model="visible"
    title="公海池高级筛选"
    :size="drawerSize"
    direction="rtl"
    destroy-on-close
  >
    <div class="px-4">
      <el-form label-position="top" class="space-y-5">
        
        <el-form-item label="前归属人">
          <el-input v-model="filterData.originalOwner" placeholder="请输入前归属人姓名" class="w-full" size="large" clearable />
        </el-form-item>

        <el-form-item label="线索来源渠道">
          <el-select v-model="filterData.source" placeholder="支持多选来源渠道" class="w-full" size="large" multiple clearable>
            <el-option
              v-for="item in dictOptions.source"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="掉落公海时间">
          <el-date-picker
            v-model="filterData.dropDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            class="!w-full"
            size="large"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

      </el-form>
    </div>

    <!-- 底部操作按钮 -->
    <template #footer>
      <div class="flex gap-4 px-4 bg-gray-50 py-3 -mx-5 -mb-5 border-t border-gray-100">
        <el-button @click="resetFilter" class="flex-1" size="large">清空重置</el-button>
        <el-button type="primary" @click="applyFilter" class="flex-1 shadow-md shadow-blue-500/30" size="large">
          立即筛选
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { computed, reactive, ref, onMounted, onUnmounted } from 'vue'
import { getDictItems } from '@/api/dict'

const windowWidth = ref(window.innerWidth)
const drawerSize = computed(() => windowWidth.value < 768 ? '100%' : '400px')

const dictOptions = reactive({
  source: []
})

const fetchDicts = async () => {
  try {
    const res = await getDictItems('source')
    dictOptions.source = res || []
  } catch (error) {
    console.error('加载来源字典失败:', error)
  }
}

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  fetchDicts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const props = defineProps({
  visible: Boolean
})

const emit = defineEmits(['update:visible', 'filter'])

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const filterData = reactive({
  originalOwner: '',
  source: [],
  dropDateRange: null
})

const resetFilter = () => {
  filterData.originalOwner = ''
  filterData.source = []
  filterData.dropDateRange = null
}

const applyFilter = () => {
  emit('filter', { ...filterData })
  visible.value = false
}
</script>

<style scoped>
:deep(.el-drawer__body) {
  padding: 1.5rem 0;
  background-color: #fff;
}
:deep(.el-drawer__header) {
  margin-bottom: 0px;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 1.25rem;
}
:deep(.el-form-item__label) {
  font-weight: 600;
  color: #334155;
  padding-bottom: 8px;
}
</style>
