<template>
  <div class="document-editor">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>{{ isEdit ? '编辑文档' : '新建文档' }}</span>
          <div>
            <el-button @click="$router.back()">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
          </div>
        </div>
      </template>

      <el-form :model="form" label-width="80px">
        <!-- 文档导入区域 -->
        <el-form-item label="导入文档">
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :on-success="handleFileUploadSuccess"
            :on-error="handleFileUploadError"
            :before-upload="beforeFileUpload"
            :show-file-list="false"
            accept=".pdf,.doc,.docx,.md,.txt"
          >
            <el-button type="default" :loading="uploading">
              <el-icon><Upload /></el-icon>
              {{ importedFileName || '点击或拖拽上传文档（支持PDF、Word、MD等格式）' }}
            </el-button>
          </el-upload>
          <span v-if="importedFileName" class="import-hint">
            已导入: {{ importedFileName }}
            <el-button size="small" @click="clearImport">清除</el-button>
          </span>
        </el-form-item>

        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入文档标题" />
        </el-form-item>
        
        <el-form-item label="摘要">
          <el-input 
            v-model="form.summary" 
            type="textarea" 
            :rows="3" 
            placeholder="文档摘要（可通过AI自动生成）" 
          />
          <el-button size="small" type="text" @click="generateSummary" :loading="generatingSummary">
            <el-icon><Help /></el-icon>
            AI生成摘要
          </el-button>
        </el-form-item>

        <el-form-item label="关键词">
          <el-input 
            v-model="keywordInput" 
            placeholder="请输入关键词，用逗号分隔"
          />
          <el-button size="small" type="text" @click="generateKeywords" :loading="generatingKeywords">
            <el-icon><Help /></el-icon>
            AI提取关键词
          </el-button>
          <div v-if="form.keywords && form.keywords.length > 0" class="keyword-tags">
            <el-tag 
              v-for="(keyword, index) in form.keywords" 
              :key="index" 
              closable 
              @close="removeKeyword(index)"
            >
              {{ keyword }}
            </el-tag>
          </div>
        </el-form-item>

        <el-form-item label="分类">
          <el-select v-model="form.category_id" placeholder="请选择分类" clearable>
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="标签">
          <el-select v-model="form.tag_ids" multiple placeholder="请选择标签" clearable>
            <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="权限">
          <el-radio-group v-model="form.permission">
            <el-radio value="public">公开</el-radio>
            <el-radio value="private">私有</el-radio>
            <el-radio value="team">团队可见</el-radio>
            <el-radio value="user">指定用户可见</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 团队权限设置 -->
        <el-form-item v-if="form.permission === 'team'" label="团队权限">
          <div class="permission-group">
            <div v-for="(teamPerm, index) in form.teamPermissions" :key="teamPerm.target_id" class="permission-item">
              <span class="permission-target">{{ getTeamName(teamPerm.target_id) }}</span>
              <el-checkbox-group v-model="form.teamPermissions[index].actions">
                <el-checkbox label="view">查看</el-checkbox>
                <el-checkbox label="edit">编辑</el-checkbox>
                <el-checkbox label="delete">删除</el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
          <el-select v-model="selectedTeam" placeholder="选择团队添加权限" @change="addTeamPermission" class="permission-select">
            <el-option v-for="team in availableTeams" :key="team.id" :label="team.name" :value="team.id" />
          </el-select>
        </el-form-item>

        <!-- 用户权限设置 -->
        <el-form-item v-if="form.permission === 'user'" label="用户权限">
          <div class="permission-group">
            <div v-for="(userPerm, index) in form.userPermissions" :key="userPerm.target_id" class="permission-item">
              <span class="permission-target">{{ getUserName(userPerm.target_id) }}</span>
              <el-checkbox-group v-model="form.userPermissions[index].actions">
                <el-checkbox label="view">查看</el-checkbox>
                <el-checkbox label="edit">编辑</el-checkbox>
                <el-checkbox label="delete">删除</el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
          <el-select v-model="selectedUser" placeholder="选择用户添加权限" @change="addUserPermission" class="permission-select">
            <el-option v-for="user in availableUsers" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="内容">
          <div class="content-tabs">
            <el-tabs type="border-card" @tab-change="handleTabChange">
              <el-tab-pane label="富文本编辑">
                <div 
                  class="rich-text-editor" 
                  contenteditable="true"
                  @input="handleRichTextInput"
                  placeholder="请输入文档内容或导入文档..."
                ></div>
              </el-tab-pane>
              <el-tab-pane label="HTML预览">
                <div class="html-preview" v-html="form.html_content || '<p>暂无预览内容</p>'"></div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 处理进度弹窗 -->
    <el-dialog title="文档处理中" :visible="showProcessingModal" :close-on-click-modal="false">
      <div class="processing-steps">
        <div v-for="(step, index) in processingSteps" :key="index" class="step">
          <CircleCheck v-if="step.completed" class="success" />
          <Refresh v-else-if="step.active" class="active" />
          <Minus v-else class="default" />
          <span :class="{ 'success': step.completed, 'active': step.active }">{{ step.text }}</span>
          <el-progress v-if="step.active" :percentage="processingProgress" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocumentStore } from '@/stores/document'
import { useCategoryStore } from '@/stores/category'
import { useTagStore } from '@/stores/tag'
import { useAIService } from '@/stores/ai'
import { ElMessage } from 'element-plus'
import { Upload, Help, CircleCheck, Minus, Refresh } from '@element-plus/icons-vue'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()
const documentStore = useDocumentStore()
const categoryStore = useCategoryStore()
const tagStore = useTagStore()
const aiService = useAIService()

const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const uploading = ref(false)
const generatingSummary = ref(false)
const generatingKeywords = ref(false)
const showProcessingModal = ref(false)
const processingProgress = ref(0)
const importedFileName = ref('')
const uploadedFileData = ref(null)

const processingSteps = ref([
  { text: '保存文档', completed: false, active: false },
  { text: '格式转换', completed: false, active: false },
  { text: '提取摘要', completed: false, active: false },
  { text: '提取关键词', completed: false, active: false },
  { text: '构建向量索引', completed: false, active: false }
])

const form = reactive({
  title: '',
  content: '',
  html_content: '',
  summary: '',
  keywords: [],
  category_id: null,
  tag_ids: [],
  permission: 'public',
  teamPermissions: [],
  userPermissions: []
})

const keywordInput = ref('')

const categories = ref([])
const tags = ref([])
const teams = ref([])
const users = ref([])
const selectedTeam = ref(null)
const selectedUser = ref(null)

// 已选中的用户（用于权限设置展示）
const selectedUsers = ref([])

const uploadUrl = computed(() => '/api/v1/ai/documents/upload')
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`
}))

// 可用于添加权限的团队（尚未添加权限的团队）
const availableTeams = computed(() => {
  const usedIds = form.teamPermissions.map(p => p.target_id)
  return teams.value.filter(t => !usedIds.includes(t.id))
})

// 可用于添加权限的用户（尚未添加权限的用户）
const availableUsers = computed(() => {
  const usedIds = form.userPermissions.map(p => p.target_id)
  return users.value.filter(u => !usedIds.includes(u.id))
})

// 添加团队权限
const addTeamPermission = (teamId) => {
  if (teamId && !form.teamPermissions.find(p => p.target_id === teamId)) {
    form.teamPermissions.push({ target_id: teamId, actions: ['view'] })
  }
  selectedTeam.value = null
}

// 添加用户权限
const addUserPermission = (userId) => {
  if (userId && !form.userPermissions.find(p => p.target_id === userId)) {
    const user = users.value.find(u => u.id === userId)
    form.userPermissions.push({ target_id: userId, actions: ['view'] })
    if (user) {
      selectedUsers.value.push(user)
    }
  }
  selectedUser.value = null
}

// 获取团队名称
const getTeamName = (teamId) => {
  const team = teams.value.find(t => t.id === teamId)
  return team ? team.name : ''
}

// 获取用户名称
const getUserName = (userId) => {
  const user = users.value.find(u => u.id === userId)
  return user ? user.username : ''
}

const fetchData = async () => {
  await categoryStore.fetchCategories()
  await tagStore.fetchTags()
  categories.value = categoryStore.categories
  tags.value = tagStore.tags

  const teamResponse = await fetch('/api/v1/teams', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
  })
  if (teamResponse.ok) {
    teams.value = await teamResponse.json()
  }

  const userResponse = await fetch('/api/v1/teams/users', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    })
    if (userResponse.ok) {
      users.value = await userResponse.json()
    }

  if (isEdit.value) {
    const doc = await documentStore.fetchDocument(route.params.id)
    form.title = doc.title
    form.content = doc.content
    form.category_id = doc.category_id
    form.permission = doc.permission
    form.summary = doc.summary || ''
    form.keywords = doc.keywords ? JSON.parse(doc.keywords) : []

    const permResponse = await fetch(`/api/v1/documents/${route.params.id}/permissions`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    })
    if (permResponse.ok) {
      const permissions = await permResponse.json()
      
      // 解析团队权限
      const teamPerms = permissions.filter(p => p.permission_type === 'team')
      form.teamPermissions = teamPerms.map(p => ({
        target_id: p.target_id,
        actions: [p.action]
      }))

      // 解析用户权限
      const userPerms = permissions.filter(p => p.permission_type === 'user')
      form.userPermissions = userPerms.map(p => {
        const user = users.value.find(u => u.id === p.target_id)
        if (user) {
          selectedUsers.value.push(user)
        }
        return {
          target_id: p.target_id,
          actions: [p.action]
        }
      })
    }
  }
}

const beforeFileUpload = (file) => {
  const maxSize = 50 * 1024 * 1024
  const allowedTypes = ['application/pdf', 'application/msword', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/markdown', 'text/plain']
  
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }
  
  if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|doc|docx|md|txt)$/i)) {
    ElMessage.error('仅支持PDF、Word、MD、TXT格式的文档')
    return false
  }
  
  uploading.value = true
  return true
}

const handleFileUploadSuccess = async (response) => {
  uploading.value = false
  if (response.success) {
    importedFileName.value = response.original_filename
    form.content = response.content
    form.html_content = response.html_content
    
    if (!form.title) {
      form.title = response.original_filename.replace(/\.(pdf|doc|docx|md|txt)$/i, '')
    }
    
    // 将HTML内容加载到富文本编辑器
    const editor = document.querySelector('.rich-text-editor')
    if (editor && response.html_content) {
      editor.innerHTML = response.html_content
    }
    
    ElMessage.success('文档导入成功，图片和表格已保留')
  } else {
    ElMessage.error('文档导入失败: ' + response.detail)
  }
}

const handleTabChange = (activeTab) => {
  // 当切换到富文本编辑时，同步内容
  if (activeTab === '0') {
    const editor = document.querySelector('.rich-text-editor')
    if (editor && form.html_content && !editor.innerHTML) {
      editor.innerHTML = form.html_content
    }
  }
}

const handleRichTextInput = () => {
  const editor = document.querySelector('.rich-text-editor')
  if (editor) {
    form.html_content = editor.innerHTML
    // 同时提取纯文本用于AI处理
    form.content = editor.innerText
  }
}

const handleFileUploadError = () => {
  uploading.value = false
  ElMessage.error('文档上传失败')
}

const clearImport = () => {
  importedFileName.value = ''
  form.content = ''
  uploadedFileData.value = null
}

const generateSummary = async () => {
  if (!form.content.trim()) {
    ElMessage.warning('请先输入文档内容或导入文档')
    return
  }
  
  generatingSummary.value = true
  form.summary = ''
  
  try {
    const response = await fetch('/api/v1/ai/documents/summary/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ content: form.content })
    })
    
    if (!response.ok) {
      throw new Error('请求失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[END]') {
            reader.cancel()
            ElMessage.success('摘要生成成功')
            return
          } else if (data.startsWith('[ERROR]') && data.endsWith('[/ERROR]')) {
            throw new Error(data.slice(7, -8))
          } else {
            form.summary += data
          }
        }
      }
    }
    
    ElMessage.success('摘要生成成功')
  } catch (error) {
    console.error('Summary error:', error)
    ElMessage.error('摘要生成失败')
  } finally {
    generatingSummary.value = false
  }
}

const generateKeywords = async () => {
  if (!form.content.trim()) {
    ElMessage.warning('请先输入文档内容或导入文档')
    return
  }
  
  generatingKeywords.value = true
  let keywordsText = ''
  
  try {
    const response = await fetch('/api/v1/ai/documents/keywords/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ content: form.content })
    })
    
    if (!response.ok) {
      throw new Error('请求失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[END]') {
            reader.cancel()
            if (keywordsText) {
              const keywords = keywordsText.split('，').map(k => k.trim()).filter(k => k)
              if (!keywords.length) {
                keywordsText.split(',').map(k => k.trim()).filter(k => k)
              }
              form.keywords = keywords
            }
            ElMessage.success('关键词提取成功')
            return
          } else if (data.startsWith('[ERROR]') && data.endsWith('[/ERROR]')) {
            throw new Error(data.slice(7, -8))
          } else {
            keywordsText += data
          }
        }
      }
    }
    
    if (keywordsText) {
      const keywords = keywordsText.split('，').map(k => k.trim()).filter(k => k)
      if (!keywords.length) {
        keywordsText.split(',').map(k => k.trim()).filter(k => k)
      }
      form.keywords = keywords
    }
    ElMessage.success('关键词提取成功')
  } catch (error) {
    console.error('Keywords error:', error)
    ElMessage.error('关键词提取失败')
  } finally {
    generatingKeywords.value = false
  }
}

const addKeyword = () => {
  const keywords = keywordInput.value.split(',').map(k => k.trim()).filter(k => k)
  keywords.forEach(k => {
    if (!form.keywords.includes(k)) {
      form.keywords.push(k)
    }
  })
  keywordInput.value = ''
}

const removeKeyword = (index) => {
  form.keywords.splice(index, 1)
}

const handleSave = async () => {
  if (!form.title.trim()) {
    ElMessage.warning('请输入文档标题')
    return
  }
  
  // 添加手动输入的关键词
  if (keywordInput.value.trim()) {
    addKeyword()
  }

  saving.value = true

  try {
    const saveForm = {
      title: form.title,
      content: form.content,
      html_content: form.html_content,
      summary: form.summary,
      keywords: JSON.stringify(form.keywords),
      category_id: form.category_id,
      tag_ids: form.tag_ids,
      permission: form.permission
    }
    
    let documentId
    if (isEdit.value) {
      await documentStore.updateDocument(route.params.id, saveForm)
      documentId = route.params.id
    } else {
      const result = await documentStore.createDocument(saveForm)
      documentId = result.id
    }

    // 构建权限数据
    const permissions = []
    
    // 添加团队权限
    for (const teamPerm of form.teamPermissions) {
      for (const action of teamPerm.actions) {
        permissions.push({
          permission_type: 'team',
          target_id: teamPerm.target_id,
          action: action
        })
      }
    }
    
    // 添加用户权限
    for (const userPerm of form.userPermissions) {
      for (const action of userPerm.actions) {
        permissions.push({
          permission_type: 'user',
          target_id: userPerm.target_id,
          action: action
        })
      }
    }
    
    // 保存权限
    await fetch(`/api/v1/documents/${documentId}/permissions`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ permissions })
    })

    ElMessage.success('文档保存成功，索引正在后台构建中...')
    router.push('/knowledge')
    
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.document-editor {
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.help-text {
  display: block;
  color: #999;
  font-size: 12px;
  margin-top: 8px;
}

.import-hint {
  display: block;
  margin-top: 10px;
  color: #67c23a;
  font-size: 14px;
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.permission-group {
  margin-bottom: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 8px;
}

.permission-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.permission-item:last-child {
  border-bottom: none;
}

.permission-target {
  min-width: 100px;
  font-weight: 500;
}

.permission-select {
  width: 200px;
  margin-top: 8px;
}

.processing-steps {
  padding: 20px;
}

.step {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.step .success {
  color: #67c23a;
}

.step .active {
  color: #409eff;
}

.step span {
  flex: 1;
}

.step .el-progress {
  flex: 2;
}
</style>
