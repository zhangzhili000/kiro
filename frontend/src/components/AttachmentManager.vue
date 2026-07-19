<template>
  <div class="attachment-manager">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>附件管理</span>
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="beforeUpload"
            multiple
            :show-file-list="false"
          >
            <el-button type="primary" :loading="uploading">
              <el-icon><Upload /></el-icon>
              上传附件
            </el-button>
          </el-upload>
        </div>
      </template>

      <el-table :data="attachments" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="original_filename" label="文件名" />
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="content_type" label="类型" width="150" />
        <el-table-column prop="uploaded_by" label="上传者ID" width="100" />
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="handleDownload(row)">下载</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="attachments.length === 0" description="暂无附件" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import request from '@open/api/request'

const props = defineProps({
  documentId: {
    type: Number,
    required: true
  }
})

const attachments = ref([])
const loading = ref(false)
const uploading = ref(false)

const uploadUrl = computed(() => `/api/v1/attachments/${props.documentId}/upload`)
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`
}))

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

const fetchAttachments = async () => {
  loading.value = true
  try {
    attachments.value = await request.get(`/attachments/${props.documentId}`)
  } catch (error) {
    ElMessage.error('获取附件列表失败')
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file) => {
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  uploading.value = true
  return true
}

const handleUploadSuccess = (response) => {
  uploading.value = false
  ElMessage.success('上传成功')
  fetchAttachments()
}

const handleUploadError = (error) => {
  uploading.value = false
  ElMessage.error('上传失败')
}

const handleDownload = async (row) => {
  try {
    const res = await request.get(`/attachments/${row.id}/download`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.download = row.original_filename
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个附件吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/attachments/${row.id}`)
    ElMessage.success('删除成功')
    fetchAttachments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(fetchAttachments)
</script>

<style scoped>
.attachment-manager {
  margin-top: 20px;
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>