<template>
  <div class="profile-container">
    <div class="profile-header">
      <div class="avatar-section">
        <el-avatar :size="120" :src="user?.avatar">
          {{ user?.username?.[0]?.toUpperCase() }}
        </el-avatar>
        <div class="user-info">
          <h2>{{ user?.username }}</h2>
          <p class="email">{{ user?.email }}</p>
          <p class="department" v-if="user?.department_name">{{ user?.department_name }}</p>
        </div>
      </div>
      <el-button @click="editProfile" class="edit-btn">编辑资料</el-button>
    </div>

    <div class="profile-content">
      <div class="stats-card">
        <div class="stat-item">
          <el-icon><Document /></el-icon>
          <div class="stat-info">
            <span class="stat-value">{{ stats.documents }}</span>
            <span class="stat-label">文档数</span>
          </div>
        </div>
        <div class="stat-item">
          <el-icon><Star /></el-icon>
          <div class="stat-info">
            <span class="stat-value">{{ stats.favorites }}</span>
            <span class="stat-label">收藏数</span>
          </div>
        </div>
        <div class="stat-item">
          <el-icon><CircleCheck /></el-icon>
          <div class="stat-info">
            <span class="stat-value">{{ stats.likes }}</span>
            <span class="stat-label">获赞数</span>
          </div>
        </div>
      </div>

      <div class="section">
        <h3>基本信息</h3>
        <el-form :model="userForm" label-width="100px">
          <el-form-item label="用户名">
            <el-input v-model="userForm.username" disabled />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="userForm.email" disabled />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="userForm.full_name" disabled />
          </el-form-item>
          <el-form-item label="部门">
            <el-input v-model="userForm.department" disabled />
          </el-form-item>
          <el-form-item label="职位">
            <el-input v-model="userForm.position" disabled />
          </el-form-item>
          <el-form-item label="注册时间">
            <el-input v-model="userForm.created_at" disabled />
          </el-form-item>
        </el-form>
      </div>

      <div class="section">
        <h3>安全设置</h3>
        <div class="setting-item">
          <span class="setting-label">修改密码</span>
          <el-button @click="showChangePassword = true" type="text">修改</el-button>
        </div>
        <div class="setting-item">
          <span class="setting-label">绑定手机号</span>
          <el-button type="text">{{ user?.phone ? '已绑定' : '未绑定' }}</el-button>
        </div>
      </div>
    </div>

    <el-dialog title="修改密码" :visible.sync="showChangePassword" width="400px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef">
        <el-form-item label="原密码" prop="oldPassword">
          <el-input type="password" v-model="passwordForm.oldPassword" />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input type="password" v-model="passwordForm.newPassword" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input type="password" v-model="passwordForm.confirmPassword" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePassword = false">取消</el-button>
        <el-button type="primary" @click="changePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { Document, Star, CircleCheck } from '@element-plus/icons-vue'

const authStore = useAuthStore()

const user = computed(() => authStore.user)

const userForm = reactive({
  username: '',
  email: '',
  full_name: '',
  department: '',
  position: '',
  created_at: ''
})

const stats = reactive({
  documents: 0,
  favorites: 0,
  likes: 0
})

const showChangePassword = ref(false)

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
  confirmPassword: [{ required: true, message: '请确认新密码', trigger: 'blur' }]
}

const passwordFormRef = ref(null)

const initUserForm = () => {
  userForm.username = user.value?.username || ''
  userForm.email = user.value?.email || ''
  userForm.full_name = user.value?.full_name || ''
  userForm.department = user.value?.department_name || ''
  userForm.position = user.value?.position || ''
  userForm.created_at = user.value?.created_at ? new Date(user.value.created_at).toLocaleString() : ''
}

const editProfile = () => {
  // TODO: 编辑资料功能
}

const changePassword = async () => {
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    alert('两次输入的密码不一致')
    return
  }
  
  try {
    await authStore.changePassword(passwordForm)
    showChangePassword.value = false
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (error) {
    console.error('修改密码失败', error)
  }
}

onMounted(() => {
  initUserForm()
})
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: #fff;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 24px;
}

.user-info h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.user-info .email {
  margin: 0 0 8px 0;
  color: #666;
}

.user-info .department {
  margin: 0;
  color: #409eff;
  font-size: 14px;
}

.edit-btn {
  padding: 8px 20px;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-card {
  display: flex;
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.stat-item:not(:last-child) {
  border-right: 1px solid #eee;
}

.stat-item .el-icon {
  font-size: 24px;
  color: #409eff;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

.section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.section h3 {
  margin: 0 0 20px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f5f5f5;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  font-size: 14px;
  color: #333;
}
</style>