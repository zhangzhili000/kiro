<template>
  <div class="collaboration-center">
    <el-tabs v-model="activeTab" class="collaboration-tabs">
      <el-tab-pane label="通知中心" name="notifications">
        <NotificationCenter />
      </el-tab-pane>
      <el-tab-pane label="订阅管理" name="subscriptions">
        <SubscriptionManage />
      </el-tab-pane>
      <el-tab-pane label="团队管理" name="teams">
        <TeamManage />
      </el-tab-pane>
      <el-tab-pane label="审批管理" name="approvals">
        <ApprovalManage />
      </el-tab-pane>
      <el-tab-pane label="模板管理" name="templates">
        <TemplateManage />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NotificationCenter from '@open/views/notification/NotificationCenter.vue'
import SubscriptionManage from '@open/views/subscription/SubscriptionManage.vue'
import TeamManage from '@open/views/team/TeamManage.vue'
import ApprovalManage from '@open/views/approval/ApprovalManage.vue'
import TemplateManage from '@open/views/template/TemplateManage.vue'

const route = useRoute()
const router = useRouter()

const activeTab = ref('notifications')

watch(() => route.query.tab, (newTab) => {
  if (newTab) {
    activeTab.value = newTab
  }
}, { immediate: true })

watch(activeTab, (newTab) => {
  router.replace({ query: { ...route.query, tab: newTab } })
})
</script>

<style scoped>
.collaboration-center {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.collaboration-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.collaboration-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.collaboration-tabs :deep(.el-tab-pane) {
  height: 100%;
}
</style>
