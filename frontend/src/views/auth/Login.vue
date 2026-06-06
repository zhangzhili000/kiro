<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>企业知识库 - 登录</h2>
      </template>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.rememberMe">记住我</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">登录</el-button>
        </el-form-item>
        <el-form-item>
          <el-link type="primary" @click="goRegister">还没有账号？去注册</el-link>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  email: '',
  password: '',
  rememberMe: false
})

const rules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  console.log('login clicked')
  if (!form.email || !form.password) {
    ElMessage.error('请输入邮箱和密码')
    return
  }

  loading.value = true
  try {
    await authStore.login(form.email, form.password)
    
    if (form.rememberMe) {
      // 保存用户邮箱到本地存储
      localStorage.setItem('remembered_email', form.email)
    } else {
      localStorage.removeItem('remembered_email')
    }
    
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    console.error('login error:', error)
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

const goRegister = () => {
  router.push('/register')
}

onMounted(() => {
  console.log('Login page mounted')
  
  // 读取保存的邮箱并自动填充
  const rememberedEmail = localStorage.getItem('remembered_email')
  if (rememberedEmail) {
    form.email = rememberedEmail
    form.rememberMe = true
  }
})
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 400px;
}
</style>