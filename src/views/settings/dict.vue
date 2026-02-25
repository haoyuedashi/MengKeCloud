<template>
  <div class="h-full flex flex-col md:flex-row gap-4 bg-transparent p-0">
    <!-- 左侧字典分类 -->
    <div class="w-full md:w-56 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden shrink-0">
      <div class="p-4 border-b border-gray-100 flex items-center bg-gray-50/50">
        <h3 class="font-bold text-gray-800 flex items-center">
          <el-icon class="mr-2 text-indigo-500"><Collection /></el-icon>
          数据字典
        </h3>
      </div>
      <div class="flex-1 overflow-y-auto p-2 space-y-1">
        <div 
          v-for="dict in dictTypes" 
          :key="dict.code"
          class="px-4 py-3 rounded-lg cursor-pointer transition-colors flex justify-between items-center group"
          :class="selectedDict?.code === dict.code ? 'bg-indigo-50 text-indigo-600 font-medium' : 'hover:bg-gray-50 text-gray-700'"
          @click="selectedDict = dict"
        >
          <span class="text-sm flex items-center">
            <el-icon class="mr-2 text-gray-400" :class="{ 'text-indigo-500': selectedDict?.code === dict.code }"><Menu /></el-icon>
            {{ dict.name }}
          </span>
        </div>
      </div>
    </div>

    <!-- 右侧字典值管理 -->
    <div class="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
      <!-- Header -->
      <div class="p-4 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-gray-50/50">
        <h3 class="font-bold text-gray-800 flex items-center">
          <span>{{ selectedDict?.name }} - 选项配置</span>
        </h3>
        <el-button type="primary" class="shadow-md shadow-blue-500/30 w-full sm:w-auto" @click="openItemDialog()">
          <el-icon class="mr-1"><Plus /></el-icon> 添加选项
        </el-button>
      </div>
      
      <!-- Table -->
      <div class="flex-1 overflow-hidden p-4">
        <el-table :data="filteredItems" height="100%" class="custom-table" row-key="id">
          <el-table-column label="排序" width="80" align="center">
            <template #default="{ $index, row }">
              <div class="flex flex-col items-center space-y-1">
                <el-icon 
                  class="cursor-pointer hover:text-indigo-600 text-gray-300"
                  :class="{ 'opacity-30 cursor-not-allowed': $index === 0 }"
                  @click="moveItem($index, -1)"
                ><CaretTop /></el-icon>
                <el-icon 
                  class="cursor-pointer hover:text-indigo-600 text-gray-300"
                  :class="{ 'opacity-30 cursor-not-allowed': $index === filteredItems.length - 1 }"
                  @click="moveItem($index, 1)"
                ><CaretBottom /></el-icon>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="label" label="选项名称" min-width="150">
            <template #default="{ row }">
              <span class="font-medium text-gray-700 flex items-center">
                <span 
                  v-if="row.color" 
                  class="w-3 h-3 rounded-full mr-2 inline-block" 
                  :style="{ backgroundColor: row.color }"
                ></span>
                {{ row.label }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="value" label="选项值 (Value)" min-width="120" class-name="text-gray-500 font-mono text-xs" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.active" size="small" :disabled="row.isSystem" @change="() => toggleDictItemActive(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right" align="center">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openItemDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" :disabled="row.isSystem" @click="deleteItem(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 添加/编辑选项抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="isEdit ? '编辑选项' : '添加选项'"
      :size="drawerSize"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="选项名称" prop="label">
          <el-input v-model="form.label" placeholder="页面上展示的文本，如：A级-强烈意向" />
        </el-form-item>
        <el-form-item label="标识值 (Value)" prop="value">
          <el-input v-model="form.value" placeholder="存储到数据库的值，如：A" :disabled="isEdit && form.isSystem" />
          <div class="text-xs text-gray-400 mt-1">建议使用英文字母或整型数字，保存后部分内置项不可改</div>
        </el-form-item>
        <el-form-item label="标记颜色" prop="color">
          <el-color-picker v-model="form.color" show-alpha :predefine="predefineColors" />
          <span class="text-xs text-gray-400 ml-3">用于在表格标签中展示时的背景色（可选）</span>
        </el-form-item>
        <el-form-item label="选项设置">
          <el-checkbox v-model="form.active" label="默认启用此选项" :disabled="form.isSystem" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="flex: auto">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="saveItem">确认保存</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Collection, Menu, Plus, CaretTop, CaretBottom } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getDictTypes,
  getDictItemsManage,
  createDictItem,
  updateDictItem,
  deleteDictItem as apiDeleteDictItem,
  moveDictItem as apiMoveDictItem
} from '@/api/settings'
import { useLeadMeta } from '@/composables/useLeadMeta'

const { invalidateLeadMeta } = useLeadMeta()

const windowWidth = ref(window.innerWidth)
const drawerSize = computed(() => windowWidth.value < 768 ? '100%' : '420px')
const handleResize = () => {
  windowWidth.value = window.innerWidth
}

// 字典分类
const dictTypes = ref([])
const selectedDict = ref(null)

const allItems = ref({})

// 预定义颜色面板
const predefineColors = ref([
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#10b981', '#14b8a6', 
  '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#db2777', '#f43f5e'
])

const filteredItems = computed(() => {
  if (!selectedDict.value) return []
  return (allItems.value[selectedDict.value.code] || []).sort((a, b) => a.sort - b.sort)
})

const loadDictTypes = async () => {
  const data = await getDictTypes()
  dictTypes.value = data || []
  if (!selectedDict.value && dictTypes.value.length > 0) {
    selectedDict.value = dictTypes.value[0]
  }
}

const loadDictItems = async (dictCode) => {
  if (!dictCode) {
    return
  }
  const data = await getDictItemsManage(dictCode)
  allItems.value[dictCode] = data.items || []
}

// 表单控制
const drawerVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = ref({
  id: null,
  label: '',
  value: '',
  color: '',
  active: true,
  isSystem: false,
  sort: 1
})

const rules = {
  label: [{ required: true, message: '请输入选项名称', trigger: 'blur' }],
  value: [{ required: true, message: '请输入选项标识值', trigger: 'blur' }]
}

const openItemDialog = (row = null) => {
  isEdit.value = !!row
  if (row) {
    form.value = { ...row }
  } else {
    const list = filteredItems.value
    const nextSort = list.length > 0 ? Math.max(...list.map(i => i.sort)) + 1 : 1
    form.value = {
      id: null,
      label: '',
      value: '',
      color: '',
      active: true,
      isSystem: false,
      sort: nextSort
    }
  }
  drawerVisible.value = true
}

const saveItem = () => {
  formRef.value.validate((valid) => {
    if (!valid) {
      return
    }
    if (isEdit.value) {
      updateDictItem(form.value.id, {
        label: form.value.label,
        value: form.value.value,
        color: form.value.color,
        active: form.value.active
      }).then(async () => {
        await loadDictItems(selectedDict.value.code)
        invalidateLeadMeta()
        drawerVisible.value = false
        ElMessage.success('修改成功')
      }).catch((error) => {
        ElMessage.error(error?.response?.data?.message || '修改失败')
      })
    } else {
      createDictItem(selectedDict.value.code, {
        label: form.value.label,
        value: form.value.value,
        color: form.value.color,
        active: form.value.active
      }).then(async () => {
        await loadDictItems(selectedDict.value.code)
        invalidateLeadMeta()
        drawerVisible.value = false
        ElMessage.success('创建成功')
      }).catch((error) => {
        ElMessage.error(error?.response?.data?.message || '创建失败')
      })
    }
  })
}

const deleteItem = (row) => {
  if (row.isSystem) {
    ElMessage.warning('系统内置字典不可删除！')
    return
  }
  ElMessageBox.confirm(
    `确定要删除选项「${row.label}」吗？已使用此值的线索将会受到影响。`,
    '高危操作确认',
    {
      confirmButtonText: '强制删除',
      cancelButtonText: '取消',
      type: 'error',
    }
  ).then(() => {
    apiDeleteDictItem(row.id).then(async () => {
      await loadDictItems(selectedDict.value.code)
      invalidateLeadMeta()
      ElMessage.success('已清空')
    }).catch((error) => {
      ElMessage.error(error?.response?.data?.message || '删除失败')
    })
  }).catch(() => {})
}

// 排序移动
const moveItem = (index, direction) => {
  if (index === 0 && direction === -1) return
  if (index === filteredItems.value.length - 1 && direction === 1) return

  const itemA = filteredItems.value[index]
  const moveDirection = direction === -1 ? 'up' : 'down'
  apiMoveDictItem(itemA.id, moveDirection).then(async () => {
    await loadDictItems(selectedDict.value.code)
    invalidateLeadMeta()
  }).catch((error) => {
    ElMessage.error(error?.response?.data?.message || '排序失败')
  })
}

const toggleDictItemActive = (row) => {
  updateDictItem(row.id, {
    active: row.active
  }).then(() => {
    invalidateLeadMeta()
  }).catch((error) => {
    ElMessage.error(error?.response?.data?.message || '状态更新失败')
    loadDictItems(selectedDict.value.code)
  })
}

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  try {
    await loadDictTypes()
    if (selectedDict.value?.code) {
      await loadDictItems(selectedDict.value.code)
    }
  } catch (error) {
    ElMessage.error('字典数据加载失败')
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

watch(
  () => selectedDict.value?.code,
  async (dictCode) => {
    if (!dictCode) {
      return
    }
    try {
      await loadDictItems(dictCode)
    } catch (error) {
      ElMessage.error('字典项加载失败')
    }
  }
)

</script>

<style scoped>
.custom-table {
  --el-table-header-bg-color: #f8fafc;
}
</style>
