<template>
  <div class="team-manage">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>团队知识库</span>
          <el-button type="primary" @click="handleCreateTeam">创建团队</el-button>
        </div>
      </template>

      <el-table :data="teams" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="团队名称" width="200" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewMembers(row)">成员</el-button>
            <el-button size="small" @click="handleViewDocuments(row)">文档</el-button>
            <el-button size="small" @click="handleEditTeam(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeleteTeam(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="teamDialogVisible" :title="isEditTeam ? '编辑团队' : '创建团队'" width="500px">
      <el-form :model="teamForm" :rules="teamRules" ref="teamFormRef" label-width="100px">
        <el-form-item label="团队名称" prop="name">
          <el-input v-model="teamForm.name" placeholder="请输入团队名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="teamForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="图标" prop="icon">
          <el-input v-model="teamForm.icon" placeholder="请输入图标URL" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="teamDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitTeam">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="memberDialogVisible" :title="`团队成员 - ${currentTeam?.name}`" width="800px">
      <div class="dialog-actions">
        <el-button type="primary" @click="handleAddMember">添加成员</el-button>
      </div>
      <el-table :data="members" style="width: 100%" v-loading="memberLoading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="user_id" label="用户ID" width="100" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="roleType(row.role)">{{ roleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="joined_at" label="加入时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleRemoveMember(row)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="addMemberDialogVisible" title="添加成员" width="400px">
      <el-form :model="addMemberForm" label-width="80px">
        <el-form-item label="用户ID">
          <el-input-number v-model="addMemberForm.user_id" :min="1" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="addMemberForm.role">
            <el-option label="成员" value="member" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addMemberDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmAddMember">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="documentDialogVisible" :title="`团队文档 - ${currentTeam?.name}`" width="900px">
      <div class="dialog-actions">
        <el-button type="primary" @click="handleAddDocument">添加文档</el-button>
      </div>
      <el-table :data="teamDocuments" style="width: 100%" v-loading="documentLoading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="author_id" label="作者ID" width="100" />
        <el-table-column prop="view_count" label="浏览" width="80" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleRemoveDocument(row)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="addDocumentDialogVisible" title="添加文档" width="400px">
      <el-form :model="addDocumentForm" label-width="80px">
        <el-form-item label="文档ID">
          <el-input-number v-model="addDocumentForm.document_id" :min="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDocumentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmAddDocument">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@open/api/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const teams = ref([])
const members = ref([])
const teamDocuments = ref([])
const loading = ref(false)
const memberLoading = ref(false)
const documentLoading = ref(false)

const teamDialogVisible = ref(false)
const memberDialogVisible = ref(false)
const documentDialogVisible = ref(false)
const addMemberDialogVisible = ref(false)
const addDocumentDialogVisible = ref(false)

const isEditTeam = ref(false)
const currentTeam = ref(null)
const teamFormRef = ref(null)

const teamForm = ref({
  name: '',
  description: '',
  icon: ''
})

const teamRules = {
  name: [{ required: true, message: '请输入团队名称', trigger: 'blur' }]
}

const addMemberForm = ref({
  user_id: null,
  role: 'member'
})

const addDocumentForm = ref({
  document_id: null
})

const roleType = (role) => {
  const types = { owner: 'danger', admin: 'warning', member: 'info' }
  return types[role] || 'info'
}

const roleText = (role) => {
  const texts = { owner: '所有者', admin: '管理员', member: '成员' }
  return texts[role] || role
}

const fetchTeams = async () => {
  loading.value = true
  try {
    teams.value = await request.get('/teams')
  } catch (error) {
    ElMessage.error('获取团队列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreateTeam = () => {
  isEditTeam.value = false
  teamForm.value = {
    name: '',
    description: '',
    icon: ''
  }
  teamDialogVisible.value = true
}

const handleEditTeam = (row) => {
  isEditTeam.value = true
  teamForm.value = { ...row }
  teamDialogVisible.value = true
}

const handleSubmitTeam = async () => {
  if (!teamFormRef.value) return
  await teamFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (isEditTeam.value) {
          await request.put(`/teams/${teamForm.value.id}`, teamForm.value)
          ElMessage.success('更新成功')
        } else {
          await request.post('/teams', teamForm.value)
          ElMessage.success('创建成功')
        }
        teamDialogVisible.value = false
        fetchTeams()
      } catch (error) {
        ElMessage.error(isEditTeam.value ? '更新失败' : '创建失败')
      }
    }
  })
}

const handleDeleteTeam = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个团队吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/teams/${id}`)
    ElMessage.success('删除成功')
    fetchTeams()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleViewMembers = async (row) => {
  currentTeam.value = row
  memberLoading.value = true
  memberDialogVisible.value = true
  try {
    members.value = await request.get(`/teams/${row.id}/members`)
  } catch (error) {
    ElMessage.error('获取成员列表失败')
  } finally {
    memberLoading.value = false
  }
}

const handleAddMember = () => {
  addMemberForm.value = {
    user_id: null,
    role: 'member'
  }
  addMemberDialogVisible.value = true
}

const handleConfirmAddMember = async () => {
  try {
    await request.post(`/teams/${currentTeam.value.id}/members`, addMemberForm.value)
    ElMessage.success('添加成功')
    addMemberDialogVisible.value = false
    handleViewMembers(currentTeam.value)
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

const handleRemoveMember = async (row) => {
  try {
    await ElMessageBox.confirm('确定要移除这个成员吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/teams/${currentTeam.value.id}/members/${row.user_id}`)
    ElMessage.success('移除成功')
    handleViewMembers(currentTeam.value)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

const handleViewDocuments = async (row) => {
  currentTeam.value = row
  documentLoading.value = true
  documentDialogVisible.value = true
  try {
    teamDocuments.value = await request.get(`/teams/${row.id}/documents`)
  } catch (error) {
    ElMessage.error('获取文档列表失败')
  } finally {
    documentLoading.value = false
  }
}

const handleAddDocument = () => {
  addDocumentForm.value = {
    document_id: null
  }
  addDocumentDialogVisible.value = true
}

const handleConfirmAddDocument = async () => {
  try {
    await request.post(`/teams/${currentTeam.value.id}/documents`, addDocumentForm.value)
    ElMessage.success('添加成功')
    addDocumentDialogVisible.value = false
    handleViewDocuments(currentTeam.value)
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

const handleRemoveDocument = async (row) => {
  try {
    await ElMessageBox.confirm('确定要从团队中移除这个文档吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/teams/${currentTeam.value.id}/documents/${row.id}`)
    ElMessage.success('移除成功')
    handleViewDocuments(currentTeam.value)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

onMounted(fetchTeams)
</script>

<style scoped>
.team-manage {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dialog-actions {
  margin-bottom: 15px;
}
</style>