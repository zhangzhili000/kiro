import { defineStore } from 'pinia'
import { subscriptionAPI } from '@/api'

export const useSubscriptionStore = defineStore('subscription', {
  state: () => ({
    subscriptions: []
  }),

  actions: {
    async fetchSubscriptions() {
      this.subscriptions = await subscriptionAPI.getSubscriptions()
    },

    async subscribe(data) {
      return await subscriptionAPI.createSubscription(data)
    },

    async unsubscribe(id) {
      await subscriptionAPI.deleteSubscription(id)
      this.subscriptions = this.subscriptions.filter(s => s.id !== id)
    }
  }
})
