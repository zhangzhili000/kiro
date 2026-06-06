import { defineStore } from 'pinia'
import { userAPI } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    users: []
  }),

  actions: {
    async fetchUsers() {
      this.users = await userAPI.getUsers()
    },

    async updateUserStatus(userId, isActive) {
      await userAPI.updateUserStatus(userId, isActive)
      const user = this.users.find(u => u.id === userId)
      if (user) {
        user.is_active = isActive
      }
    }
  }
})
