import axios from 'axios'
import { ElMessage } from 'element-plus'

// 重试配置
const MAX_RETRIES = 3
const RETRY_DELAY = 1000

// 网络错误判断
const isNetworkError = (error) => {
  return !error.response || 
         error.code === 'ECONNRESET' || 
         error.code === 'ECONNABORTED' ||
         error.code === 'ETIMEDOUT' ||
         error.message.includes('Network Error')
}

// 延迟函数
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log('Request:', config.method?.toUpperCase(), config.url, config.data)
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  response => {
    console.log('Response:', response.status, response.data)
    return response.data
  },
  async error => {
    console.error('Response error:', error.response?.status, error.response?.data, error.code)
    
    const originalRequest = error.config
    
    // 检查是否需要重试
    if (!originalRequest._retry && isNetworkError(error)) {
      originalRequest._retryCount = originalRequest._retryCount || 0
      
      if (originalRequest._retryCount < MAX_RETRIES) {
        originalRequest._retryCount++
        console.log(`Retrying request (${originalRequest._retryCount}/${MAX_RETRIES})...`)
        
        await delay(RETRY_DELAY * originalRequest._retryCount)
        return request(originalRequest)
      }
    }
    
    // 错误处理
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      } else if (status === 403) {
        ElMessage.error(data.detail || '没有权限')
      } else if (status === 404) {
        ElMessage.error(data.detail || '资源不存在')
      } else if (status === 500) {
        ElMessage.error(data.detail || '服务器错误')
      } else if (status === 502) {
        ElMessage.error('网关错误，请稍后重试')
      } else {
        ElMessage.error(data.detail || '请求失败')
      }
    } else {
      if (error.code === 'ECONNRESET') {
        ElMessage.error('连接被重置，请稍后重试')
      } else if (error.code === 'ECONNABORTED') {
        ElMessage.error('请求超时，请稍后重试')
      } else {
        ElMessage.error('网络错误，请检查网络连接')
      }
    }
    return Promise.reject(error)
  }
)

export default request