<template>
  <div class="h-full flex flex-col md:flex-row gap-4 bg-transparent p-0">
    <!-- 左侧角色列表 -->
    <div class="w-full md:w-64 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden shrink-0">
      <div class="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h3 class="font-bold text-gray-800 flex items-center">
          <el-icon class="mr-2 text-indigo-500"><Avatar /></el-icon>
          角色列表
        </h3>
        <el-button type="primary" link @click="handleAddRole">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <div class="flex-1 overflow-y-auto p-2 space-y-1">
        <div 
          v-for="role in roles" 
          :key="role.id"
          class="px-4 py-3 rounded-lg cursor-pointer transition-colors flex justify-between items-center group"
          :class="selectedRole?.id === role.id ? 'bg-indigo-50 text-indigo-600' : 'hover:bg-gray-50 text-gray-700'"
          @click="selectRole(role)"
        >
          <div class="flex items-center">
            <el-icon class="mr-2"><User /></el-icon>
            <span class="font-medium text-sm">{{ role.name }}</span>
          </div>
          <div class="flex items-center gap-1">
            <el-button
              type="primary"
              link
              size="small"
              class="opacity-0 group-hover:opacity-100"
              @click.stop="openEditRole(role)"
            >
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button
              v-if="!role.isSystem"
              type="danger"
              link
              size="small"
              class="opacity-0 group-hover:opacity-100"
              @click.stop="deleteRole(role)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
            <el-tag v-else size="small" type="info" effect="plain" class="scale-90">系统</el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧权限配置 -->
    <div class="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
      <div class="p-4 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-gray-50/50">
        <h3 class="font-bold text-gray-800 flex items-center">
          <span v-if="selectedRole">正在配置: <span class="text-indigo-600 ml-1">{{ selectedRole.name }}</span></span>
          <span v-else>请选择一个角色</span>
        </h3>
        <div class="flex items-center gap-3">
          <span v-if="selectedRole && isRoleDirty" class="text-xs text-amber-600">有未保存修改</span>
          <el-button type="primary" class="shadow-md shadow-blue-500/30" :disabled="!selectedRole || !isRoleDirty" @click="savePermissions">
            保存配置
          </el-button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-6" v-if="selectedRole">
        <el-tabs v-model="activeTab" class="custom-tabs">
          <el-tab-pane label="菜单与功能权限" name="menu">
            <div class="bg-gray-50/50 border border-gray-100 rounded-lg p-4 mt-2">
              <el-tree
                ref="treeRef"
                :data="menuData"
                show-checkbox
                node-key="id"
                default-expand-all
                class="bg-transparent"
              />
            </div>
          </el-tab-pane>
          <el-tab-pane label="数据可见范围" name="data">
            <div class="bg-gray-50/50 border border-gray-100 rounded-lg p-6 mt-2">
              <div class="mb-4 text-sm text-gray-500">设置该角色在系统内可以查看和操作哪部分数据（如线索、公海、报表等）。</div>
              <el-radio-group v-model="selectedRole.dataScope" class="flex flex-col space-y-4">
                <el-radio :value="'all'" size="large" class="!mr-0 bg-white border border-gray-200 px-4 py-2 rounded-lg hover:border-indigo-300 transition-colors">
                  <span class="font-bold text-gray-800">全部数据可见 (老板/超级管理员)</span>
                  <p class="text-xs text-gray-400 mt-1 pl-6 whitespace-normal">可查看和操作全公司所有业务部门的数据，包括系统配置和业绩报表。</p>
                </el-radio>
                <el-radio :value="'dept'" size="large" class="!mr-0 bg-white border border-gray-200 px-4 py-2 rounded-lg hover:border-indigo-300 transition-colors">
                  <span class="font-bold text-gray-800">本部门及下属部门可见 (主管/经理)</span>
                  <p class="text-xs text-gray-400 mt-1 pl-6 whitespace-normal">仅可查看所属部门以及所有子部门的线索和员工业绩数据。</p>
                </el-radio>
                <el-radio :value="'self'" size="large" class="!mr-0 bg-white border border-gray-200 px-4 py-2 rounded-lg hover:border-indigo-300 transition-colors">
                  <span class="font-bold text-gray-800">仅看本人数据 (普通销售)</span>
                  <p class="text-xs text-gray-400 mt-1 pl-6 whitespace-normal">仅能在列表中看到分配给自己或自己录入的线索，无法看到其他人的数据。</p>
                </el-radio>
              </el-radio-group>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <div v-else class="flex-1 flex items-center justify-center text-gray-400">
        <el-empty description="点击左侧列表选择要配置的角色" />
      </div>
    </div>

    <el-dialog v-model="roleDialog.visible" :title="roleDialog.title" width="460px">
      <el-form label-position="top">
        <el-form-item label="角色名称">
          <el-input v-model="roleDialog.form.name" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="默认数据可见范围">
          <el-radio-group v-model="roleDialog.form.dataScope">
            <el-radio :value="'all'">全部数据</el-radio>
            <el-radio :value="'dept'">本部门及下属部门</el-radio>
            <el-radio :value="'self'">仅本人数据</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="roleDialog.form.active" inline-prompt active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitRoleDialog">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed, nextTick } from 'vue'
import { Plus, Avatar, User, Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoles, createRole, updateRole, deleteRole as apiDeleteRole } from '@/api/settings'

const activeTab = ref('menu')
const treeRef = ref(null)

const menuData = ref([
  {
    id: 1,
    label: '工作台',
    children: [
      { id: 11, label: '查看个人简报' }
    ]
  },
  {
    id: 2,
        label: '客户管理',
    children: [
      { id: 21, label: '客户列表查询与跟进' },
      { id: 22, label: '客户导出Excel权限' }
    ]
  },
  {
    id: 3,
    label: '公海池',
    children: [
      { id: 31, label: '查看公海池' },
      { id: 32, label: '捞取公海客户' },
      { id: 33, label: '定向分配公海客户' }
    ]
  },
  {
    id: 4,
    label: '数据报表',
    children: [
      { id: 41, label: '查看全局营收与排行看板' }
    ]
  },
  {
    id: 5,
    label: '系统配置',
    children: [
      { id: 51, label: '组织架构管理' },
      { id: 52, label: '账号与权限' },
      { id: 53, label: '字段自定义' },
      { id: 54, label: '字典管理' },
      { id: 55, label: '自动回收规则' }
    ]
  }
])

const collectMenuIds = (nodes = []) => {
  const ids = []
  nodes.forEach((node) => {
    ids.push(Number(node.id))
    if (Array.isArray(node.children) && node.children.length > 0) {
      ids.push(...collectMenuIds(node.children))
    }
  })
  return ids
}

const menuIdSet = computed(() => new Set(collectMenuIds(menuData.value)))

const roles = ref([])
const roleDialog = ref({
  visible: false,
  title: '新建角色',
  mode: 'create',
  roleId: null,
  form: {
    name: '',
    dataScope: 'self',
    active: true
  }
})

const selectedRole = ref(null)
const baselineRoleState = ref(null)

const normalizeMenuKeys = (keys = []) => {
  const normalized = [...new Set((keys || []).map((item) => Number(item)))]
    .filter((item) => menuIdSet.value.has(item))
    .sort((a, b) => a - b)
  return normalized
}

const roleStateSnapshot = (role, menuKeys) => {
  if (!role) {
    return null
  }
  return {
    id: role.id,
    name: role.name,
    dataScope: role.dataScope,
    active: role.active ?? true,
    menuKeys: normalizeMenuKeys(menuKeys)
  }
}

const getCurrentMenuKeys = () => {
  if (!treeRef.value) {
    return selectedRole.value?.menuKeys || []
  }
  return normalizeMenuKeys(treeRef.value.getCheckedKeys())
}

const isRoleDirty = computed(() => {
  if (!selectedRole.value || !baselineRoleState.value) {
    return false
  }
  const current = roleStateSnapshot(selectedRole.value, getCurrentMenuKeys())
  return JSON.stringify(current) !== JSON.stringify(baselineRoleState.value)
})

const loadRoles = async () => {
  const data = await getRoles()
  roles.value = (data.list || []).map((item) => ({
    ...item,
    menuKeys: normalizeMenuKeys(item.menuKeys || [])
  }))
  if (!selectedRole.value && roles.value.length > 0) {
    selectedRole.value = roles.value[0]
  } else if (selectedRole.value) {
    selectedRole.value = roles.value.find((item) => item.id === selectedRole.value.id) || roles.value[0] || null
  }
}

onMounted(async () => {
  try {
    await loadRoles()
  } catch (error) {
    ElMessage.error('角色数据加载失败')
  }
})

const selectRole = (role) => {
  if (selectedRole.value?.id === role.id) {
    return
  }
  if (isRoleDirty.value) {
    ElMessageBox.confirm(
      `当前角色「${selectedRole.value?.name || ''}」有未保存修改，是否放弃后切换？`,
      '未保存变更提醒',
      {
        type: 'warning',
        confirmButtonText: '放弃并切换',
        cancelButtonText: '继续编辑'
      }
    ).then(() => {
      selectedRole.value = role
    }).catch(() => {})
    return
  }
  selectedRole.value = role
}

// 解决切换角色时树状复选框未更新的问题
watch(selectedRole, (newVal) => {
  if (treeRef.value && newVal) {
    treeRef.value.setCheckedKeys(normalizeMenuKeys(newVal.menuKeys || []))
    nextTick(() => {
      baselineRoleState.value = roleStateSnapshot(newVal, getCurrentMenuKeys())
    })
  }
})

watch(
  () => [treeRef.value, selectedRole.value?.id],
  () => {
    if (!treeRef.value || !selectedRole.value || baselineRoleState.value) {
      return
    }
    treeRef.value.setCheckedKeys(normalizeMenuKeys(selectedRole.value.menuKeys || []))
    nextTick(() => {
      baselineRoleState.value = roleStateSnapshot(selectedRole.value, getCurrentMenuKeys())
    })
  }
)

const handleAddRole = () => {
  roleDialog.value = {
    visible: true,
    title: '新建角色',
    mode: 'create',
    roleId: null,
    form: {
      name: '',
      dataScope: 'self',
      active: true
    }
  }
}

const openEditRole = (role) => {
  roleDialog.value = {
    visible: true,
    title: role.isSystem ? '查看/调整系统角色' : '编辑角色',
    mode: 'edit',
    roleId: role.id,
    form: {
      name: role.name,
      dataScope: role.dataScope,
      active: role.active ?? true
    }
  }
}

const submitRoleDialog = () => {
  const form = roleDialog.value.form
  if (!form.name.trim()) {
    ElMessage.warning('请输入角色名称')
    return
  }
  const normalizedName = form.name.trim()
  const duplicated = roles.value.some((role) => {
    if (roleDialog.value.mode === 'edit' && role.id === roleDialog.value.roleId) {
      return false
    }
    return role.name === normalizedName
  })
  if (duplicated) {
    ElMessage.warning('角色名称已存在')
    return
  }

  if (roleDialog.value.mode === 'create') {
    createRole({
      name: normalizedName,
      menuKeys: [],
      dataScope: form.dataScope,
      active: form.active
    }).then(async (created) => {
      roleDialog.value.visible = false
      await loadRoles()
      selectedRole.value = roles.value.find((item) => item.id === created.id) || selectedRole.value
      ElMessage.success('已新建角色，请配置权限')
    }).catch((error) => {
      ElMessage.error(error?.response?.data?.message || '创建角色失败')
    })
    return
  }

  const editingId = roleDialog.value.roleId
  updateRole(editingId, {
    name: normalizedName,
    dataScope: form.dataScope,
    active: form.active
  }).then(async () => {
    roleDialog.value.visible = false
    await loadRoles()
    selectedRole.value = roles.value.find((item) => item.id === editingId) || selectedRole.value
    ElMessage.success('角色信息已更新')
  }).catch((error) => {
    ElMessage.error(error?.response?.data?.message || '更新角色失败')
  })
}

const deleteRole = (role) => {
  if (role.isSystem) {
    ElMessage.warning('系统内置角色无法删除')
    return
  }
  apiDeleteRole(role.id).then(async () => {
    await loadRoles()
    ElMessage.success('角色已删除')
  }).catch((error) => {
    ElMessage.error(error?.response?.data?.message || '删除失败')
  })
}

const savePermissions = () => {
  if (!selectedRole.value) return
  if (treeRef.value) {
     selectedRole.value.menuKeys = normalizeMenuKeys(treeRef.value.getCheckedKeys())
  }
  updateRole(selectedRole.value.id, {
    name: selectedRole.value.name,
    menuKeys: selectedRole.value.menuKeys,
    dataScope: selectedRole.value.dataScope,
    active: selectedRole.value.active ?? true
  }).then(async () => {
    await loadRoles()
    selectedRole.value = roles.value.find((item) => item.id === selectedRole.value.id) || selectedRole.value
    if (selectedRole.value) {
      baselineRoleState.value = roleStateSnapshot(selectedRole.value, selectedRole.value.menuKeys)
    }
    ElMessage.success(`${selectedRole.value.name} 权限配置已保存`)
  }).catch((error) => {
    ElMessage.error(error?.response?.data?.message || '保存失败')
  })
}
</script>

<style scoped>
.custom-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 500;
}
.custom-tabs :deep(.el-tabs__active-bar) {
  background-color: #4f46e5; /* indigo-600 */
}
.custom-tabs :deep(.el-tabs__item.is-active) {
  color: #4f46e5;
}
</style>
