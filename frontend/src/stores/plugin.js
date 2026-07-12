import { defineStore } from 'pinia'

export const usePluginStore = defineStore('plugin', {
  state: () => ({
    menus: [
      { path: '/', label: '首页', icon: 'HomeFilled', order: 1 },
      { path: '/knowledge', label: '知识管理', icon: 'Document', order: 2 },
      { path: '/collaboration', label: '协作中心', icon: 'UserFilled', order: 3 },
      { path: '/statistics', label: '统计分析', icon: 'DataAnalysis', order: 4 },
      { path: '/admin', label: '系统管理', icon: 'OfficeBuilding', order: 10, adminOnly: true }
    ],
    routes: []
  }),

  getters: {
    allMenus: (state) => state.menus,
    allRoutes: (state) => state.routes
  },

  actions: {
    init(menus, routes) {
      this.menus = menus
      this.routes = routes
    },

    getMenusByRole(role) {
      if (role === 'admin') {
        return this.menus
      }
      return this.menus.filter(menu => !menu.adminOnly)
    }
  }
})
