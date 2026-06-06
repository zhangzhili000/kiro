<template>
  <div class="role-manage">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>角色管理</span>
          <el-button type="primary" @click="openCreateModal">新增角色</el-button>
        </div>
      </template>

      <el-table :data="roles" style="width: 100%">
        <el-table-column prop="name" label="角色名称" />
        <el-table-column prop="code" label="角色代码" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="permissions" label="权限" width="300">
          <template #default="{ row }">
            <el-tag v-for="(perm, idx) in row.permissions.slice(0, 3)" :key="idx" size="small">
              {{ getPermissionLabel(perm) }}
            </el-tag>
            <span v-if="row.permissions.length > 3" class="more-perms">
              +{{ row.permissions.length - 3 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="openEditModal(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteRole(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建角色弹窗 -->
    <el-dialog title="新增角色" v-model="createModalVisible" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="角色名称" required>
          <el-input v-model="createForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色代码" required>
          <el-input v-model="createForm.code" placeholder="请输入角色代码（如：admin）" />
        </el-form-item>
        <el-form-item label="角色描述">
          <el-input v-model="createForm.description" type="textarea" placeholder="请输入角色描述" />
        </el-form-item>
        <el-form-item label="权限列表">
          <el-select v-model="createForm.permissions" multiple placeholder="请选择权限">
            <el-option v-for="perm in permissionOptions" :key="perm.value" :label="perm.label" :value="perm.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createModalVisible = false">取消</el-button>
        <el-button type="primary" @click="createRole">确认创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑角色弹窗 -->
    <el-dialog title="编辑角色" v-model="editModalVisible" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="角色名称" required>
          <el-input v-model="editForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色代码">
          <el-input v-model="editForm.code" disabled />
        </el-form-item>
        <el-form-item label="角色描述">
          <el-input v-model="editForm.description" type="textarea" placeholder="请输入角色描述" />
        </el-form-item>
        <el-form-item label="权限列表">
          <el-select v-model="editForm.permissions" multiple placeholder="请选择权限">
            <el-option v-for="perm in permissionOptions" :key="perm.value" :label="perm.label" :value="perm.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editModalVisible = false">取消</el-button>
        <el-button type="primary" @click="updateRole">确认更新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const roles = ref([])
const createModalVisible = ref(false)
const editModalVisible = ref(false)

// 权限映射配置 - 统一使用点号格式存储
const permissionOptions = [
  { label: '全部权限', value: '*' },
  { label: '文档创建', value: 'document.create' },
  { label: '文档编辑', value: 'document.edit' },
  { label: '文档删除', value: 'document.delete' },
  { label: '文档阅读', value: 'document.read' },
  { label: '分类管理', value: 'category.manage' },
  { label: '标签管理', value: 'tag.manage' },
  { label: '用户管理', value: 'user.manage' },
  { label: '角色管理', value: 'role.manage' },
  { label: '部门管理', value: 'department.manage' }
]

// 创建权限代码到中文的映射对象
const permissionMap = {}
permissionOptions.forEach(perm => {
  permissionMap[perm.value] = perm.label
})

// 获取权限的中文显示名称
const getPermissionLabel = (permission) => {
  // 处理旧格式（冒号分隔）转换为新格式（点号分隔）
  const normalizedPerm = permission.replace(':', '.')
  return permissionMap[normalizedPerm] || permission
}

const createForm = ref({
  name: '',
  code: '',
  description: '',
  permissions: []
})

const editForm = ref({
  id: '',
  name: '',
  code: '',
  description: '',
  permissions: []
})

const fetchRoles = async () => {
  try {
    const response = await fetch('/api/v1/admin/roles', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      // 确保数据是数组
      roles.value = Array.isArray(data) ? data : []
    } else {
      ElMessage.error('获取角色列表失败')
      roles.value = []
    }
  } catch (error) {
    ElMessage.error('获取角色列表失败')
    roles.value = []
  }
}

const openCreateModal = () => {
  createForm.value = {
    name: '',
    code: '',
    description: '',
    permissions: []
  }
  createModalVisible.value = true
}

const createRole = async () => {
  try {
    const response = await fetch('/api/v1/admin/roles', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(createForm.value)
    })
    if (response.ok) {
      ElMessage.success('角色创建成功')
      createModalVisible.value = false
      await fetchRoles()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '创建角色失败')
    }
  } catch (error) {
    ElMessage.error('创建角色失败')
  }
}

const openEditModal = (role) => {
  editForm.value = {
    id: role.id,
    name: role.name,
    code: role.code,
    description: role.description,
    permissions: role.permissions || []
  }
  editModalVisible.value = true
}

const updateRole = async () => {
  try {
    const response = await fetch(`/api/v1/admin/roles/${editForm.value.id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: editForm.value.name,
        description: editForm.value.description,
        permissions: editForm.value.permissions
      })
    })
    if (response.ok) {
      ElMessage.success('角色更新成功')
      editModalVisible.value = false
      await fetchRoles()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '更新角色失败')
    }
  } catch (error) {
    ElMessage.error('更新角色失败')
  }
}

const deleteRole = async (role) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色「${role.name}」吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const response = await fetch(`/api/v1/admin/roles/${role.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    if (response.ok) {
      ElMessage.success('角色删除成功')
      await fetchRoles()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '删除角色失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除角色失败')
    }
  }
}

onMounted(() => {
  fetchRoles()
})
</script>

<style scoped>
.role-manage {
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.more-perms {
  margin-left: 8px;
  color: #999;
  font-size: 12px;
}
</style>