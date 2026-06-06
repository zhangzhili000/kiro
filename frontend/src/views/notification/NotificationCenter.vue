<template>
  <div class="notification-center">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>通知中心</span>
          <el-button @click="handleMarkAllRead" :disabled="notificationStore.unreadCount === 0">
            全部标为已读
          </el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="未读" name="unread" />
      </el-tabs>

      <div class="notification-list">
        <div
          v-for="notification in filteredNotifications"
          :key="notification.id"
          class="notification-item"
          :class="{ unread: !notification.is_read }"
          @click="handleRead(notification)"
        >
          <div class="notification-icon">
            <el-icon v-if="!notification.is_read"><Bell /></el-icon>
            <el-icon v-else><BellFilled /></el-icon>
          </div>
          <div class="notification-content">
            <div class="notification-title">{{ notification.title }}</div>
            <div class="notification-text">{{ notification.content }}</div>
            <div class="notification-time">{{ notification.created_at }}</div>
          </div>
        </div>
        <el-empty v-if="filteredNotifications.length === 0" description="暂无通知" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()
const activeTab = ref('all')

const filteredNotifications = computed(() => {
  if (activeTab.value === 'unread') {
    return notificationStore.notifications.filter(n => !n.is_read)
  }
  return notificationStore.notifications
})

const handleRead = async (notification) => {
  if (!notification.is_read) {
    await notificationStore.markAsRead(notification.id)
  }
}

const handleMarkAllRead = async () => {
  await notificationStore.markAllAsRead()
}

onMounted(() => {
  notificationStore.fetchNotifications()
})
</script>

<style scoped>
.notification-center {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.notification-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.notification-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}
.notification-item:hover {
  background: #e6e6e6;
}
.notification-item.unread {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}
.notification-icon {
  font-size: 24px;
  color: #409eff;
}
.notification-content {
  flex: 1;
}
.notification-title {
  font-weight: bold;
  margin-bottom: 5px;
}
.notification-text {
  color: #666;
  margin-bottom: 5px;
}
.notification-time {
  font-size: 12px;
  color: #999;
}
</style>
