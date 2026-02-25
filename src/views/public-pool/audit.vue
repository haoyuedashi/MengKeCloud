<template>
  <div class="h-full flex flex-col bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <!-- 顶部标题与操作区 -->
    <div class="p-4 border-b border-gray-100 shrink-0 bg-white">
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <!-- 左侧大标题 -->
        <div class="flex items-center gap-3 shrink-0">
          <h2 class="text-xl font-bold text-gray-800 flex items-center whitespace-nowrap leading-none tracking-tight">
            <div class="w-1.5 h-5 bg-gradient-to-b from-teal-400 to-teal-600 rounded-full mr-2"></div>
            公海流转审计
          </h2>
          <el-tag type="info" round class="bg-slate-100 border-none text-slate-500 whitespace-nowrap font-medium px-3">
            共 {{ total }} 条记录
          </el-tag>
        </div>

        <div class="flex items-center gap-2 w-full md:w-auto">
          <!-- 这里做一个模拟权限切换按钮，演示前端控制分配权限以及发送对应的 Token -->
          <el-radio-group v-model="mockRole" size="large" @change="switchMockRole">
            <el-radio-button value="employee">普通员工 (ST001)</el-radio-button>
            <el-radio-button value="admin">系统主管 (admin)</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- 搜索与筛选 Console -->
      <div class="mt-4 bg-slate-50/80 border border-slate-100 rounded-xl p-3 flex flex-col md:flex-row md:flex-wrap items-stretch md:items-center gap-3 shadow-inner">
        <el-input
          v-model="searchLeadId"
          placeholder="检索线索 ID..."
          class="w-full md:w-56 bg-white shrink-0"
          clearable
          @keyup.enter="loadAuditData"
        >
          <template #prefix>
            <el-icon class="text-gray-400"><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select v-model="filterAction" placeholder="流转动作" class="w-full md:w-40 bg-white shrink-0" clearable @change="loadAuditData">
          <el-option label="捞取 (Claim)" value="claim" />
          <el-option label="分配 (Assign)" value="assign" />
          <el-option label="退回公海 (Drop)" value="drop" />
        </el-select>

        <el-button type="primary" plain class="border-teal-200 bg-teal-50/50 hover:bg-teal-100 text-teal-700 w-full md:w-auto" @click="loadAuditData">
          <el-icon class="mr-1"><Search /></el-icon> 查询记录
        </el-button>
      </div>
    </div>

    <!-- 表格区域 -->
    <div class="flex-1 overflow-hidden p-4">
      <el-table 
        v-loading="loading"
        :data="tableData" 
        style="width: 100%" 
        height="100%"
        class="custom-table"
        :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '600' }"
      >
        <el-table-column prop="id" label="审计流 ID" width="100" />
        <el-table-column prop="lead_id" label="线索 ID" min-width="100">
          <template #default="scope">
            <span class="font-mono text-gray-600">{{ scope.row.lead_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="流转动作" min-width="120">
          <template #default="scope">
            <el-tag :type="getActionTagType(scope.row.action)" class="font-bold border-none" effect="light">
              {{ scope.row.action.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="from_pool" label="原属公海" min-width="100">
          <template #default="scope">
            {{ scope.row.from_pool ? '是' : '否' }}
          </template>
        </el-table-column>
        <el-table-column prop="to_user" label="目标人员" min-width="120">
          <template #default="scope">
            <div class="flex items-center text-teal-700 font-medium">
               <el-icon class="mr-1"><User /></el-icon> {{ scope.row.to_user || '--' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" min-width="120">
          <template #default="scope">
            <span class="text-sm text-gray-500">{{ scope.row.operator || '系统' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发生时间" width="180">
          <template #default="scope">
            <span class="text-gray-500 text-sm">{{ formatTimestamp(scope.row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 底部 -->
    <div class="p-4 border-t border-gray-100 bg-gray-50 flex justify-end shrink-0">
       <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        layout="total, prev, pager, next"
        :total="total"
        background
        @size-change="loadAuditData"
        @current-change="loadAuditData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getPoolTransfers } from '@/api/pool'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

const currentPage = ref(1)
const pageSize = ref(20)
const searchLeadId = ref('')
const filterAction = ref('')

import { SignJWT } from 'jose'

// TODO: 使用 Pinia 下沉，此处仅为页面级演示
const mockRole = ref(localStorage.getItem('mengke_role') === 'admin' ? 'admin' : 'employee')

const generateMockJWT = async (role, staffId) => {
  const secret = new TextEncoder().encode('change-me-in-production-with-at-least-32-chars')
  const jwt = await new SignJWT({ staffId, role, tokenType: 'access' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('2h')
    .sign(secret)
  return jwt
}

const switchMockRole = async (role) => {
  if (role === 'admin') {
    const token = await generateMockJWT('admin', 'admin')
    localStorage.setItem('mengke_token', token)
    localStorage.setItem('mengke_role', 'admin')
    ElMessage.success('已切换至系统主管身份 (获得完全控制权与分配权限)')
  } else {
    const token = await generateMockJWT('employee', 'ST001')
    localStorage.setItem('mengke_token', token)
    localStorage.setItem('mengke_role', 'employee')
    ElMessage.success('已切换至普通员工身份 (分配线索将被拦截)')
  }
}

const getActionTagType = (action) => {
  if (action === 'claim') return 'primary'
  if (action === 'assign') return 'success'
  if (action === 'drop') return 'danger'
  return 'info'
}

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

const loadAuditData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value
    }
    if (searchLeadId.value) params.lead_id = searchLeadId.value
    if (filterAction.value) params.action = filterAction.value

    const res = await getPoolTransfers(params)
    
    // 兼容后端响应层级
    const records = res.list || res.data || res || []
    tableData.value = records
    total.value = res.total || records.length
  } catch (error) {
    console.error('获取公海审计记录失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // 预设一个普通员工 Token
  if (!localStorage.getItem('mengke_token')) {
    await switchMockRole('employee')
  }
  loadAuditData()
})
</script>

<style scoped>
.custom-table {
  --el-table-border-color: #f1f5f9;
  --el-table-header-bg-color: #f8fafc;
}
</style>
