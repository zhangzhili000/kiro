import { defineStore } from 'pinia'
import { tagAPI } from '@/api'

export const useTagStore = defineStore('tag', {
  state: () => ({
    tags: []
  }),

  actions: {
    async fetchTags() {
      this.tags = await tagAPI.getTags()
    },

    async createTag(data) {
      return await tagAPI.createTag(data)
    },

    async updateTag(id, data) {
      return await tagAPI.updateTag(id, data)
    },

    async deleteTag(id) {
      await tagAPI.deleteTag(id)
      this.tags = this.tags.filter(t => t.id !== id)
    }
  }
})
