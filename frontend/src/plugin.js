export default {
  name: 'open',
  version: '1.1.0',
  routes: [
    {
      path: '',
      name: 'Home',
      component: () => import('./views/ai/AIChat.vue')
    },
    {
      path: 'documents/:id',
      name: 'DocumentDetail',
      component: () => import('./views/document/DocumentDetail.vue')
    },
    {
      path: 'documents/new',
      name: 'DocumentCreate',
      component: () => import('./views/document/DocumentEditor.vue')
    },
    {
      path: 'documents/:id/edit',
      name: 'DocumentEdit',
      component: () => import('./views/document/DocumentEditor.vue')
    },
    {
      path: 'documents/trash',
      name: 'DocumentTrash',
      component: () => import('./views/document/DocumentTrash.vue')
    },
    {
      path: 'profile',
      name: 'Profile',
      component: () => import('./views/profile/Profile.vue')
    },
    {
      path: 'knowledge',
      name: 'KnowledgeManage',
      component: () => import('./views/knowledge/KnowledgeManage.vue')
    },
    {
      path: 'collaboration',
      name: 'CollaborationCenter',
      component: () => import('./views/collaboration/CollaborationCenter.vue')
    },
    {
      path: 'statistics',
      name: 'StatisticsDashboard',
      component: () => import('./views/statistics/StatisticsDashboard.vue')
    },
    {
      path: 'admin',
      name: 'SystemManage',
      component: () => import('./views/admin/SystemManage.vue'),
      meta: { requiresAdmin: true }
    }
  ],
  menus: [
    {
      path: '/',
      label: '首页',
      icon: 'HomeFilled',
      order: 1
    },
    {
      path: '/knowledge',
      label: '知识管理',
      icon: 'Document',
      order: 2
    },
    {
      path: '/collaboration',
      label: '协作中心',
      icon: 'UserFilled',
      order: 3
    },
    {
      path: '/statistics',
      label: '统计分析',
      icon: 'DataAnalysis',
      order: 4
    },
    {
      path: '/admin',
      label: '系统管理',
      icon: 'OfficeBuilding',
      order: 10,
      adminOnly: true
    }
  ]
}
