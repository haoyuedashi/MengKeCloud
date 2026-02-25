<template>
  <div class="h-full flex flex-col md:flex-row gap-4 bg-transparent p-0">
    <!-- 左侧业务对象列表 -->
    <div class="w-full md:w-56 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden shrink-0">
      <div class="p-4 border-b border-gray-100 flex items-center bg-gray-50/50">
        <h3 class="font-bold text-gray-800 flex items-center">
          <el-icon class="mr-2 text-indigo-500"><DocumentCopy /></el-icon>
          业务对象
        </h3>
      </div>
      <div class="flex-1 overflow-y-auto p-2 space-y-1">
        <div 
          v-for="entity in entities" 
          :key="entity.id"
          class="px-4 py-3 rounded-lg cursor-pointer transition-colors flex justify-between items-center group"
          :class="selectedEntity?.id === entity.id ? 'bg-indigo-50 text-indigo-600 font-medium' : 'hover:bg-gray-50 text-gray-700'"
          @click="selectedEntity = entity"
        >
          <div class="flex items-center">
            <el-icon class="mr-2"><component :is="entity.icon" /></el-icon>
            <span class="text-sm">{{ entity.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧字段表格 -->
    <div class="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
      <!-- Header -->
      <div class="p-4 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-gray-50/50">
        <h3 class="font-bold text-gray-800 flex items-center">
          <span>{{ selectedEntity?.name }} - 字段设置</span>
        </h3>
        <el-button type="primary" class="shadow-md shadow-blue-500/30" @click="openFieldDialog()">
          <el-icon class="mr-1"><Plus /></el-icon> 新建字段
        </el-button>
      </div>
      
      <!-- Table -->
      <div class="flex-1 overflow-hidden p-4">
        <el-table :data="fieldsData" height="100%" class="custom-table" row-key="id">
          <el-table-column prop="name" label="字段名称" min-width="120">
            <template #default="{ row }">
              <span class="font-medium text-gray-700">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="code" label="英文字段名" min-width="120" class-name="text-gray-500 font-mono text-xs" />
          <el-table-column prop="type" label="字段类型" width="100">
            <template #default="{ row }">
              <el-tag size="small" type="info" effect="plain">{{ getTypeName(row.type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="isRequired" label="是否必填" width="90" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.isRequired" :disabled="row.isSystem" size="small" @change="() => updateFieldSwitch(row)" />
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.isSystem" type="success" size="small">内置</el-tag>
              <el-switch v-else v-model="row.active" size="small" @change="() => updateFieldSwitch(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openFieldDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" :disabled="row.isSystem" @click="deleteField(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 新建/编辑字段抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="isEdit ? '编辑字段' : '新建字段'"
      :size="drawerSize"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="字段名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入中文字段名称，如：客户预算" />
        </el-form-item>
        <el-form-item label="英文字段名" prop="code">
          <el-input v-model="form.code" placeholder="如：customer_budget" :disabled="isEdit" />
          <div class="text-xs text-gray-400 mt-1">创建后不可修改，用于API对接和系统底层标识</div>
        </el-form-item>
        <el-form-item label="字段类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择字段类型" class="w-full" :disabled="isEdit">
            <el-option label="单行文本 (Text)" value="text" />
            <el-option label="多行文本 (Textarea)" value="textarea" />
            <el-option label="数字 (Number)" value="number" />
            <el-option label="单选菜单 (Select)" value="select" />
            <el-option label="日期 (Date)" value="date" />
          </el-select>
        </el-form-item>
        <el-form-item label="占位提示 (Placeholder)">
          <el-input v-model="form.placeholder" placeholder="输入框内灰色的提示文字" />
        </el-form-item>
        <el-form-item v-if="form.type === 'select'" label="下拉选项">
          <div class="w-full space-y-2">
            <div v-for="(option, index) in form.fieldOptions" :key="`opt-${index}`" class="grid grid-cols-[1fr_1fr_auto] gap-2 items-center">
              <el-input v-model="option.label" placeholder="显示名称，如：预算50万内" />
              <el-input v-model="option.value" placeholder="选项值，如：budget_50" />
              <el-button text type="danger" @click="removeFieldOption(index)">删除</el-button>
            </div>
            <el-button text type="primary" @click="addFieldOption">+ 添加选项</el-button>
            <div class="text-xs text-gray-400">建议 2-10 个选项；显示名称给业务看，选项值用于系统存储。</div>
          </div>
        </el-form-item>
        <el-form-item label="其他设置">
          <div class="flex items-center space-x-6">
            <el-checkbox v-model="form.isRequired" label="设为必填" />
            <el-checkbox v-model="form.active" label="默认启用" />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="flex: auto">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="saveField">确认保存</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { DocumentCopy, Postcard, Avatar, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCustomFields, createCustomField, updateCustomField, deleteCustomField as apiDeleteCustomField } from '@/api/settings'
import { useLeadMeta } from '@/composables/useLeadMeta'

const { invalidateLeadMeta } = useLeadMeta()

const windowWidth = ref(window.innerWidth)
const drawerSize = computed(() => windowWidth.value < 768 ? '100%' : '400px')

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

const entities = ref([
  { id: 'lead', name: '客户模块', icon: 'Postcard' }
])
const selectedEntity = ref(entities.value[0])

const typeDict = {
  text: '单行文本',
  textarea: '多行文本',
  number: '数字金额',
  select: '下拉单选',
  date: '日期时间'
}
const getTypeName = (type) => typeDict[type] || type

const allFields = ref({ lead: [] })

const fieldsData = computed(() => {
  if (!selectedEntity.value) return []
  return allFields.value[selectedEntity.value.id] || []
})

const loadFields = async () => {
  if (!selectedEntity.value?.id) {
    return
  }
  const data = await getCustomFields(selectedEntity.value.id)
  allFields.value[selectedEntity.value.id] = data.list || []
}

const drawerVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = ref({
  id: null,
  name: '',
  code: '',
  type: 'text',
  placeholder: '',
  fieldOptions: [],
  isRequired: false,
  active: true,
  isSystem: false
})

const rules = {
  name: [{ required: true, message: '请输入字段名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入英文字段名', trigger: 'blur' },
    { pattern: /^[a-z_][a-z0-9_]*$/, message: '只能包含小写字母、数字和下划线，且不能以数字开头', trigger: 'blur' }
  ],
  type: [{ required: true, message: '请选择字段类型', trigger: 'change' }]
}

const openFieldDialog = (row = null) => {
  isEdit.value = !!row
  if (row) {
    form.value = {
      ...row,
      fieldOptions: (row.fieldOptions || []).map((item) => ({
        label: item.label || '',
        value: item.value || ''
      }))
    }
  } else {
    form.value = {
      id: null,
      name: '',
      code: '',
      type: 'text',
      placeholder: '',
      fieldOptions: [],
      isRequired: false,
      active: true,
      isSystem: false
    }
  }
  drawerVisible.value = true
}

const addFieldOption = () => {
  form.value.fieldOptions.push({ label: '', value: '' })
}

const removeFieldOption = (index) => {
  form.value.fieldOptions.splice(index, 1)
}

const normalizeFieldOptions = () => {
  const seen = new Set()
  const normalized = []
  for (const item of form.value.fieldOptions || []) {
    const label = (item?.label || '').trim()
    const value = (item?.value || '').trim()
    if (!label || !value || seen.has(value)) {
      continue
    }
    seen.add(value)
    normalized.push({ label, value })
  }
  return normalized
}

const saveField = () => {
  formRef.value.validate((valid) => {
    if (!valid) {
      return
    }

    const normalizedFieldOptions = normalizeFieldOptions()
    if (form.value.type === 'select' && normalizedFieldOptions.length === 0) {
      ElMessage.warning('下拉菜单字段至少需要一个有效选项')
      return
    }

    if (isEdit.value) {
      updateCustomField(form.value.id, {
        name: form.value.name,
        placeholder: form.value.placeholder,
        fieldOptions: normalizedFieldOptions,
        isRequired: form.value.isRequired,
        active: form.value.active
      }).then(async () => {
        await loadFields()
        invalidateLeadMeta()
        drawerVisible.value = false
        ElMessage.success('修改成功')
      }).catch((error) => {
        ElMessage.error(error?.response?.data?.message || '修改失败')
      })
    } else {
      createCustomField(selectedEntity.value.id, {
        name: form.value.name,
        code: form.value.code,
        type: form.value.type,
        placeholder: form.value.placeholder,
        fieldOptions: normalizedFieldOptions,
        isRequired: form.value.isRequired,
        active: form.value.active
      }).then(async () => {
        await loadFields()
        invalidateLeadMeta()
        drawerVisible.value = false
        ElMessage.success('创建成功')
      }).catch((error) => {
        ElMessage.error(error?.response?.data?.message || '创建失败')
      })
    }
  })
}

const deleteField = (row) => {
  ElMessageBox.confirm(
    `确定要删除自定义字段「${row.name}」吗？相关数据可能无法显示。`,
    '删除确认',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    apiDeleteCustomField(row.id).then(async () => {
      await loadFields()
      invalidateLeadMeta()
      ElMessage.success('已删除')
    }).catch((error) => {
      ElMessage.error(error?.response?.data?.message || '删除失败')
    })
  }).catch(() => {})
}

const updateFieldSwitch = (row) => {
  updateCustomField(row.id, {
    isRequired: row.isRequired,
    active: row.active
  }).then(() => {
    invalidateLeadMeta()
  }).catch((error) => {
    ElMessage.error(error?.response?.data?.message || '字段状态更新失败')
    loadFields()
  })
}

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  try {
    await loadFields()
  } catch (error) {
    ElMessage.error('字段配置加载失败')
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.custom-table {
  --el-table-header-bg-color: #f8fafc;
}
</style>
