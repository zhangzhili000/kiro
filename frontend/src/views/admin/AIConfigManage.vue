<template>
  <div class="ai-config-manage">
    <div class="config-header">
      <h3 class="config-title">AI助手配置管理</h3>
      <p class="config-desc">管理AI助手的提示词配置，包括角色定义和规则设置</p>
    </div>

    <div class="config-content">
      <!-- 角色定义 -->
      <div class="config-section">
        <div class="section-header">
          <h4 class="section-title">🤖 角色定义</h4>
          <div v-if="isAdmin" class="section-actions">
            <button 
              v-if="!isRoleDefinitionEditing"
              @click="editRoleDefinition" 
              class="action-btn edit"
            >
              编辑
            </button>
          </div>
        </div>
        <div class="section-content">
          <el-form :model="aiConfig.roleDefinition" :disabled="!isRoleDefinitionEditing">
            <el-form-item label="角色名称">
              <el-input v-model="aiConfig.roleDefinition.name" placeholder="请输入AI助手角色名称" />
            </el-form-item>
            <el-form-item label="角色描述">
              <el-input 
                v-model="aiConfig.roleDefinition.description" 
                type="textarea"
                placeholder="请输入AI助手角色描述"
                :rows="4"
              />
            </el-form-item>
            <el-form-item label="行为准则">
              <el-input 
                v-model="aiConfig.roleDefinition.guidelines" 
                type="textarea"
                placeholder="请输入AI助手的行为准则"
                :rows="6"
              />
            </el-form-item>
          </el-form>
          <div v-if="isRoleDefinitionEditing" class="section-footer">
            <el-button @click="cancelRoleDefinitionEdit">取消</el-button>
            <el-button 
              type="primary" 
              @click="saveRoleDefinition" 
              :loading="isSaving"
            >
              保存角色定义
            </el-button>
          </div>
        </div>
      </div>

      <!-- 规则配置 -->
      <div class="config-section">
        <div class="section-header">
          <h4 class="section-title">📋 规则配置</h4>
          <div v-if="isAdmin" class="section-actions">
            <button 
              v-if="!isRulesEditing"
              @click="editRules" 
              class="action-btn edit"
            >
              编辑
            </button>
          </div>
        </div>
        <div class="section-content">
          <el-form :model="aiConfig.rules" :disabled="!isRulesEditing">
            <el-form-item label="回答策略">
              <el-select v-model="aiConfig.rules.answerStrategy" placeholder="请选择回答策略">
                <el-option label="基于知识库" value="knowledge_base" />
                <el-option label="基于规则" value="rule_based" />
                <el-option label="混合模式" value="hybrid" />
              </el-select>
            </el-form-item>
            <el-form-item label="最大回答长度">
              <el-input-number v-model="aiConfig.rules.maxAnswerLength" :min="100" :max="5000" />
            </el-form-item>
            <el-form-item label="是否引用来源">
              <el-switch v-model="aiConfig.rules.citeSources" />
            </el-form-item>
            <el-form-item label="温度系数">
              <el-slider 
                v-model="aiConfig.rules.temperature" 
                :min="0" 
                :max="1" 
                :step="0.1"
                :show-input="true"
              />
              <span class="slider-desc">控制回答的随机性，值越高越随机</span>
            </el-form-item>
            <el-form-item label="专业领域">
              <el-select 
                v-model="aiConfig.rules.domains" 
                multiple 
                filterable 
                allow-create
                placeholder="请选择或输入专业领域"
                :reserve-keyword="true"
              >
                <el-option label="数据标准" value="数据标准" />
                <el-option label="法律法规" value="法律法规" />
                <el-option label="技术文档" value="技术文档" />
                <el-option label="业务流程" value="业务流程" />
                <el-option label="其他" value="其他" />
              </el-select>
              <span class="slider-desc">支持自定义输入新的专业领域</span>
            </el-form-item>
          </el-form>
          <div v-if="isRulesEditing" class="section-footer">
            <el-button @click="cancelRulesEdit">取消</el-button>
            <el-button 
              type="primary" 
              @click="saveRules" 
              :loading="isSaving"
            >
              保存规则配置
            </el-button>
          </div>
        </div>
      </div>

      <!-- 提示词模板 -->
      <div class="config-section">
        <div class="section-header">
          <h4 class="section-title">📝 提示词模板</h4>
          <button 
            v-if="isAdmin"
            @click="addTemplate" 
            class="add-btn"
          >
            + 添加模板
          </button>
        </div>
        <div class="section-content">
          <div class="template-list">
            <div 
              v-for="(template, index) in aiConfig.promptTemplates" 
              :key="template.id"
              class="template-card"
            >
              <div class="template-header">
                <span class="template-name">{{ template.name }}</span>
                <span class="template-tag" :class="template.type">{{ getTemplateTypeLabel(template.type) }}</span>
              </div>
              <div class="template-content">
                <pre class="template-text">{{ template.content }}</pre>
              </div>
              <div class="template-footer">
                <span class="template-description">{{ template.description }}</span>
                <div v-if="isAdmin" class="template-actions">
                  <button @click="editTemplate(index)" class="action-btn edit">编辑</button>
                  <button @click="deleteTemplate(index)" class="action-btn delete">删除</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- 添加/编辑模板弹窗 -->
    <el-dialog 
      v-model="showTemplateModal"
      :title="editingTemplate !== null ? '编辑提示词模板' : '添加提示词模板'" 
      width="600px"
    >
      <el-form :model="templateForm">
        <el-form-item label="模板名称" required>
          <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="模板类型" required>
          <el-select v-model="templateForm.type" placeholder="请选择模板类型">
            <el-option label="角色定义" value="role" />
            <el-option label="回答规则" value="rule" />
            <el-option label="格式要求" value="format" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input v-model="templateForm.description" placeholder="请输入模板描述" />
        </el-form-item>
        <el-form-item label="模板内容" required>
          <el-input 
            v-model="templateForm.content" 
            type="textarea"
            placeholder="请输入提示词模板内容"
            :rows="8"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showTemplateModal = false">取消</el-button>
          <el-button type="primary" @click="saveTemplate">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useAIService } from '@/stores/ai'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const aiService = useAIService()
const authStore = useAuthStore()

const isAdmin = computed(() => {
  const user = authStore.user
  if (!user) {
    console.warn('User not loaded yet, isAdmin defaulting to false')
    return false
  }
  return user.role === 'admin' || user.is_superuser
})

const isSaving = ref(false)
const showTemplateModal = ref(false)
const editingTemplate = ref(null)
const isRoleDefinitionEditing = ref(false)
const isRulesEditing = ref(false)

// 备份原始数据用于取消操作
const originalRoleDefinition = reactive({
  name: '',
  description: '',
  guidelines: ''
})
const originalRules = reactive({
  answerStrategy: 'hybrid',
  maxAnswerLength: 2000,
  citeSources: true,
  temperature: 0.7,
  domains: []
})

const aiConfig = reactive({
  roleDefinition: {
    name: '',
    description: '',
    guidelines: ''
  },
  rules: {
    answerStrategy: 'hybrid',
    maxAnswerLength: 2000,
    citeSources: true,
    temperature: 0.7,
    domains: []
  },
  promptTemplates: []
})

const templateForm = reactive({
  name: '',
  type: 'role',
  description: '',
  content: ''
})

const getTemplateTypeLabel = (type) => {
  const labels = {
    role: '角色定义',
    rule: '回答规则',
    format: '格式要求',
    other: '其他'
  }
  return labels[type] || type
}

const loadConfig = async () => {
  try {
    const config = await aiService.getAIConfig()
    if (config) {
      // 正确处理嵌套对象的赋值
      if (config.roleDefinition) {
        aiConfig.roleDefinition.name = config.roleDefinition.name || ''
        aiConfig.roleDefinition.description = config.roleDefinition.description || ''
        aiConfig.roleDefinition.guidelines = config.roleDefinition.guidelines || ''
      }
      if (config.rules) {
        aiConfig.rules.answerStrategy = config.rules.answerStrategy || 'hybrid'
        aiConfig.rules.maxAnswerLength = config.rules.maxAnswerLength || 2000
        aiConfig.rules.citeSources = config.rules.citeSources !== undefined ? config.rules.citeSources : true
        aiConfig.rules.temperature = config.rules.temperature !== undefined ? config.rules.temperature : 0.7
        aiConfig.rules.domains = config.rules.domains || []
      }
      // 确保 promptTemplates 是数组
      aiConfig.promptTemplates = Array.isArray(config.promptTemplates) ? config.promptTemplates : []
    }
  } catch (error) {
    console.error('Failed to load AI config:', error)
    // 使用默认配置
    aiConfig.promptTemplates = []
  }
}

const editRoleDefinition = () => {
  // 备份当前数据用于取消操作
  originalRoleDefinition.name = aiConfig.roleDefinition.name
  originalRoleDefinition.description = aiConfig.roleDefinition.description
  originalRoleDefinition.guidelines = aiConfig.roleDefinition.guidelines
  isRoleDefinitionEditing.value = true
}

const cancelRoleDefinitionEdit = () => {
  // 恢复原始数据
  aiConfig.roleDefinition.name = originalRoleDefinition.name
  aiConfig.roleDefinition.description = originalRoleDefinition.description
  aiConfig.roleDefinition.guidelines = originalRoleDefinition.guidelines
  isRoleDefinitionEditing.value = false
}

const saveRoleDefinition = async () => {
  if (!isAdmin.value) {
    ElMessage.error('没有权限保存')
    return
  }
  
  isSaving.value = true
  try {
    await aiService.updateRoleDefinition(aiConfig.roleDefinition)
    ElMessage.success('角色定义保存成功')
    isRoleDefinitionEditing.value = false
  } catch (error) {
    ElMessage.error('角色定义保存失败')
    console.error('Failed to save role definition:', error)
  } finally {
    isSaving.value = false
  }
}

const editRules = () => {
  // 备份当前数据用于取消操作
  originalRules.answerStrategy = aiConfig.rules.answerStrategy
  originalRules.maxAnswerLength = aiConfig.rules.maxAnswerLength
  originalRules.citeSources = aiConfig.rules.citeSources
  originalRules.temperature = aiConfig.rules.temperature
  originalRules.domains = [...aiConfig.rules.domains]
  isRulesEditing.value = true
}

const cancelRulesEdit = () => {
  // 恢复原始数据
  aiConfig.rules.answerStrategy = originalRules.answerStrategy
  aiConfig.rules.maxAnswerLength = originalRules.maxAnswerLength
  aiConfig.rules.citeSources = originalRules.citeSources
  aiConfig.rules.temperature = originalRules.temperature
  aiConfig.rules.domains = [...originalRules.domains]
  isRulesEditing.value = false
}

const saveRules = async () => {
  if (!isAdmin.value) return
  
  isSaving.value = true
  try {
    await aiService.updateRules(aiConfig.rules)
    ElMessage.success('规则配置保存成功')
    isRulesEditing.value = false
  } catch (error) {
    ElMessage.error('规则配置保存失败')
    console.error('Failed to save rules:', error)
  } finally {
    isSaving.value = false
  }
}

const addTemplate = () => {
  editingTemplate.value = null
  templateForm.name = ''
  templateForm.type = 'role'
  templateForm.description = ''
  templateForm.content = ''
  showTemplateModal.value = true
}

const editTemplate = (index) => {
  editingTemplate.value = index
  const template = aiConfig.promptTemplates[index]
  templateForm.name = template.name
  templateForm.type = template.type
  templateForm.description = template.description
  templateForm.content = template.content
  showTemplateModal.value = true
}

const deleteTemplate = async (index) => {
  if (!isAdmin.value) return
  
  const template = aiConfig.promptTemplates[index]
  
  try {
    await ElMessageBox.confirm(
      `确定要删除提示词模板 "${template.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await aiService.deletePromptTemplate(template.id)
    aiConfig.promptTemplates.splice(index, 1)
    ElMessage.success('模板删除成功')
  } catch (error) {
    if (error === 'cancel') {
      // 用户取消删除，不做任何操作
      return
    }
    ElMessage.error('模板删除失败')
    console.error('Failed to delete template:', error)
  }
}

const saveTemplate = async () => {
  if (!isAdmin.value) return
  
  if (!templateForm.name || !templateForm.content) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  try {
    const templateData = {
      name: templateForm.name,
      type: templateForm.type,
      description: templateForm.description,
      content: templateForm.content
    }
    
    if (editingTemplate.value !== null) {
      // 更新模板
      templateData.id = aiConfig.promptTemplates[editingTemplate.value].id
      await aiService.updatePromptTemplate(templateData)
      aiConfig.promptTemplates[editingTemplate.value] = { ...templateData }
      ElMessage.success('模板更新成功')
    } else {
      // 添加模板
      const result = await aiService.addPromptTemplate(templateData)
      aiConfig.promptTemplates.push(result)
      ElMessage.success('模板添加成功')
    }
    
    showTemplateModal.value = false
  } catch (error) {
    ElMessage.error('操作失败')
    console.error('Failed to save template:', error)
  }
}

onMounted(async () => {
  // 确保用户信息已加载
  if (!authStore.user && authStore.accessToken) {
    try {
      await authStore.getCurrentUser()
    } catch (error) {
      console.error('Failed to load user info:', error)
    }
  }
  await loadConfig()
})
</script>

<style scoped>
.ai-config-manage {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  background: #f8fafc;
}

.config-header {
  margin-bottom: 24px;
}

.config-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.config-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.config-content {
  max-width: 900px;
}

.config-section {
  background: white;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.edit-badge {
  font-size: 12px;
  color: #3b82f6;
  background: #dbeafe;
  padding: 4px 10px;
  border-radius: 4px;
}

.section-content {
  padding: 20px;
}

.section-actions {
  display: flex;
  gap: 8px;
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

.template-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.template-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8fafc;
}

.template-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.template-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}

.template-tag.role {
  background: #dbeafe;
  color: #1d4ed8;
}

.template-tag.rule {
  background: #dcfce7;
  color: #166534;
}

.template-tag.format {
  background: #fef3c7;
  color: #92400e;
}

.template-tag.other {
  background: #e2e8f0;
  color: #64748b;
}

.template-content {
  padding: 12px 16px;
}

.template-text {
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.template-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.section-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.template-description {
  font-size: 12px;
  color: #94a3b8;
}

.template-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  font-size: 12px;
  padding: 4px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.edit {
  background: #f1f5f9;
  color: #475569;
}

.action-btn.edit:hover {
  background: #e2e8f0;
}

.action-btn.delete {
  background: #fee2e2;
  color: #dc2626;
}

.action-btn.delete:hover {
  background: #fecaca;
}

.config-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.slider-desc {
  display: block;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
}

:deep(.el-textarea__inner) {
  font-family: monospace;
}
</style>