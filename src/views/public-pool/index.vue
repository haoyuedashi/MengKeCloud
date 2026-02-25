<template>
  <div class="h-full flex flex-col bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden relative">
    
    <!-- 顶部操作与筛选区 -->
    <div class="p-4 border-b border-gray-100 shrink-0 bg-slate-50/50">
      <div class="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4">
        <div class="flex items-center gap-3 shrink-0">
          <h2 class="text-lg font-bold text-gray-800 flex items-center whitespace-nowrap">
            <div class="w-1 h-4 bg-teal-500 rounded-full mr-2"></div>
            公海池
          </h2>
          <el-tag type="warning" effect="light" round class="border-orange-200 text-orange-600 font-medium whitespace-nowrap">
            共有 {{ total }} 条待捞取线索
          </el-tag>
        </div>
        
        <div class="flex items-center gap-3 flex-wrap justify-start xl:justify-end w-full xl:w-auto">
          <el-input
            v-model="searchQuery"
            placeholder="搜索姓名或部分尾号"
            class="w-full sm:w-64"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select v-model="filterReason" placeholder="掉落原因" class="w-full sm:w-36" clearable>
            <el-option label="超时未跟进" value="timeout" />
            <el-option label="超时未成单" value="overdue" />
            <el-option label="手动退回" value="manual" />
            <el-option label="无效线索" value="invalid" />
          </el-select>

          <!-- 高级筛选 -->
          <el-button type="primary" plain class="border-blue-200 w-full sm:w-auto" @click="filterDrawerVisible = true">
            <el-icon class="mr-1"><Filter /></el-icon> 高级筛选
          </el-button>
        </div>
      </div>
    </div>

    <!-- 批量操作悬浮条 (当有选中项时出现) -->
    <transition name="el-zoom-in-top">
      <div v-if="selectedRows.length > 0" class="absolute top-16 left-1/2 -translate-x-1/2 z-10 bg-slate-800 text-white px-6 py-3 rounded-full shadow-xl flex items-center space-x-6">
        <span class="text-sm font-medium">已选择 <span class="text-blue-400 text-lg mx-1">{{ selectedRows.length }}</span> 条线索</span>
        <div class="flex space-x-2">
          <el-button type="primary" size="small" round @click="handleBatchClaim" class="border-none">
            <el-icon class="mr-1"><Pointer /></el-icon> 批量捞取
          </el-button>
          <el-button v-if="isAdmin" type="success" size="small" round @click="handleBatchAssign" class="bg-teal-500 hover:bg-teal-600 border-none">
            <el-icon class="mr-1"><Position /></el-icon> 批量分配
          </el-button>
          <el-button v-if="isAdmin" type="danger" size="small" round plain @click="handleBatchDelete">
            批量删除
          </el-button>
        </div>
        <el-icon class="cursor-pointer text-gray-400 hover:text-white transition-colors ml-4" @click="clearSelection"><Close /></el-icon>
      </div>
    </transition>

    <!-- 表格区域 -->
    <div class="flex-1 overflow-hidden p-4 pt-2">
      <el-table 
        ref="tableRef"
        v-loading="loading"
        :data="tableData" 
        style="width: 100%" 
        height="100%"
        class="custom-table"
        :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '600' }"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        
        <el-table-column prop="name" label="客户信息" min-width="150">
          <template #default="scope">
            <div class="flex items-center group">
              <el-avatar :size="32" class="bg-teal-100 text-teal-600 font-bold mr-3">{{ scope.row.name.charAt(0) }}</el-avatar>
              <div>
                <!-- 公海通常脱敏展示姓名和电话 -->
                <div class="font-medium text-gray-800">{{ scope.row.name }}</div>
                <div class="text-xs text-gray-500 font-mono mt-0.5">{{ scope.row.phone }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="source" label="来源渠道" min-width="120">
          <template #default="scope">
            <el-tag size="small" type="info" class="bg-gray-50 border-gray-200 text-gray-600">
              {{ getSourceLabel(scope.row.source) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="dropReason" label="掉落原因及说明" min-width="180">
          <template #default="scope">
             <div class="flex flex-col">
               <span class="text-sm text-red-500 flex items-center">
                 <el-icon class="mr-1"><WarningFilled /></el-icon> {{ scope.row.dropReasonType }}
               </span>
               <span class="text-xs text-gray-400 mt-1 line-clamp-1" :title="scope.row.dropReasonDetail">
                 {{ scope.row.dropReasonDetail }}
               </span>
             </div>
          </template>
        </el-table-column>

        <el-table-column prop="dropTime" label="掉入公海时间" width="160" sortable>
          <template #default="scope">
            <span class="text-gray-500 text-sm">{{ formatTimestamp(scope.row.dropTime) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="originalOwner" label="前归属人" min-width="100">
          <template #default="scope">
            <span class="text-sm text-gray-600">{{ scope.row.originalOwner || '--' }}</span>
          </template>
        </el-table-column>
        
        <!-- 操作列 -->
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="scope">
            <div class="flex space-x-2">
              <el-button type="primary" size="small" plain @click="handleClaim(scope.row)">
                <el-icon class="mr-1"><Pointer /></el-icon>捞取
              </el-button>
              <!-- 演示分配权限，一般只有老板/主管可见 -->
              <el-button v-if="isAdmin" type="success" size="small" class="bg-teal-50 text-teal-600 border-teal-200 hover:bg-teal-100 hover:text-teal-700" @click="handleAssign(scope.row)">
                分配
              </el-button>
              <el-button v-if="isAdmin" type="danger" size="small" plain @click="handleDelete(scope.row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页区域 -->
    <div class="p-4 border-t border-gray-100 flex flex-col xl:flex-row justify-between items-center gap-3 bg-gray-50 shrink-0 overflow-x-auto">
      <div class="text-sm text-gray-500 shrink-0">
        <!-- 捞取限制说明 -->
        今日您还可捞取 <span class="font-bold text-blue-600">8</span> / 10 条
      </div>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        background
        size="small"
        class="shrink-0"
        @size-change="loadPoolData"
        @current-change="loadPoolData"
      />
    </div>

    <!-- 分配线索弹窗 -->
    <AssignDialog v-model:visible="assignVisible" :leads="assignedLeads" @success="onAssignSuccess" />

    <!-- 高级筛选抽屉 -->
    <PublicPoolFilterDrawer v-model:visible="filterDrawerVisible" @filter="onAdvancedFilter" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Search, Filter, Pointer, Position, Close, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AssignDialog from '@/components/public-pool/AssignDialog.vue'
import PublicPoolFilterDrawer from '@/components/public-pool/PublicPoolFilterDrawer.vue'
import { getPoolLeads, claimLead, batchClaimLeads, assignLead, batchAssignLeads, deletePoolLead, deletePoolLeadsBatch } from '@/api/pool'
import { useLeadMeta } from '@/composables/useLeadMeta'
import { getCurrentRole } from '@/utils/auth'

// 权限判定
const currentRole = getCurrentRole()
const isAdmin = computed(() => {
  return currentRole === 'admin'
})

// 搜索与筛选状态
const searchQuery = ref('')
const filterReason = ref('')

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(45)

// 表格多选控制
const tableRef = ref(null)
const selectedRows = ref([])

const handleSelectionChange = (val) => {
  selectedRows.value = val
}

const clearSelection = () => {
  if (tableRef.value) {
    tableRef.value.clearSelection()
  }
}

// 弹窗状态
const assignVisible = ref(false)
const filterDrawerVisible = ref(false)
const assignedLeads = ref([]) // 要分配的线索列表（单个或批量）

// 数据状态
const tableData = ref([])
const loading = ref(false)
const route = useRoute()
const { getSourceLabel, loadLeadMeta } = useLeadMeta()

const applyRouteQuery = () => {
  const keyword = typeof route.query.keyword === 'string' ? route.query.keyword : ''
  const reason = typeof route.query.reason === 'string' ? route.query.reason : ''
  searchQuery.value = keyword
  filterReason.value = reason
}

// 格式化时间戳避免乱码
const formatTimestamp = (ts) => {
  if (!ts) return '--'
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ts
    return d.toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
  } catch (e) {
    return ts
  }
}

const loadPoolData = async () => {
  loading.value = true
  try {
    const res = await getPoolLeads({
      page: currentPage.value,
      pageSize: pageSize.value,
      keyword: searchQuery.value,
      reason: filterReason.value
    })
    
    // 兼容不同结构的返回 (按照后端最新结构 res.list)
    if (res && res.list) {
      tableData.value = res.list
      total.value = res.total || res.list.length
    } else if (res && res.items) {
      tableData.value = res.items
      total.value = res.total || res.items.length
    } else if (Array.isArray(res)) {
      tableData.value = res
      total.value = res.length
    } else if (res && res.data) {
      tableData.value = res.data
      total.value = res.total || res.data.length
    }
  } catch (error) {
    console.error('获取公海数据失败:', error)
  } finally {
    loading.value = false
  }
}

watch(
  () => route.query,
  async () => {
    currentPage.value = 1
    applyRouteQuery()
    await loadLeadMeta()
    await loadPoolData()
  },
  { immediate: true, deep: true }
)

// 捞取操作
const handleClaim = (row) => {
  ElMessageBox.confirm(`确认捞取客户 ${row.name} 到您的私海吗？`, '捞取确认', {
    confirmButtonText: '立即捞取',
    cancelButtonText: '取消',
    type: 'info'
  }).then(async () => {
    try {
      await claimLead(row.id)
      ElMessage.success(`捞取成功！客户 ${row.name} 已归入您的私海。`)
      loadPoolData()
    } catch (error) {
      console.error('捞取失败:', error)
    }
  }).catch(() => {})
}

const handleBatchClaim = () => {
    ElMessageBox.confirm(`确认批量捞取这 ${selectedRows.value.length} 条线索到您的私海吗？`, '批量捞取确认', {
    confirmButtonText: '立即捞取',
    cancelButtonText: '取消',
    type: 'info'
  }).then(async () => {
    try {
      const ids = selectedRows.value.map(s => s.id)
      await Promise.all(ids.map(id => claimLead(id)))
      ElMessage.success(`批量捞取成功 ${selectedRows.value.length} 条线索！`)
      clearSelection()
      loadPoolData()
    } catch (error) {
      console.error('批量捞取失败:', error)
    }
  }).catch(() => {})
}

// 分配操作
const handleAssign = (row) => {
  assignedLeads.value = [row]
  assignVisible.value = true
}

const handleBatchAssign = () => {
  assignedLeads.value = selectedRows.value
  assignVisible.value = true
}

const handleDelete = (row) => {
    ElMessageBox.confirm(`确认彻底删除公海客户 ${row.name} 吗？删除后不可恢复。`, '删除确认', {
    confirmButtonText: '确认删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deletePoolLead(row.id)
    ElMessage.success(`已删除客户 ${row.name}`)
      await loadPoolData()
    } catch (error) {
    console.error('删除公海客户失败:', error)
      ElMessage.error(error?.response?.data?.message || '删除失败')
    }
  }).catch(() => {})
}

const handleBatchDelete = () => {
  const ids = selectedRows.value.map((item) => item.id)
  if (ids.length === 0) return
    ElMessageBox.confirm(`确认彻底删除这 ${ids.length} 条公海客户吗？删除后不可恢复。`, '批量删除确认', {
    confirmButtonText: '确认删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const data = await deletePoolLeadsBatch(ids)
    ElMessage.success(`已删除 ${data.count} 条客户`)
      clearSelection()
      await loadPoolData()
    } catch (error) {
    console.error('批量删除公海客户失败:', error)
      ElMessage.error(error?.response?.data?.message || '批量删除失败')
    }
  }).catch(() => {})
}

const onAssignSuccess = async (targetUser) => {
  try {
    const ids = assignedLeads.value.map(s => s.id)
    await batchAssignLeads(ids, targetUser.id)
    ElMessage.success(`成功将 ${assignedLeads.value.length} 条线索分配给 ${targetUser.name}`)
    clearSelection()
    assignVisible.value = false
    loadPoolData()
  } catch (error) {
    console.error('分配线索失败:', error)
  }
}

const onAdvancedFilter = (filters) => {
  console.log('公海池应用高级筛选:', filters)
  ElMessage.success('已应用公海池筛选条件')
}
</script>

<style scoped>
.custom-table {
  --el-table-border-color: #f1f5f9;
  --el-table-header-bg-color: #f8fafc;
}
.custom-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
/* 优化勾选框在 Tailwind 下的样式对齐 */
:deep(.el-checkbox) {
  margin-right: 0;
}
</style>
