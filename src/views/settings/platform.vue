<template>
  <div class="h-full flex flex-col bg-gray-50 overflow-hidden relative">
    
    <!-- 顶部 Header -->
    <div class="shrink-0 bg-white border-b border-gray-200 p-4 flex justify-between items-center z-10 shadow-sm relative">
      <div class="flex items-center gap-3">
        <el-button @click="$router.push('/')" circle>
          <el-icon><Back /></el-icon>
        </el-button>
        <h2 class="text-xl font-bold text-gray-800 flex items-center tracking-tight">
          <div class="w-1.5 h-5 bg-gradient-to-b from-blue-500 to-indigo-600 rounded-full mr-2"></div>
          平台全局设置
        </h2>
        <el-tag size="small" type="primary" effect="light" round class="ml-2 font-medium">商业版</el-tag>
      </div>
      <div>
        <el-button type="primary" class="shadow-md shadow-blue-500/30 px-6 font-medium transition-transform hover:-translate-y-0.5" @click="handleSave">
          <el-icon class="mr-1"><Check /></el-icon> 保存配置
        </el-button>
      </div>
    </div>

    <!-- 主体区域：左侧导航 + 右侧表单组 -->
    <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
      
      <!-- 左侧锚点导航 -->
      <div class="w-full md:w-56 bg-white border-b md:border-b-0 md:border-r border-gray-200 shrink-0 overflow-x-auto md:overflow-y-auto p-4 flex flex-row md:flex-col gap-2">
        <div 
          v-for="(item, index) in navItems" 
          :key="index"
          @click="scrollTo(item.id)"
          class="px-4 py-3 rounded-xl cursor-pointer transition-all duration-300 flex items-center gap-3 whitespace-nowrap"
          :class="activeSection === item.id ? 'bg-blue-50 text-blue-600 font-bold shadow-sm' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
        >
          <el-icon :size="18">
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.title }}</span>
        </div>
      </div>

      <!-- 右侧表单内容区 -->
      <div class="flex-1 overflow-y-auto p-6 scroll-smooth" id="scroll-container" @scroll="onScroll">
        <div class="max-w-4xl mx-auto space-y-8 pb-20">
          
          <!-- 1. 基础企业信息 -->
          <el-card shadow="never" class="border-gray-100 rounded-2xl overflow-hidden" id="section-basic">
            <template #header>
              <div class="flex items-center gap-2">
                <el-icon class="text-blue-500" size="20"><OfficeBuilding /></el-icon>
                <span class="font-bold text-gray-800 text-lg">基础企业信息墙</span>
              </div>
            </template>
            <el-form label-position="top">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <el-form-item label="企业主体名称" required>
                  <el-input v-model="form.companyName" placeholder="例如：某某科技有限公司" size="large">
                    <template #prefix>
                      <el-icon><Suitcase /></el-icon>
                    </template>
                  </el-input>
                  <div class="text-xs text-gray-400 mt-1">用于系统顶头、报表导出水印显示。</div>
                </el-form-item>
                
                <el-form-item label="官方联系电话">
                  <el-input v-model="form.officialPhone" placeholder="例如：400-888-8888" size="large">
                    <template #prefix>
                      <el-icon><Phone /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </div>

              <el-form-item label="全局系统公告" class="mt-4">
                <el-input 
                  v-model="form.announcement" 
                  type="textarea" 
                  :rows="3" 
                  placeholder="例如：热烈庆祝本系统上线！本月全员冲刺100万目标！"
                  maxlength="200"
                  show-word-limit
                ></el-input>
                <div class="text-xs text-blue-500 mt-2 flex items-center bg-blue-50 p-2 rounded-lg">
                  <el-icon class="mr-1"><InfoFilled /></el-icon>
                  此公告将在所有员工工作台(Dashboard)顶部醒目滚动展示。
                </div>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 2. 多维业绩目标矩阵 -->
          <el-card shadow="never" class="border-gray-100 rounded-2xl overflow-hidden" id="section-targets">
            <template #header>
              <div class="flex items-center gap-2">
                <el-icon class="text-orange-500" size="20"><DataLine /></el-icon>
                <span class="font-bold text-gray-800 text-lg">多维度成单目标矩阵 (按单数算)</span>
              </div>
            </template>
            <el-form label-position="top">
              <el-form-item label="年度总成单目标 (单)" required>
                <el-input-number 
                  v-model="form.annualTarget" 
                  :min="0" 
                  :step="1" 
                  size="large" 
                  class="!w-48"
                  controls-position="right"
                />
              </el-form-item>
              
              <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                <div class="font-medium text-gray-700 mb-4 flex items-center justify-between">
                  <span>月度成单目标拆解 (1-12月)</span>
                  <el-button link type="primary" @click="autoDivideTarget">均分年度成单目标</el-button>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  <div v-for="month in 12" :key="month" class="bg-white p-3 rounded-lg border border-gray-200">
                    <div class="text-sm text-gray-500 mb-2 font-medium">{{ month }}月</div>
                    <el-input-number 
                      v-model="form.monthlyTargets[month - 1]" 
                      :min="0" 
                      :step="1"
                      class="!w-full"
                      controls-position="right"
                      size="small"
                    />
                  </div>
                </div>
                <div class="mt-3 flex items-center justify-end text-sm">
                  <span class="text-gray-500 mr-2">当前排期拆解总单数：</span>
                  <span :class="computedMonthlyTotal === form.annualTarget ? 'text-green-600 font-bold' : 'text-red-500 font-bold'">
                    {{ computedMonthlyTotal.toLocaleString() }}
                  </span>
                  <span class="text-gray-500 ml-1">单</span>
                </div>
              </div>
            </el-form>
          </el-card>

          <!-- 3. 风控与跟单规则兜底 -->
          <el-card shadow="never" class="border-gray-100 rounded-2xl overflow-hidden" id="section-rules">
            <template #header>
              <div class="flex items-center gap-2">
                <el-icon class="text-red-500" size="20"><WarnTriangleFilled /></el-icon>
                <span class="font-bold text-gray-800 text-lg">风控与交易规则兜底</span>
              </div>
            </template>
            <el-form label-position="top">
              
              <el-form-item>
                <template #label>
                  <div class="flex items-center font-bold text-gray-700">
                    销售线索最大保有量上限
                    <el-tooltip content="防止销售盲目捞取公海线索屯单。" placement="top">
                      <el-icon class="ml-1 text-gray-400 cursor-pointer"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </div>
                </template>
                <div class="flex items-center gap-3">
                  <el-input-number v-model="form.maxLeadsPerRep" :min="1" :max="2000" class="!w-32" />
                  <span class="text-gray-500">条 / 每人</span>
                </div>
                <div class="text-xs text-gray-400 mt-2">
                  当单一销售人员手中未转交、未完结的活动线索达到此上限时，将无法新建或从公海捞取新线索。
                </div>
              </el-form-item>

              <el-divider border-style="dashed" />

              <el-form-item>
                <template #label>
                  <div class="flex items-center font-bold text-gray-700">
                    全局公海掉落红色预警
                    <el-tooltip content="将在距离掉落公海前 X 天向销售发送强提醒。" placement="top">
                      <el-icon class="ml-1 text-gray-400 cursor-pointer"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </div>
                </template>
                <div class="flex items-center gap-3">
                  <span class="text-gray-600">距离自动掉落公海前</span>
                  <el-input-number v-model="form.globalDropWarningDays" :min="1" :max="30" class="!w-24" size="small" />
                  <span class="text-gray-600">天时，触发红色列表高光预警。</span>
                </div>
              </el-form-item>

            </el-form>
          </el-card>

          <!-- 4. AI模型配置 -->
          <el-card shadow="never" class="border-gray-100 rounded-2xl overflow-hidden" id="section-ai">
            <template #header>
              <div class="flex items-center gap-2">
                <el-icon class="text-indigo-500" size="20"><Setting /></el-icon>
                <span class="font-bold text-gray-800 text-lg">AI模型配置（老板可维护）</span>
              </div>
            </template>
            <el-form label-position="top">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <el-form-item label="启用AI助手">
                  <el-switch v-model="form.aiEnabled" active-text="已开启" inactive-text="已关闭" />
                </el-form-item>

                <el-form-item label="超时秒数">
                  <el-input-number v-model="form.aiTimeoutSeconds" :min="3" :max="60" class="!w-40" />
                </el-form-item>

                <el-form-item label="模型地址">
                  <el-input v-model="form.aiBaseUrl" placeholder="https://api.openai.com/v1" />
                </el-form-item>

                <el-form-item label="模型名称">
                  <el-input v-model="form.aiModel" placeholder="gpt-4o-mini" />
                </el-form-item>
              </div>

              <el-form-item label="模型Key（留空表示不修改）">
                <el-input
                  v-model="form.aiApiKey"
                  type="password"
                  show-password
                  :placeholder="form.aiApiKeyMasked ? `已配置: ${form.aiApiKeyMasked}` : '请输入新的API Key'"
                />
              </el-form-item>

              <div class="flex items-center gap-3 mt-1">
                <el-button type="primary" plain :loading="aiTesting" @click="handleTestAiConnection">
                  测试联通模型
                </el-button>
                <span v-if="aiTestResult" class="text-sm" :class="aiTestResult.ok ? 'text-green-600' : 'text-red-500'">
                  {{ aiTestResult.message }}
                  <span v-if="aiTestResult.latencyMs">（{{ aiTestResult.latencyMs }}ms）</span>
                </span>
              </div>
            </el-form>
          </el-card>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Back, Check, OfficeBuilding, Suitcase, Phone, InfoFilled, 
  DataLine, WarnTriangleFilled, QuestionFilled, Location, Setting 
} from '@element-plus/icons-vue'
import { getPlatformSettings, savePlatformSettings, testPlatformAiConnection } from '@/api/settings'

// 导航数据
const navItems = [
  { id: 'section-basic', title: '基础企业信息', icon: 'OfficeBuilding' },
  { id: 'section-targets', title: '多维业绩目标', icon: 'DataLine' },
  { id: 'section-rules', title: '交易风控规则', icon: 'WarnTriangleFilled' },
  { id: 'section-ai', title: 'AI模型配置', icon: 'Setting' }
]

const activeSection = ref('section-basic')

// 表单数据绑定
const form = reactive({
  companyName: '',
  officialPhone: '',
  announcement: '',
  annualTarget: 0,
  monthlyTargets: Array(12).fill(0),
  maxLeadsPerRep: 0,
  globalDropWarningDays: 0,
  aiEnabled: false,
  aiApiKeyMasked: '',
  aiApiKey: '',
  aiBaseUrl: 'https://api.openai.com/v1',
  aiModel: 'gpt-4o-mini',
  aiTimeoutSeconds: 12
})

const aiTesting = ref(false)
const aiTestResult = ref(null)

onMounted(async () => {
  try {
    const data = await getPlatformSettings()
    Object.assign(form, data)
    form.aiApiKey = ''
  } catch(e) {
    console.error('获取平台配置失败', e)
  }
})

// 计算月度目标总和
const computedMonthlyTotal = computed(() => {
  return form.monthlyTargets.reduce((sum, val) => sum + (val || 0), 0)
})

// 均分年度目标到12个月
const autoDivideTarget = () => {
  const annual = form.annualTarget || 0
  const monthly = Math.floor(annual / 12)
  const remainder = annual % 12
  
  for (let i = 0; i < 12; i++) {
    form.monthlyTargets[i] = monthly
  }
  // 如果有余数，加在一月
  if (remainder > 0) {
    form.monthlyTargets[0] += remainder
  }
  ElMessage.success('已自动将目标平级分配至各个自然月。')
}

// 锚点跳转滚动到特定区域
const scrollTo = (id) => {
  activeSection.value = id
  const container = document.getElementById('scroll-container')
  const el = document.getElementById(id)
  if (container && el) {
    // 留点顶部余量
    container.scrollTo({ top: el.offsetTop - container.offsetTop - 20, behavior: 'smooth' })
  }
}

// 监听滚动，反向高亮左侧菜单 (可选功能提升体验)
const onScroll = (e) => {
  const scrollTop = e.target.scrollTop
  const sections = navItems.map(item => document.getElementById(item.id))
  
  let currentId = navItems[0].id
  for (let i = sections.length - 1; i >= 0; i--) {
    const el = sections[i]
    if (el && scrollTop >= (el.offsetTop - e.target.offsetTop - 100)) {
      currentId = el.id
      break
    }
  }
  
  if (activeSection.value !== currentId) {
    activeSection.value = currentId
  }
}

// 保存逻辑
const handleSave = async () => {
  try {
    const payload = {
      companyName: form.companyName,
      officialPhone: form.officialPhone,
      announcement: form.announcement,
      annualTarget: form.annualTarget,
      monthlyTargets: form.monthlyTargets,
      maxLeadsPerRep: form.maxLeadsPerRep,
      globalDropWarningDays: form.globalDropWarningDays,
      aiEnabled: form.aiEnabled,
      aiApiKey: form.aiApiKey?.trim() ? form.aiApiKey.trim() : null,
      aiBaseUrl: form.aiBaseUrl,
      aiModel: form.aiModel,
      aiTimeoutSeconds: form.aiTimeoutSeconds
    }
    const data = await savePlatformSettings(payload)
    Object.assign(form, data)
    form.aiApiKey = ''
    ElMessage({
      message: '平台及风控规则配置已保存，将在刷新后全局生效。',
      type: 'success',
      duration: 3000
    })
  } catch(e) {
    ElMessage.error('保存失败')
  }
}

const handleTestAiConnection = async () => {
  aiTesting.value = true
  aiTestResult.value = null
  try {
    const data = await testPlatformAiConnection({
      aiEnabled: form.aiEnabled,
      aiApiKey: form.aiApiKey?.trim() ? form.aiApiKey.trim() : null,
      aiBaseUrl: form.aiBaseUrl,
      aiModel: form.aiModel,
      aiTimeoutSeconds: form.aiTimeoutSeconds
    })
    aiTestResult.value = data
    if (data.ok) {
      ElMessage.success(`模型连通成功 (${data.latencyMs}ms)`)
    } else {
      ElMessage.warning(data.message || '模型连通失败')
    }
  } catch (e) {
    ElMessage.error('模型联通测试失败')
  } finally {
    aiTesting.value = false
  }
}
</script>

<style scoped>
/* 自定义滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
