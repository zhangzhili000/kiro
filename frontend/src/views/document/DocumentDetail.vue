<template>
  <div class="document-detail">
    <div class="page-header">
      <el-button @click="$router.push('/knowledge')" class="btn-back">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
      <h1 class="page-title">{{ document?.title || '文档详情' }}</h1>
    </div>

    <el-card v-if="document" class="detail-card">
      <template #header>
        <div class="header-actions">
          <div class="header-info">
            <h2>{{ document.title }}</h2>
          </div>
          <div class="header-buttons">
            <el-button @click="handleFavorite">
              <el-icon><Star /></el-icon> {{ isFavorited ? '取消收藏' : '收藏' }}
            </el-button>
            <el-button @click="handleLike">
              <el-icon><Pointer /></el-icon> {{ isLiked ? '取消点赞' : '点赞' }} ({{ document.like_count }})
            </el-button>
            <el-button @click="handleShare">
              <el-icon><Share /></el-icon>
              分享
            </el-button>
            <el-button type="primary" @click="$router.push(`/documents/${document.id}/edit`)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
          </div>
        </div>
      </template>

      <div class="document-meta">
        <div class="meta-item">
          <el-icon><User /></el-icon>
          <span>作者：{{ document.author_name }}</span>
        </div>
        <div class="meta-item">
          <el-icon><Folder /></el-icon>
          <span>分类：{{ document.category_name || '未分类' }}</span>
        </div>
        <div class="meta-item">
          <el-icon><View /></el-icon>
          <span>浏览：{{ document.view_count }}</span>
        </div>
        <div class="meta-item">
          <el-icon><Clock /></el-icon>
          <span>更新时间：{{ document.updated_at }}</span>
        </div>
      </div>

      <div class="index-status-section">
        <div class="index-status-header">
          <div class="index-status-label">
            <el-icon><DataLine /></el-icon>
            索引状态
          </div>
          <div class="index-status-badge" :class="getIndexStatusClass()">
            <el-icon v-if="indexStatus === 'processing'" class="spin-icon" :size="14"><Refresh /></el-icon>
            <el-icon v-else-if="indexStatus === 'completed'" class="success-icon" :size="14"><CircleCheck /></el-icon>
            <el-icon v-else-if="indexStatus === 'pending'" class="pending-icon" :size="14"><Clock /></el-icon>
            <el-icon v-else-if="indexStatus === 'failed'" class="error-icon" :size="14"><CircleClose /></el-icon>
            <span>{{ getIndexStatusText() }}</span>
          </div>
        </div>
        <div class="index-chunk-count" v-if="chunkCount">
          <el-icon><Document /></el-icon>
          Chunk数：{{ chunkCount }}
        </div>
      </div>

      <div class="document-tags" v-if="document.tags && document.tags.length">
        <el-tag v-for="tag in document.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
      </div>

      <el-divider />

      <div class="document-content" v-html="document.html_content || document.content"></div>

      <el-divider />

      <AttachmentManager :document-id="document.id" />

      <el-divider />

      <!-- 权限设置面板 -->
      <div class="permissions-section">
        <h3>
          <el-icon><Lock /></el-icon>
          文档权限
        </h3>
        <div class="permissions-content">
          <el-button type="primary" @click="openPermissionsDialog">
            <el-icon><Setting /></el-icon>
            设置权限
          </el-button>
          <div class="permissions-summary" v-if="permissions.length > 0">
            <el-tag v-for="perm in permissions" :key="perm.id" size="small" class="permission-tag">
              {{ getPermissionLabel(perm) }}
            </el-tag>
          </div>
          <div class="no-permissions" v-else>
            <span>暂无额外权限设置</span>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="comments-section">
        <h3>
          <el-icon><ChatDotRound /></el-icon>
          评论 ({{ comments.length }})
        </h3>
        <div class="comment-form">
          <el-input v-model="newComment" type="textarea" placeholder="写下你的评论..." :rows="3" />
          <el-button type="primary" @click="submitComment" :loading="submitting" class="btn-submit">
            <el-icon><ChatLineSquare /></el-icon>
            发表评论
          </el-button>
        </div>
        <div class="comment-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-avatar">
              <el-avatar :size="40">{{ comment.user_name?.[0] || 'U' }}</el-avatar>
            </div>
            <div class="comment-content-wrapper">
              <div class="comment-header">
                <strong>{{ comment.user_name }}</strong>
                <span>{{ comment.created_at }}</span>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 分享弹窗 -->
    <el-dialog
      title="分享文档"
      v-model="shareDialogVisible"
      width="480px"
      :close-on-click-modal="false"
      class="share-dialog"
    >
      <div v-if="shareUrl" class="share-content">
        <p>复制以下链接分享给他人：</p>
        <el-input
          :value="shareUrl"
          readonly
          class="share-input"
        />
        <div class="share-actions">
          <el-button
            type="primary"
            @click="copyShareUrl"
            :loading="copying"
            class="btn-copy"
          >
            <el-icon><CopyDocument /></el-icon> {{ copySuccess ? '已复制!' : '复制链接' }}
          </el-button>
        </div>
      </div>
      <div v-else class="share-loading">
        <el-icon class="loading-icon" :size="40"><Loading /></el-icon>
        <span>正在生成分享链接...</span>
      </div>
    </el-dialog>

    <!-- 权限设置弹窗 -->
    <el-dialog
      title="文档权限设置"
      v-model="permissionsDialogVisible"
      width="600px"
      :close-on-click-modal="false"
      class="permissions-dialog"
    >
      <div class="permissions-form">
        <el-tabs v-model="activePermissionTab">
          <el-tab-pane label="团队权限" name="team">
            <div class="permission-row">
              <el-select v-model="selectedTeam" placeholder="选择团队" style="width: 200px">
                <el-option v-for="team in teams" :key="team.id" :label="team.name" :value="team.id" />
              </el-select>
              <el-checkbox-group v-model="teamActions">
                <el-checkbox label="view">查看</el-checkbox>
                <el-checkbox label="edit">编辑</el-checkbox>
                <el-checkbox label="delete">删除</el-checkbox>
              </el-checkbox-group>
              <el-button type="primary" size="small" @click="addTeamPermission">添加</el-button>
            </div>
          </el-tab-pane>
          <el-tab-pane label="个人权限" name="user">
            <div class="permission-row">
              <el-select v-model="selectedUser" placeholder="选择用户" style="width: 200px">
                <el-option v-for="user in users" :key="user.id" :label="user.username" :value="user.id" />
              </el-select>
              <el-checkbox-group v-model="userActions">
                <el-checkbox label="view">查看</el-checkbox>
                <el-checkbox label="edit">编辑</el-checkbox>
                <el-checkbox label="delete">删除</el-checkbox>
              </el-checkbox-group>
              <el-button type="primary" size="small" @click="addUserPermission">添加</el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
        
        <el-divider />
        
        <div class="current-permissions">
          <h4>当前权限列表</h4>
          <el-table :data="permissions" style="width: 100%" v-if="permissions.length > 0">
            <el-table-column prop="permission_type" label="类型" width="100">
              <template #default="{ row }">
                {{ getPermissionTypeLabel(row.permission_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="target_name" label="目标" width="150" />
            <el-table-column prop="action" label="操作" width="100">
              <template #default="{ row }">
                {{ getActionLabel(row.action) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="danger" size="small" @click="removePermission(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-else class="no-permissions-table">
            <span>暂无权限设置</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="permissionsDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="savePermissions" :loading="savingPermissions">保存</el-button>
      </template>
    </el-dialog>

    <!-- 索引内容弹窗 -->
    <el-dialog
      title="索引内容详情"
      v-model="indexContentDialogVisible"
      width="800px"
      class="index-content-dialog"
    >
      <div class="index-content-container" v-loading="loadingIndexContent">
        <div v-if="indexChunks.length === 0" class="no-chunks">
          <el-icon :size="48"><Document /></el-icon>
          <p>暂无索引内容</p>
        </div>
        <div v-else class="chunk-list">
          <div v-for="(chunk, index) in indexChunks" :key="index" class="chunk-item">
            <div class="chunk-header">
              <span class="chunk-number">Chunk #{{ index + 1 }}</span>
              <span v-if="chunk.distance" class="chunk-distance">距离: {{ chunk.distance }}</span>
            </div>
            <div class="chunk-content">{{ chunk.content || chunk.chunk_content }}</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocumentStore } from '@/stores/document'
import { commentAPI } from '@/api'
import { ElMessage } from 'element-plus'
import { 
  CopyDocument, 
  ArrowLeft, 
  User, 
  Folder, 
  View, 
  Document, 
  Clock, 
  Star, 
  Pointer, 
  Share, 
  Edit, 
  ChatDotRound, 
  ChatLineSquare, 
  Loading,
  Refresh,
  CircleCheck,
  CircleClose,
  DataLine,
  Lock,
  Setting
} from '@element-plus/icons-vue'
import AttachmentManager from '@/components/AttachmentManager.vue'

const route = useRoute()
const router = useRouter()
const documentStore = useDocumentStore()

const document = ref(null)
const comments = ref([])
const newComment = ref('')
const submitting = ref(false)
const isFavorited = ref(false)
const isLiked = ref(false)
const chunkCount = ref(null)
const indexStatus = ref('pending')
const indexContentDialogVisible = ref(false)
const loadingIndexContent = ref(false)
const indexChunks = ref([])
let pollInterval = null

// 分享弹窗相关
const shareDialogVisible = ref(false)
const shareUrl = ref('')
const copying = ref(false)
const copySuccess = ref(false)

// 权限设置相关
const permissionsDialogVisible = ref(false)
const permissions = ref([])
const teams = ref([])
const users = ref([])
const activePermissionTab = ref('team')
const selectedTeam = ref(null)
const selectedUser = ref(null)
const teamActions = ref(['view'])
const userActions = ref(['view'])
const savingPermissions = ref(false)
const pendingPermissions = ref([])

const fetchDocument = async () => {
  try {
    document.value = await documentStore.fetchDocument(route.params.id)
    // 获取索引状态和chunk数量
    fetchIndexStatus()
  } catch (error) {
    ElMessage.error('获取文档失败')
  }
}

const fetchIndexStatus = async () => {
  try {
    const response = await fetch(`/api/v1/documents/${route.params.id}/index-status`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    })
    if (response.ok) {
      const data = await response.json()
      chunkCount.value = data.chunk_count
      indexStatus.value = data.status || 'completed'
    }
  } catch (error) {
    console.error('获取索引状态失败:', error)
  }
}

const startIndexStatusPolling = () => {
  // 立即获取一次索引状态
  fetchIndexStatus()
  
  // 轮询索引状态
  pollInterval = setInterval(async () => {
    if (indexStatus.value !== 'completed' && indexStatus.value !== 'failed') {
      await fetchIndexStatus()
    }
  }, 3000)
}

const getIndexStatusClass = () => {
  return `status-${indexStatus.value}`
}

const getIndexStatusText = () => {
  const texts = {
    processing: '索引生成中...',
    completed: '已完成',
    pending: '等待中',
    failed: '生成失败'
  }
  return texts[indexStatus.value] || indexStatus.value
}

const fetchComments = async () => {
  try {
    comments.value = await commentAPI.getComments(route.params.id)
  } catch (error) {
    console.error('Failed to fetch comments:', error)
  }
}

// 权限相关方法
const openPermissionsDialog = async () => {
  permissionsDialogVisible.value = true
  await Promise.all([
    fetchPermissions(),
    fetchTeams(),
    fetchUsers()
  ])
}

const fetchPermissions = async () => {
  try {
    const response = await fetch(`/api/v1/documents/${route.params.id}/permissions`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    })
    if (response.ok) {
      permissions.value = await response.json()
      pendingPermissions.value = JSON.parse(JSON.stringify(permissions.value))
    }
  } catch (error) {
    console.error('获取权限失败:', error)
  }
}

const fetchTeams = async () => {
  try {
    const response = await fetch('/api/v1/teams', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    })
    if (response.ok) {
      teams.value = await response.json()
    }
  } catch (error) {
    console.error('获取团队失败:', error)
  }
}

const fetchUsers = async () => {
  try {
    const response = await fetch('/api/v1/users', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    })
    if (response.ok) {
      users.value = await response.json()
    }
  } catch (error) {
    console.error('获取用户失败:', error)
  }
}

const addTeamPermission = () => {
  if (!selectedTeam.value) {
    ElMessage.warning('请选择团队')
    return
  }
  if (teamActions.value.length === 0) {
    ElMessage.warning('请选择至少一个操作权限')
    return
  }
  
  const team = teams.value.find(t => t.id === selectedTeam.value)
  teamActions.value.forEach(action => {
    pendingPermissions.value.push({
      permission_type: 'team',
      target_id: selectedTeam.value,
      action: action,
      target_name: team?.name || '',
      is_new: true
    })
  })
  
  selectedTeam.value = null
  teamActions.value = ['view']
}

const addUserPermission = () => {
  if (!selectedUser.value) {
    ElMessage.warning('请选择用户')
    return
  }
  if (userActions.value.length === 0) {
    ElMessage.warning('请选择至少一个操作权限')
    return
  }
  
  const user = users.value.find(u => u.id === selectedUser.value)
  userActions.value.forEach(action => {
    pendingPermissions.value.push({
      permission_type: 'user',
      target_id: selectedUser.value,
      action: action,
      target_name: user?.username || '',
      is_new: true
    })
  })
  
  selectedUser.value = null
  userActions.value = ['view']
}

const removePermission = (permissionId) => {
  const index = pendingPermissions.value.findIndex(p => p.id === permissionId || p.temp_id)
  if (index !== -1) {
    pendingPermissions.value.splice(index, 1)
  }
}

const savePermissions = async () => {
  savingPermissions.value = true
  try {
    // 获取所有新权限
    const newPermissions = pendingPermissions.value
      .filter(p => p.is_new)
      .map(p => ({
        permission_type: p.permission_type,
        target_id: p.target_id,
        action: p.action
      }))
    
    // 批量更新权限
    const response = await fetch(`/api/v1/documents/${route.params.id}/permissions`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ permissions: newPermissions })
    })
    
    if (response.ok) {
      ElMessage.success('权限保存成功')
      await fetchPermissions()
      permissionsDialogVisible.value = false
    } else {
      ElMessage.error('权限保存失败')
    }
  } catch (error) {
    ElMessage.error('权限保存失败')
    console.error(error)
  } finally {
    savingPermissions.value = false
  }
}

const getPermissionLabel = (perm) => {
  const typeLabel = getPermissionTypeLabel(perm.permission_type)
  const actionLabel = getActionLabel(perm.action)
  return `${perm.target_name || perm.target_id} (${typeLabel}-${actionLabel})`
}

const getPermissionTypeLabel = (type) => {
  const labels = { team: '团队', user: '个人' }
  return labels[type] || type
}

const getActionLabel = (action) => {
  const labels = { view: '查看', edit: '编辑', delete: '删除' }
  return labels[action] || action
}

const submitComment = async () => {
  if (!newComment.value.trim()) return
  submitting.value = true
  try {
    await commentAPI.createComment(route.params.id, {
      content: newComment.value,
      document_id: parseInt(route.params.id)
    })
    newComment.value = ''
    ElMessage.success('评论成功')
    fetchComments()
  } catch (error) {
    ElMessage.error('评论失败')
  } finally {
    submitting.value = false
  }
}

const handleFavorite = async () => {
  try {
    const res = await documentStore.toggleFavorite(route.params.id)
    isFavorited.value = res.is_favorited
    ElMessage.success(res.message)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleLike = async () => {
  try {
    const res = await documentStore.toggleLike(route.params.id)
    isLiked.value = res.is_liked
    if (document.value) {
      document.value.like_count += res.is_liked ? 1 : -1
    }
    ElMessage.success(res.message)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleShare = async () => {
  shareDialogVisible.value = true
  shareUrl.value = ''
  copySuccess.value = false
  
  try {
    const res = await documentStore.shareDocument(route.params.id)
    shareUrl.value = res.share_url
  } catch (error) {
    ElMessage.error('分享失败')
    shareDialogVisible.value = false
  }
}

const copyShareUrl = async () => {
  copying.value = true
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    copySuccess.value = true
    setTimeout(() => {
      copySuccess.value = false
    }, 2000)
  } catch (error) {
    ElMessage.error('复制失败')
  } finally {
    copying.value = false
  }
}

onMounted(async () => {
  await fetchDocument()
  fetchComments()
  startIndexStatusPolling()
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<style scoped>
.document-detail {
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 64px);
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.detail-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.header-buttons {
  display: flex;
  gap: 12px;
}

.header-buttons .el-button {
  display: flex;
  align-items: center;
  gap: 6px;
}

.document-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  color: #6b7280;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.meta-item .el-icon {
  font-size: 16px;
  color: #9ca3af;
}

.index-status-section {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  border: 1px solid #e5e7eb;
}

.index-status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
  transition: all 0.2s;
}

.index-status-header:hover {
  background: #f3f4f6;
  margin: -4px -8px;
  padding: 4px 8px;
  border-radius: 6px;
}

.index-status-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.index-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-processing {
  background-color: #f0f5ff;
  color: #409eff;
}

.status-completed {
  background-color: #f0f9eb;
  color: #67c23a;
}

.status-pending {
  background-color: #fefce8;
  color: #e6a23c;
}

.status-failed {
  background-color: #fef0f0;
  color: #f56c6c;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.view-detail-icon {
  color: #9ca3af;
  font-size: 14px;
}

.index-chunk-count {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
  font-size: 13px;
  color: #6b7280;
}

.index-chunk-count .el-icon {
  font-size: 14px;
}

.document-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.document-content {
  padding: 20px 0;
  line-height: 1.8;
  font-size: 15px;
  color: #374151;
}

.document-content :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}

/* 权限设置面板 */
.permissions-section h3 {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  color: #1f2937;
}

.permissions-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.permissions-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.permission-tag {
  margin-right: 4px;
}

.no-permissions {
  color: #909399;
  font-size: 14px;
}

.permission-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
}

.permission-row .el-select {
  flex: 0 0 200px;
}

.permission-row .el-checkbox-group {
  display: flex;
  gap: 16px;
}

.current-permissions {
  margin-top: 16px;
}

.current-permissions h4 {
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.no-permissions-table {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.comments-section h3 {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  color: #1f2937;
}

.comment-form {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-submit {
  align-self: flex-end;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  border-radius: 8px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comment-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.comment-content-wrapper {
  flex: 1;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-header strong {
  font-size: 15px;
  color: #1f2937;
}

.comment-header span {
  font-size: 13px;
  color: #9ca3af;
}

.comment-content {
  color: #374151;
  font-size: 14px;
  line-height: 1.6;
}

/* 分享弹窗样式 */
.share-dialog :deep(.el-dialog__header) {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.share-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.share-content {
  padding: 10px 0;
}

.share-content p {
  margin-bottom: 16px;
  color: #374151;
  font-size: 15px;
}

.share-input {
  margin-bottom: 20px;
}

.share-actions {
  display: flex;
  justify-content: center;
}

.btn-copy {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 32px;
  border-radius: 8px;
}

.share-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  gap: 16px;
  color: #6b7280;
}

.loading-icon {
  animation: spin 1s linear infinite;
  color: #409eff;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 索引内容弹窗样式 */
.index-content-dialog :deep(.el-dialog__header) {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.index-content-dialog :deep(.el-dialog__body) {
  padding: 24px;
  max-height: 600px;
  overflow-y: auto;
}

.index-content-container {
  min-height: 200px;
}

.no-chunks {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
  color: #9ca3af;
}

.no-chunks .el-icon {
  color: #d1d5db;
}

.no-chunks p {
  margin: 0;
  font-size: 14px;
}

.chunk-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chunk-item {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.chunk-number {
  font-weight: 600;
  font-size: 14px;
  color: #374151;
}

.chunk-distance {
  font-size: 12px;
  color: #9ca3af;
}

.chunk-content {
  font-size: 14px;
  line-height: 1.8;
  color: #4b5563;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
