<template>
  <el-drawer
    v-model="visible"
    title="高级筛选面板"
    size="400px"
    direction="rtl"
    destroy-on-close
  >
    <div class="px-4">
      <el-form label-position="top" class="space-y-5">
        
        <el-form-item label="归属人员">
          <el-select v-model="filterData.owner" placeholder="请选择跟进人" class="w-full" size="large" clearable>
            <el-option label="我的线索 (自己)" value="me" />
            <el-option label="本组线索 (下属)" value="subordinates" />
            <el-option label="全部线索" value="all" />
          </el-select>
        </el-form-item>

            <el-form-item label="客户来源渠道">
          <el-select v-model="filterData.source" placeholder="支持多选来源渠道" class="w-full" size="large" multiple clearable>
            <el-option
              v-for="item in normalizedSourceOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="线索创建时间">
          <el-date-picker
            v-model="filterData.createDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            class="!w-full"
            size="large"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="最后跟进时间">
          <el-date-picker
            v-model="filterData.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            class="!w-full"
            size="large"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="客户意向评级">
          <el-radio-group v-model="filterData.level" class="w-full flex gap-2" size="large">
            <el-radio-button
              v-for="item in normalizedLevelOptions"
              :key="item.value"
              :value="item.value"
              class="flex-1"
            >
              {{ item.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="标签过滤">
          <div class="flex flex-wrap gap-2">
            <el-tag 
              v-for="tag in normalizedTagOptions" 
              :key="tag.value"
              :effect="filterData.tags.includes(tag.value) ? 'dark' : 'plain'"
              class="cursor-pointer transition-colors"
              @click="toggleTag(tag.value)"
            >
              {{ tag.label }}
            </el-tag>
          </div>
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
import { computed, reactive } from 'vue'

const props = defineProps({
  visible: Boolean,
  sourceOptions: {
    type: Array,
    default: () => []
  },
  levelOptions: {
    type: Array,
    default: () => []
  },
  tagOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:visible', 'filter'])

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const normalizedSourceOptions = computed(() => {
  if (props.sourceOptions.length > 0) {
    return props.sourceOptions
  }
  return [
    { value: 'douyin', label: '抖音广告' },
    { value: 'baidu', label: '百度搜索' },
    { value: 'expo', label: '线下展会' },
    { value: 'referral', label: '其他转介绍' }
  ]
})

const normalizedLevelOptions = computed(() => {
  if (props.levelOptions.length > 0) {
    return props.levelOptions
  }
  return [
    { value: 'A', label: 'A级' },
    { value: 'B', label: 'B级' },
    { value: 'C', label: 'C级' },
    { value: 'D', label: 'D级' }
  ]
})

const normalizedTagOptions = computed(() => {
  if (props.tagOptions.length > 0) {
    return props.tagOptions
  }
  return [
    { value: 'high_value', label: '高净值' },
    { value: 'franchise_exp', label: '曾加盟过' },
    { value: 'mall_shop', label: '商场铺' },
    { value: 'competitor_convert', label: '竞品转出' }
  ]
})

const filterData = reactive({
  owner: '',
  source: [],
  createDateRange: null,
  dateRange: null,
  level: '',
  tags: []
})

const toggleTag = (tag) => {
  const index = filterData.tags.indexOf(tag)
  if (index > -1) {
    filterData.tags.splice(index, 1)
  } else {
    filterData.tags.push(tag)
  }
}

const resetFilter = () => {
  filterData.owner = ''
  filterData.source = []
  filterData.createDateRange = null
  filterData.dateRange = null
  filterData.level = ''
  filterData.tags = []
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
/* 美化 Radio Button 让它看起来像现代的卡片选择器 */
:deep(.el-radio-button__inner) {
  width: 100%;
  border-radius: 8px !important;
  border: 1px solid #e2e8f0 !important;
  box-shadow: none !important;
  background: #f8fafc;
}
:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: #e0f2fe;
  color: #2563eb;
  border-color: #bfdbfe !important;
}
:deep(.el-radio-button:first-child .el-radio-button__inner),
:deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 8px !important;
}
</style>
