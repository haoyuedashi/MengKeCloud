<template>
  <div class="login-page min-h-screen flex items-center justify-center p-4 md:p-8">
    <div class="login-shell w-full max-w-5xl rounded-3xl overflow-hidden border border-white/30">
      <div class="grid grid-cols-1 lg:grid-cols-2 min-h-[640px]">
        <section class="relative hidden lg:flex flex-col justify-between p-10 text-white hero-panel">
          <div class="space-y-3">
            <div class="inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-1 text-sm tracking-wide">
              盟客云智能增长中台
            </div>
            <h1 class="text-5xl font-semibold leading-tight brand-title">盟客云 CRM</h1>
            <p class="text-white/85 text-base leading-relaxed max-w-sm">
              将客户、跟进、公海与签约数据统一到一个稳定可控的系统，让团队协作更快，决策更准。
            </p>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm text-white/85">
            <div class="rounded-2xl border border-white/20 bg-white/10 p-4">
              <div class="text-2xl font-semibold">3</div>
              <div>角色分权闭环</div>
            </div>
            <div class="rounded-2xl border border-white/20 bg-white/10 p-4">
              <div class="text-2xl font-semibold">24h</div>
              <div>客户流转可追溯</div>
            </div>
          </div>
        </section>

        <section class="bg-white/95 backdrop-blur-md p-6 md:p-10 lg:p-12 flex flex-col justify-center">
          <div class="max-w-md w-full mx-auto">
            <div class="lg:hidden mb-8">
              <h1 class="text-3xl font-semibold text-slate-800 brand-title">盟客云 CRM</h1>
              <p class="text-slate-500 mt-2">手机号 + 密码登录</p>
            </div>

            <div class="hidden lg:block mb-10">
              <h2 class="text-3xl font-semibold text-slate-800 brand-title">欢迎回来</h2>
              <p class="text-slate-500 mt-2">请输入账号信息进入工作台</p>
            </div>

            <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @submit.prevent>
              <el-form-item label="手机号" prop="phone" class="mb-5">
                <el-input v-model="form.phone" maxlength="11" placeholder="请输入手机号" size="large" class="!h-12" />
              </el-form-item>
              <el-form-item label="密码" prop="password" class="mb-6">
                <el-input
                  v-model="form.password"
                  type="password"
                  show-password
                  placeholder="请输入密码"
                  size="large"
                  class="!h-12"
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
              <el-button type="primary" class="w-full !h-12 text-base" :loading="loading" @click="handleLogin">
                登录系统
              </el-button>
            </el-form>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { loginByPhone } from '@/api/auth'
import { saveSession } from '@/utils/auth'

const router = useRouter()
const loading = ref(false)
const formRef = ref()

const form = reactive({
  phone: '',
  password: ''
})

const rules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  const phone = form.phone.trim()
  if (!/^1\d{10}$/.test(phone)) {
    ElMessage.error('请输入正确的手机号')
    return
  }
  if (!form.password) {
    ElMessage.error('请输入密码')
    return
  }

  try {
    loading.value = true
    const data = await loginByPhone({ phone, password: form.password })
    saveSession(data)
    if (data?.mustChangePassword) {
      await ElMessageBox.alert('首次登录需先修改密码，修改后才可进入系统。', '安全提示', {
        type: 'warning',
        confirmButtonText: '立即修改'
      })
      router.replace('/account/change-password')
      return
    }
    ElMessage.success('登录成功')
    router.replace('/')
  } catch (_error) {
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  background:
    radial-gradient(1200px 600px at 10% 10%, rgba(14, 116, 144, 0.35), transparent),
    radial-gradient(900px 540px at 90% 90%, rgba(30, 64, 175, 0.25), transparent),
    linear-gradient(135deg, #0f172a 0%, #1e293b 45%, #334155 100%);
}

.login-shell {
  box-shadow: 0 32px 80px rgba(15, 23, 42, 0.4);
}

.hero-panel {
  background:
    linear-gradient(165deg, rgba(8, 47, 73, 0.92), rgba(30, 64, 175, 0.86)),
    linear-gradient(35deg, rgba(56, 189, 248, 0.2), rgba(165, 180, 252, 0.12));
}

.brand-title {
  font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", serif;
  letter-spacing: 0.02em;
}
</style>
