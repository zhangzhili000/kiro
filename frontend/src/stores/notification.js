import { defineStore } from 'pinia'
import { notificationAPI } from '@open/api'

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: [],
    unreadCount: 0
  }),

  actions: {
    async fetchNotifications() {
      this.notifications = await notificationAPI.getNotifications()
      this.unreadCount = this.notifications.filter(n => !n.is_read).length
    },

    async markAsRead(id) {
      await notificationAPI.markAsRead(id)
      const notification = this.notifications.find(n => n.id === id)
      if (notification) {
        notification.is_read = true
        this.unreadCount = Math.max(0, this.unreadCount - 1)
      }
    },

    async markAllAsRead() {
      await notificationAPI.markAllAsRead()
      this.notifications.forEach(n => n.is_read = true)
      this.unreadCount = 0
    }
  }
})
