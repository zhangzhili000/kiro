<template>
  <div class="document-detail">
    <div class="page-header">
      <el-button @click="$router.push('/documents')" class="btn-back">
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
  DataLine
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
