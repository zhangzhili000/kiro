<template>
  <el-container class="app-layout">
    <el-header class="app-header">
      <div class="header-left">
        <h1 
          class="logo" 
          @click="handleLogoClick"
          :class="{ 'disabled': isAIChatLoading }"
        >企业知识库</h1>
      </div>
      <div class="header-center">
        <SearchInput 
          v-model="searchKeyword" 
          placeholder="搜索文档..." 
          @search="handleSearch"
          :disabled="isAIChatLoading"
        />
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info" :class="{ 'disabled': isAIChatLoading }">
            <el-avatar :size="32" :src="authStore.user?.avatar">
              {{ authStore.user?.username?.[0]?.toUpperCase() }}
            </el-avatar>
            <span class="username">{{ authStore.user?.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile" :disabled="isAIChatLoading">个人中心</el-dropdown-item>
              <el-dropdown-item command="settings" :disabled="isAIChatLoading">设置</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
          <el-icon 
            :size="20" 
            @click="handleNotificationClick"
            :class="{ 'disabled': isAIChatLoading }"
          >
            <Bell />
          </el-icon>
        </el-badge>
      </div>
    </el-header>
    <el-container class="app-container">
      <el-aside class="app-sidebar" :width="isCollapse ? '65px' : '200px'">
        <el-menu 
          class="sidebar-menu"
          :class="{ 'disabled': isAIChatLoading && isInAIChat }"
          :default-active="activeMenu"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
        >
          <el-menu-item 
            index="/" 
            :disabled="isAIChatLoading && isInAIChat"
          >
            <el-icon><HomeFilled /></el-icon>
            <template #title>首页</template>
          </el-menu-item>
          <el-menu-item 
            index="/knowledge" 
            :disabled="isAIChatLoading && isInAIChat"
          >
            <el-icon><Document /></el-icon>
            <template #title>知识管理</template>
          </el-menu-item>
          <el-menu-item 
            index="/collaboration" 
            :disabled="isAIChatLoading && isInAIChat"
          >
            <el-icon><UserFilled /></el-icon>
            <template #title>协作中心</template>
          </el-menu-item>
          <el-menu-item 
            index="/statistics" 
            :disabled="isAIChatLoading && isInAIChat"
          >
            <el-icon><DataAnalysis /></el-icon>
            <template #title>统计分析</template>
          </el-menu-item>
          
          <el-menu-item 
            v-if="authStore.isAdmin" 
            index="/admin" 
            :disabled="isAIChatLoading && isInAIChat"
          >
            <el-icon><OfficeBuilding /></el-icon>
            <template #title>系统管理</template>
          </el-menu-item>
        </el-menu>
        <!-- <div class="collapse-btn" @click="isCollapse = !isCollapse">
          <el-icon v-if="isCollapse"><DArrowRight /></el-icon>
          <el-icon v-else><DArrowLeft /></el-icon>
        </div> -->
      </el-aside>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <keep-alive include="AIChat,KnowledgeManage,CollaborationCenter,SystemManage">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import SearchInput from '@/components/common/SearchInput.vue'
import {
  HomeFilled, Document, UserFilled, DataAnalysis, Help,
  OfficeBuilding, ArrowDown, DArrowLeft, DArrowRight
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const isCollapse = ref(true)
const searchKeyword = ref('')

// AI聊天加载状态
const isAIChatLoading = ref(false)

// 是否在AI聊天页面
const isInAIChat = computed(() => {
  return route.path === '/'
})

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/documents')) return '/knowledge'
  if (path.startsWith('/categories')) return '/knowledge'
  if (path.startsWith('/tags')) return '/knowledge'
  if (path.startsWith('/search')) return '/knowledge'
  if (path.startsWith('/knowledge-graph')) return '/knowledge'
  if (path.startsWith('/notifications')) return '/collaboration'
  if (path.startsWith('/subscriptions')) return '/collaboration'
  if (path.startsWith('/teams')) return '/collaboration'
  if (path.startsWith('/approvals')) return '/collaboration'
  if (path.startsWith('/templates')) return '/collaboration'
  if (path.startsWith('/departments')) return '/admin'
  if (path.startsWith('/admin')) return '/admin'
  return path
})

const unreadCount = computed(() => notificationStore.unreadCount)

const handleSearch = (keyword) => {
  if (isAIChatLoading.value) {
    return
  }
  if (keyword) {
    router.push({ path: '/search', query: { q: keyword } })
  }
}

const handleLogoClick = () => {
  if (isAIChatLoading.value) {
    return
  }
  router.push('/')
}

const handleNotificationClick = () => {
  if (isAIChatLoading.value) {
    return
  }
  router.push('/notifications')
}

const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      if (!isAIChatLoading.value) {
        router.push('/profile')
      }
      break
    case 'settings':
      if (!isAIChatLoading.value) {
        router.push('/settings')
      }
      break
    case 'logout':
      await authStore.logout()
      router.push('/login')
      break
  }
}

// 监听全局事件
const handleAIChatStart = () => {
  isAIChatLoading.value = true
}

const handleAIChatEnd = () => {
  isAIChatLoading.value = false
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    notificationStore.fetchNotifications()
  }
  // 添加事件监听
  window.addEventListener('ai-chat-start', handleAIChatStart)
  window.addEventListener('ai-chat-end', handleAIChatEnd)
})

onUnmounted(() => {
  // 移除事件监听
  window.removeEventListener('ai-chat-start', handleAIChatStart)
  window.removeEventListener('ai-chat-end', handleAIChatEnd)
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  font-size: 20px;
  color: #409eff;
  cursor: pointer;
  margin: 0;
  transition: opacity 0.2s;
}

.logo.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 0 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.user-info.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.username {
  font-size: 14px;
}

.notification-badge {
  cursor: pointer;
}

.app-container {
  height: calc(100vh - 60px);
}

.app-sidebar {
  background: #fff;
  border-right: 1px solid #e6e6e6;
  position: relative;
  transition: width 0.3s;
}

.sidebar-menu {
  border-right: 0;
}

.sidebar-menu.disabled {
  opacity: 0.5;
}

.collapse-btn {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  cursor: pointer;
  color: #666;
}

.app-main {
  background: #f5f7fa;
  padding: 10px;
  overflow-y: auto;
  height: 100%;
}

.el-icon.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
