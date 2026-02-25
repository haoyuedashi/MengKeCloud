<template>
  <div v-if="showWidget" class="fixed bottom-8 right-8 z-50 flex flex-col items-end gap-3">
    <!-- Popover for testing -->
    <el-popover
      v-model:visible="visible"
      placement="top-end"
      :width="300"
      trigger="click"
    >
      <div class="p-2">
        <h4 class="font-bold mb-3 flex items-center text-indigo-600">
          <el-icon class="mr-2"><Microphone /></el-icon> AI 辅助排障 / 测试
        </h4>
        <div class="text-xs text-gray-500 mb-3">
          当前状态: <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
        </div>
        <el-input
          v-model="testMsg"
          type="textarea"
          :rows="2"
          placeholder="模拟客户语音，如：他觉得价格高，先推按揭方案"
          class="mb-3"
        />
        <el-button type="primary" class="w-full bg-gradient-to-r from-indigo-500 to-purple-500 border-none shadow-md shadow-indigo-500/30" @click="sendTestMessage" :disabled="!isConnected">
          模拟语音流推送
        </el-button>
      </div>
      <template #reference>
        <!-- Floating Button -->
        <div 
          class="w-14 h-14 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/40 flex items-center justify-center cursor-pointer hover:scale-110 transition-transform relative group"
        >
          <div v-if="isConnected" class="absolute top-0 right-0 w-3 h-3 bg-green-400 border-2 border-white rounded-full"></div>
          <div v-else class="absolute top-0 right-0 w-3 h-3 bg-red-400 border-2 border-white rounded-full"></div>
          <el-icon class="text-white text-2xl"><Service /></el-icon>
        </div>
      </template>
    </el-popover>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Microphone, Service } from '@element-plus/icons-vue'
import { ElNotification } from 'element-plus'
import { getAccessToken, getCurrentStaffId } from '@/utils/auth'

const visible = ref(false)
const testMsg = ref('他觉得价格高，先推按揭方案')

// WebSocket state
let ws = null
const isConnected = ref(false)
const staffId = ref('')
const showWidget = computed(() => window.location.pathname !== '/login' && Boolean(getAccessToken()) && Boolean(staffId.value))

const statusText = computed(() => isConnected.value ? '已连接 (监听中)' : '未连接/断开')
const statusType = computed(() => isConnected.value ? 'success' : 'danger')

const connectWS = () => {
  if (ws) {
    ws.close()
  }

  const token = getAccessToken()
  const currentStaffId = getCurrentStaffId()
  staffId.value = currentStaffId
  if (!token || !currentStaffId) {
    return
  }

  // 使用当前 host 进行代理，解决硬编码端口导致的问题
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/voice-assist/${staffId.value}?token=${encodeURIComponent(token)}`
  
  try {
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('AI Voice Assist WS Connected')
      isConnected.value = true
    }

    ws.onmessage = (event) => {
      console.log('WS Message Data:', event.data)
      try {
        const data = JSON.parse(event.data)
        
        // 当收到类型为 ai_hint 的消息时，弹出沉浸式通知
        if (data.type === 'ai_hint') {
          ElNotification({
            title: '✨ AI 话术导航',
            message: data.content,
            type: 'success',
            duration: 8000,
            position: 'top-right',
            customClass: 'ai-hint-notification'
          })
        }
      } catch (e) {
        console.error('Failed to parse WS message', e)
      }
    }

    ws.onclose = () => {
      console.log('AI Voice Assist WS Disconnected')
      isConnected.value = false
      // 断线重连机制
      setTimeout(() => {
        if (!isConnected.value && showWidget.value) connectWS()
      }, 5000)
    }

    ws.onerror = (error) => {
      console.error('WS Error:', error)
      ws.close()
    }
  } catch (err) {
    console.error('WebSocket connection failed:', err)
  }
}

const sendTestMessage = () => {
  if (ws && isConnected.value) {
    const payload = JSON.stringify({
      type: 'publish_test',
      content: testMsg.value
    })
    ws.send(payload)
    ElNotification({
      title: '已发送测试包',
      message: '等待后端 AI Worker 经由 Redis Pub/Sub 推送回包...',
      type: 'info',
      duration: 3000
    })
    visible.value = false
  }
}

onMounted(() => {
  if (showWidget.value) {
    connectWS()
  }
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style>
/* カスタム Notification Style */
.ai-hint-notification {
  border-left: 4px solid #8b5cf6 !important;
  background: linear-gradient(145deg, #ffffff, #f5f3ff) !important;
}
.ai-hint-notification .el-notification__title {
  color: #6d28d9 !important;
  font-weight: bold;
}
.ai-hint-notification .el-notification__content {
  color: #4c1d95 !important;
  font-size: 14px;
}
</style>
