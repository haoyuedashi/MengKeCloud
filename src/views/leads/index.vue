<template>
  <div class="h-full flex flex-col bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    
    <!-- 顶部操作与筛选区 (Professional 2-Tier Layout) -->
    <div class="p-4 border-b border-gray-100 shrink-0 bg-white">
      
      <!-- Tier 1: Header & Primary Actions -->
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
        <!-- 左侧大标题 -->
        <div class="flex items-center gap-3 shrink-0">
          <h2 class="text-xl font-bold text-gray-800 flex items-center whitespace-nowrap leading-none tracking-tight">
            <div class="w-1.5 h-5 bg-gradient-to-b from-blue-400 to-blue-600 rounded-full mr-2"></div>
            客户管理
          </h2>
          <el-tag type="info" round class="bg-slate-100 border-none text-slate-500 whitespace-nowrap font-medium px-3">共 {{ total }} 条</el-tag>
        </div>
        
        <!-- 右侧全局核心操作 -->
        <div class="flex flex-wrap items-center gap-2 shrink-0 w-full md:w-auto">
          <!-- 显隐列设置 -->
          <el-popover placement="bottom-end" trigger="click" width="340" :offset="12">
            <template #reference>
              <el-button class="text-gray-500 hover:text-blue-600 px-3 border-none bg-slate-50 hover:bg-slate-100 transition-colors">
                <el-icon size="18"><Setting /></el-icon>
              </el-button>
            </template>
            <div class="font-bold text-gray-700 mb-3 border-b border-gray-100 pb-2 flex items-center">
              自定义列表属性
            </div>
            <div class="text-xs text-gray-500 mb-2">
              自定义字段最多显示 {{ MAX_VISIBLE_CUSTOM_COLUMNS }} 列，关键列可钉在左右侧。
            </div>
            <div class="space-y-1">
              <div v-for="(key, index) in columnOrder" :key="key" class="flex items-center gap-1">
                <el-checkbox
                  :model-value="showCols[key]"
                  :label="getColumnLabel(key)"
                  class="flex-1 !ml-0"
                  @change="(checked) => toggleColumnVisibility(key, checked)"
                />
                <el-button
                  link
                  class="!px-1"
                  :type="pinState[key] === 'left' ? 'primary' : 'default'"
                  @click.stop="setColumnPin(key, pinState[key] === 'left' ? 'none' : 'left')"
                >左钉</el-button>
                <el-button
                  link
                  class="!px-1"
                  :type="pinState[key] === 'right' ? 'primary' : 'default'"
                  @click.stop="setColumnPin(key, pinState[key] === 'right' ? 'none' : 'right')"
                >右钉</el-button>
                <el-button
                  link
                  :disabled="index === 0"
                  class="!px-1"
                  @click.stop="moveColumn(key, 'left')"
                >
                  <el-icon><ArrowLeft /></el-icon>
                </el-button>
                <el-button
                  link
                  :disabled="index === columnOrder.length - 1"
                  class="!px-1"
                  @click.stop="moveColumn(key, 'right')"
                >
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
          </el-popover>

          <!-- 导入按钮 -->
          <el-button plain class="border-gray-200 text-gray-600 hover:text-orange-600 hover:border-orange-200 hover:bg-orange-50 transition-colors" @click="importVisible = true">
            <el-icon class="mr-1"><Upload /></el-icon> 导入数据
          </el-button>

          <!-- 导出按钮 -->
          <el-button v-if="currentRole === 'admin'" plain @click="handleExport" class="border-gray-200 text-gray-600 hover:text-green-600 hover:border-green-200 hover:bg-green-50 transition-colors">
          <el-icon class="mr-1"><Download /></el-icon> 导出客户
          </el-button>
          
          <!-- 新建线索主按钮 -->
          <el-button type="primary" class="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 border-none shadow-lg shadow-blue-500/30 font-medium px-5 transition-transform hover:-translate-y-0.5" @click="handleCreate">
          <el-icon class="mr-1"><Plus /></el-icon> 录入新客户
          </el-button>

          <el-button
            v-if="canAssign && selectedRows.length > 0"
            type="success"
            plain
            class="border-teal-200 bg-teal-50 text-teal-700"
            @click="openBatchAssign"
          >
            批量分配 ({{ selectedRows.length }})
          </el-button>

          <el-button
            v-if="selectedRows.length > 0"
            type="warning"
            plain
            class="border-amber-200 bg-amber-50 text-amber-700"
            @click="handleBatchTransferToPool"
          >
            转入公海 ({{ selectedRows.length }})
          </el-button>
        </div>
      </div>

      <!-- Tier 2: Search & Filter Query Console -->
      <div class="bg-slate-50/80 border border-slate-100 rounded-xl p-3 flex flex-col md:flex-row md:flex-wrap items-stretch md:items-center gap-3 shadow-inner">
        <el-input
          v-model="searchQuery"
          placeholder="检索姓名或电话..."
          class="w-full md:w-56 bg-white shrink-0"
          clearable
        >
          <template #prefix>
            <el-icon class="text-gray-400"><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select v-model="filterStatus" placeholder="筛选状态" class="w-full md:w-36 bg-white shrink-0" clearable effect="light">
          <el-option
            v-for="item in dictStatus"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>

        <!-- 排序组件 -->
        <el-dropdown trigger="click" @command="handleSortCommand" class="w-full md:w-auto">
          <el-button class="text-gray-600 hover:text-blue-600 bg-white border-gray-200 hover:bg-slate-50 w-full md:w-auto justify-start" plain>
            <el-icon class="mr-1"><Sort /></el-icon> 
            {{ sortConfig.label || '默认排序' }}
          </el-button>
          <template #dropdown>
            <el-dropdown-menu class="min-w-[180px]">
              <el-dropdown-item command="createTime_desc" :class="{'text-blue-600 bg-blue-50': sortConfig.value === 'createTime_desc'}">最新入库优先 (默认)</el-dropdown-item>
              <el-dropdown-item divided command="lastFollowUp_desc" :class="{'text-blue-600 bg-blue-50': sortConfig.value === 'lastFollowUp_desc'}">最近跟进优先</el-dropdown-item>
              <el-dropdown-item command="lastFollowUp_asc" :class="{'text-blue-600 bg-blue-50': sortConfig.value === 'lastFollowUp_asc'}">最久未联系优先</el-dropdown-item>
              <el-dropdown-item divided command="level_desc" :class="{'text-blue-600 bg-blue-50': sortConfig.value === 'level_desc'}">高意向优先 (A-D)</el-dropdown-item>
              <el-dropdown-item command="level_asc" :class="{'text-blue-600 bg-blue-50': sortConfig.value === 'level_asc'}">低意向优先 (D-A)</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <div class="h-6 w-px bg-gray-200 mx-1 hidden sm:block"></div>

        <el-button type="primary" plain class="border-blue-200 bg-blue-50/50 hover:bg-blue-100 border-dashed" @click="filterDrawerVisible = true">
          <el-icon class="mr-1"><Filter /></el-icon> 全能高级筛选
        </el-button>
      </div>
      
    </div>

    <!-- 表格区域 -->
    <div class="flex-1 overflow-hidden p-4">
      <el-table 
        :data="sortedTableData" 
        v-loading="loading"
        style="width: 100%" 
        height="100%"
        class="custom-table"
        :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '600' }"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column type="index" width="50" align="center" />
        
        <el-table-column
          v-for="column in visibleColumnDefs"
          :key="column.key"
          :prop="column.prop"
          :fixed="getColumnFixed(column.key)"
          :label="getColumnLabel(column.key)"
          :min-width="column.minWidth"
          :width="column.width"
          :align="column.align"
          :sortable="column.sortable"
        >
          <template v-if="column.key === 'name'" #default="scope">
            <div class="flex items-center cursor-pointer group" @click="openDrawer(scope.row)">
              <el-avatar :size="32" class="bg-blue-100 text-blue-600 font-bold mr-3">{{ scope.row.name.charAt(0) }}</el-avatar>
              <span class="font-medium text-gray-800 group-hover:text-blue-500 transition-colors">{{ scope.row.name }}</span>
            </div>
          </template>

          <template v-else-if="column.key === 'source'" #default="scope">
            <el-tag size="small" type="info" class="bg-gray-50 border-gray-200 text-gray-600">
              {{ getSourceText(scope.row.source) }}
            </el-tag>
          </template>

          <template v-else-if="column.key === 'city'" #default="scope">
            <span class="text-gray-700 text-sm">{{ scope.row.dynamicData?.city || '--' }}</span>
          </template>

          <template v-else-if="column.key === 'status'" #default="{ row }">
            <div class="flex items-center">
              <span class="w-2 h-2 rounded-full mr-2" :class="getStatusColor(row.status).dot"></span>
              <span class="text-sm font-medium" :class="getStatusColor(row.status).text">{{ getStatusText(row.status) }}</span>
            </div>
          </template>

          <template v-else-if="column.key === 'level'" #default="scope">
            <span class="inline-block w-6 h-6 leading-6 text-center rounded text-sm font-bold" :class="getLevelStyle(scope.row.level)">
              {{ scope.row.level || '-' }}
            </span>
          </template>

          <template v-else-if="column.key === 'tags'" #default="scope">
            <div class="flex flex-wrap gap-1">
              <el-tag
                v-for="tag in scope.row.tags"
                :key="tag"
                size="small"
                effect="plain"
                class="border-gray-200 text-gray-500 bg-white"
              >
                {{ getTagLabel(tag) }}
              </el-tag>
              <span v-if="!scope.row.tags?.length" class="text-gray-400 text-sm">--</span>
            </div>
          </template>

          <template v-else-if="column.key === 'lastFollowUp'" #default="scope">
            <span class="text-gray-500 text-sm">{{ formatTimestamp(scope.row.lastFollowUp) }}</span>
          </template>

          <template v-else-if="column.key === 'owner'" #default="scope">
            <span class="text-gray-700">{{ getOwnerDisplay(scope.row.owner) }}</span>
          </template>

          <template v-else-if="isDynamicColumnKey(column.key)" #default="scope">
            <span class="text-gray-700 text-sm">{{ getDynamicFieldDisplay(column.key, scope.row) }}</span>
          </template>
        </el-table-column>
        
        <!-- 操作列 -->
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <div class="flex space-x-2">
              <el-button link type="primary" size="small" @click="openDrawer(scope.row)">
                详情
              </el-button>
              <el-button link type="success" size="small" class="flex items-center" @click.stop="openAddFollowUp(scope.row)">
                <el-icon class="mr-1"><Phone /></el-icon>去跟进
              </el-button>
              <el-button v-if="canAssign" link type="warning" size="small" @click.stop="openSingleAssign(scope.row)">
                分配
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="p-4 border-t border-gray-100 flex justify-end bg-gray-50 shrink-0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        background
        @size-change="loadLeadsData"
        @current-change="loadLeadsData"
      />
    </div>

    <!-- 预留详情抽屉位 -->
    <LeadDetailDrawer v-model:visible="drawerVisible" :lead="selectedLead" @updated="loadLeadsData" />

    <!-- 新建线索弹窗 -->
    <CreateLeadDialog v-model:visible="createVisible" :assignee-options="assigneeOptions" :show-assignee="canAssign" @success="onCreateSuccess" />

    <!-- 高级筛选抽屉 -->
    <AdvancedFilterDrawer
      v-model:visible="filterDrawerVisible"
      :source-options="sourceOptions"
      :level-options="levelOptions"
      :tag-options="tagOptions"
      @filter="onAdvancedFilter"
    />
    
    <!-- 导入 Excel 弹窗 -->
    <el-dialog
      v-model="importVisible"
      title="批量导入线索"
      width="480px"
      class="rounded-xl"
      destroy-on-close
    >
      <div class="px-4 py-2 border border-blue-100 bg-blue-50/50 rounded-lg mb-6">
        <p class="text-sm text-blue-700 flex items-center mb-1">
          <el-icon class="mr-1"><InfoFilled /></el-icon> 导入说明
        </p>
        <p class="text-xs text-gray-500 mb-2">请按模板填写，必填字段：客户姓名、手机号码、来源渠道。其余字段均可选，支持跟进记录导入。</p>
        <el-button link type="primary" size="small" class="underline underline-offset-2" @click="downloadImportTemplate">下载 CSV 导入模板</el-button>
      </div>

      <el-upload
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".csv"
        class="w-full text-center"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽表格文件到此处，或 <em>点击上传</em>
        </div>
      </el-upload>
      
      <div v-if="importing" class="mt-4">
        <el-progress :percentage="importProgress" :format="(p) => p === 100 ? '导入完成' : '解析入库中 ' + p + '%'" status="success" />
      </div>

      <template #footer>
        <div class="dialog-footer flex justify-end gap-3 mt-4">
          <el-button @click="importVisible = false" size="large" :disabled="importing">取消</el-button>
          <el-button type="primary" size="large" class="shadow-md shadow-blue-500/30" :loading="importing" @click="startImport">
            <el-icon class="mr-1"><Check /></el-icon>确认导入
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 添加跟进弹窗 -->
    <AddFollowUpDialog v-model:visible="addFollowUpVisible" :lead="activeLeadForFollowUp" @success="onFollowUpSuccess" />

    <AssignLeadDialog
      v-model:visible="assignVisible"
      :leads="assigningLeads"
      :staff-options="assigneeOptions"
      @success="handleAssignConfirm"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Search, Plus, Phone, Filter, Download, Setting, Sort, Upload, InfoFilled, UploadFilled, Check, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import LeadDetailDrawer from '@/components/leads/LeadDetailDrawer.vue'
import CreateLeadDialog from '@/components/leads/CreateLeadDialog.vue'
import AdvancedFilterDrawer from '@/components/leads/AdvancedFilterDrawer.vue'
import AddFollowUpDialog from '@/components/leads/AddFollowUpDialog.vue'
import AssignLeadDialog from '@/components/leads/AssignLeadDialog.vue'
import { getLeads, assignLeads, getAssignableStaff, transferLeadsToPool, exportLeads, importLeads } from '@/api/leads'
import { useLeadMeta } from '@/composables/useLeadMeta'
import { getCurrentRole, getCurrentStaffId, getCurrentUser } from '@/utils/auth'

// 搜索与筛选状态
const searchQuery = ref('')
const filterStatus = ref('')
const COLUMN_CONFIG_STORAGE_KEY = 'leads_table_column_config_v1'
const BASE_STATIC_COLUMN_ORDER = ['name', 'phone', 'city', 'source', 'status', 'level', 'tags', 'lastFollowUp', 'owner']
const MAX_VISIBLE_CUSTOM_COLUMNS = 6
const DEFAULT_SHOW_COLS = {
  name: true,
  phone: true,
  city: true,
  source: true,
  status: true,
  level: true,
  tags: true,
  lastFollowUp: true,
  owner: true
}

// 显示列设置控制
const showCols = reactive({ ...DEFAULT_SHOW_COLS })
const columnOrder = ref([...BASE_STATIC_COLUMN_ORDER])
const pinState = reactive({})
const columnConfigReady = ref(false)

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(100)

// 弹窗与抽屉状态
const drawerVisible = ref(false)
const createVisible = ref(false)
const filterDrawerVisible = ref(false)
const addFollowUpVisible = ref(false)
const importVisible = ref(false)
const importing = ref(false)
const importProgress = ref(0)
const importFile = ref(null)
const selectedLead = ref(null)
const activeLeadForFollowUp = ref(null)
const selectedRows = ref([])
const assignVisible = ref(false)
const assigningLeads = ref([])
const assigneeOptions = ref([])
const ownerNameMap = ref({})
const canAssign = ref(false)

const tableData = ref([])
const loading = ref(false)
const route = useRoute()
const currentStaffId = getCurrentStaffId()
const currentRole = getCurrentRole()
const currentUser = getCurrentUser()
const staticColumnOrder = computed(() =>
  currentRole === 'sales'
    ? BASE_STATIC_COLUMN_ORDER.filter((key) => key !== 'owner')
    : BASE_STATIC_COLUMN_ORDER
)
const advancedFilters = ref({})
const { statusOptions, sourceOptions, levelOptions, tagOptions, getTagLabel, normalizeTagValues, getBaseFieldLabel, loadLeadMeta, businessCustomFields, getFieldOptions } = useLeadMeta()

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const loadAssignableStaff = async () => {
  if (currentRole === 'sales') {
    ownerNameMap.value = {
      [currentStaffId]: currentUser?.name || '我'
    }
    assigneeOptions.value = []
    canAssign.value = false
    return
  }

  try {
    const data = await getAssignableStaff()
    const users = data.list || []
    ownerNameMap.value = users.reduce((acc, user) => {
      acc[user.id] = user.name
      return acc
    }, {})
    assigneeOptions.value = users.map((user) => ({
      id: user.id,
      label: `${user.name}${user.deptName ? ` (${user.deptName})` : ''}`
    }))
    canAssign.value = assigneeOptions.value.length > 0
  } catch (error) {
    ownerNameMap.value = {}
    assigneeOptions.value = []
    canAssign.value = false
    if (error?.response?.status && error.response.status !== 403) {
      ElMessage.error('可分配员工加载失败')
    }
  }
}

const dynamicColumnKeys = computed(() => businessCustomFields.value.map((field) => `cf:${field.code}`))
const visibleCustomColumnCount = computed(() =>
  dynamicColumnKeys.value.filter((key) => !!showCols[key]).length
)

const allColumnKeys = computed(() => [...staticColumnOrder.value, ...dynamicColumnKeys.value])

const normalizeColumnOrder = (candidate) => {
  const allowed = allColumnKeys.value
  const list = Array.isArray(candidate) ? candidate.filter((item) => allowed.includes(item)) : []
  const deduped = []
  for (const key of list) {
    if (!deduped.includes(key)) {
      deduped.push(key)
    }
  }
  for (const key of allowed) {
    if (!deduped.includes(key)) {
      deduped.push(key)
    }
  }
  return deduped
}

const ensureDynamicColumnState = () => {
  const keys = allColumnKeys.value
  for (const key of keys) {
    if (typeof showCols[key] !== 'boolean') {
      showCols[key] = key.startsWith('cf:') ? false : true
    }
    if (!['left', 'right', 'none'].includes(pinState[key])) {
      pinState[key] = 'none'
    }
  }

  const nextOrder = normalizeColumnOrder(columnOrder.value)
  if (nextOrder.length !== columnOrder.value.length || nextOrder.some((key, index) => key !== columnOrder.value[index])) {
    columnOrder.value = nextOrder
  }

  const orderedDynamicKeys = columnOrder.value.filter((key) => key.startsWith('cf:'))
  let visibleCount = 0
  for (const key of orderedDynamicKeys) {
    if (!showCols[key]) {
      continue
    }
    visibleCount += 1
    if (visibleCount > MAX_VISIBLE_CUSTOM_COLUMNS) {
      showCols[key] = false
    }
  }
}

const loadColumnConfig = () => {
  try {
    const raw = localStorage.getItem(COLUMN_CONFIG_STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    columnOrder.value = normalizeColumnOrder(parsed?.order)

    const visible = parsed?.visible && typeof parsed.visible === 'object' ? parsed.visible : {}
    const pinned = parsed?.pinned && typeof parsed.pinned === 'object' ? parsed.pinned : {}
    for (const key of allColumnKeys.value) {
      if (typeof visible[key] === 'boolean') {
        showCols[key] = visible[key]
      } else {
        showCols[key] = key.startsWith('cf:') ? false : !!DEFAULT_SHOW_COLS[key]
      }
      pinState[key] = ['left', 'right', 'none'].includes(pinned[key]) ? pinned[key] : 'none'
    }
    ensureDynamicColumnState()
  } catch (_error) {
    columnOrder.value = [...staticColumnOrder.value]
    for (const key of allColumnKeys.value) {
      showCols[key] = key.startsWith('cf:') ? false : !!DEFAULT_SHOW_COLS[key]
      pinState[key] = 'none'
    }
  }
}

const saveColumnConfig = () => {
  if (!columnConfigReady.value) return
  const visible = {}
  const pinned = {}
  for (const key of columnOrder.value) {
    visible[key] = !!showCols[key]
    pinned[key] = pinState[key] || 'none'
  }
  localStorage.setItem(
    COLUMN_CONFIG_STORAGE_KEY,
    JSON.stringify({
      order: columnOrder.value,
      visible,
      pinned
    })
  )
}

const toggleColumnVisibility = (key, checked) => {
  const isChecked = !!checked
  const isCustom = key.startsWith('cf:')
  if (isCustom && isChecked && !showCols[key] && visibleCustomColumnCount.value >= MAX_VISIBLE_CUSTOM_COLUMNS) {
    ElMessage.warning(`最多同时显示 ${MAX_VISIBLE_CUSTOM_COLUMNS} 个自定义字段列`)
    return
  }
  showCols[key] = isChecked
}

const setColumnPin = (key, side) => {
  if (!['left', 'right', 'none'].includes(side)) {
    return
  }
  pinState[key] = side
}

const getColumnFixed = (key) => {
  const side = pinState[key]
  if (side === 'left' || side === 'right') {
    return side
  }
  return false
}

const applyRouteQuery = () => {
  const status = typeof route.query.status === 'string' ? route.query.status : ''
  const keyword = typeof route.query.keyword === 'string' ? route.query.keyword : ''
  const source = typeof route.query.source === 'string' ? route.query.source : ''

  filterStatus.value = status
  searchQuery.value = keyword

  const nextAdvancedFilters = { ...advancedFilters.value }
  if (source) {
    nextAdvancedFilters.source = [source]
  } else if ('source' in nextAdvancedFilters) {
    delete nextAdvancedFilters.source
  }
  advancedFilters.value = nextAdvancedFilters
}
const loadLeadsData = async () => {
  loading.value = true
  try {
    const res = await getLeads({
      page: currentPage.value,
      pageSize: pageSize.value,
      keyword: searchQuery.value || undefined, 
      status: filterStatus.value || undefined,
      source: Array.isArray(advancedFilters.value.source) && advancedFilters.value.source.length > 0
        ? advancedFilters.value.source[0]
        : undefined
      // backend partially handles keyword, status, source. For complex filters frontend will also filter locally.
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
    console.error('获取线索数据失败:', error)
  } finally {
    loading.value = false
  }
}

const nameLabel = computed(() => getBaseFieldLabel('name', '客户姓名'))
const phoneLabel = computed(() => getBaseFieldLabel('phone', '联系电话'))
const sourceLabel = computed(() => getBaseFieldLabel('source', '来源渠道'))
const statusLabel = computed(() => getBaseFieldLabel('status', '跟进状态'))
const levelLabel = computed(() => getBaseFieldLabel('level', '意向评级'))
const getColumnLabel = (key) => {
  if (key === 'name') return nameLabel.value
  if (key === 'phone') return phoneLabel.value
  if (key === 'city') return '城市'
  if (key === 'source') return sourceLabel.value
  if (key === 'status') return statusLabel.value
  if (key === 'level') return levelLabel.value
  if (key === 'tags') return '客户标签'
  if (key === 'lastFollowUp') return '最后跟进时间'
  if (key === 'owner') return '归属销售'
  if (key.startsWith('cf:')) {
    const code = key.slice(3)
    const field = businessCustomFields.value.find((item) => item.code === code)
    return field?.name || code
  }
  return key
}

const columnDefMap = {
  name: { key: 'name', prop: 'name', minWidth: 120 },
  phone: { key: 'phone', prop: 'phone', minWidth: 130 },
  city: { key: 'city', prop: 'city', minWidth: 120 },
  source: { key: 'source', prop: 'source', minWidth: 100 },
  status: { key: 'status', prop: 'status', minWidth: 120 },
  level: { key: 'level', prop: 'level', width: 90, align: 'center' },
  tags: { key: 'tags', prop: 'tags', minWidth: 180 },
  lastFollowUp: { key: 'lastFollowUp', prop: 'lastFollowUp', width: 160, sortable: true },
  owner: { key: 'owner', prop: 'owner', minWidth: 120 }
}

const dynamicColumnDefMap = computed(() => {
  const map = {}
  for (const field of businessCustomFields.value) {
    const key = `cf:${field.code}`
    map[key] = {
      key,
      prop: key,
      minWidth: field.type === 'textarea' ? 180 : 140
    }
  }
  return map
})

const isDynamicColumnKey = (key) => key.startsWith('cf:')

const getDynamicFieldDisplay = (columnKey, row) => {
  const code = columnKey.slice(3)
  const value = row?.dynamicData?.[code]
  if (value === null || value === undefined || value === '') {
    return '--'
  }
  const field = businessCustomFields.value.find((item) => item.code === code)
  if (field?.type === 'select') {
    const option = getFieldOptions(code).find((item) => item.value === value)
    return option?.label || String(value)
  }
  return String(value)
}

const visibleColumnDefs = computed(() =>
  columnOrder.value
    .filter((key) => showCols[key])
    .map((key) => columnDefMap[key] || dynamicColumnDefMap.value[key])
    .filter(Boolean)
)

const moveColumn = (key, direction) => {
  const currentIndex = columnOrder.value.indexOf(key)
  if (currentIndex === -1) return
  const targetIndex = direction === 'left' ? currentIndex - 1 : currentIndex + 1
  if (targetIndex < 0 || targetIndex >= columnOrder.value.length) return
  const nextOrder = [...columnOrder.value]
  ;[nextOrder[currentIndex], nextOrder[targetIndex]] = [nextOrder[targetIndex], nextOrder[currentIndex]]
  columnOrder.value = nextOrder
}

const getOwnerDisplay = (ownerId) => {
  if (!ownerId) return '--'
  const ownerName = ownerNameMap.value[ownerId]
  return ownerName || '未知员工'
}
const dictStatus = computed(() => statusOptions.value || [])
const sourceLabelMap = computed(() => {
  const map = {}
  for (const item of sourceOptions.value || []) {
    if (item?.value) {
      map[item.value] = item.label
    }
  }
  if (map.douyin && !map.douying) {
    map.douying = map.douyin
  }
  return map
})
const statusLabelMap = computed(() => {
  const map = {}
  for (const item of dictStatus.value) {
    if (item?.value) {
      map[item.value] = item.label
    }
  }
  return map
})

onMounted(async () => {
  await loadLeadMeta(true)
  ensureDynamicColumnState()
  loadColumnConfig()
  columnConfigReady.value = true
  loadAssignableStaff()
})

watch(
  () => businessCustomFields.value,
  () => {
    ensureDynamicColumnState()
  },
  { deep: true }
)

watch(
  () => columnOrder.value,
  () => {
    saveColumnConfig()
  },
  { deep: true }
)

watch(
  showCols,
  () => {
    saveColumnConfig()
  },
  { deep: true }
)

watch(
  pinState,
  () => {
    saveColumnConfig()
  },
  { deep: true }
)

watch(
  () => route.query,
  async () => {
    currentPage.value = 1
    applyRouteQuery()
    await loadLeadsData()
  },
  { immediate: true, deep: true }
)

// 状态标签颜色映射
const getStatusColor = (status) => {
  const map = {
    'pending': { dot: 'bg-gray-400', text: 'text-gray-500' },
    'communicating': { dot: 'bg-blue-400', text: 'text-blue-600' },
    'deep_following': { dot: 'bg-blue-600', text: 'text-blue-700' },
    'invited': { dot: 'bg-indigo-500', text: 'text-indigo-600' },
    'visited': { dot: 'bg-indigo-700', text: 'text-indigo-800' },
    'deposit_paid': { dot: 'bg-cyan-500', text: 'text-cyan-600' },
    'signed': { dot: 'bg-teal-500', text: 'text-teal-600' },
    'invalid': { dot: 'bg-slate-400', text: 'text-slate-500' },
    'lost': { dot: 'bg-red-500', text: 'text-red-600' }
  }
  return map[status] || { dot: 'bg-gray-400', text: 'text-gray-600' }
}

const getStatusText = (status) => {
  const fallbackMap = {
    pending: '待跟进',
    communicating: '初步沟通',
    deep_following: '深度跟进',
    invited: '已邀约',
    visited: '已到访',
    deposit_paid: '已交定金',
    signed: '已签约',
    invalid: '无效客户',
    lost: '战败流失'
  }
  return statusLabelMap.value[status] || fallbackMap[status] || status || '未知'
}

const normalizeSourceValue = (value) => {
  if (value === 'douying') {
    return 'douyin'
  }
  return value
}

const getSourceText = (source) => {
  const normalized = normalizeSourceValue(source)
  return sourceLabelMap.value[normalized] || sourceLabelMap.value[source] || source || '--'
}

const getLevelStyle = (level) => {
  const map = {
    'A': 'bg-red-100 text-red-600',
    'B': 'bg-orange-100 text-orange-600',
    'C': 'bg-blue-100 text-blue-600',
    'D': 'bg-gray-100 text-gray-500',
  }
  return map[level] || 'bg-gray-50 text-gray-400'
}

// 综合排序配置
const sortConfig = reactive({
  value: 'createTime_desc',
  label: '最新入库优先 (默认)'
})

const handleSortCommand = (command) => {
  sortConfig.value = command
  const map = {
    'createTime_desc': '最新入库优先 (默认)',
    'lastFollowUp_desc': '最近跟进优先',
    'lastFollowUp_asc': '最久未联系',
    'level_desc': '意向最高',
    'level_asc': '意向最低',
  }
  sortConfig.label = map[command] || '默认排序'
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

// 经过排序后的最终数据展现
const sortedTableData = computed(() => {
  let result = tableData.value.filter(item => {
    // 基础搜索与简单筛选
    const matchSearch = item.name.includes(searchQuery.value) || item.phone.includes(searchQuery.value)
    const matchStatus = filterStatus.value ? item.status === filterStatus.value : true
    if (!matchSearch || !matchStatus) return false
    
    // 高级筛选对接
    const ad = advancedFilters.value
    if (Object.keys(ad).length === 0) return true
    
    if (ad.owner === 'me' && item.owner !== currentStaffId) return false
    if (ad.level && item.level?.charAt(0) !== ad.level) return false
    if (ad.source && ad.source.length > 0) {
      const normalizedItemSource = normalizeSourceValue(item.source)
      const normalizedSelectedSources = ad.source.map(normalizeSourceValue)
      if (!normalizedSelectedSources.includes(normalizedItemSource)) return false
    }
    
    // 标签匹配
    if (ad.tags && ad.tags.length > 0) {
      const leadTags = normalizeTagValues(item.tags || [])
      const selectedTags = normalizeTagValues(ad.tags || [])
      const hasTag = selectedTags.some(t => leadTags.includes(t))
      if (!hasTag) return false
    }

    // 时间段过滤
    if (ad.dateRange && ad.dateRange.length === 2) {
      if (!item.lastFollowUp) return false
      const [start, end] = ad.dateRange
      const ts = new Date(item.lastFollowUp).getTime()
      if (ts < new Date(start).getTime() || ts > new Date(end + ' 23:59:59').getTime()) return false
    }
    
    if (ad.createDateRange && ad.createDateRange.length === 2) {
      if (!item.createdAt) return false
      const [start, end] = ad.createDateRange
      const ts = new Date(item.createdAt).getTime()
      if (ts < new Date(start).getTime() || ts > new Date(end + ' 23:59:59').getTime()) return false
    }
    
    return true
  })

  // Then sorting
  result.sort((a, b) => {
    switch (sortConfig.value) {
      case 'lastFollowUp_desc':
        return new Date(b.lastFollowUp).getTime() - new Date(a.lastFollowUp).getTime()
      case 'lastFollowUp_asc':
        return new Date(a.lastFollowUp).getTime() - new Date(b.lastFollowUp).getTime()
      case 'createTime_desc':
        return new Date(b.createdAt || b.createTime || 0).getTime() - new Date(a.createdAt || a.createTime || 0).getTime()
      case 'level_desc': // A -> D
        return (a.level || 'Z').localeCompare(b.level || 'Z')
      case 'level_asc': // D -> A
        return (b.level || 'Z').localeCompare(a.level || 'Z')
      default:
        return 0
    }
  })

  return result
})


const handleCreate = async () => {
  await loadAssignableStaff()
  createVisible.value = true
}

const onCreateSuccess = async () => {
  currentPage.value = 1
  await loadLeadsData()
}

const handleExport = () => {
  exportLeads({
    keyword: searchQuery.value || undefined,
    status: filterStatus.value || undefined,
    source: Array.isArray(advancedFilters.value.source) && advancedFilters.value.source.length > 0
      ? advancedFilters.value.source[0]
      : undefined
  }).then((blob) => {
    const fileBlob = blob instanceof Blob ? blob : new Blob([blob], { type: 'text/csv;charset=utf-8' })
    const url = window.URL.createObjectURL(fileBlob)
    const a = document.createElement('a')
    a.href = url
    a.download = `客户导出-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  }).catch((error) => {
    ElMessage.error(error?.response?.data?.message || '导出失败')
  })
}

const onAdvancedFilter = (filters) => {
  console.log('应用高级筛选:', filters)
  advancedFilters.value = filters
  ElMessage.success('已应用高级筛选条件: 当前列表页数据已本地过滤')
  // 如果需要后端全局过滤可以触发 loadLeadsData()，这里因为是单页演示暂用前端 computed 强过滤
}

const openDrawer = (row) => {
  selectedLead.value = row
  drawerVisible.value = true
}

const openAddFollowUp = (row) => {
  activeLeadForFollowUp.value = row
  addFollowUpVisible.value = true
}

const openSingleAssign = async (row) => {
  if (!canAssign.value) {
    ElMessage.warning('当前账号无改派权限')
    return
  }
  await loadAssignableStaff()
  assigningLeads.value = [row]
  assignVisible.value = true
}

const openBatchAssign = async () => {
  if (!canAssign.value) {
    ElMessage.warning('当前账号无改派权限')
    return
  }
  await loadAssignableStaff()
  assigningLeads.value = [...selectedRows.value]
  assignVisible.value = true
}

const handleAssignConfirm = async (staffId) => {
  const leadIds = assigningLeads.value.map((item) => item.id)
  if (leadIds.length === 0) {
    return
  }
  try {
    await assignLeads(leadIds, staffId)
    ElMessage.success(`已完成 ${leadIds.length} 条客户分配`)
    assignVisible.value = false
    assigningLeads.value = []
    selectedRows.value = []
    await loadLeadsData()
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '分配失败')
  }
}

const handleBatchTransferToPool = async () => {
  const leadIds = selectedRows.value.map((item) => item.id)
  if (leadIds.length === 0) {
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认将选中的 ${leadIds.length} 条客户转入公海？`,
      '转入公海确认',
      {
        confirmButtonText: '确认转入',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const data = await transferLeadsToPool(leadIds)
    ElMessage.success(`已转入公海 ${data.count} 条客户`)
    selectedRows.value = []
    await loadLeadsData()
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    ElMessage.error(error?.response?.data?.message || '转入公海失败')
  }
}

const onFollowUpSuccess = (data) => {
  console.log('添加跟进成功:', data)
  // Demo logic: update last follow up time on that object if found
  if (data.leadId) {
    const lead = tableData.value.find(l => l.id === data.leadId)
    if (lead) {
      lead.lastFollowUp = new Date().toLocaleString()
      if (data.status) {
        lead.status = data.status
        // also would map statusText appropriately here
      }
    }
  }
}

// 模拟 Excel 导入逻辑
const handleFileChange = (file) => {
  if (file.name.toLowerCase().endsWith('.csv')) {
    importFile.value = file.raw || null
    ElMessage.success(`已选择文件: ${file.name}`)
  } else {
    importFile.value = null
    ElMessage.error('仅支持 .csv 格式文件！')
  }
}

const downloadImportTemplate = () => {
  const content = '客户姓名,手机号码,来源渠道,跟进状态,意向评级,归属销售,客户标签,最后跟进时间,跟进记录,跟进方式,跟进人,跟进时间,扩展字段JSON\n'
  const blob = new Blob(['\uFEFF', content], { type: 'text/csv;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
    a.download = '客户导入模板.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

const startImport = () => {
  if (!importFile.value) {
    ElMessage.warning('请先选择 CSV 文件')
    return
  }
  importing.value = true
  importProgress.value = 20
  importLeads(importFile.value)
    .then(async (data) => {
      importProgress.value = 100
      importing.value = false
      importVisible.value = false
      importFile.value = null
      ElMessage.success(`导入完成：成功 ${data.success} 条，失败 ${data.failed} 条`)
      if (Array.isArray(data.errors) && data.errors.length > 0) {
        ElMessageBox.alert(data.errors.join('\n'), '部分导入失败', { type: 'warning' })
      }
      await loadLeadsData()
    })
    .catch((error) => {
      importing.value = false
      importProgress.value = 0
      ElMessage.error(error?.response?.data?.message || '导入失败')
    })
}
</script>

<style scoped>
/* 优雅地覆盖 Element Plus 表格某些边框，让 Tailwind 的卡片感更加突显 */
.custom-table {
  --el-table-border-color: #f1f5f9;
  --el-table-header-bg-color: #f8fafc;
}
.custom-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
</style>
