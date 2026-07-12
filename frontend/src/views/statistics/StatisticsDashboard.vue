<template>
  <div class="statistics-dashboard">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>知识库统计分析</span>
          <div>
            <el-button @click="fetchOverview">刷新</el-button>
            <el-button type="primary" @click="handleExport">导出报表</el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="概览" name="overview">
          <el-row :gutter="20" v-loading="loading">
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-value">{{ overview.total_documents }}</div>
                <div class="stat-label">文档总数</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-value">{{ overview.total_categories }}</div>
                <div class="stat-label">分类总数</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-value">{{ overview.total_users }}</div>
                <div class="stat-label">用户总数</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-value">{{ overview.total_views }}</div>
                <div class="stat-label">总浏览量</div>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="20" class="mt-4">
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-value">{{ overview.new_documents_this_month }}</div>
                <div class="stat-label">本月新增文档</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-value">{{ overview.total_likes }}</div>
                <div class="stat-label">总点赞数</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-value">{{ overview.total_comments }}</div>
                <div class="stat-label">总评论数</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-value">{{ overview.total_tags }}</div>
                <div class="stat-label">标签总数</div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="文档统计" name="documents">
          <el-row :gutter="20" v-loading="loading">
            <el-col :span="12">
              <el-card>
                <template #header>按分类统计</template>
                <el-table :data="documentStats.by_category" style="width: 100%">
                  <el-table-column prop="category_name" label="分类名称" />
                  <el-table-column prop="count" label="文档数量" width="100" />
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card>
                <template #header>按权限统计</template>
                <el-table :data="documentStats.by_permission" style="width: 100%">
                  <el-table-column prop="permission" label="权限">
                    <template #default="{ row }">
                      {{ permissionText(row.permission) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="count" label="数量" width="100" />
                </el-table>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="20" class="mt-4">
            <el-col :span="12">
              <el-card>
                <template #header>按状态统计</template>
                <el-table :data="documentStats.by_status" style="width: 100%">
                  <el-table-column prop="status" label="状态">
                    <template #default="{ row }">
                      {{ statusText(row.status) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="count" label="数量" width="100" />
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card>
                <template #header>近7天趋势</template>
                <el-table :data="documentStats.weekly_trend" style="width: 100%">
                  <el-table-column prop="date" label="日期" width="120" />
                  <el-table-column prop="count" label="新增文档" width="100" />
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="用户活跃度" name="users">
          <el-row :gutter="20" v-loading="loading">
            <el-col :span="12">
              <el-card>
                <template #header>活跃度概览</template>
                <div class="activity-item">
                  <span>本月活跃用户数：</span>
                  <el-tag type="success">{{ userActivity.active_users_this_month }}</el-tag>
                </div>
                <div class="activity-item">
                  <span>今日活跃用户数：</span>
                  <el-tag type="primary">{{ userActivity.today_active_users }}</el-tag>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card>
                <template #header>贡献排行榜</template>
                <el-table :data="userActivity.top_contributors" style="width: 100%">
                  <el-table-column prop="username" label="用户名" />
                  <el-table-column prop="document_count" label="文档数" width="80" />
                  <el-table-column prop="total_views" label="总浏览" width="80" />
                  <el-table-column prop="total_likes" label="总点赞" width="80" />
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="热门文档" name="popular">
          <div class="period-selector">
            <el-radio-group v-model="popularPeriod" @change="fetchPopularDocuments">
              <el-radio-button value="day">今日</el-radio-button>
              <el-radio-button value="week">本周</el-radio-button>
              <el-radio-button value="month">本月</el-radio-button>
              <el-radio-button value="all">全部</el-radio-button>
            </el-radio-group>
          </div>
          <el-table :data="popularDocuments" style="width: 100%" v-loading="loading">
            <el-table-column prop="rank" label="排名" width="80" />
            <el-table-column prop="title" label="标题">
              <template #default="{ row }">
                <router-link :to="`/documents/${row.id}`" class="link">{{ row.title }}</router-link>
              </template>
            </el-table-column>
            <el-table-column prop="view_count" label="浏览" width="80" />
            <el-table-column prop="like_count" label="点赞" width="80" />
            <el-table-column prop="comment_count" label="评论" width="80" />
            <el-table-column prop="score" label="综合评分" width="100" />
            <el-table-column prop="updated_at" label="更新时间" width="180" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="用户贡献度" name="contribution">
          <el-table :data="userContributions" style="width: 100%" v-loading="loading">
            <el-table-column prop="rank" label="排名" width="80" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="document_count" label="文档数" width="80" />
            <el-table-column prop="total_views" label="总浏览" width="100" />
            <el-table-column prop="total_likes" label="总点赞" width="100" />
            <el-table-column prop="contribution_score" label="贡献分" width="100" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="exportDialogVisible" title="导出报表" width="400px">
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="报表类型">
          <el-select v-model="exportForm.type">
            <el-option label="概览报表" value="overview" />
            <el-option label="文档统计" value="documents" />
            <el-option label="用户统计" value="users" />
            <el-option label="热门文档" value="popular" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exportDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmExport">导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const activeTab = ref('overview')
const popularPeriod = ref('month')
const loading = ref(false)

const overview = ref({
  total_documents: 0,
  total_categories: 0,
  total_tags: 0,
  total_users: 0,
  new_documents_this_month: 0,
  total_views: 0,
  total_likes: 0,
  total_comments: 0
})

const documentStats = ref({
  by_category: [],
  by_permission: [],
  by_status: [],
  weekly_trend: []
})

const userActivity = ref({
  active_users_this_month: 0,
  today_active_users: 0,
  top_contributors: []
})

const popularDocuments = ref([])
const userContributions = ref([])

const exportDialogVisible = ref(false)
const exportForm = ref({
  type: 'overview'
})

const permissionText = (permission) => {
  const texts = { public: '公开', private: '私有' }
  return texts[permission] || permission
}

const statusText = (status) => {
  const texts = { draft: '草稿', pending_review: '待审核', published: '已发布', rejected: '已拒绝' }
  return texts[status] || status
}

const fetchOverview = async () => {
  loading.value = true
  try {
    overview.value = await request.get('/statistics/overview')
  } catch (error) {
    ElMessage.error('获取概览数据失败')
  } finally {
    loading.value = false
  }
}

const fetchDocumentStats = async () => {
  loading.value = true
  try {
    const result = await request.get('/statistics/documents')
    // 确保数据结构正确
    documentStats.value = {
      by_category: Array.isArray(result?.by_category) ? result.by_category : [],
      by_permission: Array.isArray(result?.by_permission) ? result.by_permission : [],
      by_status: Array.isArray(result?.by_status) ? result.by_status : [],
      weekly_trend: Array.isArray(result?.weekly_trend) ? result.weekly_trend : []
    }
  } catch (error) {
    ElMessage.error('获取文档统计失败')
    documentStats.value = {
      by_category: [],
      by_permission: [],
      by_status: [],
      weekly_trend: []
    }
  } finally {
    loading.value = false
  }
}

const fetchUserActivity = async () => {
  loading.value = true
  try {
    const result = await request.get('/statistics/users/activity')
    // 确保 top_contributors 是数组
    userActivity.value = {
      ...result,
      top_contributors: Array.isArray(result?.top_contributors) ? result.top_contributors : []
    }
  } catch (error) {
    ElMessage.error('获取用户活跃度失败')
    userActivity.value = {
      active_users_this_month: 0,
      top_contributors: []
    }
  } finally {
    loading.value = false
  }
}

const fetchPopularDocuments = async () => {
  loading.value = true
  try {
    const result = await request.get('/statistics/documents/popular', {
      params: { period: popularPeriod.value }
    })
    // 确保返回的是数组
    popularDocuments.value = Array.isArray(result) ? result : []
  } catch (error) {
    ElMessage.error('获取热门文档失败')
    popularDocuments.value = []
  } finally {
    loading.value = false
  }
}

const fetchUserContributions = async () => {
  loading.value = true
  try {
    const result = await request.get('/statistics/users/contribution')
    // 确保返回的是数组
    userContributions.value = Array.isArray(result) ? result : []
  } catch (error) {
    ElMessage.error('获取用户贡献度失败')
    userContributions.value = []
  } finally {
    loading.value = false
  }
}

const handleExport = () => {
  exportDialogVisible.value = true
}

const handleConfirmExport = async () => {
  try {
    const res = await request.get('/statistics/export', {
      params: { type: exportForm.value.type },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${exportForm.value.type}_statistics.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    ElMessage.success('导出成功')
    exportDialogVisible.value = false
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  fetchOverview()
})
</script>

<style scoped>
.statistics-dashboard {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stat-card {
  text-align: center;
}
.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}
.stat-label {
  font-size: 14px;
  color: #666;
}
.mt-4 {
  margin-top: 20px;
}
.activity-item {
  margin-bottom: 15px;
  font-size: 16px;
}
.period-selector {
  margin-bottom: 20px;
}
.link {
  color: #409eff;
  text-decoration: none;
}
.link:hover {
  text-decoration: underline;
}
</style>