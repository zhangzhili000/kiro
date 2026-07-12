<template>
  <div class="search-result">
    <el-card>
      <template #header>
        <div class="search-box">
          <el-input
            v-model="keyword"
            placeholder="搜索文档..."
            @keyup.enter="handleSearch"
            class="search-input"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
          <div class="search-actions">
            <el-button @click="showAdvanced = !showAdvanced">
              {{ showAdvanced ? '收起' : '高级搜索' }}
            </el-button>
          </div>
        </div>

        <el-collapse-transition>
          <div v-show="showAdvanced" class="advanced-search">
            <el-form :model="advancedFilter" label-width="100px">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="搜索范围">
                    <el-radio-group v-model="advancedFilter.search_scope">
                      <el-radio value="all">全部</el-radio>
                      <el-radio value="title">仅标题</el-radio>
                      <el-radio value="content">仅内容</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="权限">
                    <el-select v-model="advancedFilter.permission" placeholder="选择权限" clearable>
                      <el-option label="公开" value="public" />
                      <el-option label="私有" value="private" />
                    
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="状态">
                    <el-select v-model="advancedFilter.status" placeholder="选择状态" clearable>
                      <el-option label="草稿" value="draft" />
                      <el-option label="待审核" value="pending_review" />
                      <el-option label="已发布" value="published" />
                      <el-option label="已拒绝" value="rejected" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="排序">
                    <el-select v-model="advancedFilter.sort_by">
                      <el-option label="更新时间" value="updated_at" />
                      <el-option label="创建时间" value="created_at" />
                      <el-option label="浏览量" value="view_count" />
                      <el-option label="点赞数" value="like_count" />
                    </el-select>
                    <el-select v-model="advancedFilter.sort_order" style="width: 80px; margin-left: 10px;">
                      <el-option label="降序" value="desc" />
                      <el-option label="升序" value="asc" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="浏览量范围">
                    <el-input-number v-model="advancedFilter.min_view_count" :min="0" placeholder="最小" />
                    <span style="margin: 0 10px;">-</span>
                    <el-input-number v-model="advancedFilter.max_view_count" :min="0" placeholder="最大" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="点赞数范围">
                    <el-input-number v-model="advancedFilter.min_like_count" :min="0" placeholder="最小" />
                    <span style="margin: 0 10px;">-</span>
                    <el-input-number v-model="advancedFilter.max_like_count" :min="0" placeholder="最大" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="创建时间">
                    <el-date-picker
                      v-model="createdTimeRange"
                      type="daterange"
                      range-separator="至"
                      start-placeholder="开始日期"
                      end-placeholder="结束日期"
                      @change="handleCreatedTimeChange"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="更新时间">
                    <el-date-picker
                      v-model="updatedTimeRange"
                      type="daterange"
                      range-separator="至"
                      start-placeholder="开始日期"
                      end-placeholder="结束日期"
                      @change="handleUpdatedTimeChange"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </el-collapse-transition>

        <div class="search-filters">
          <el-select v-model="filter.category_id" placeholder="分类筛选" clearable @change="handleSearch">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
          <el-button @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </template>

      <div class="result-count" v-if="advancedResults.total !== undefined">
        找到 {{ advancedResults.total }} 个结果
      </div>
      <div class="result-count" v-else>
        找到 {{ results.length }} 个结果
      </div>

      <div class="result-list">
        <div v-for="doc in displayResults" :key="doc.id" class="result-item">
          <router-link :to="`/documents/${doc.id}`" class="title">{{ doc.title }}</router-link>
          <div class="content-preview">{{ doc.content }}</div>
          <div class="meta">
            <span>作者ID：{{ doc.author_id }}</span>
            <span v-if="doc.category_id">分类ID：{{ doc.category_id }}</span>
            <span v-if="doc.status">状态：{{ statusText(doc.status) }}</span>
            <span>浏览：{{ doc.view_count }}</span>
            <span>更新时间：{{ doc.updated_at }}</span>
          </div>
        </div>
        <el-empty v-if="displayResults.length === 0 && searched" description="未找到相关文档" />
      </div>

      <el-pagination
        v-if="advancedResults.total !== undefined"
        v-model:current-page="advancedPage"
        :page-size="advancedPageSize"
        :total="advancedResults.total"
        layout="total, prev, pager, next"
        @current-change="handleAdvancedSearch"
        class="mt-4"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSearchStore } from '@/stores/search'
import { useCategoryStore } from '@/stores/category'
import { Search } from '@element-plus/icons-vue'
import request from '@/api/request'

const route = useRoute()
const searchStore = useSearchStore()
const categoryStore = useCategoryStore()

const keyword = ref('')
const results = ref([])
const advancedResults = ref({ total: 0, results: [] })
const searched = ref(false)
const showAdvanced = ref(false)
const categories = ref([])

const advancedPage = ref(1)
const advancedPageSize = ref(20)

const createdTimeRange = ref([])
const updatedTimeRange = ref([])

const filter = ref({
  category_id: null,
  sort_by: 'relevance'
})

const advancedFilter = ref({
  keywords: '',
  title_only: false,
  content_only: false,
  category_ids: [],
  tag_ids: [],
  author_ids: [],
  permission: '',
  status: '',
  min_view_count: null,
  max_view_count: null,
  min_like_count: null,
  max_like_count: null,
  created_after: '',
  created_before: '',
  updated_after: '',
  updated_before: '',
  sort_by: 'updated_at',
  sort_order: 'desc'
})

const displayResults = computed(() => {
  return showAdvanced.value ? advancedResults.value.results : results.value
})

const statusText = (status) => {
  const texts = { draft: '草稿', pending_review: '待审核', published: '已发布', rejected: '已拒绝' }
  return texts[status] || status
}

const handleCreatedTimeChange = (dates) => {
  if (dates && dates.length === 2) {
    advancedFilter.value.created_after = dates[0].toISOString()
    advancedFilter.value.created_before = dates[1].toISOString()
  } else {
    advancedFilter.value.created_after = ''
    advancedFilter.value.created_before = ''
  }
}

const handleUpdatedTimeChange = (dates) => {
  if (dates && dates.length === 2) {
    advancedFilter.value.updated_after = dates[0].toISOString()
    advancedFilter.value.updated_before = dates[1].toISOString()
  } else {
    advancedFilter.value.updated_after = ''
    advancedFilter.value.updated_before = ''
  }
}

const handleSearch = async () => {
  if (!keyword.value.trim()) return
  searched.value = true
  
  if (showAdvanced.value) {
    await handleAdvancedSearch()
  } else {
    await searchStore.search({
      q: keyword.value,
      ...filter.value
    })
    results.value = searchStore.results
  }
}

const handleAdvancedSearch = async () => {
  const params = {
    keywords: keyword.value,
    title_only: advancedFilter.value.search_scope === 'title',
    content_only: advancedFilter.value.search_scope === 'content',
    category_ids: filter.value.category_id ? [filter.value.category_id] : [],
    permission: advancedFilter.value.permission || undefined,
    status: advancedFilter.value.status || undefined,
    min_view_count: advancedFilter.value.min_view_count || undefined,
    max_view_count: advancedFilter.value.max_view_count || undefined,
    min_like_count: advancedFilter.value.min_like_count || undefined,
    max_like_count: advancedFilter.value.max_like_count || undefined,
    created_after: advancedFilter.value.created_after || undefined,
    created_before: advancedFilter.value.created_before || undefined,
    updated_after: advancedFilter.value.updated_after || undefined,
    updated_before: advancedFilter.value.updated_before || undefined,
    sort_by: advancedFilter.value.sort_by,
    sort_order: advancedFilter.value.sort_order,
    page: advancedPage.value,
    page_size: advancedPageSize.value
  }

  try {
    advancedResults.value = await request.post('/search/advanced', params)
  } catch (error) {
    console.error('高级搜索失败', error)
  }
}

const handleReset = () => {
  keyword.value = ''
  filter.value = {
    category_id: null,
    sort_by: 'relevance'
  }
  advancedFilter.value = {
    keywords: '',
    title_only: false,
    content_only: false,
    category_ids: [],
    tag_ids: [],
    author_ids: [],
    permission: '',
    status: '',
    min_view_count: null,
    max_view_count: null,
    min_like_count: null,
    max_like_count: null,
    created_after: '',
    created_before: '',
    updated_after: '',
    updated_before: '',
    sort_by: 'updated_at',
    sort_order: 'desc'
  }
  createdTimeRange.value = []
  updatedTimeRange.value = []
  results.value = []
  advancedResults.value = { total: 0, results: [] }
  searched.value = false
}

onMounted(async () => {
  await categoryStore.fetchCategories()
  categories.value = categoryStore.categories

  if (route.query.q) {
    keyword.value = route.query.q
    handleSearch()
  }
})
</script>

<style scoped>
.search-result {
}
.search-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.search-input {
  flex: 1;
  max-width: 600px;
}
.search-actions {
  display: flex;
  gap: 10px;
}
.advanced-search {
  margin-bottom: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}
.search-filters {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}
.result-count {
  margin-bottom: 15px;
  color: #666;
}
.result-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.result-item {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}
.title {
  font-size: 18px;
  color: #409eff;
  text-decoration: none;
  display: block;
  margin-bottom: 8px;
}
.title:hover {
  text-decoration: underline;
}
.content-preview {
  color: #666;
  margin-bottom: 8px;
  font-size: 14px;
}
.meta {
  display: flex;
  gap: 15px;
  color: #666;
  font-size: 14px;
}
.mt-4 {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
