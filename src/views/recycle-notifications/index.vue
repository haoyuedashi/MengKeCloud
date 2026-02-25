<template>
  <div class="h-full bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
    <div class="p-4 border-b border-gray-100 bg-gray-50/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
      <h3 class="font-bold text-gray-800 flex items-center">
        <el-icon class="mr-2 text-amber-500"><Bell /></el-icon>
        回收预警通知
      </h3>
      <div class="flex items-center gap-2">
        <el-switch v-model="unreadOnly" inline-prompt active-text="仅未读" inactive-text="全部" @change="loadData" />
        <el-button plain @click="handleReadAll">一键已读</el-button>
        <el-button v-if="isAdmin" type="primary" plain :loading="runningNow" @click="handleRunNow">立即执行扫描</el-button>
      </div>
    </div>

    <div class="p-4 border-b border-gray-100 bg-white">
      <el-radio-group v-model="categoryPrefix" @change="loadData">
        <el-radio-button :value="'recycle_'">回收通知</el-radio-button>
        <el-radio-button :value="''">全部分类</el-radio-button>
      </el-radio-group>
    </div>

    <div class="flex-1 overflow-hidden p-4">
      <el-table :data="rows" height="100%" class="custom-table">
        <el-table-column prop="createdAt" label="时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="content" label="内容" min-width="320" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatNotificationContent(row.content) }}
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="140">
          <template #default="{ row }">
            <el-tag :type="row.category === 'recycle_warning' ? 'warning' : 'info'">{{ formatCategoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isRead" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.isRead ? 'info' : 'danger'">{{ row.isRead ? '已读' : '未读' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.isRead" @click="markRead(row)">标记已读</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="p-3 border-t border-gray-100 flex justify-end bg-gray-50 shrink-0">
      <el-pagination
        layout="total, prev, pager, next"
        :total="total"
        :current-page="page"
        :page-size="pageSize"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getCurrentRole } from '@/utils/auth'
import { getNotifications, markAllNotificationsRead, markNotificationRead, runRecycleNow } from '@/api/notifications'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const unreadOnly = ref(false)
const categoryPrefix = ref('recycle_')
const runningNow = ref(false)

const role = getCurrentRole()
const isAdmin = computed(() => role === 'admin')

const formatDateTime = (value) => {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

const formatCategoryLabel = (category) => {
  if (category === 'recycle_warning') return '回收预警'
  if (category === 'recycle_summary') return '回收结果'
  return category || '--'
}

const formatNotificationContent = (content) => {
  const text = String(content || '')
  return text
    .replace(/线索\s+(LD[\w-]*)/g, '客户编号：$1')
    .replace(/(?<!客户编号：)\b(LD[\w-]*)\b/g, '客户编号：$1')
}

const loadData = async () => {
  const data = await getNotifications({
    unreadOnly: unreadOnly.value,
    categoryPrefix: categoryPrefix.value || undefined,
    page: page.value,
    pageSize: pageSize.value
  })
  rows.value = data.list || []
  total.value = data.total || 0
}

const markRead = async (row) => {
  await markNotificationRead(row.id)
  ElMessage.success('已标记为已读')
  await loadData()
  window.dispatchEvent(new Event('recycle-notification-updated'))
}

const handleReadAll = async () => {
  try {
    const data = await markAllNotificationsRead({
      categoryPrefix: categoryPrefix.value || undefined
    })
    ElMessage.success(`已批量标记 ${data.updatedCount} 条通知`)
    await loadData()
    window.dispatchEvent(new Event('recycle-notification-updated'))
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '批量标记失败')
  }
}

const handlePageChange = async (nextPage) => {
  page.value = nextPage
  await loadData()
}

const handleRunNow = async () => {
  runningNow.value = true
  try {
    const data = await runRecycleNow()
    ElMessage.success(`执行完成：回收 ${data.recycledCount} 条，预警 ${data.beforeNotifiedCount} 条`) 
    await loadData()
    window.dispatchEvent(new Event('recycle-notification-updated'))
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '执行失败')
  } finally {
    runningNow.value = false
  }
}

onMounted(async () => {
  try {
    await loadData()
  } catch (_error) {
    ElMessage.error('通知列表加载失败')
  }
})
</script>

<style scoped>
.custom-table {
  --el-table-header-bg-color: #f8fafc;
}
</style>
