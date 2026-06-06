import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/ai/AIChat.vue')
      },
      {
        path: 'documents/:id',
        name: 'DocumentDetail',
        component: () => import('@/views/document/DocumentDetail.vue')
      },
      {
        path: 'documents/new',
        name: 'DocumentCreate',
        component: () => import('@/views/document/DocumentEditor.vue')
      },
      {
        path: 'documents/:id/edit',
        name: 'DocumentEdit',
        component: () => import('@/views/document/DocumentEditor.vue')
      },
      {
        path: 'documents/trash',
        name: 'DocumentTrash',
        component: () => import('@/views/document/DocumentTrash.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Profile.vue')
      },
      {
        path: 'knowledge',
        name: 'KnowledgeManage',
        component: () => import('@/views/knowledge/KnowledgeManage.vue')
      },
      {
        path: 'collaboration',
        name: 'CollaborationCenter',
        component: () => import('@/views/collaboration/CollaborationCenter.vue')
      },
      {
        path: 'statistics',
        name: 'StatisticsDashboard',
        component: () => import('@/views/statistics/StatisticsDashboard.vue')
      },
      {
        path: 'admin',
        name: 'SystemManage',
        component: () => import('@/views/admin/SystemManage.vue'),
        meta: { requiresAdmin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 如果有 token 但没有用户信息，尝试恢复用户信息
  if (authStore.accessToken && !authStore.user) {
    try {
      await authStore.getCurrentUser()
    } catch (error) {
      console.error('Failed to get current user:', error)
    }
  }

  // 公共页面（登录/注册）
  if (to.path === '/login' || to.path === '/register') {
    if (authStore.isAuthenticated) {
      next('/')
    } else {
      next()
    }
    return
  }

  // 需要认证的页面
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 需要管理员权限的页面
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/')
    return
  }

  next()
})

export default router
