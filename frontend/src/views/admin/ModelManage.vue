<template>
  <div class="model-manage">
    <div class="manage-header">
      <h3 class="manage-title"> 模型管理</h3>
      <p class="manage-desc">管理系统使用的各类AI模型配置，至少需要配置1个对话大模型和1个向量模型</p>
    </div>
    <div class="model-content">
      <!-- 智能对话模型 -->
      <div class="model-section">
        <div class="section-header">
          <div class="header-left">
            <h4 class="section-title"> 智能对话模型</h4>
            <el-tag size="small" type="danger">必选</el-tag>
            <el-tag size="small" type="primary">大模型</el-tag>
          </div>
          <button v-if="isAdmin" @click="addModel('chat')" class="add-btn">
            + 添加
          </button>
        </div>
        <div class="section-content">
          <div class="model-list">
            <div 
              v-for="model in getModelsByType('chat')" 
              :key="model.id"
              class="model-card"
              :class="{ active: selectedModel?.id === model.id, disabled: model.status === 'disabled' }"
            >
              <div class="model-header">
                <div class="model-info-left">
                  <span class="model-provider">{{ getProviderName(model.api_type) }}</span>
                  <span class="model-divider">/</span>
                  <span class="model-name">{{ model.model_id }}</span>
                  <el-tag size="small" type="primary">智能对话模型</el-tag>
                </div>
                <div class="model-info-right">
                  <span class="model-status-text" :class="model.status">
                    {{ model.status === 'active' ? '状态正常' : '已禁用' }}
                  </span>
                  <button v-if="isAdmin" @click="editModelAction(model)" class="edit-btn">修改</button>
                </div>
              </div>
              <div class="model-desc">
                在智能问答和摘要生成过程中使用。
              </div>
            </div>
            <div v-if="getModelsByType('chat').length === 0" class="empty-tip">
              <span>暂无配置，请添加模型</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 向量模型 -->
      <div class="model-section">
        <div class="section-header">
          <div class="header-left">
            <h4 class="section-title">🔢 向量模型</h4>
            <el-tag size="small" type="danger">必选</el-tag>
            <el-tag size="small" type="warning">小模型</el-tag>
          </div>
          <button v-if="isAdmin" @click="addModel('embedding')" class="add-btn">
            + 添加
          </button>
        </div>
        <div class="section-content">
          <div class="model-list">
            <div 
              v-for="model in getModelsByType('embedding')" 
              :key="model.id"
              class="model-card"
              :class="{ active: selectedModel?.id === model.id, disabled: model.status === 'disabled' }"
            >
              <div class="model-header">
                <div class="model-info-left">
                  <span class="model-provider">{{ getProviderName(model.api_type) }}</span>
                  <span class="model-divider">/</span>
                  <span class="model-name">{{ model.model_id }}</span>
                  <el-tag size="small" type="warning">向量模型</el-tag>
                </div>
                <div class="model-info-right">
                  <span class="model-status-text" :class="model.status">
                    {{ model.status === 'active' ? '状态正常' : '已禁用' }}
                  </span>
                  <button v-if="isAdmin" @click="editModelAction(model)" class="edit-btn">修改</button>
                </div>
              </div>
              <div class="model-desc">
                在内容发布和智能问答和智能搜索过程中使用。
              </div>
            </div>
            <div v-if="getModelsByType('embedding').length === 0" class="empty-tip">
              <span>暂无配置，请添加模型</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 重排序模型 -->
      <div class="model-section">
        <div class="section-header">
          <div class="header-left">
            <h4 class="section-title">🔄 重排序模型</h4>
            <el-tag size="small" type="info">可选</el-tag>
            <el-tag size="small" type="warning">小模型</el-tag>
          </div>
          <button v-if="isAdmin" @click="addModel('rerank')" class="add-btn">
            + 添加
          </button>
        </div>
        <div class="section-content">
          <div class="model-list">
            <div 
              v-for="model in getModelsByType('rerank')" 
              :key="model.id"
              class="model-card"
              :class="{ active: selectedModel?.id === model.id, disabled: model.status === 'disabled' }"
            >
              <div class="model-header">
                <div class="model-info-left">
                  <span class="model-provider">{{ getProviderName(model.api_type) }}</span>
                  <span class="model-divider">/</span>
                  <span class="model-name">{{ model.model_id }}</span>
                  <el-tag size="small" type="warning">重排序模型</el-tag>
                </div>
                <div class="model-info-right">
                  <span class="model-status-text" :class="model.status">
                    {{ model.status === 'active' ? '状态正常' : '已禁用' }}
                  </span>
                  <button v-if="isAdmin" @click="editModelAction(model)" class="edit-btn">修改</button>
                </div>
              </div>
              <div class="model-desc">
                在智能问答和智能搜索过程中使用。
              </div>
            </div>
            <div v-if="getModelsByType('rerank').length === 0" class="empty-tip">
              <span>暂无配置，请添加模型</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 文档分析模型 -->
      <div class="model-section">
        <div class="section-header">
          <div class="header-left">
            <h4 class="section-title"> 文档分析模型</h4>
            <el-tag size="small" type="info">可选</el-tag>
            <el-tag size="small" type="warning">小模型</el-tag>
          </div>
          <button v-if="isAdmin" @click="addModel('document')" class="add-btn">
            + 添加
          </button>
        </div>
        <div class="section-content">
          <div class="model-list">
            <div 
              v-for="model in getModelsByType('document')" 
              :key="model.id"
              class="model-card"
              :class="{ active: selectedModel?.id === model.id, disabled: model.status === 'disabled' }"
            >
              <div class="model-header">
                <div class="model-info-left">
                  <span class="model-provider">{{ getProviderName(model.api_type) }}</span>
                  <span class="model-divider">/</span>
                  <span class="model-name">{{ model.model_id }}</span>
                  <el-tag size="small" type="warning">文档分析模型</el-tag>
                </div>
                <div class="model-info-right">
                  <span class="model-status-text" :class="model.status">
                    {{ model.status === 'active' ? '状态正常' : '已禁用' }}
                  </span>
                  <button v-if="isAdmin" @click="editModelAction(model)" class="edit-btn">修改</button>
                </div>
              </div>
              <div class="model-desc">
                在内容发布和智能问答过程中使用。
              </div>
            </div>
            <div v-if="getModelsByType('document').length === 0" class="empty-tip">
              <span>暂无配置，请添加模型</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 图像分析模型 -->
      <div class="model-section">
        <div class="section-header">
          <div class="header-left">
            <h4 class="section-title">🖼️ 图像分析模型</h4>
            <el-tag size="small" type="info">可选</el-tag>
            <el-tag size="small" type="success">视觉模型</el-tag>
          </div>
          <button v-if="isAdmin" @click="addModel('image')" class="add-btn">
            + 添加
          </button>
        </div>
        <div class="section-content">
          <div class="model-list">
            <div 
              v-for="model in getModelsByType('image')" 
              :key="model.id"
              class="model-card"
              :class="{ active: selectedModel?.id === model.id, disabled: model.status === 'disabled' }"
            >
              <div class="model-header">
                <div class="model-info-left">
                  <span class="model-provider">{{ getProviderName(model.api_type) }}</span>
                  <span class="model-divider">/</span>
                  <span class="model-name">{{ model.model_id }}</span>
                  <el-tag size="small" type="success">视觉模型</el-tag>
                  <el-switch 
                    v-model="model.status"
                    :active-value="'active'"
                    :inactive-value="'disabled'"
                    size="small"
                    @change="toggleModelStatus(model)"
                  />
                </div>
                <div class="model-info-right">
                  <span class="model-status-text" :class="model.status">
                    {{ model.status === 'active' ? '状态正常' : '已禁用' }}
                  </span>
                  <button v-if="isAdmin" @click="editModelAction(model)" class="edit-btn">修改</button>
                </div>
              </div>
              <div class="model-desc">
                在内容发布和智能问答过程中使用，启用后图像分析能力可用，可选配置。
              </div>
            </div>
            <div v-if="getModelsByType('image').length === 0" class="empty-tip">
              <span>暂无配置，如需图像分析能力请添加模型</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑/添加模型弹窗 -->
    <el-dialog 
      v-model="showModal"
      :title="editingModel ? '修改模型配置' : '添加模型'" 
      width="700px"
    >
      <el-form :model="modelForm" label-width="120px">
        <el-form-item label="模型类型" required>
          <el-select 
            v-model="modelForm.type" 
            placeholder="请选择模型类型"
            :disabled="!!editingModel"
            @change="onTypeChange"
          >
            <el-option label="智能对话模型" value="chat" />
            <el-option label="向量模型" value="embedding" />
            <el-option label="重排序模型" value="rerank" />
            <el-option label="文档分析模型" value="document" />
            <el-option label="图像分析模型" value="image" />
          </el-select>
        </el-form-item>
        
        <!-- 文档分析模型的API类型 -->
        <el-form-item v-if="modelForm.type === 'document'" label="API类型" required>
          <el-select v-model="modelForm.api_type" placeholder="请选择API类型" @change="updateApiFields">
            <el-option label="不使用（使用默认方案）" value="" />
            <el-option label="MinerU" value="mineru" />
          </el-select>
        </el-form-item>
        
        <!-- 其他模型的API类型 -->
        <el-form-item v-if="modelForm.type !== 'document'" label="API类型" required>
          <el-select v-model="modelForm.api_type" placeholder="请选择API类型" @change="updateApiFields">
            <el-option label="阿里百炼" value="alibaba_duilian" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="智谱AI" value="zhipu" />
            <el-option label="硅基流动" value="siliconflow" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        
        <!-- MinerU解析模式选择 -->
        <el-form-item v-if="modelForm.api_type === 'mineru'" label="解析模式" required>
          <el-select v-model="modelForm.model_id" placeholder="请选择解析模式">
            <el-option label="轻量解析API（免Token，IP限频）" value="agent" />
            <el-option label="精准解析API（需Token，高精度）" value="precision" />
          </el-select>
        </el-form-item>
        
        <!-- 其他模型的模型标识 -->
        <el-form-item v-if="modelForm.type !== 'document' && modelForm.api_type !== 'mineru'" label="模型标识" required>
          <el-input v-model="modelForm.model_id" placeholder="请输入模型标识（如 deepseek-chat, bge-m3）" />
        </el-form-item>
        
        <!-- MinerU的Token输入 -->
        <el-form-item v-if="modelForm.type === 'document' && modelForm.api_type === 'mineru' && modelForm.model_id === 'precision'" label="API密钥">
          <el-input 
            v-model="modelForm.api_key" 
            type="password" 
            autocomplete="off"
            placeholder="请输入MinerU Token（精准解析API需要）"
            :show-password="showApiKey"
          />
        </el-form-item>
        
        <!-- 其他模型的API密钥 -->
        <el-form-item v-if="modelForm.type !== 'document' && modelForm.api_type !== 'mineru'" label="API密钥" required>
          <el-input 
            v-model="modelForm.api_key" 
            type="password" 
            autocomplete="off"
            placeholder="请输入API密钥"
            :show-password="showApiKey"
          />
        </el-form-item>
        
        <el-form-item label="API端点">
          <el-input v-model="modelForm.api_base" placeholder="请输入API端点地址" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="modelForm.description" 
            type="textarea"
            placeholder="请输入模型描述"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showModal = false">取消</el-button>
          <el-button type="primary" @click="saveModel">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 配置检查提示 -->
    <el-dialog 
      v-model="showConfigWarning"
      title="模型配置不完整"
      width="500px"
      :close-on-click-modal="false"
    >
      <p>系统需要至少配置1个智能对话模型和1个向量模型才能正常使用。</p>
      <div class="warning-list">
        <div v-if="!hasChatModel" class="warning-item">
          <el-icon><Warning /></el-icon>
          <span>缺少智能对话模型</span>
        </div>
        <div v-if="!hasEmbeddingModel" class="warning-item">
          <el-icon><Warning /></el-icon>
          <span>缺少向量模型</span>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="showConfigWarning = false">我知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useAuthStore } from '@open/stores/auth'
import { ElMessage } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import { modelAPI } from '@open/api'

const authStore = useAuthStore()

const isAdmin = computed(() => {
  const user = authStore.user
  if (!user) return false
  return user.role === 'admin' || user.is_superuser
})

const showModal = ref(false)
const showConfigWarning = ref(false)
const editingModel = ref(null)
const showApiKey = ref(false)
const selectedModel = ref(null)
const models = ref([])

const modelForm = reactive({
  id: null,
  type: 'chat',
  api_type: 'openai',
  model_id: '',
  api_key: '',
  api_base: '',
  description: '',
  status: 'active'
})

const hasChatModel = computed(() => {
  return models.value.some(m => m.type === 'chat' && m.status === 'active')
})

const hasEmbeddingModel = computed(() => {
  return models.value.some(m => m.type === 'embedding' && m.status === 'active')
})

const providerNames = {
  alibaba_duilian: '阿里百炼',
  deepseek: 'DeepSeek',
  openai: 'OpenAI',
  zhipu: '智谱AI',
  siliconflow: '硅基流动',
  mineru: 'MinerU',
  custom: '自定义'
}

const getProviderName = (apiType) => {
  return providerNames[apiType] || apiType
}

const defaultApiBases = {
  alibaba_duilian: 'https://dashscope.aliyuncs.com/api/v1',
  deepseek: 'https://api.deepseek.com/v1',
  openai: 'https://api.openai.com/v1',
  zhipu: 'https://open.bigmodel.cn/api/paas/v4',
  siliconflow: 'https://api.siliconflow.cn/v1',
  mineru: 'https://mineru.net/api/v4',
  custom: ''
}

const updateApiFields = () => {
  // 文档分析模型不需要设置默认API端点
  if (modelForm.type === 'document' && modelForm.api_type === 'mineru') {
    modelForm.api_base = 'https://mineru.net/api/v1/agent'
  } else if (modelForm.type === 'document') {
    modelForm.api_base = ''
  } else {
    modelForm.api_base = defaultApiBases[modelForm.api_type] || ''
  }
}

const onTypeChange = () => {
  // 模型类型变化时，重置相关字段
  if (modelForm.type === 'document') {
    // 文档分析模型默认不使用
    modelForm.api_type = ''
    modelForm.model_id = ''
    modelForm.api_key = ''
    modelForm.api_base = ''
  } else {
    // 其他模型类型
    modelForm.api_type = 'openai'
    modelForm.model_id = ''
    modelForm.api_key = ''
    modelForm.api_base = defaultApiBases['openai']
  }
}

const getModelsByType = (type) => {
  return models.value.filter(m => m.type === type)
}

const loadModels = async () => {
  try {
    const response = await modelAPI.getModels()
    models.value = response || []

    // 检查配置完整性
    if (!hasChatModel.value || !hasEmbeddingModel.value) {
      showConfigWarning.value = true
    }
  } catch (error) {
    console.error('Failed to load models:', error)
    // 如果API调用失败，显示空列表
    models.value = []
  }
}

const addModel = (type) => {
  editingModel.value = null
  if (type === 'document') {
    // 文档分析模型默认不使用MinerU
    Object.assign(modelForm, {
      id: null,
      type: type,
      api_type: '',
      model_id: '',
      api_key: '',
      api_base: '',
      description: '',
      status: 'active'
    })
  } else {
    Object.assign(modelForm, {
      id: null,
      type: type,
      api_type: 'openai',
      model_id: '',
      api_key: '',
      api_base: defaultApiBases['openai'],
      description: '',
      status: 'active'
    })
  }
  showModal.value = true
}

const editModelAction = (model) => {
  editingModel.value = model
  Object.assign(modelForm, model)
  showModal.value = true
}

const saveModel = async () => {
  // 文档分析模型验证逻辑
  if (modelForm.type === 'document') {
    if (modelForm.api_type === 'mineru') {
      if (!modelForm.model_id) {
        ElMessage.warning('请选择解析模式')
        return
      }
      // 精准解析需要Token
      if (modelForm.model_id === 'precision' && !modelForm.api_key) {
        ElMessage.warning('精准解析API需要配置Token')
        return
      }
    } else {
      // 文档分析模型不使用MinerU时，不需要填写其他字段
      // 允许 api_type 为空（即不使用任何配置）
    }
  } else {
    // 其他模型验证逻辑
    if (!modelForm.model_id || !modelForm.api_key) {
      ElMessage.warning('请填写必填项')
      return
    }
  }

  try {
    if (editingModel.value) {
      // 更新现有模型
      await modelAPI.updateModel(modelForm.id, modelForm)
      const index = models.value.findIndex(m => m.id === editingModel.value.id)
      if (index !== -1) {
        models.value[index] = { ...modelForm }
      }
      ElMessage.success('模型配置更新成功')
    } else {
      // 添加新模型
      const response = await modelAPI.createModel(modelForm)
      models.value.push(response)
      ElMessage.success('模型添加成功')
    }
    showModal.value = false
    
    // 重新检查配置完整性
    if (hasChatModel.value && hasEmbeddingModel.value) {
      showConfigWarning.value = false
    }
  } catch (error) {
    ElMessage.error('操作失败')
    console.error('Failed to save model:', error)
  }
}

const toggleModelStatus = async (model) => {
  try {
    const newStatus = model.status === 'active' ? 'disabled' : 'active'
    await modelAPI.updateModelStatus(model.id, { status: newStatus })
    model.status = newStatus
    const action = model.status === 'active' ? '启用' : '禁用'
    ElMessage.success(`模型已${action}`)
    
    // 重新检查配置完整性
    if ((model.type === 'chat' || model.type === 'embedding') && model.status === 'disabled') {
      showConfigWarning.value = true
    }
  } catch (error) {
    ElMessage.error('操作失败')
    console.error('Failed to toggle model status:', error)
  }
}

onMounted(async () => {
  if (!authStore.user && authStore.accessToken) {
    try {
      await authStore.getCurrentUser()
    } catch (error) {
      console.error('Failed to load user info:', error)
    }
  }
  await loadModels()
})
</script>

<style scoped>
.model-manage {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  background: #f8fafc;
}

.manage-header {
  margin-bottom: 24px;
}

.manage-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.manage-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.model-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1200px;
}

.model-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.add-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.add-btn:hover {
  background: #2563eb;
}

.section-content {
  padding: 16px 20px;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.model-card {
  padding: 16px 20px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.2s;
}

.model-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.model-card.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.model-card.disabled {
  opacity: 0.6;
  background: #f9fafb;
}

.model-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.model-info-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-provider {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

.model-divider {
  color: #94a3b8;
}

.model-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.model-info-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-status-text {
  font-size: 12px;
  color: #10b981;
}

.model-status-text.disabled {
  color: #6b7280;
}

.edit-btn {
  background: #f1f5f9;
  color: #475569;
  border: none;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn:hover {
  background: #e2e8f0;
}

.model-desc {
  font-size: 12px;
  color: #64748b;
  margin-top: 8px;
  padding-left: 8px;
}

.empty-tip {
  text-align: center;
  padding: 20px;
  color: #94a3b8;
  font-size: 13px;
}

.warning-list {
  margin-top: 16px;
}

.warning-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  color: #dc2626;
}

.dialog-footer {
  display: flex;
  gap: 8px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
}
</style>
