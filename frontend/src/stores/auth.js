import { defineStore } from 'pinia'
import { authAPI, userAPI } from '@open/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user_info') || 'null'),
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    isAdmin: (state) => state.user?.role === 'admin',
    isEditor: (state) => state.user?.role === 'editor'
  },

  actions: {
    async login(email, password) {
      const res = await authAPI.login({ email, password })
      this.accessToken = res.access_token
      this.refreshToken = res.refresh_token
      localStorage.setItem('access_token', res.access_token)
      localStorage.setItem('refresh_token', res.refresh_token)
      await this.getCurrentUser()
    },

    async register(email, username, password) {
      const res = await authAPI.register({ email, username, password })
      this.accessToken = res.access_token
      this.refreshToken = res.refresh_token
      localStorage.setItem('access_token', res.access_token)
      localStorage.setItem('refresh_token', res.refresh_token)
    },

    async getCurrentUser() {
      try {
        this.user = await userAPI.getCurrentUser()
        localStorage.setItem('user_info', JSON.stringify(this.user))
      } catch (error) {
        this.logout()
      }
    },

    async logout() {
      try {
        await authAPI.logout()
      } catch (e) {}
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
    },

    async refreshToken() {
      const res = await authAPI.refresh({ refresh_token: this.refreshToken })
      this.accessToken = res.access_token
      this.refreshToken = res.refresh_token
      localStorage.setItem('access_token', res.access_token)
      localStorage.setItem('refresh_token', res.refresh_token)
    },

    async changePassword(data) {
      await userAPI.changePassword(data)
    }
  }
})
