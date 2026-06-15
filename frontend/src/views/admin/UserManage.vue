<template>
  <div class="user-manage">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>用户管理</span>
          <el-button type="primary" @click="openCreateModal">新增用户</el-button>
        </div>
      </template>

      <el-table :data="users" style="width: 100%">
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="full_name" label="姓名" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="roleType(row.role)">{{ roleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department_name" label="部门" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="openEditModal(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'danger' : 'primary'"
              @click="toggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建用户弹窗 -->
    <el-dialog title="新增用户" v-model="createModalVisible" width="500px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px" autocomplete="off">
        <el-form-item label="邮箱" required prop="email">
          <el-input v-model="createForm.email" type="email" placeholder="请输入邮箱" autocomplete="off" />
        </el-form-item>
        <el-form-item label="用户名" required>
          <el-input v-model="createForm.username" placeholder="请输入用户名" autocomplete="off" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="createForm.full_name" placeholder="请输入姓名" autocomplete="off" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" type="password" placeholder="请输入密码" autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="createForm.role" placeholder="请选择角色">
            <el-option label="管理员" value="admin" />
            <el-option label="编辑者" value="editor" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="createForm.department_id" placeholder="请选择部门">
            <el-option :label="dept.name" :value="dept.id" v-for="dept in departments" :key="dept.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createModalVisible = false">取消</el-button>
        <el-button type="primary" @click="createUser">确认创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户弹窗 -->
    <el-dialog title="编辑用户" v-model="editModalVisible" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" disabled />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="editForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" placeholder="请选择角色">
            <el-option label="管理员" value="admin" />
            <el-option label="编辑者" value="editor" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="editForm.department_id" placeholder="请选择部门">
            <el-option :label="dept.name" :value="dept.id" v-for="dept in departments" :key="dept.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editModalVisible = false">取消</el-button>
        <el-button type="primary" @click="updateUser">确认更新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const users = ref([])
const departments = ref([])
const createModalVisible = ref(false)
const editModalVisible = ref(false)

const createFormRef = ref(null)

const createRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const createForm = ref({
  email: '',
  username: '',
  full_name: '',
  password: '',
  role: 'user',
  department_id: null
})

const editForm = ref({
  id: '',
  email: '',
  username: '',
  full_name: '',
  role: '',
  department_id: null
})

const roleType = (role) => {
  const types = { admin: 'danger', editor: 'warning', user: '' }
  return types[role] || ''
}

const roleText = (role) => {
  const texts = { admin: '管理员', editor: '编辑者', user: '用户' }
  return texts[role] || role
}

const fetchUsers = async () => {
  try {
    const response = await fetch('/api/v1/admin/users', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      // 确保数据是数组
      if (Array.isArray(data)) {
        // 添加部门名称
        users.value = data.map(user => ({
          ...user,
          department_name: departments.value.find(d => d.id === user.department_id)?.name || '-'
        }))
      } else {
        users.value = []
      }
    } else {
      ElMessage.error('获取用户列表失败')
      users.value = []
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
    users.value = []
  }
}

const fetchDepartments = async () => {
  try {
    const response = await fetch('/api/v1/departments', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    if (response.ok) {
      departments.value = await response.json()
    }
  } catch (error) {
    console.error('获取部门列表失败', error)
  }
}

const openCreateModal = async () => {
  // 打开弹窗前刷新部门列表
  await fetchDepartments()
  createForm.value = {
    email: '',
    username: '',
    full_name: '',
    password: '',
    role: 'user',
    department_id: null
  }
  createModalVisible.value = true
}

const createUser = async () => {
  try {
    // 表单验证
    const valid = await createFormRef.value.validate()
    if (!valid) {
      return
    }
    
    const response = await fetch('/api/v1/admin/users', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(createForm.value)
    })
    if (response.ok) {
      ElMessage.success('用户创建成功')
      createModalVisible.value = false
      await fetchUsers()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '创建用户失败')
    }
  } catch (error) {
    ElMessage.error('创建用户失败')
  }
}

const openEditModal = async (user) => {
  // 打开编辑弹窗前刷新部门列表
  await fetchDepartments()
  editForm.value = {
    id: user.id,
    email: user.email,
    username: user.username,
    full_name: user.full_name,
    role: user.role,
    department_id: user.department_id
  }
  editModalVisible.value = true
}

const updateUser = async () => {
  try {
    const response = await fetch(`/api/v1/admin/users/${editForm.value.id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: editForm.value.username,
        full_name: editForm.value.full_name,
        role: editForm.value.role,
        department_id: editForm.value.department_id
      })
    })
    if (response.ok) {
      ElMessage.success('用户更新成功')
      editModalVisible.value = false
      await fetchUsers()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '更新用户失败')
    }
  } catch (error) {
    ElMessage.error('更新用户失败')
  }
}

const toggleStatus = async (user) => {
  try {
    const response = await fetch(`/api/v1/admin/users/${user.id}/status?is_active=${!user.is_active}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    if (response.ok) {
      user.is_active = !user.is_active
      ElMessage.success(`用户已${user.is_active ? '启用' : '禁用'}`)
    } else {
      ElMessage.error('操作失败')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户「${user.email}」吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const response = await fetch(`/api/v1/admin/users/${user.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    if (response.ok) {
      ElMessage.success('用户删除成功')
      await fetchUsers()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '删除用户失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除用户失败')
    }
  }
}

onMounted(async () => {
  await fetchDepartments()
  await fetchUsers()
})
</script>

<style scoped>
.user-manage {
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>