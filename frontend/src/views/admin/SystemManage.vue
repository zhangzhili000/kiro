<template>
  <div class="system-manage">
    <el-tabs v-model="activeTab" class="system-tabs">
      <el-tab-pane label="用户管理" name="users">
        <UserManage />
      </el-tab-pane>
      <el-tab-pane label="角色管理" name="roles">
        <RoleManage />
      </el-tab-pane>
      <el-tab-pane label="AI助手管理" name="ai-config">
        <AIConfigManage />
      </el-tab-pane>
      <el-tab-pane label="模型管理" name="models">
        <ModelManage />
      </el-tab-pane>
      <el-tab-pane label="审计日志" name="audit-logs">
        <AuditLog />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UserManage from '@/views/admin/UserManage.vue'
import RoleManage from '@/views/admin/RoleManage.vue'
import AIConfigManage from '@/views/admin/AIConfigManage.vue'
import ModelManage from '@/views/admin/ModelManage.vue'
import AuditLog from '@/views/admin/AuditLog.vue'

const route = useRoute()
const router = useRouter()

const activeTab = ref('users')

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
.system-manage {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.system-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.system-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.system-tabs :deep(.el-tab-pane) {
  height: 100%;
}
</style>
