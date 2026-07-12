<template>
  <div class="document-list">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">文档列表</h1>
        <p class="page-desc">管理您的知识库文档</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="$router.push('/documents/new')" class="btn-create">
          <el-icon><DocumentAdd /></el-icon>
          新建文档
        </el-button>
        <el-button @click="$router.push('/documents/trash')" class="btn-trash">
          <el-icon><Delete /></el-icon>
          回收站
        </el-button>
      </div>
    </div>

    <div class="document-grid" v-loading="loading">
      <div class="document-card" v-for="doc in documents" :key="doc.id" @click="$router.push(`/documents/${doc.id}`)">
        <div class="card-header">
          <div class="doc-icon">
            <el-icon :size="28"><Document /></el-icon>
          </div>
          <div class="doc-badges">
            <el-tag :type="permissionType(doc.permission)" size="small">{{ permissionText(doc.permission) }}</el-tag>
            <el-tag v-if="getChunkCount(doc.id)" size="small" type="info">{{ getChunkCount(doc.id) }} Chunk</el-tag>
          </div>
        </div>
        
        <div class="card-body">
              <el-tooltip :content="doc.title" placement="top" :disabled="doc.title.length <= 20">
                <h3 class="doc-title">{{ doc.title }}</h3>
              </el-tooltip>
              <p class="doc-info">
                <span class="info-item">
                  <el-icon><User /></el-icon>
                  {{ doc.author_name || '未知' }}
                </span>
                <span class="info-item" v-if="doc.category_name">
                  <el-icon><Folder /></el-icon>
                  {{ doc.category_name }}
                </span>
              </p>
              <p class="doc-update-time">
                <el-icon><Calendar /></el-icon>
                更新时间：{{ doc.updated_at }}
              </p>
            </div>

        <div class="card-footer">
          <div class="doc-stats">
            <span class="stat-item">
              <el-icon><View /></el-icon>
              {{ doc.view_count || 0 }}
            </span>
            <span class="stat-item">
              <el-icon><Star /></el-icon>
              {{ doc.like_count || 0 }}
            </span>
            <span class="stat-item">
              <el-icon><ChatDotRound /></el-icon>
              {{ doc.comment_count || 0 }}
            </span>
          </div>
          <div class="doc-actions" @click.stop>
            <el-button size="small" @click="$router.push(`/documents/${doc.id}/edit`)" class="btn-edit">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(doc.id)" class="btn-delete">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="documents.length === 0 && !loading" class="empty-state">
      <el-icon :size="80" class="empty-icon"><Document /></el-icon>
      <h3 class="empty-title">暂无文档</h3>
      <p class="empty-desc">点击"新建文档"开始创建您的第一个文档</p>
    </div>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchDocuments"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDocumentStore } from '@/stores/document'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Calendar, 
  Document, 
  DocumentAdd, 
  Delete, 
  User, 
  Folder, 
  View, 
  Star, 
  ChatDotRound, 
  Edit
} from '@element-plus/icons-vue'

const documentStore = useDocumentStore()
const documents = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const fetchDocuments = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    const res = await documentStore.fetchDocuments(params)
    documents.value = res
    total.value = res.length
  } catch (error) {
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

const getChunkCount = (documentId) => {
  // 暂时不显示Chunk数，因为不再轮询索引状态
  return null
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文档吗？', '提示', {
      type: 'warning'
    })
    await documentStore.deleteDocument(id)
    ElMessage.success('删除成功')
    fetchDocuments()
  } catch (error) {
    if (error !== 'cancel') { ElMessage.error('删除失败') }
  }
}

const permissionType = (permission) => {
  const types = { public: 'success', private: 'info' }
  return types[permission] || 'info'
}

const permissionText = (permission) => {
  const texts = { public: '公开', private: '私有' }
  return texts[permission] || permission
}

onMounted(fetchDocuments)
</script>

<style scoped>
.document-list {
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 64px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.page-desc {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.header-right {
  display: flex;
  gap: 12px;
}

.btn-create,
.btn-trash {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  font-weight: 500;
  border-radius: 8px;
}

.document-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.document-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  cursor: pointer;
  overflow: hidden;
  border: 1px solid transparent;
}

.document-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.doc-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: white;
}

.doc-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.card-body {
  padding: 20px;
  padding-top: 12px;
}

.doc-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #6b7280;
}

.info-item .el-icon {
  font-size: 14px;
}

.doc-update-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #9ca3af;
  margin-top: 12px;
}

.doc-update-time .el-icon {
  font-size: 14px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid #f3f4f6;
  background: #fafafa;
}

.doc-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #6b7280;
}

.stat-item .el-icon {
  font-size: 14px;
}

.doc-actions {
  display: flex;
  gap: 8px;
}

.btn-edit,
.btn-delete {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.empty-icon {
  color: #d1d5db;
  margin-bottom: 20px;
}

.empty-title {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.empty-desc {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  background: white;
  padding: 10px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
</style>
