<template>
  <div class="space-y-6">
    <el-alert
      v-if="dashboardAnnouncement"
      :title="`系统公告：${dashboardAnnouncement}`"
      type="info"
      :closable="false"
      show-icon
      class="border border-blue-100"
    />
    <!-- 欢迎卡片 (展示 Tailwind 混合 Element Plus) -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 flex flex-col md:flex-row items-center justify-between overflow-hidden relative group">
      <!-- 装饰性背景球 -->
      <div class="absolute -right-16 -top-16 w-64 h-64 bg-blue-50 rounded-full blur-3xl opacity-50 group-hover:opacity-100 transition-opacity duration-700"></div>
      <div class="absolute -left-16 -bottom-16 w-48 h-48 bg-teal-50 rounded-full blur-2xl opacity-50 group-hover:opacity-100 transition-opacity duration-700"></div>

      <div class="relative z-10 flex-1 w-full md:w-auto text-center md:text-left">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-800 mb-3 tracking-tight">
          欢迎使用 <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-teal-500">加盟CRM系统</span>
        </h1>
        <p class="text-gray-500 text-sm md:text-base max-w-lg mx-auto md:mx-0 leading-relaxed">
          这里是 MengKeCloud 智能业务流转中心。您可以点击左侧菜单轻松管理您的线索、公海池和业务报表。让工作更高效，业务更精细。
        </p>
        <div class="mt-6 flex flex-wrap justify-center md:justify-start gap-4">
          <el-button type="primary" size="large" class="shadow-md shadow-blue-500/30" @click="() => $router.push('/leads')">
              <el-icon class="mr-1"><User /></el-icon> 录入新客户
          </el-button>
        </div>
      </div>
      
      <div class="relative z-10 hidden md:block mt-8 md:mt-0 md:ml-8">
        <!-- 插图占位 (可以使用任意业务插画) -->
        <div class="w-64 h-48 bg-blue-50 rounded-xl border border-blue-100 flex items-center justify-center p-4">
           <el-icon size="80" class="text-blue-300"><DataLine /></el-icon>
        </div>
      </div>
    </div>

    <!-- 营收与简报总览视图 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <el-card shadow="hover" class="border-none rounded-xl cursor-pointer hover:-translate-y-0.5 transition-transform" @click="goToTodayLeads">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500 mb-1">今日新增线索</p>
            <h3 class="text-2xl font-bold text-gray-800">{{ dashboardData.stats.todayNewLeads.value }}</h3>
          </div>
          <div class="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-500">
            <el-icon size="24"><User /></el-icon>
          </div>
        </div>
        <div class="mt-4 flex items-center text-sm">
          <span class="text-green-500 flex items-center">
            <el-icon><TopRight /></el-icon> {{ Math.abs(dashboardData.stats.todayNewLeads.trend) }}%
          </span>
          <span class="text-gray-400 ml-2">较昨日</span>
        </div>
      </el-card>

      <el-card shadow="hover" class="border-none rounded-xl cursor-pointer hover:-translate-y-0.5 transition-transform" @click="goToWeeklyFollowUps">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500 mb-1">本周跟进人次</p>
            <h3 class="text-2xl font-bold text-gray-800">{{ dashboardData.stats.weekFollowUps.value }}</h3>
          </div>
          <div class="w-12 h-12 rounded-full bg-teal-50 flex items-center justify-center text-teal-500">
            <el-icon size="24"><ChatDotRound /></el-icon>
          </div>
        </div>
        <div class="mt-4 flex items-center text-sm">
          <span class="text-green-500 flex items-center">
            <el-icon><TopRight /></el-icon> {{ Math.abs(dashboardData.stats.weekFollowUps.trend) }}%
          </span>
          <span class="text-gray-400 ml-2">较上周</span>
        </div>
      </el-card>

      <el-card shadow="hover" class="border-none rounded-xl cursor-pointer hover:-translate-y-0.5 transition-transform" @click="goToSignedLeads">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500 mb-1">本月新签客户</p>
            <h3 class="text-2xl font-bold text-gray-800">{{ dashboardData.stats.monthSigned.value }}</h3>
          </div>
          <div class="w-12 h-12 rounded-full bg-orange-50 flex items-center justify-center text-orange-500">
            <el-icon size="24"><Trophy /></el-icon>
          </div>
        </div>
        <div class="mt-4 flex items-center text-sm">
          <span class="text-red-500 flex items-center">
            <el-icon><BottomRight /></el-icon> {{ Math.abs(dashboardData.stats.monthSigned.trend) }}%
          </span>
          <span class="text-gray-400 ml-2">较上月</span>
        </div>
      </el-card>

      <!-- 修复HTML闭合导致的混乱，移除悬挂的闭合标签并调整网格 -->
    </div>

    <!-- 列表与简报区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- 今日待跟进客户 -->
      <el-card shadow="never" class="border-gray-100 rounded-xl">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-bold text-gray-800 flex items-center">
              <el-icon class="mr-2 text-blue-500"><BellFilled /></el-icon>
              今日待跟进 ({{ dashboardData.todoList.length }})
            </span>
            <el-button type="primary" link @click="goToLeadsList">查看全部</el-button>
          </div>
        </template>
          <div class="space-y-4">
          <div
            v-for="item in dashboardData.todoList"
            :key="item.leadId"
            class="flex items-start p-3 hover:bg-gray-50 rounded-lg transition-colors border border-transparent hover:border-gray-100 cursor-pointer"
            @click="goToLeadByKeyword(item)"
          >
            <el-avatar :size="40" class="bg-blue-100 text-blue-600 font-bold shrink-0">{{ item.name.charAt(0) }}</el-avatar>
            <div class="ml-4 flex-1">
              <div class="flex justify-between items-center mb-1">
                <span class="font-medium text-gray-800">{{ item.name }}</span>
                <span class="text-xs text-orange-500 bg-orange-50 px-2 py-1 rounded">{{ item.level }}</span>
              </div>
              <p class="text-sm text-gray-500 line-clamp-1">{{ item.summary }}</p>
            </div>
          </div>
          <el-empty v-if="dashboardData.todoList.length === 0" description="暂无待跟进客户" />
        </div>
      </el-card>

      <!-- 逾期未联系 / 个人业绩 -->
      <div class="space-y-6">
        <!-- 逾期提醒 -->
        <el-card shadow="never" class="border-red-100 bg-red-50/30 rounded-xl">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="font-bold text-red-600 flex items-center">
                <el-icon class="mr-2"><WarningFilled /></el-icon>
                即将掉落公海 ({{ dashboardData.poolWarnings.length }})
              </span>
            </div>
          </template>
          <div class="space-y-3">
            <div
              v-for="item in dashboardData.poolWarnings"
              :key="item.leadId"
              class="flex justify-between items-center bg-white p-3 rounded-lg border border-red-100 shadow-sm"
            >
              <div>
                <div class="font-medium text-gray-800">{{ item.name }}</div>
                <div class="text-xs text-gray-500 mt-1">已超过 {{ item.daysOverdue }} 天未联系</div>
              </div>
              <el-button type="danger" size="small" plain @click="goToPoolLead(item)">挽回跟进</el-button>
            </div>
            <el-empty v-if="dashboardData.poolWarnings.length === 0" description="暂无公海预警" />
          </div>
        </el-card>

        <!-- 个人业绩简报 -->
        <el-card shadow="never" class="border-gray-100 rounded-xl">
          <template #header>
            <div class="font-bold text-gray-800 flex items-center">
              <el-icon class="mr-2 text-teal-500"><DataLine /></el-icon>
              本月业绩达成率
            </div>
          </template>
          <div class="pt-2">
            <div class="flex justify-between mb-2">
              <span class="text-sm text-gray-500">新签成单数目标 ({{ dashboardData.performance.signed.current }}单 / 目标{{ dashboardData.performance.signed.target }}单)</span>
              <span class="text-sm font-bold text-teal-600">{{ dashboardData.performance.signed.percent }}%</span>
            </div>
            <el-progress :percentage="dashboardData.performance.signed.percent" :stroke-width="10" color="#14b8a6" />

          </div>
        </el-card>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User, TopRight, ChatDotRound, Trophy, BottomRight,
  BellFilled, WarningFilled, DataLine,
} from '@element-plus/icons-vue'
import { getDashboardOverview } from '@/api/dashboard'
import { getCurrentRole } from '@/utils/auth'

const dashboardData = ref({
  stats: {
    todayNewLeads: { value: 0, trend: 0 },
    weekFollowUps: { value: 0, trend: 0 },
    monthSigned: { value: 0, trend: 0 }
  },
  todoList: [],
  poolWarnings: [],
  performance: {
    followUp: { current: 0, target: 100, percent: 0 },
    signed: { current: 0, target: 10, percent: 0 },
    personalSigned: { current: 0, target: 0, percent: 0 },
    departmentSigned: { current: 0, target: 0, percent: 0 }
  },
  announcement: ''
})

const dashboardAnnouncement = computed(() => String(dashboardData.value?.announcement || '').trim())

const router = useRouter()
const currentRole = getCurrentRole()

const loadDashboardOverview = async () => {
  dashboardData.value = await getDashboardOverview()
}

const goToLeadsList = () => {
  router.push({ path: '/leads' })
}

const goToTodayLeads = () => {
  router.push({ path: '/reports', query: { trendWindow: '7days' } })
}

const goToWeeklyFollowUps = () => {
  router.push({ path: '/reports', query: { trendWindow: '7days' } })
}

const goToSignedLeads = () => {
  router.push({ path: '/leads', query: { status: 'signed' } })
}

const goToLeadByKeyword = (item) => {
  router.push({ path: '/leads', query: { keyword: item.name } })
}

const goToPoolLead = (item) => {
  router.push({ path: '/public-pool', query: { keyword: item.name } })
}

onMounted(async () => {
  try {
    await loadDashboardOverview()
  } catch (error) {
    ElMessage.error('工作台数据加载失败')
  }
})
</script>
