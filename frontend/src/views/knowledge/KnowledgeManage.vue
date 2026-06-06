<template>
  <div class="knowledge-manage">
    <el-tabs v-model="activeTab" class="knowledge-tabs">
      <el-tab-pane label="文档列表" name="documents">
        <DocumentList />
      </el-tab-pane>
      <el-tab-pane label="分类管理" name="categories">
        <CategoryManage />
      </el-tab-pane>
      <el-tab-pane label="标签管理" name="tags">
        <TagManage />
      </el-tab-pane>
      <el-tab-pane label="搜索" name="search">
        <SearchResult />
      </el-tab-pane>
      <el-tab-pane label="知识图谱" name="knowledge-graph">
        <KnowledgeGraph />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DocumentList from '@/views/document/DocumentList.vue'
import CategoryManage from '@/views/category/CategoryManage.vue'
import TagManage from '@/views/tag/TagManage.vue'
import SearchResult from '@/views/search/SearchResult.vue'
import KnowledgeGraph from '@/views/knowledge/KnowledgeGraph.vue'

const route = useRoute()
const router = useRouter()

const activeTab = ref('documents')

watch(() => route.query.tab, (newTab) => {
  if (newTab) {
    activeTab.value = newTab
  }
}, { immediate: true })

watch(activeTab, (newTab) => {
  router.replace({ query: { ...route.query, tab: newTab } })
})
</script>

<style scoped>
.knowledge-manage {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.knowledge-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.knowledge-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.knowledge-tabs :deep(.el-tab-pane) {
  height: 100%;
}
</style>
