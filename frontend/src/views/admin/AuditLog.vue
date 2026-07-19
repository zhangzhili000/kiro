<template>
  <div class="audit-log">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>审计日志</span>
        </div>
      </template>

      <el-table :data="logs" style="width: 100%" v-loading="loading">
        <el-table-column prop="user_name" label="用户" width="120" />
        <el-table-column prop="action" label="操作" width="120" />
        <el-table-column prop="resource_type" label="资源类型" width="120" />
        <el-table-column prop="resource_id" label="资源ID" width="100" />
        <el-table-column prop="details" label="详情" />
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { auditAPI } from '@open/api'

const logs = ref([])
const loading = ref(false)

const fetchLogs = async () => {
  loading.value = true
  try {
    const result = await auditAPI.getAuditLogs()
    // 确保数据是数组
    logs.value = Array.isArray(result) ? result : []
  } catch (error) {
    console.error('Failed to fetch audit logs:', error)
    logs.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchLogs)
</script>

<style scoped>
.audit-log {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
