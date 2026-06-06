<template>
  <div class="approval-manage">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>审批流程管理</span>
          <div>
            <el-button @click="activeTab = 'pending'">待审批</el-button>
            <el-button @click="activeTab = 'templates'">审批模板</el-button>
            <el-button type="primary" @click="handleCreateTemplate">新建模板</el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="待审批" name="pending">
          <el-table :data="pendingApprovals" style="width: 100%" v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="document_id" label="文档ID" width="80" />
            <el-table-column prop="template_id" label="模板ID" width="80" />
            <el-table-column prop="current_step" label="当前步骤" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)">
                  {{ statusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="submitted_by" label="提交人" width="100" />
            <el-table-column prop="submitted_at" label="提交时间" width="180" />
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" type="success" @click="handleApprove(row)">通过</el-button>
                <el-button size="small" type="danger" @click="handleReject(row)">拒绝</el-button>
                <el-button size="small" @click="handleViewHistory(row)">历史</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="审批模板" name="templates">
          <el-table :data="templates" style="width: 100%" v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="模板名称" width="200" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="handleEditTemplate(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDeleteTemplate(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="templateDialogVisible" :title="isEditTemplate ? '编辑模板' : '新建模板'" width="600px">
      <el-form :model="templateForm" :rules="templateRules" ref="templateFormRef" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="templateForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="流程配置" prop="flow_config">
          <el-input v-model="flowConfigJson" type="textarea" :rows="6" placeholder='{"steps": [{"step": 0, "role": "admin"}]}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitTemplate">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="actionDialogVisible" :title="actionDialogTitle" width="500px">
      <el-form :model="actionForm" label-width="80px">
        <el-form-item label="审批意见">
          <el-input v-model="actionForm.comment" type="textarea" :rows="4" placeholder="请输入审批意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmAction">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="historyDialogVisible" title="审批历史" width="600px">
      <el-timeline>
        <el-timeline-item
          v-for="item in history"
          :key="item.id"
          :timestamp="item.created_at"
          placement="top"
        >
          <el-card>
            <h4>步骤 {{ item.step }}</h4>
            <p>审批人ID: {{ item.approver_id }}</p>
            <p>操作: {{ actionText(item.action) }}</p>
            <p v-if="item.comment">意见: {{ item.comment }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('pending')
const pendingApprovals = ref([])
const templates = ref([])
const history = ref([])
const loading = ref(false)

const templateDialogVisible = ref(false)
const actionDialogVisible = ref(false)
const historyDialogVisible = ref(false)
const isEditTemplate = ref(false)
const actionDialogTitle = ref('')
const templateFormRef = ref(null)

const templateForm = ref({
  name: '',
  description: '',
  flow_config: {}
})

const flowConfigJson = ref('')

const actionForm = ref({
  comment: ''
})

const currentApproval = ref(null)

const templateRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  flow_config: [{ required: true, message: '请输入流程配置', trigger: 'blur' }]
}

const statusType = (status) => {
  const types = { pending: 'warning', approved: 'success', rejected: 'danger', cancelled: 'info' }
  return types[status] || 'info'
}

const statusText = (status) => {
  const texts = { pending: '待审批', approved: '已通过', rejected: '已拒绝', cancelled: '已取消' }
  return texts[status] || status
}

const actionText = (action) => {
  const texts = { approve: '通过', reject: '拒绝', transfer: '转交' }
  return texts[action] || action
}

const fetchPendingApprovals = async () => {
  loading.value = true
  try {
    pendingApprovals.value = await request.get('/approvals/pending')
  } catch (error) {
    ElMessage.error('获取待审批列表失败')
  } finally {
    loading.value = false
  }
}

const fetchTemplates = async () => {
  loading.value = true
  try {
    templates.value = await request.get('/approvals/templates')
  } catch (error) {
    ElMessage.error('获取模板列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreateTemplate = () => {
  isEditTemplate.value = false
  templateForm.value = {
    name: '',
    description: '',
    flow_config: {}
  }
  flowConfigJson.value = ''
  templateDialogVisible.value = true
}

const handleEditTemplate = (row) => {
  isEditTemplate.value = true
  templateForm.value = { ...row }
  flowConfigJson.value = JSON.stringify(row.flow_config, null, 2)
  templateDialogVisible.value = true
}

const handleSubmitTemplate = async () => {
  if (!templateFormRef.value) return
  await templateFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        templateForm.value.flow_config = JSON.parse(flowConfigJson.value)
        if (isEditTemplate.value) {
          await request.put(`/approvals/templates/${templateForm.value.id}`, templateForm.value)
          ElMessage.success('更新成功')
        } else {
          await request.post('/approvals/templates', templateForm.value)
          ElMessage.success('创建成功')
        }
        templateDialogVisible.value = false
        fetchTemplates()
      } catch (error) {
        ElMessage.error(isEditTemplate.value ? '更新失败' : '创建失败')
      }
    }
  })
}

const handleDeleteTemplate = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个模板吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/approvals/templates/${id}`)
    ElMessage.success('删除成功')
    fetchTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleApprove = (row) => {
  currentApproval.value = row
  actionDialogTitle.value = '审批通过'
  actionForm.value.comment = ''
  actionDialogVisible.value = true
}

const handleReject = (row) => {
  currentApproval.value = row
  actionDialogTitle.value = '拒绝审批'
  actionForm.value.comment = ''
  actionDialogVisible.value = true
}

const handleConfirmAction = async () => {
  try {
    const action = actionDialogTitle.value === '审批通过' ? 'approve' : 'reject'
    await request.post(`/approvals/${currentApproval.value.id}/${action}`, actionForm.value)
    ElMessage.success(action === 'approve' ? '审批通过' : '已拒绝')
    actionDialogVisible.value = false
    fetchPendingApprovals()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleViewHistory = async (row) => {
  try {
    history.value = await request.get(`/approvals/${row.id}/history`)
    historyDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取历史记录失败')
  }
}

onMounted(() => {
  fetchPendingApprovals()
  fetchTemplates()
})
</script>

<style scoped>
.approval-manage {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>