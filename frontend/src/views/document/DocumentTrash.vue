<template>
  <div class="document-trash">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>回收站</span>
          <el-button @click="$router.push('/knowledge')">返回文档列表</el-button>
        </div>
      </template>

      <el-table :data="documents" style="width: 100%" v-loading="loading">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="author_name" label="作者" width="120" />
        <el-table-column prop="deleted_at" label="删除时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleRestore(row.id)">恢复</el-button>
            <el-button size="small" type="danger" @click="handlePermanentDelete(row.id)">永久删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDocumentStore } from '@/stores/document'
import { ElMessage, ElMessageBox } from 'element-plus'

const documentStore = useDocumentStore()
const documents = ref([])
const loading = ref(false)

const fetchTrash = async () => {
  loading.value = true
  try {
    await documentStore.fetchTrash()
    documents.value = documentStore.trashDocuments
  } catch (error) {
    ElMessage.error('获取回收站失败')
  } finally {
    loading.value = false
  }
}

const handleRestore = async (id) => {
  try {
    await documentStore.restoreDocument(id)
    ElMessage.success('恢复成功')
    fetchTrash()
  } catch (error) {
    ElMessage.error('恢复失败')
  }
}

const handlePermanentDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要永久删除吗？此操作不可恢复！', '警告', {
      type: 'warning'
    })
    ElMessage.success('永久删除成功')
    fetchTrash()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(fetchTrash)
</script>

<style scoped>
.document-trash {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
