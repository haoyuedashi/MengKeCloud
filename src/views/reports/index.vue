<template>
  <div class="h-full overflow-y-auto space-y-6 pb-6 pr-2">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-12 gap-4 items-end">
        <div class="xl:col-span-5 min-w-0">
          <div class="text-xs text-gray-500 mb-1">统计区间</div>
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="w-full"
          />
        </div>
        <div v-if="isAdmin" class="xl:col-span-3 min-w-0">
          <div class="text-xs text-gray-500 mb-1">所属部门</div>
          <el-select v-model="filters.deptName" clearable placeholder="全部部门" class="w-full">
            <el-option
              v-for="item in departmentOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </div>
        <div v-if="!isSales" class="xl:col-span-2 min-w-0">
          <div class="text-xs text-gray-500 mb-1">销售人员</div>
          <el-select v-model="filters.ownerId" clearable placeholder="全部人员" class="w-full">
            <el-option
              v-for="item in staffOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </div>
        <div class="xl:col-span-2 flex gap-2 justify-end md:justify-start xl:justify-end">
          <el-button @click="handleResetFilters">重置</el-button>
          <el-button type="primary" @click="handleApplyFilters">应用筛选</el-button>
        </div>
      </div>
    </div>

    <!-- 顶部概览指标 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
      <!-- 汇总卡片组件化 (演示用手写即可) -->
      <div 
        v-for="(card, index) in summaryCards" 
        :key="index"
        class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center justify-between"
      >
        <div>
          <div class="text-sm font-medium text-gray-500 mb-1">{{ card.title }}</div>
          <div class="text-2xl font-bold text-gray-800">{{ card.value }}</div>
          <div class="mt-2 text-xs font-medium flex items-center" :class="card.trend > 0 ? 'text-green-500' : 'text-red-500'">
            <el-icon class="mr-1">
              <Top v-if="card.trend > 0" />
              <Bottom v-else />
            </el-icon>
            {{ Math.abs(card.trend) }}% <span class="text-gray-400 ml-1 font-normal">较上月</span>
          </div>
        </div>
        <div class="w-12 h-12 rounded-full flex items-center justify-center" :class="card.iconBg">
          <el-icon :class="card.iconColor" size="24">
            <component :is="card.icon" />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 图表区：线索新增趋势与漏斗图 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- 趋势折线图容器 (横跨2列) -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 lg:col-span-2 flex flex-col">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-base font-bold text-gray-800 flex items-center">
            <div class="w-1 h-4 bg-blue-500 rounded-full mr-2"></div>
            新增线索量趋势
          </h3>
          <el-radio-group v-model="trendTime" size="small">
            <el-radio-button :value="'7days'">近7天</el-radio-button>
            <el-radio-button :value="'30days'">近30天</el-radio-button>
          </el-radio-group>
        </div>
        <!-- ECharts 挂载点 -->
        <div ref="trendChartRef" class="w-full flex-1 min-h-[300px]"></div>
      </div>

      <!-- 销售漏斗图容器 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex flex-col">
        <div class="mb-4">
          <h3 class="text-base font-bold text-gray-800 flex items-center">
            <div class="w-1 h-4 bg-purple-500 rounded-full mr-2"></div>
            销售转化漏斗 (当月)
          </h3>
        </div>
        <!-- ECharts 挂载点 -->
        <div ref="funnelChartRef" class="w-full flex-1 min-h-[300px]"></div>
      </div>
    </div>

    <!-- 图表区2：战败原因与人员表现 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- 战败流失原因分布饼图 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex flex-col">
        <div class="mb-4">
          <h3 class="text-base font-bold text-gray-800 flex items-center">
            <div class="w-1 h-4 bg-red-500 rounded-full mr-2"></div>
            战败流失原因分布
          </h3>
        </div>
        <!-- ECharts 挂载点 -->
        <div ref="lossChartRef" class="w-full flex-1 min-h-[300px]"></div>
      </div>

      <!-- 底部人员表现 -->
      <div v-if="!isSales" class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 lg:col-span-2">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-base font-bold text-gray-800 flex items-center">
            <div class="w-1 h-4 bg-orange-500 rounded-full mr-2"></div>
            销售人员跟进排行榜 (当月)
          </h3>
          <el-button type="primary" plain size="small" class="border-blue-200">去打分 <el-icon class="ml-1"><ArrowRight /></el-icon></el-button>
        </div>

        <el-table :data="staffRanking" style="width: 100%" :header-cell-style="{ background: '#f8fafc' }" class="rank-table">
          <el-table-column type="index" label="排名" width="80" align="center">
            <template #default="scope">
              <span class="inline-block w-6 h-6 leading-6 text-center text-xs font-bold rounded-full"
                :class="{
                  'bg-yellow-100 text-yellow-600': scope.$index === 0,
                  'bg-gray-200 text-gray-600': scope.$index === 1,
                  'bg-orange-100 text-orange-600': scope.$index === 2,
                  'text-gray-400': scope.$index > 2
                }"
              >
                {{ scope.$index + 1 }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="销售人员">
             <template #default="scope">
               <div class="flex items-center">
                 <el-avatar :size="28" class="mr-2">{{ scope.row.name.charAt(0) }}</el-avatar>
                 <span class="font-medium text-gray-700">{{ scope.row.name }}</span>
               </div>
             </template>
          </el-table-column>
          <el-table-column prop="newLeads" label="分配数" align="center" sortable />
          <el-table-column prop="followUps" label="跟进次数" align="center" sortable />
          <el-table-column prop="signed" label="成交" align="center" sortable>
            <template #default="scope">
              <span class="text-green-600 font-bold">{{ scope.row.signed }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="conversion" label="转化率" align="center" width="120" sortable>
             <template #default="scope">
               <el-progress :percentage="scope.row.conversion" :color="getProgressColor" :width="50" />
             </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 lg:col-span-2">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-gray-800 flex items-center">
            <div class="w-1 h-4 bg-emerald-500 rounded-full mr-2"></div>
            我的本月目标进度
          </h3>
          <span class="text-xs text-gray-400">仅个人数据</span>
        </div>

        <div class="space-y-5">
          <div>
            <div class="flex justify-between text-sm mb-2">
              <span class="text-gray-500">签约目标</span>
              <span class="font-medium text-gray-700">
                {{ personalGoal.signedCurrent }} / {{ personalGoal.signedTarget }}
              </span>
            </div>
            <el-progress :percentage="personalGoal.signedPercent" :stroke-width="10" color="#10b981" />
          </div>

          <div class="grid grid-cols-2 gap-3 pt-2">
            <div class="rounded-lg bg-gray-50 border border-gray-100 p-3">
              <div class="text-xs text-gray-500">已签约</div>
              <div class="text-lg font-bold text-emerald-600 mt-1">{{ personalGoal.signedCurrent }}</div>
            </div>
            <div class="rounded-lg bg-gray-50 border border-gray-100 p-3">
              <div class="text-xs text-gray-500">剩余签约</div>
              <div class="text-lg font-bold text-orange-500 mt-1">{{ Math.max(0, personalGoal.signedTarget - personalGoal.signedCurrent) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, markRaw, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { User, Position, Phone, Trophy, Top, Bottom, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
// ECharts import
import * as echarts from 'echarts'
import { getReportsOverview } from '@/api/reports'
import { getCurrentRole } from '@/utils/auth'

const overviewData = ref({
  summary: {
    newLeads: { value: 0, trend: 0 },
    assignedLeads: { value: 0, trend: 0 },
    followUps: { value: 0, trend: 0 },
    signedLeads: { value: 0, trend: 0 },
    invitationRate: { value: 0, trend: 0 },
    visitRate: { value: 0, trend: 0 }
  },
  trend: {
    window: '7days',
    xAxis: [],
    series: []
  },
  funnel: [],
  loss: [],
  staffRanking: [],
  filtersMeta: {
    departments: [],
    staffs: []
  },
  personalGoal: null
})

const filters = ref({
  dateRange: [],
  deptName: '',
  ownerId: ''
})

const departmentOptions = computed(() => {
  const options = overviewData.value.filtersMeta?.departments || []
  const seen = new Set()
  return options.filter((item) => {
    const value = (item?.value || '').trim()
    if (!value || seen.has(value)) {
      return false
    }
    seen.add(value)
    return true
  })
})
const staffOptions = computed(() => overviewData.value.filtersMeta?.staffs || [])

const summaryCards = computed(() => ([
  {
      title: '本月新增客户',
    value: overviewData.value.summary.newLeads.value.toLocaleString(),
    trend: overviewData.value.summary.newLeads.trend,
    icon: markRaw(Position),
    iconBg: 'bg-blue-50',
    iconColor: 'text-blue-500'
  },
  {
    title: '本月分配总数',
    value: overviewData.value.summary.assignedLeads.value.toLocaleString(),
    trend: overviewData.value.summary.assignedLeads.trend,
    icon: markRaw(User),
    iconBg: 'bg-indigo-50',
    iconColor: 'text-indigo-500'
  },
  {
    title: '本月跟进次数',
    value: overviewData.value.summary.followUps.value.toLocaleString(),
    trend: overviewData.value.summary.followUps.trend,
    icon: markRaw(Phone),
    iconBg: 'bg-green-50',
    iconColor: 'text-green-500'
  },
  {
    title: '成功转化签约',
    value: overviewData.value.summary.signedLeads.value.toLocaleString(),
    trend: overviewData.value.summary.signedLeads.trend,
    icon: markRaw(Trophy),
    iconBg: 'bg-orange-50',
    iconColor: 'text-orange-500'
  },
  {
    title: '本月销售邀约率',
    value: `${overviewData.value.summary.invitationRate.value}%`,
    trend: overviewData.value.summary.invitationRate.trend,
    icon: markRaw(Phone),
    iconBg: 'bg-violet-50',
    iconColor: 'text-violet-500'
  },
  {
    title: '本月销售到访率',
    value: `${overviewData.value.summary.visitRate.value}%`,
    trend: overviewData.value.summary.visitRate.trend,
    icon: markRaw(User),
    iconBg: 'bg-cyan-50',
    iconColor: 'text-cyan-500'
  }
]))

const staffRanking = computed(() => overviewData.value.staffRanking || [])
const personalGoal = computed(() => overviewData.value.personalGoal || {
  signedCurrent: 0,
  signedTarget: 0,
  signedPercent: 0
})

const getProgressColor = (percentage) => {
  if (percentage < 3) return '#f56c6c'
  if (percentage < 6) return '#e6a23c'
  return '#5cb87a'
}

// 图表配置
const trendTime = ref('7days')
const trendChartRef = ref(null)
const funnelChartRef = ref(null)
const lossChartRef = ref(null)

let trendChart = null
let funnelChart = null
let lossChart = null
const route = useRoute()
const router = useRouter()
const currentRole = getCurrentRole()
const isAdmin = computed(() => currentRole === 'admin')
const isSales = computed(() => currentRole === 'sales')

const applyRouteQuery = () => {
  const trendWindow = typeof route.query.trendWindow === 'string' ? route.query.trendWindow : ''
  const startDate = typeof route.query.startDate === 'string' ? route.query.startDate : ''
  const endDate = typeof route.query.endDate === 'string' ? route.query.endDate : ''
  const deptName = typeof route.query.deptName === 'string' ? route.query.deptName : ''
  const ownerId = typeof route.query.ownerId === 'string' ? route.query.ownerId : ''

  trendTime.value = trendWindow === '30days' ? '30days' : '7days'
  if (startDate && endDate) {
    filters.value.dateRange = [startDate, endDate]
  } else {
    filters.value.dateRange = []
  }
  filters.value.deptName = deptName
  filters.value.ownerId = ownerId
}

let syncingRoute = false

const syncRouteQuery = async () => {
  const [startDate, endDate] = filters.value.dateRange || []
  const query = {
    trendWindow: trendTime.value,
    startDate: startDate || undefined,
    endDate: endDate || undefined,
    deptName: filters.value.deptName || undefined,
    ownerId: filters.value.ownerId || undefined
  }
  syncingRoute = true
  try {
    await router.replace({ query })
  } finally {
    syncingRoute = false
  }
}

const updateTrendChart = () => {
  if (!trendChart) return
  const trend = overviewData.value.trend
  trendChart.setOption({
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trend.xAxis,
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { color: '#64748b' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
      axisLabel: { color: '#64748b' }
    },
    color: ['#3b82f6'],
    series: [
      {
      name: '新增客户',
        type: 'line',
        smooth: true,
        data: trend.series,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.4)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
          ])
        },
        itemStyle: { borderWidth: 2 }
      }
    ]
  }, true)
}

const updateFunnelChart = () => {
  if (!funnelChart) return
  funnelChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b} : {c}' },
    color: ['#818cf8', '#60a5fa', '#34d399', '#fce7f3', '#fcd34d'],
    series: [
      {
        name: '转化漏斗',
        type: 'funnel',
        left: '10%',
        right: '10%',
        top: '5%',
        bottom: '5%',
        minSize: '0%',
        maxSize: '100%',
        sort: 'descending',
        gap: 2,
        label: { show: true, position: 'inside', formatter: '{b}' },
        labelLine: { show: false },
        itemStyle: { borderColor: '#fff', borderWidth: 1 },
        data: overviewData.value.funnel
      }
    ]
  }, true)
}

const updateLossChart = () => {
  if (!lossChart) return
  lossChart.setOption({
    tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
    legend: {
      bottom: '5%',
      left: 'center',
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#64748b', fontSize: 12 }
    },
    color: ['#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#94a3b8'],
    series: [
      {
        name: '战败原因',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: {
            show: true,
            fontSize: '16',
            fontWeight: 'bold',
            formatter: '{b}\n{c} ({d}%)'
          }
        },
        labelLine: { show: false },
        data: overviewData.value.loss
      }
    ]
  }, true)
}

const initCharts = () => {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }

  if (funnelChartRef.value) {
    funnelChart = echarts.init(funnelChartRef.value)
  }

  if (lossChartRef.value) {
    lossChart = echarts.init(lossChartRef.value)
  }
  updateTrendChart()
  updateFunnelChart()
  updateLossChart()
  
  // 增加下钻点击交互演示
  if (lossChart) {
    lossChart.on('click', (params) => {
      ElMessage.success(`数据下钻：正在展示「${params.name}」的 ${params.value} 条详细战败记录...`)
    })
  }

  // 处理响应式调整
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  trendChart?.resize()
  funnelChart?.resize()
  lossChart?.resize()
}

const loadOverview = async () => {
  const [startDate, endDate] = filters.value.dateRange || []
  const data = await getReportsOverview({
    trendWindow: trendTime.value,
    startDate,
    endDate,
    deptName: isAdmin.value ? (filters.value.deptName || undefined) : undefined,
    ownerId: isSales.value ? undefined : (filters.value.ownerId || undefined)
  })
  overviewData.value = data
}

const handleApplyFilters = async () => {
  try {
    await syncRouteQuery()
    await loadOverview()
    await nextTick()
    updateTrendChart()
    updateFunnelChart()
    updateLossChart()
  } catch (error) {
    ElMessage.error('应用筛选失败')
  }
}

const handleResetFilters = async () => {
  filters.value = {
    dateRange: [],
    deptName: '',
    ownerId: ''
  }
  await handleApplyFilters()
}

watch(trendTime, async () => {
  try {
    await syncRouteQuery()
    await loadOverview()
    await nextTick()
    updateTrendChart()
    updateFunnelChart()
    updateLossChart()
  } catch (error) {
    ElMessage.error('趋势数据刷新失败')
  }
})

watch(
  () => route.query,
  async () => {
    if (syncingRoute) return
    try {
      applyRouteQuery()
      await loadOverview()
      await nextTick()
      updateTrendChart()
      updateFunnelChart()
      updateLossChart()
    } catch (error) {
      ElMessage.error('路由筛选同步失败')
    }
  },
  { deep: true }
)

onMounted(async () => {
  try {
    applyRouteQuery()
    await loadOverview()
    await nextTick()
    setTimeout(() => {
      initCharts()
    }, 100)
  } catch (error) {
    ElMessage.error('报表数据加载失败')
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  funnelChart?.dispose()
  lossChart?.dispose()
})
</script>

<style scoped>
.rank-table {
  --el-table-border-color: #f1f5f9;
}
.rank-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
</style>
