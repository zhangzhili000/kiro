import { defineStore } from 'pinia'
import { searchAPI } from '@open/api'

export const useSearchStore = defineStore('search', {
  state: () => ({
    results: [],
    suggestions: [],
    keyword: ''
  }),

  actions: {
    async search(params) {
      this.results = await searchAPI.search(params)
      this.keyword = params.q
    },

    async getSuggestions(q) {
      if (!q) {
        this.suggestions = []
        return
      }
      this.suggestions = await searchAPI.getSuggestions(q)
    }
  }
})
