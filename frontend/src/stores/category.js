import { defineStore } from 'pinia'
import { categoryAPI } from '@open/api'

export const useCategoryStore = defineStore('category', {
  state: () => ({
    categories: [],
    categoryTree: []
  }),

  actions: {
    async fetchCategories() {
      this.categories = await categoryAPI.getCategories()
    },

    async fetchCategoryTree() {
      this.categoryTree = await categoryAPI.getCategoryTree()
    },

    async createCategory(data) {
      return await categoryAPI.createCategory(data)
    },

    async updateCategory(id, data) {
      return await categoryAPI.updateCategory(id, data)
    },

    async deleteCategory(id) {
      await categoryAPI.deleteCategory(id)
      this.categories = this.categories.filter(c => c.id !== id)
    }
  }
})
