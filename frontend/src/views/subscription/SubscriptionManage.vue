<template>
  <div class="subscription-manage">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>我的订阅</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="订阅列表" name="list">
          <el-table :data="subscriptions" style="width: 100%" v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="subscription_type" label="订阅类型" width="120">
              <template #default="{ row }">
                <el-tag>{{ subscriptionTypeText(row.subscription_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="target_id" label="目标ID" width="100" />
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="订阅时间" width="180" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="handleUnsubscribe(row)">取消订阅</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="订阅推送" name="feed">
          <div class="feed-filters">
            <el-button @click="fetchFeed">刷新</el-button>
          </div>
          <el-table :data="feed" style="width: 100%" v-loading="feedLoading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="title" label="标题">
              <template #default="{ row }">
                <router-link :to="`/documents/${row.id}`" class="link">{{ row.title }}</router-link>
              </template>
            </el-table-column>
            <el-table-column prop="author_id" label="作者ID" width="100" />
            <el-table-column prop="category_id" label="分类ID" width="100" />
            <el-table-column prop="updated_at" label="更新时间" width="180" />
          </el-table>
          <el-pagination
            v-model:current-page="feedPage"
            :page-size="feedPageSize"
            :total="feedTotal"
            layout="total, prev, pager, next"
            @current-change="fetchFeed"
            class="mt-4"
          />
        </el-tab-pane>

        <el-tab-pane label="快速订阅" name="quick">
          <el-form :model="quickForm" label-width="100px">
            <el-form-item label="订阅分类">
              <el-select v-model="quickForm.category_id" placeholder="选择分类" clearable>
                <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
              </el-select>
              <el-button type="primary" @click="handleSubscribeCategory" :disabled="!quickForm.category_id">订阅</el-button>
            </el-form-item>
            <el-form-item label="订阅作者">
              <el-input-number v-model="quickForm.author_id" :min="1" placeholder="输入用户ID" />
              <el-button type="primary" @click="handleSubscribeAuthor" :disabled="!quickForm.author_id">订阅</el-button>
            </el-form-item>
            <el-form-item label="订阅文档">
              <el-input-number v-model="quickForm.document_id" :min="1" placeholder="输入文档ID" />
              <el-button type="primary" @click="handleSubscribeDocument" :disabled="!quickForm.document_id">订阅</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('list')
const subscriptions = ref([])
const feed = ref([])
const categories = ref([])
const loading = ref(false)
const feedLoading = ref(false)

const feedPage = ref(1)
const feedPageSize = ref(20)
const feedTotal = ref(0)

const quickForm = ref({
  category_id: null,
  author_id: null,
  document_id: null
})

const subscriptionTypeText = (type) => {
  const texts = { category: '分类', author: '作者', document: '文档' }
  return texts[type] || type
}

const fetchSubscriptions = async () => {
  loading.value = true
  try {
    subscriptions.value = await request.get('/subscriptions')
  } catch (error) {
    ElMessage.error('获取订阅列表失败')
  } finally {
    loading.value = false
  }
}

const fetchFeed = async () => {
  feedLoading.value = true
  try {
    const res = await request.get('/subscriptions/feed', {
      params: {
        page: feedPage.value,
        page_size: feedPageSize.value
      }
    })
    feed.value = res.results
    feedTotal.value = res.total
  } catch (error) {
    ElMessage.error('获取推送内容失败')
  } finally {
    feedLoading.value = false
  }
}

const fetchCategories = async () => {
  try {
    categories.value = await request.get('/categories')
  } catch (error) {
    console.error('获取分类列表失败', error)
  }
}

const handleUnsubscribe = async (row) => {
  try {
    await ElMessageBox.confirm('确定要取消订阅吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/subscriptions/${row.id}`)
    ElMessage.success('取消订阅成功')
    fetchSubscriptions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消订阅失败')
    }
  }
}

const handleSubscribeCategory = async () => {
  try {
    await request.post(`/subscriptions/category/${quickForm.value.category_id}`)
    ElMessage.success('订阅成功')
    fetchSubscriptions()
  } catch (error) {
    ElMessage.error('订阅失败')
  }
}

const handleSubscribeAuthor = async () => {
  try {
    await request.post(`/subscriptions/author/${quickForm.value.author_id}`)
    ElMessage.success('订阅成功')
    fetchSubscriptions()
  } catch (error) {
    ElMessage.error('订阅失败')
  }
}

const handleSubscribeDocument = async () => {
  try {
    await request.post(`/subscriptions/document/${quickForm.value.document_id}`)
    ElMessage.success('订阅成功')
    fetchSubscriptions()
  } catch (error) {
    ElMessage.error('订阅失败')
  }
}

onMounted(() => {
  fetchSubscriptions()
  fetchCategories()
})
</script>

<style scoped>
.subscription-manage {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.feed-filters {
  margin-bottom: 15px;
}
.link {
  color: #409eff;
  text-decoration: none;
}
.link:hover {
  text-decoration: underline;
}
.mt-4 {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>