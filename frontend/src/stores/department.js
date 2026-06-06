import { defineStore } from 'pinia'
import { departmentAPI } from '@/api'

export const useDepartmentStore = defineStore('department', {
  state: () => ({
    departments: [],
    departmentTree: []
  }),

  actions: {
    async fetchDepartments() {
      this.departments = await departmentAPI.getDepartments()
    },

    async fetchDepartmentTree() {
      this.departmentTree = await departmentAPI.getDepartmentTree()
    },

    async createDepartment(data) {
      return await departmentAPI.createDepartment(data)
    },

    async updateDepartment(id, data) {
      return await departmentAPI.updateDepartment(id, data)
    },

    async deleteDepartment(id) {
      await departmentAPI.deleteDepartment(id)
      this.departments = this.departments.filter(d => d.id !== id)
    }
  }
})
