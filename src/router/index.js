import { createRouter, createWebHistory } from 'vue-router'
import { getCurrentRole, getMustChangePassword, isLoggedIn } from '@/utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/index.vue'),
    meta: { title: '工作台', roles: ['admin', 'manager', 'sales'] }
  },
  {
    path: '/leads',
    name: 'Leads',
    component: () => import('@/views/leads/index.vue'),
      meta: { title: '客户管理', roles: ['admin', 'manager', 'sales'] }
  },
  {
    path: '/public-pool',
    name: 'PublicPool',
    component: () => import('@/views/public-pool/index.vue'),
    meta: { title: '公海池', roles: ['admin', 'manager', 'sales'] }
  },
  {
    path: '/public-pool/audit',
    name: 'PublicPoolAudit',
    component: () => import('@/views/public-pool/audit.vue'),
    meta: { title: '公海流转审计', roles: ['admin', 'manager'] }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/reports/index.vue'),
    meta: { title: '数据报表', roles: ['admin', 'manager', 'sales'] }
  },
  {
    path: '/settings/recycle-notifications',
    name: 'RecycleNotifications',
    component: () => import('@/views/recycle-notifications/index.vue'),
    meta: { title: '回收预警通知', roles: ['admin', 'manager'] }
  },
  {
    path: '/recycle-notifications',
    redirect: '/settings/recycle-notifications'
  },
  {
    path: '/settings/org',
    name: 'SettingsOrg',
    component: () => import('@/views/settings/org.vue'),
    meta: { title: '组织架构管理', roles: ['admin'] }
  },
  {
    path: '/settings/roles',
    name: 'SettingsRoles',
    component: () => import('@/views/settings/roles.vue'),
    meta: { title: '账号与权限', roles: ['admin'] }
  },
  {
    path: '/settings/fields',
    name: 'SettingsFields',
    component: () => import('@/views/settings/fields.vue'),
    meta: { title: '字段自定义', roles: ['admin'] }
  },
  {
    path: '/settings/dict',
    name: 'SettingsDict',
    component: () => import('@/views/settings/dict.vue'),
    meta: { title: '字典管理', roles: ['admin'] }
  },
  {
    path: '/settings/rules',
    name: 'SettingsRules',
    component: () => import('@/views/settings/rules.vue'),
    meta: { title: '自动回收规则', roles: ['admin'] }
  },
  {
    path: '/settings/platform',
    name: 'SettingsPlatform',
    component: () => import('@/views/settings/platform.vue'),
    meta: { title: '平台设置', roles: ['admin'] }
  },
  {
    path: '/account/change-password',
    name: 'AccountChangePassword',
    component: () => import('@/views/account/change-password.vue'),
    meta: { title: '修改密码', roles: ['admin', 'manager', 'sales'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  if (to.meta.public) {
    if (to.path === '/login' && isLoggedIn()) {
      next('/')
      return
    }
    next()
    return
  }

  if (!isLoggedIn()) {
    next('/login')
    return
  }

  if (getMustChangePassword() && to.path !== '/account/change-password') {
    next('/account/change-password')
    return
  }

  const role = getCurrentRole()
  const allowed = to.meta.roles || []
  if (Array.isArray(allowed) && allowed.length > 0 && !allowed.includes(role)) {
    next('/')
    return
  }

  next()
})

export default router
