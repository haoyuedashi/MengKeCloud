<template>
  <div class="h-full flex flex-col md:flex-row gap-4 bg-transparent p-0">
    <!-- 左侧部门树 -->
    <div class="w-full md:w-72 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden shrink-0">
      <div class="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h3 class="font-bold text-gray-800 flex items-center">
          <el-icon class="mr-2 text-blue-500"><OfficeBuilding /></el-icon>
          组织架构
        </h3>
        <el-button type="primary" link @click="handleAddDept">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <div class="p-3 flex-1 overflow-y-auto">
        <el-input
          v-model="filterText"
          placeholder="搜索部门"
          clearable
          class="mb-4"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-tree
          ref="treeRef"
          :data="deptData"
          node-key="id"
          default-expand-all
          draggable
          :allow-drop="allowDeptDrop"
          :filter-node-method="filterNode"
          :expand-on-click-node="false"
          class="custom-tree"
          @node-click="handleNodeClick"
          @node-drop="handleDeptDrop"
        >
          <template #default="{ node, data }">
            <div class="flex-1 flex justify-between items-center group pr-2 text-sm">
              <span class="flex items-center" :class="{ 'font-semibold text-blue-600': selectedDept?.id === data.id }">
                <el-icon class="mr-1 text-gray-400" v-if="data.children && data.children.length > 0"><FolderOpened /></el-icon>
                <el-icon class="mr-1 text-gray-400" v-else><Document /></el-icon>
                {{ node.label }}
              </span>
              <div class="opacity-0 group-hover:opacity-100 transition-opacity flex items-center space-x-1">
                <el-button type="primary" link size="small" @click.stop="() => append(data)"><el-icon><Plus /></el-icon></el-button>
                <el-button type="primary" link size="small" @click.stop="() => openDeptDialog('edit', data)"><el-icon><Edit /></el-icon></el-button>
                <el-button type="danger" link size="small" @click.stop="() => remove(node, data)"><el-icon><Delete /></el-icon></el-button>
              </div>
            </div>
          </template>
        </el-tree>
      </div>
    </div>

    <!-- 右侧人员列表 -->
    <div class="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
      <!-- 头部 -->
      <div class="p-4 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-gray-50/50">
        <h3 class="font-bold text-gray-800 flex items-center">
          <el-icon class="mr-2 text-indigo-500"><UserFilled /></el-icon>
          员工管理
          <span v-if="selectedDept" class="ml-2 text-sm font-normal text-gray-500 px-2 py-1 bg-gray-100 rounded-md">
            {{ selectedDept.label }}
          </span>
        </h3>
        <div class="flex space-x-2">
          <el-input v-model="searchUser" placeholder="搜索员工姓名/电话" class="w-48" clearable>
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button type="primary" class="shadow-md shadow-blue-500/30" @click="handleAddUser">
            <el-icon class="mr-1"><Plus /></el-icon> 添加员工
          </el-button>
        </div>
      </div>
      
      <!-- 表格 -->
      <div class="flex-1 overflow-hidden p-4">
        <el-table :data="filteredUsers" height="100%" class="custom-table">
          <el-table-column prop="name" label="姓名" width="120">
            <template #default="{ row }">
              <div class="flex items-center">
                <el-avatar :size="28" class="mr-2 bg-blue-100 text-blue-600 font-bold">{{ row.name.charAt(0) }}</el-avatar>
                <span class="font-medium text-gray-700">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="所属部门" min-width="180">
            <template #default="{ row }">
              <span>{{ getDeptLabel(row.deptId) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号码" width="130" />
          <el-table-column prop="role" label="系统角色" width="120">
            <template #default="{ row }">
              <el-tag :type="row.role === 'manager' ? 'warning' : (row.role === 'admin' ? 'danger' : 'info')" size="small">
                {{ roleLabel(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="账号状态" width="100">
            <template #default="{ row }">
              <el-switch v-model="row.active" inline-prompt active-text="启用" inactive-text="停用" @change="(val) => handleUserActiveChange(row, val)" />
            </template>
          </el-table-column>
          <el-table-column prop="monthlyTarget" label="月目标(单)" width="110" align="center" />
          <el-table-column prop="joinDate" label="加入时间" min-width="160">
            <template #default="{ row }">
              <span>{{ formatJoinDate(row.joinDate) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openUserDialog('edit', row)">编辑</el-button>
              <el-button link type="primary" size="small" @click="openUserDialog('dept', row)">更换部门</el-button>
              <el-button v-if="row.id !== 'ST001'" link type="danger" size="small" @click="handleDeleteUser(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <!-- 分页 -->
      <div class="p-3 border-t border-gray-100 flex justify-end bg-gray-50 shrink-0">
        <el-pagination layout="total, prev, pager, next" :total="filteredUsers.length" />
      </div>
    </div>

    <el-dialog v-model="deptDialog.visible" :title="deptDialog.title" width="460px">
      <el-form label-position="top">
        <el-form-item label="部门名称">
          <el-input v-model="deptDialog.form.label" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="部门负责人">
          <el-select v-model="deptDialog.form.leaderStaffId" filterable class="w-full" placeholder="请选择负责人">
            <el-option
              v-for="user in activeUserOptions"
              :key="user.id"
              :label="`${user.name} (${user.phone})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="deptDialog.form.sortOrder" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="部门月目标(单)">
          <el-input-number v-model="deptDialog.form.monthlyTarget" :min="0" :max="10000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deptDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitDeptDialog">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="userDialog.visible" :title="userDialog.title" width="520px">
      <el-form label-position="top">
        <el-form-item label="姓名" v-if="userDialog.mode !== 'dept'">
          <el-input v-model="userDialog.form.name" maxlength="64" />
        </el-form-item>
        <el-form-item label="手机号" v-if="userDialog.mode !== 'dept'">
          <el-input v-model="userDialog.form.phone" maxlength="32" />
        </el-form-item>
        <el-form-item label="系统角色" v-if="userDialog.mode !== 'dept'">
          <el-select v-model="userDialog.form.role" class="w-full">
            <el-option label="管理员" value="admin" />
            <el-option label="主管" value="manager" />
            <el-option label="销售" value="sales" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属部门">
          <el-select v-model="userDialog.form.deptId" class="w-full">
            <el-option v-for="dept in flatDepartments" :key="dept.id" :label="dept.label" :value="dept.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="userDialog.mode === 'create' ? '初始密码' : '重置密码(可选)'" v-if="userDialog.mode !== 'dept'">
          <el-input
            v-model="userDialog.form.password"
            type="password"
            show-password
            autocomplete="new-password"
            placeholder="留空则默认 12345678（创建）或不修改（编辑）"
          />
        </el-form-item>
        <el-form-item v-if="userDialog.mode !== 'dept' && userDialog.form.role === 'sales'" label="员工月目标(单)">
          <el-input-number v-model="userDialog.form.monthlyTarget" :min="0" :max="10000" class="w-full" />
        </el-form-item>
        <el-form-item label="账号状态" v-if="userDialog.mode !== 'dept'">
          <el-switch v-model="userDialog.form.active" inline-prompt active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitUserDialog">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { OfficeBuilding, Plus, Search, FolderOpened, Document, Delete, UserFilled, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getOrgData, createDepartment, updateDepartment, deleteDepartment, createOrgUser, updateOrgUser, deleteOrgUser } from '@/api/settings'

const filterText = ref('')
const treeRef = ref(null)

const selectedDept = ref(null)
const flatDepartments = ref([])
const deptData = ref([])
const deptDialog = ref({
  visible: false,
  title: '编辑部门',
  mode: 'edit',
  departmentId: null,
  parentId: null,
  form: {
    label: '',
    leaderStaffId: '',
    sortOrder: 1,
    monthlyTarget: 0
  }
})

const userDialog = ref({
  visible: false,
  title: '编辑员工',
  mode: 'edit',
  userId: null,
  form: {
    name: '',
    phone: '',
    role: 'sales',
    password: '',
    deptId: null,
    active: true,
    monthlyTarget: 0
  }
})

watch(filterText, (val) => {
  treeRef.value.filter(val)
})

const filterNode = (value, data) => {
  if (!value) return true
  return data.label.includes(value)
}

const handleNodeClick = (data) => {
  selectedDept.value = data
}

const allUsers = ref([])

const searchUser = ref('')

const activeUserOptions = computed(() => allUsers.value.filter((user) => user.active))

const deptChildrenMap = computed(() => {
  const map = new Map()
  flatDepartments.value.forEach((dept) => {
    if (!map.has(dept.parentId)) {
      map.set(dept.parentId, [])
    }
    map.get(dept.parentId).push(dept)
  })
  return map
})

const collectDeptIds = (deptId) => {
  const result = new Set([deptId])
  const stack = [deptId]
  while (stack.length > 0) {
    const current = stack.pop()
    const children = deptChildrenMap.value.get(current) || []
    children.forEach((child) => {
      if (!result.has(child.id)) {
        result.add(child.id)
        stack.push(child.id)
      }
    })
  }
  return result
}

const filteredUsers = computed(() => {
  const currentDeptId = selectedDept.value?.id
  const deptIds = currentDeptId ? collectDeptIds(currentDeptId) : null

  return allUsers.value.filter(u => {
    const isDeptMatch = !deptIds || deptIds.has(u.deptId)
    const isTermMatch = u.name.includes(searchUser.value) || u.phone.includes(searchUser.value)
    return isDeptMatch && isTermMatch
  })
})

const formatJoinDate = (value) => {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }

  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

const getDeptLabel = (deptId) => {
  const dept = flatDepartments.value.find((item) => item.id === deptId)
  return dept?.label || '--'
}

const roleLabel = (role) => {
  if (role === 'admin') return '管理员'
  if (role === 'manager') return '主管'
  if (role === 'sales') return '销售'
  return role || '--'
}

const normalizeRoleValue = (role) => {
  const text = String(role || '').trim().toLowerCase()
  if (['admin', 'administrator', '管理员', '超级管理员'].includes(text)) return 'admin'
  if (['manager', '主管', '销售主管'].includes(text)) return 'manager'
  if (['sales', '普通销售', '员工'].includes(text)) return 'sales'
  return 'sales'
}

const buildTree = (parentId = null) => {
  const children = (deptChildrenMap.value.get(parentId) || []).sort((a, b) => a.sortOrder - b.sortOrder)
  return children.map((dept) => ({
    ...dept,
    children: buildTree(dept.id)
  }))
}

const flattenTreeForUpdate = (nodes, parentId = null, output = []) => {
  nodes.forEach((node, index) => {
    output.push({
      id: node.id,
      parentId,
      sortOrder: index + 1,
      label: node.label,
      active: node.active
    })
    if (node.children?.length) {
      flattenTreeForUpdate(node.children, node.id, output)
    }
  })
  return output
}

const allowDeptDrop = (draggingNode, dropNode) => {
  const draggingId = draggingNode?.data?.id
  const dropId = dropNode?.data?.id
  if (!draggingId || !dropId) {
    return true
  }
  const subtreeIds = collectDeptIds(draggingId)
  return !subtreeIds.has(dropId)
}

const hasCycleInTree = (records) => {
  const parentMap = new Map(records.map((item) => [item.id, item.parentId]))
  for (const item of records) {
    const visited = new Set([item.id])
    let parentId = item.parentId
    while (parentId != null) {
      if (visited.has(parentId)) {
        return true
      }
      visited.add(parentId)
      parentId = parentMap.get(parentId) ?? null
    }
  }
  return false
}

const loadData = async () => {
  const data = await getOrgData()
  flatDepartments.value = data.departments || []
  allUsers.value = (data.users || []).map((user) => ({
    ...user,
    role: normalizeRoleValue(user.role)
  }))
  deptData.value = buildTree(null)

  if (!selectedDept.value && deptData.value.length > 0) {
    selectedDept.value = deptData.value[0]
  } else if (selectedDept.value) {
    const latest = flatDepartments.value.find((item) => item.id === selectedDept.value.id)
    selectedDept.value = latest || deptData.value[0] || null
  }
}

onMounted(async () => {
  try {
    await loadData()
  } catch (error) {
    ElMessage.error('组织数据加载失败')
  }
})

const append = (data) => {
  openDeptDialog('create-child', data)
}

const remove = (node, data) => {
  deleteDepartment(data.id).then(async () => {
    await loadData()
    ElMessage.success('部门已删除')
  }).catch((error) => {
    ElMessage.error(error?.response?.data?.message || '删除失败，请先迁移子部门或员工')
  })
}

const handleAddDept = () => {
  openDeptDialog('create-root')
}

const handleAddUser = () => {
  if (!selectedDept.value?.id) {
    ElMessage.warning('请先选择一个部门')
    return
  }
  openUserDialog('create')
}

const openDeptDialog = (mode, row = null) => {
  const baseTitle = mode === 'edit' ? '编辑部门' : '新建部门'
  deptDialog.value = {
    visible: true,
    title: baseTitle,
    mode,
    departmentId: row?.id || null,
    parentId: mode === 'create-child' ? row?.id || null : row?.parentId || null,
    form: {
      label: mode === 'edit' ? row?.label || '' : '',
      leaderStaffId: mode === 'edit' ? (row?.leaderStaffId || '') : '',
      sortOrder: mode === 'edit' ? row?.sortOrder || 1 : 1,
      monthlyTarget: mode === 'edit' ? row?.monthlyTarget || 0 : 0
    }
  }
}

const submitDeptDialog = async () => {
  const form = deptDialog.value.form
  if (!form.label?.trim()) {
    ElMessage.warning('请输入部门名称')
    return
  }
  if (!form.leaderStaffId) {
    ElMessage.warning('请选择部门负责人')
    return
  }
  const normalizedName = form.label.trim()
  const siblingParentId = deptDialog.value.mode === 'edit' ? flatDepartments.value.find((item) => item.id === deptDialog.value.departmentId)?.parentId ?? null : deptDialog.value.parentId
  const duplicated = flatDepartments.value.some((item) => {
    if (deptDialog.value.mode === 'edit' && item.id === deptDialog.value.departmentId) {
      return false
    }
    return item.parentId === siblingParentId && item.label === normalizedName
  })
  if (duplicated) {
    ElMessage.warning('同级部门名称不能重复')
    return
  }

  try {
    if (deptDialog.value.mode === 'edit') {
      await updateDepartment(deptDialog.value.departmentId, {
        label: normalizedName,
        leaderStaffId: form.leaderStaffId,
        sortOrder: form.sortOrder,
        monthlyTarget: form.monthlyTarget
      })
      ElMessage.success('部门已更新')
    } else {
      await createDepartment({
        label: normalizedName,
        leaderStaffId: form.leaderStaffId,
        parentId: deptDialog.value.parentId,
        sortOrder: form.sortOrder,
        active: true,
        monthlyTarget: form.monthlyTarget
      })
      ElMessage.success('部门已创建')
    }
    deptDialog.value.visible = false
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '保存部门失败')
  }
}

const openUserDialog = (mode, row = null) => {
  const currentDeptId = mode === 'create' ? selectedDept.value?.id || null : row?.deptId || null
  userDialog.value = {
    visible: true,
    title: mode === 'create' ? '添加员工' : mode === 'dept' ? '更换部门' : '编辑员工',
    mode,
    userId: row?.id || null,
    form: {
      name: row?.name || '',
      phone: row?.phone || '',
      role: normalizeRoleValue(row?.role || 'sales'),
      password: '',
      deptId: currentDeptId,
      active: row?.active ?? true,
      monthlyTarget: row?.monthlyTarget ?? 0
    }
  }
}

const submitUserDialog = async () => {
  const form = userDialog.value.form
  if (!form.deptId) {
    ElMessage.warning('请选择所属部门')
    return
  }
  if (userDialog.value.mode !== 'dept') {
    if (!form.name.trim()) {
      ElMessage.warning('请输入员工姓名')
      return
    }
    if (!/^1\d{10}$/.test(form.phone.trim())) {
      ElMessage.warning('请输入有效的11位手机号')
      return
    }
    if (form.password && form.password.length < 8) {
      ElMessage.warning('密码至少 8 位')
      return
    }
    const duplicatedPhone = allUsers.value.some((item) => {
      if (userDialog.value.mode !== 'create' && item.id === userDialog.value.userId) {
        return false
      }
      return item.phone === form.phone.trim()
    })
    if (duplicatedPhone) {
      ElMessage.warning('手机号已存在')
      return
    }
  }
  try {
    if (userDialog.value.mode === 'create') {
      await createOrgUser({
        name: form.name.trim(),
        phone: form.phone.trim(),
        role: form.role,
        password: form.password || undefined,
        deptId: form.deptId,
        active: form.active,
        monthlyTarget: form.role === 'sales' ? form.monthlyTarget : 0
      })
      ElMessage.success('员工已创建')
    } else {
      const payload = userDialog.value.mode === 'dept'
        ? { deptId: form.deptId }
        : {
            name: form.name.trim(),
            phone: form.phone.trim(),
            role: form.role,
            password: form.password || undefined,
            deptId: form.deptId,
            active: form.active,
            monthlyTarget: form.role === 'sales' ? form.monthlyTarget : 0
          }
      await updateOrgUser(userDialog.value.userId, payload)
      ElMessage.success('员工信息已更新')
    }
    userDialog.value.visible = false
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '保存员工失败')
  }
}

const handleUserActiveChange = (row, active) => {
  updateOrgUser(row.id, { active }).catch(() => {
    row.active = !active
    ElMessage.error('更新账号状态失败')
  })
}

const handleDeleteUser = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除员工「${row.name}」吗？此操作不可撤销。`,
      '删除员工',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  try {
    await deleteOrgUser(row.id)
    ElMessage.success('员工已删除')
    await loadData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '删除员工失败')
  }
}

const handleDeptDrop = async () => {
  const nextOrder = flattenTreeForUpdate(deptData.value)
  if (hasCycleInTree(nextOrder)) {
    await loadData()
    ElMessage.error('检测到循环挂载风险，已自动回滚本次拖拽')
    return
  }

  const oldMap = new Map(flatDepartments.value.map((item) => [item.id, item]))
  const changed = nextOrder.filter((item) => {
    const oldItem = oldMap.get(item.id)
    if (!oldItem) {
      return false
    }
    return oldItem.parentId !== item.parentId || oldItem.sortOrder !== item.sortOrder
  })

  if (changed.length === 0) {
    return
  }

  try {
    await ElMessageBox.confirm(
      `检测到 ${changed.length} 处组织结构变更，确认保存吗？`,
      '保存组织变更',
      {
        type: 'warning',
        confirmButtonText: '确认保存',
        cancelButtonText: '撤销本次拖拽'
      }
    )
  } catch {
    await loadData()
    ElMessage.info('已撤销本次拖拽变更')
    return
  }

  try {
    await Promise.all(changed.map((item) => updateDepartment(item.id, {
      parentId: item.parentId,
      sortOrder: item.sortOrder
    })))
    await loadData()
    ElMessage.success('组织架构已更新')
  } catch (error) {
    await loadData()
    ElMessage.error(error?.response?.data?.message || '部门拖拽保存失败')
  }
}
</script>

<style scoped>
.custom-tree {
  --el-tree-node-hover-bg-color: #f1f5f9;
}
.custom-tree :deep(.el-tree-node__content) {
  height: 38px;
  border-radius: 6px;
  margin-bottom: 4px;
}
.custom-table {
  --el-table-header-bg-color: #f8fafc;
}
</style>
