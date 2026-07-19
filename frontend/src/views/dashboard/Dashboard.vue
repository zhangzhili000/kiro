<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <template #header>文档总数</template>
          <div class="stat-value">{{ stats.documentCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>本周新增</template>
          <div class="stat-value">{{ stats.weeklyNew }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>总浏览量</template>
          <div class="stat-value">{{ stats.totalViews }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>总收藏数</template>
          <div class="stat-value">{{ stats.totalFavorites }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-4">
      <el-col :span="16">
        <el-card>
          <template #header>最近文档</template>
          <el-table :data="recentDocuments" style="width: 100%">
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="author_name" label="作者" width="120" />
            <el-table-column prop="updated_at" label="更新时间" width="180" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>快捷操作</template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/documents/new')">新建文档</el-button>
            <el-button @click="$router.push('/knowledge')">文档列表</el-button>
            <el-button @click="$router.push({ path: '/knowledge', query: { tab: 'categories' } })">分类管理</el-button>
            <el-button @click="$router.push({ path: '/knowledge', query: { tab: 'tags' } })">标签管理</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { documentAPI } from '@open/api'

const stats = ref({
  documentCount: 0,
  weeklyNew: 0,
  totalViews: 0,
  totalFavorites: 0
})

const recentDocuments = ref([])

onMounted(async () => {
  try {
    const documents = await documentAPI.getDocuments({ page: 1, page_size: 5 })
    recentDocuments.value = documents
    stats.value.documentCount = documents.length
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
})
</script>

<style scoped>
.dashboard {
}
.stat-value {
  font-size: 32px;
  font-weight: bold;
  text-align: center;
  color: #409eff;
}
.mt-4 {
  margin-top: 20px;
}
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.quick-actions .el-button {
  width: 100%;
}
</style>
