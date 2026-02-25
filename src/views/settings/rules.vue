<template>
  <div class="h-full bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
    <!-- Header -->
    <div class="p-4 border-b border-gray-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-gray-50/50">
      <h3 class="font-bold text-gray-800 flex items-center">
        <el-icon class="mr-2 text-indigo-500"><Setting /></el-icon>
        自动回收规则 (沉睡线索掉落公海)
      </h3>
      <el-button type="primary" class="shadow-md shadow-blue-500/30 w-full sm:w-auto" @click="saveRules" :loading="saving">
        保存规则设置
      </el-button>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6 bg-gray-50/30">
      <div class="max-w-4xl mx-auto space-y-6">
        
        <!-- 全局开关 -->
        <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h4 class="text-base font-bold text-gray-800 mb-1">启用自动回收机制</h4>
            <p class="text-sm text-gray-500">开启后，系统将在每天凌晨执行扫描，将符合条件的沉睡线索自动放入公海池</p>
          </div>
          <el-switch v-model="rulesForm.enabled" size="large" />
        </div>

        <!-- 详细规则列表 (受控于全局开关) -->
        <el-collapse-transition>
          <div v-show="rulesForm.enabled" class="space-y-6">
            
            <!-- 规则 1: 录入后未跟进 -->
            <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm transition-all hover:border-indigo-300">
              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
                <div class="flex items-start sm:items-center">
                  <div class="w-8 h-8 shrink-0 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold mr-3">1</div>
                  <div>
                    <h4 class="text-base font-bold text-gray-800">分配后未及时跟进</h4>
                    <p class="text-xs text-gray-500 mt-1">防止销售囤积线索不打，白白浪费新鲜资源</p>
                  </div>
                </div>
                <el-switch v-model="rulesForm.rule1.active" />
              </div>
              <div class="pl-11 pr-4 py-4 bg-gray-50 rounded-lg flex items-center space-x-3" :class="{'opacity-50 pointer-events-none': !rulesForm.rule1.active}">
                <span class="text-gray-700 text-sm">线索分配给销售后，超过</span>
                <el-input-number v-model="rulesForm.rule1.days" :min="1" :max="30" size="small" controls-position="right" class="w-24" />
                <span class="text-gray-700 text-sm">天未添加任何跟进记录，则自动回收。</span>
              </div>
            </div>

            <!-- 规则 2: 长时间未再跟进 -->
            <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm transition-all hover:border-indigo-300">
              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
                <div class="flex items-start sm:items-center">
                  <div class="w-8 h-8 shrink-0 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold mr-3">2</div>
                  <div>
                    <h4 class="text-base font-bold text-gray-800">跟进后长时间无联系</h4>
                    <p class="text-xs text-gray-500 mt-1">线索进入沉睡状态，可能需要更换销售重新激活</p>
                  </div>
                </div>
                <el-switch v-model="rulesForm.rule2.active" />
              </div>
              <div class="pl-11 pr-4 py-4 bg-gray-50 rounded-lg flex items-center space-x-3" :class="{'opacity-50 pointer-events-none': !rulesForm.rule2.active}">
                <span class="text-gray-700 text-sm">线索最后一次跟进时间距今已超过</span>
                <el-input-number v-model="rulesForm.rule2.days" :min="1" :max="90" size="small" controls-position="right" class="w-24" />
                <span class="text-gray-700 text-sm">天，则自动回收。</span>
              </div>
              
              <!-- 保护特例 -->
              <div class="pl-11 mt-3" :class="{'opacity-50 pointer-events-none': !rulesForm.rule2.active}">
                <el-checkbox v-model="rulesForm.rule2.protectHighIntent" label="排除 A 级 (近期可成交) 意向线索" class="text-gray-600" />
              </div>
            </div>

            <!-- 规则 3: 达到跟进上限 -->
            <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm transition-all hover:border-indigo-300">
              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
                <div class="flex items-start sm:items-center">
                  <div class="w-8 h-8 shrink-0 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold mr-3">3</div>
                  <div>
                    <h4 class="text-base font-bold text-gray-800">久攻不下死单</h4>
                    <p class="text-xs text-gray-500 mt-1">单一销售死磕未果，强制流转让其他人尝试</p>
                  </div>
                </div>
                <el-switch v-model="rulesForm.rule3.active" />
              </div>
              <div class="pl-11 pr-4 py-4 bg-gray-50 rounded-lg flex items-center space-x-3" :class="{'opacity-50 pointer-events-none': !rulesForm.rule3.active}">
                <span class="text-gray-700 text-sm">同一个线索被同一个销售累计添加了</span>
                <el-input-number v-model="rulesForm.rule3.count" :min="5" :max="100" size="small" controls-position="right" class="w-24" />
                <span class="text-gray-700 text-sm">条跟进记录仍未成交，则自动回收。</span>
              </div>
            </div>

            <!-- 通知设置 -->
            <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm mt-8">
              <h4 class="text-base font-bold text-gray-800 mb-4 flex items-center">
                <el-icon class="mr-2 text-yellow-500"><Bell /></el-icon>
                回收预警通知
              </h4>
              <div class="flex flex-col space-y-4 px-2">
                <el-checkbox v-model="rulesForm.notify.beforeDrop" label="线索掉落公海前 1 天，向负责销售发送系统消息提醒" />
                <el-checkbox v-model="rulesForm.notify.afterDrop" label="线索掉落公海后，汇总清单并抄送给销售主管" />
              </div>
            </div>

          </div>
        </el-collapse-transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Setting, Bell } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getRecycleRules, saveRecycleRules } from '@/api/settings'

const saving = ref(false)

const rulesForm = ref({
  enabled: true, // 全局开关
  rule1: {
    active: true,
    days: 3
  },
  rule2: {
    active: true,
    days: 15,
    protectHighIntent: true
  },
  rule3: {
    active: false,
    count: 20
  },
  notify: {
    beforeDrop: true,
    afterDrop: false
  }
})

const saveRules = () => {
  saving.value = true
  saveRecycleRules(rulesForm.value).then(() => {
    ElMessage({
      message: '自动回收规则配置已更新！将在今晚 00:00 生效。',
      type: 'success',
      duration: 4000
    })
  }).catch((error) => {
    ElMessage.error(error?.response?.data?.message || '保存失败')
  }).finally(() => {
    saving.value = false
  })
}

onMounted(async () => {
  try {
    const data = await getRecycleRules()
    rulesForm.value = data
  } catch (error) {
    ElMessage.error('自动回收规则加载失败')
  }
})
</script>

<style scoped>
/* 隐藏 el-input-number 默认难看的边框，使其更融于背景 */
:deep(.el-input-number.is-controls-right .el-input__wrapper) {
  box-shadow: 0 0 0 1px #e5e7eb inset; /* border-gray-200 */
}
:deep(.el-input-number.is-controls-right:hover .el-input__wrapper) {
  box-shadow: 0 0 0 1px #a5b4fc inset; /* border-indigo-300 */
}
:deep(.el-input-number.is-controls-right .el-input-number__increase),
:deep(.el-input-number.is-controls-right .el-input-number__decrease) {
  border-left-color: #e5e7eb;
}
</style>
