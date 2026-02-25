<template>
  <div class="min-h-full flex items-center justify-center py-8">
    <div class="w-full max-w-xl bg-white rounded-2xl shadow-sm border border-gray-100 p-6 md:p-8">
      <h2 class="text-2xl font-bold text-gray-800">修改密码</h2>
      <p class="text-sm text-gray-500 mt-2">为保障账号安全，请设置一个强密码。</p>

      <el-alert
        v-if="mustChangePassword"
        title="首次登录需要先完成密码修改"
        type="warning"
        :closable="false"
        show-icon
        class="mt-4"
      />

      <el-form label-position="top" class="mt-5" @submit.prevent>
        <el-form-item label="当前密码">
          <el-input
            v-model="form.currentPassword"
            type="password"
            show-password
            autocomplete="current-password"
            placeholder="请输入当前密码"
          />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="form.newPassword"
            type="password"
            show-password
            autocomplete="new-password"
            placeholder="至少8位，避免弱口令"
          />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            autocomplete="new-password"
            placeholder="请再次输入新密码"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        <div class="flex items-center gap-3">
          <el-button type="primary" :loading="loading" @click="handleSubmit">保存新密码</el-button>
          <el-button v-if="!mustChangePassword" @click="goBack">返回</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { changePassword } from '@/api/auth'
import { getMustChangePassword, saveSession } from '@/utils/auth'

const router = useRouter()
const loading = ref(false)
const mustChangePassword = getMustChangePassword()

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const goBack = () => {
  router.replace('/')
}

const handleSubmit = async () => {
  if (!form.currentPassword) {
    ElMessage.warning('请输入当前密码')
    return
  }
  if (!form.newPassword || form.newPassword.length < 8) {
    ElMessage.warning('新密码至少 8 位')
    return
  }
  if (form.newPassword !== form.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  try {
    loading.value = true
    const data = await changePassword({
      currentPassword: form.currentPassword,
      newPassword: form.newPassword
    })
    saveSession(data)
    ElMessage.success('密码修改成功')
    goBack()
  } catch (_error) {
  } finally {
    loading.value = false
  }
}
</script>
