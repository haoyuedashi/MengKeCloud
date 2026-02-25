<template>
  <el-container v-if="!isAuthPage" class="h-screen w-full bg-gray-50 flex overflow-hidden">
    <!-- 左侧固定的深色侧边栏 (PC端专用) -->
    <el-aside
      :width="isCollapse ? '64px' : '240px'"
      class="bg-slate-900 text-white transition-all duration-300 ease-in-out hidden md:flex flex-col shadow-xl z-20 shrink-0"
    >
      <!-- Logo 区域 -->
      <div class="h-16 flex items-center justify-center border-b border-slate-800 bg-slate-900 shrink-0">
        <svg v-if="isCollapse" class="w-8 h-8 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2L2 7l10 5 10-5-10-5zm0 22l-10-5v-6l10 5 10-5v6l-10 5z"/>
        </svg>
        <span v-else class="text-xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-400 truncate px-2">
          MengKeCloud
        </span>
      </div>

      <!-- 菜单区域 -->
      <el-menu
        :default-active="route.path"
        class="flex-1 border-none bg-transparent"
        :collapse="isCollapse"
        :collapse-transition="false"
        background-color="transparent"
        text-color="#94a3b8"
        active-text-color="#3b82f6"
        router
      >
        <el-menu-item index="/" class="hover:bg-slate-800 rounded-lg mx-2 mt-2">
          <el-icon><Odometer /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>
        
        <el-menu-item index="/leads" class="hover:bg-slate-800 rounded-lg mx-2 mt-1">
          <el-icon><User /></el-icon>
          <template #title>客户管理</template>
        </el-menu-item>
        
        <el-menu-item index="/public-pool" class="hover:bg-slate-800 rounded-lg mx-2 mt-1">
          <el-icon><Box /></el-icon>
          <template #title>公海池</template>
        </el-menu-item>
        
        <el-menu-item index="/reports" class="hover:bg-slate-800 rounded-lg mx-2 mt-1">
          <el-icon><DataLine /></el-icon>
          <template #title>数据报表</template>
        </el-menu-item>

        <el-sub-menu v-if="isAdmin || isManager" index="5" class="mx-2 mt-1 rounded-lg">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统配置</span>
          </template>
          <!-- 子菜单使用了默认背景，因此需要覆盖 element 样式或保持简洁 -->
          <el-menu-item v-if="isAdmin" index="/settings/platform" class="hover:bg-slate-800 bg-slate-900">平台设置</el-menu-item>
          <el-menu-item v-if="isAdmin" index="/settings/org" class="hover:bg-slate-800 bg-slate-900">组织架构管理</el-menu-item>
          <el-menu-item v-if="isAdmin" index="/settings/roles" class="hover:bg-slate-800 bg-slate-900">账号与权限</el-menu-item>
          <el-menu-item v-if="isAdmin" index="/settings/fields" class="hover:bg-slate-800 bg-slate-900">字段自定义</el-menu-item>
          <el-menu-item v-if="isAdmin" index="/settings/dict" class="hover:bg-slate-800 bg-slate-900">字典管理</el-menu-item>
          <el-menu-item v-if="isAdmin" index="/settings/rules" class="hover:bg-slate-800 bg-slate-900">自动回收规则</el-menu-item>
          <el-menu-item index="/settings/recycle-notifications" class="hover:bg-slate-800 bg-slate-900">回收预警通知</el-menu-item>
        </el-sub-menu>
      </el-menu>
      
      <!-- 底部版权或版本信息 -->
      <div v-show="!isCollapse" class="p-4 text-xs text-slate-500 text-center border-t border-slate-800">
        v1.0.0
      </div>
    </el-aside>
    
    <!-- 移动端专属悬浮导航抽屉 -->
    <el-drawer
      v-model="mobileMenuVisible"
      direction="ltr"
      size="240px"
      :with-header="false"
      class="bg-slate-900 text-white !p-0"
    >
      <div class="h-full flex flex-col bg-slate-900">
        <div class="h-16 flex items-center justify-center border-b border-slate-800 bg-slate-900 shrink-0">
          <span class="text-xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-400">
            MengKeCloud
          </span>
        </div>
        <el-menu
          :default-active="route.path"
          class="flex-1 border-none bg-transparent overflow-y-auto"
          background-color="transparent"
          text-color="#94a3b8"
          active-text-color="#3b82f6"
          router
          @select="mobileMenuVisible = false"
        >
          <el-menu-item index="/" class="hover:bg-slate-800 rounded-lg mx-2 mt-2">
            <el-icon><Odometer /></el-icon>
            <template #title>工作台</template>
          </el-menu-item>
          <el-menu-item index="/leads" class="hover:bg-slate-800 rounded-lg mx-2 mt-1">
            <el-icon><User /></el-icon>
            <template #title>客户管理</template>
          </el-menu-item>
          <el-menu-item index="/public-pool" class="hover:bg-slate-800 rounded-lg mx-2 mt-1">
            <el-icon><Box /></el-icon>
            <template #title>公海池</template>
          </el-menu-item>
          <el-menu-item index="/reports" class="hover:bg-slate-800 rounded-lg mx-2 mt-1">
            <el-icon><DataLine /></el-icon>
            <template #title>数据报表</template>
          </el-menu-item>
          <el-sub-menu v-if="isAdmin || isManager" index="5" class="mx-2 mt-1 rounded-lg">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统配置</span>
            </template>
            <el-menu-item v-if="isAdmin" index="/settings/platform" class="hover:bg-slate-800 bg-slate-900">平台设置</el-menu-item>
            <el-menu-item v-if="isAdmin" index="/settings/org" class="hover:bg-slate-800 bg-slate-900">组织架构管理</el-menu-item>
            <el-menu-item v-if="isAdmin" index="/settings/roles" class="hover:bg-slate-800 bg-slate-900">账号与权限</el-menu-item>
            <el-menu-item v-if="isAdmin" index="/settings/fields" class="hover:bg-slate-800 bg-slate-900">字段自定义</el-menu-item>
            <el-menu-item v-if="isAdmin" index="/settings/dict" class="hover:bg-slate-800 bg-slate-900">字典管理</el-menu-item>
            <el-menu-item v-if="isAdmin" index="/settings/rules" class="hover:bg-slate-800 bg-slate-900">自动回收规则</el-menu-item>
            <el-menu-item index="/settings/recycle-notifications" class="hover:bg-slate-800 bg-slate-900">回收预警通知</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </div>
    </el-drawer>

    <el-container class="flex flex-col relative w-full h-full">
      <!-- 顶部状态栏 -->
      <el-header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm z-10 shrink-0">
        <div class="flex items-center">
          <!-- PC侧边栏切换按钮 -->
          <div 
            class="hidden md:flex cursor-pointer text-gray-500 hover:text-blue-500 hover:bg-blue-50 p-2 rounded-lg transition-colors items-center justify-center mr-2"
            @click="toggleCollapse"
          >
            <el-icon size="20">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
          </div>
          
          <!-- 移动端汉堡菜单 -->
          <div 
            class="md:hidden cursor-pointer text-gray-700 hover:text-blue-500 p-2 rounded-lg flex items-center justify-center mr-2"
            @click="mobileMenuVisible = true"
          >
            <el-icon size="24"><Menu /></el-icon>
          </div>
          
          <!-- 移动端顶部Title -->
          <span class="md:hidden font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-400">
            MengKeCloud
          </span>
        </div>

        <!-- 右侧用户信息 -->
        <div class="flex items-center space-x-4">
          <el-badge v-if="isAdmin || isManager" :value="unreadRecycleCount" :hidden="unreadRecycleCount <= 0" :max="99">
            <el-button circle text @click="goRecycleNotifications">
              <el-icon size="18"><Bell /></el-icon>
            </el-button>
          </el-badge>
          <el-dropdown trigger="click">
            <div class="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded-lg transition-colors">
              <el-avatar 
                :size="32" 
                src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" 
                class="mr-3"
              />
              <span class="text-sm font-medium text-gray-700 select-none">你好，{{ displayName }}</span>
              <el-icon class="ml-1 text-gray-400"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goChangePassword">修改密码</el-dropdown-item>
                <el-dropdown-item divided class="text-red-500" @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="bg-gray-50 p-6 overflow-y-auto">
        <router-view v-slot="{ Component }">
          <transition name="el-fade-in" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
    
    <!-- 全局悬浮 AI 语音助手插件 -->
    <AIAssistWidget />
  </el-container>
  <router-view v-else />
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import AIAssistWidget from '@/components/AIAssistWidget.vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  Odometer, User, Box, DataLine, Setting, Bell,
  Fold, Expand, ArrowDown, SwitchButton, Menu
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { logout } from '@/api/auth'
import { getNotifications } from '@/api/notifications'
import { clearSession, getCurrentUser, getRefreshToken } from '@/utils/auth'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)
const mobileMenuVisible = ref(false)
const isAuthPage = computed(() => route.path === '/login')
const currentUser = ref(getCurrentUser())
const currentRole = computed(() => currentUser.value?.role || '')
const isAdmin = computed(() => currentRole.value === 'admin')
const isManager = computed(() => currentRole.value === 'manager')
const displayName = computed(() => currentUser.value?.name || '用户')
const unreadRecycleCount = ref(0)

const loadUnreadRecycleCount = async () => {
  if (!isAdmin.value && !isManager.value) {
    unreadRecycleCount.value = 0
    return
  }
  try {
    const data = await getNotifications({
      unreadOnly: true,
      categoryPrefix: 'recycle_',
      page: 1,
      pageSize: 1
    })
    unreadRecycleCount.value = data.total || 0
  } catch (_error) {
    unreadRecycleCount.value = 0
  }
}

watch(
  () => route.fullPath,
  () => {
    currentUser.value = getCurrentUser()
    loadUnreadRecycleCount()
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('recycle-notification-updated', loadUnreadRecycleCount)
  loadUnreadRecycleCount()
})

onUnmounted(() => {
  window.removeEventListener('recycle-notification-updated', loadUnreadRecycleCount)
})

// 切换折叠
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const goRecycleNotifications = () => {
  router.push('/settings/recycle-notifications')
}

const goChangePassword = () => {
  router.push('/account/change-password')
}

// 退出登录占位方法
const handleLogout = async () => {
  try {
    const refreshToken = getRefreshToken()
    if (refreshToken) {
      await logout(refreshToken)
    }
  } catch (_error) {
  } finally {
    clearSession()
    ElMessage.success('已安全退出登录')
    router.replace('/login')
  }
}
</script>

<style>
/* 可以在此处增加局部样式，或任由 Tailwind CSS 处理 */
/* Element Plus 的暗色侧边栏修复 */
.el-menu-item:hover, .el-sub-menu__title:hover {
  background-color: transparent !important;
}
.el-menu-item.is-active {
  background-color: #1e293b !important;
  color: #3b82f6 !important;
  font-weight: 600;
}
</style>
