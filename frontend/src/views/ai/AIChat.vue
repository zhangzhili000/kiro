<template>
  <div class="ai-chat-container">
    <!-- 侧边栏 - 对话列表 -->
    <div class="sidebar">
      <!-- <div class="sidebar-header">
        <h3 class="sidebar-title">对话列表</h3>
      </div> -->
      
      <div class="history-list">
        <div
          v-for="(history, index) in conversationHistory"
          :key="history.id"
          :class="['history-item', { 'active': selectedConversationId === history.id, 'disabled': isLoading && loadingConversationId === selectedConversationId && selectedConversationId !== history.id }]"
        >
          <div 
            class="history-content" 
            @click="handleHistoryClick(history)"
            :class="{ 'disabled': isLoading && loadingConversationId === selectedConversationId && selectedConversationId !== history.id }"
          >
            <div class="history-question">{{ truncate(history.title || history.question, 30) }}</div>
            <div class="history-meta">
              <span class="history-time">{{ formatTime(history.created_at) }}</span>
              <span v-if="history.status === 'pending'" class="history-status pending">AI 正在思考...</span>
              <span v-else-if="history.status === 'error'" class="history-status error">对话失败</span>
            </div>
          </div>
          <div class="history-menu-wrapper">
            <button 
              class="history-menu-btn"
              @click.stop="toggleMenu(history.conversation_uuid)"
              title="更多操作"
              :disabled="isLoading && loadingConversationId === selectedConversationId"
            >
              <span class="menu-dot"></span>
              <span class="menu-dot"></span>
              <span class="menu-dot"></span>
            </button>
            <div 
              v-if="activeMenuUuid === history.conversation_uuid"
              :class="['history-menu', { 'menu-up': conversationHistory.length > 7 && index >= conversationHistory.length - 2 }]"
              @click.stop
            >
              <div class="menu-item" @click="handleEditTitle(history)">
                <span class="menu-icon">✏️</span>
                <span class="menu-text">重命名</span>
              </div>
              <div class="menu-item" @click="handleDeleteConversation(history)">
                <span class="menu-icon">🗑️</span>
                <span class="menu-text">删除</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="conversationHistory.length === 0" class="empty-history">
          <div class="empty-icon">📝</div>
          <div>暂无对话历史</div>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <button 
          @click="startNewChat" 
          class="new-chat-btn"
          :disabled="isLoading && loadingConversationId === selectedConversationId"
        >
          <svg class="new-chat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>新对话</span>
        </button>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 消息列表 -->
      <div class="message-list" ref="messageList">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-section">
          <div class="welcome-icon">🤖</div>
          <h3>欢迎使用 AI 智能助手</h3>
          <p>我可以帮您：</p>
          <div class="welcome-tips">
            <div class="tip-item">📚 查询知识库内容</div>
            <div class="tip-item">❓ 回答您的问题</div>
            <div class="tip-item">💡 提供专业建议</div>
          </div>
          <div class="permission-notice" v-if="accessibleDocCount !== null">
            <el-icon><InfoFilled /></el-icon>
            <span>您当前有权限访问 <strong>{{ accessibleDocCount }}</strong> 篇文档</span>
          </div>
        </div>
        
        <!-- 消息列表 -->
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message', { 'user-message': message.isUser, 'ai-message': !message.isUser }]"
        >
          <div class="message-avatar">
            <span v-if="message.isUser">👤</span>
            <span v-else>🤖</span>
          </div>
          
          <div class="message-content-wrapper">
            <!-- 处理步骤（历史对话中显示） -->
            <div v-if="message.processingSteps && message.processingSteps.length > 0" class="processing-steps">
              <div
                v-for="step in message.processingSteps.sort((a, b) => a.step - b.step)"
                :key="step.step"
                :class="['step-item', 'step-completed']"
              >
                <div class="step-header" @click="toggleStep(message.id, step.step)">
                  <div class="step-icon">
                    <span>✅</span>
                  </div>
                  <div class="step-info">
                    <div class="step-title">{{ step.title }}</div>
                    <div class="step-description">{{ step.description }}</div>
                    <div class="step-duration">{{ formatDuration(step.duration) }}</div>
                  </div>
                  <div class="step-toggle" :class="{ 'expanded': isStepExpanded(message.id, step.step) }">
                    <span>▼</span>
                  </div>
                </div>
                <!-- 步骤子内容 -->
                <div v-if="isStepExpanded(message.id, step.step)" class="step-content">
                  <!-- 问题分析作为"理解提问"的子模块 -->
                  <div v-if="step.title === '理解提问' && message.questionAnalysis" class="question-analysis">
                    <div class="analysis-content">{{ message.questionAnalysis }}</div>
                  </div>
                  <!-- 检索结果作为"检索相关内容"的子模块 -->
                  <div v-if="step.title === '检索相关内容' && step.search_results && step.search_results.length > 0" class="search-results-inline">
                    <div class="search-result-item" v-for="(result, idx) in step.search_results" :key="idx">
                      <span class="result-index">{{ idx + 1 }}.</span>
                      <span class="result-title">{{ result.document_title || `文档 ${result.document_id}` }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 处理步骤（实时对话中显示） -->
            <div v-else-if="message.steps && message.steps.length > 0" class="processing-steps">
              <div
                v-for="step in message.steps"
                :key="step.step"
                :class="['step-item', {
                  'step-in-progress': step.status === 'in_progress',
                  'step-completed': step.status === 'completed',
                  'step-error': step.status === 'error'
                }]"
              >
                <div class="step-header" @click="toggleStep(message.id, step.step)">
                  <div class="step-icon">
                    <span v-if="step.status === 'in_progress'">⏳</span>
                    <span v-else-if="step.status === 'completed'">✅</span>
                    <span v-else>❌</span>
                  </div>
                  <div class="step-info">
                    <div class="step-title">{{ step.title }}</div>
                    <div class="step-description">{{ step.description }}</div>
                  </div>
                  <div class="step-toggle" :class="{ 'expanded': isStepExpanded(message.id, step.step) }">
                    <span>▼</span>
                  </div>
                </div>
                <!-- 步骤子内容 -->
                <div v-if="isStepExpanded(message.id, step.step)" class="step-content">
                  <!-- 问题分析作为"理解提问"的子模块 -->
                  <div v-if="step.title === '理解提问' && message.questionAnalysis" class="question-analysis">
                    <div class="analysis-content">{{ message.questionAnalysis }}</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 待处理状态显示加载动画 -->
            <div v-if="message.status === 'pending'" class="loading-message">
              <div class="loading-spinner"></div>
              <span>AI 正在思考...</span>
            </div>
            
            <!-- AI 回答 -->
            <div v-else-if="message.content" class="message-text" v-html="formatMarkdown(message.content)"></div>
            
            <!-- 参考来源按钮 -->
            <div 
              v-if="!message.isUser && getReferenceSources(message).length > 0"
              class="reference-sources-btn"
              @click="openReferenceDrawer(message)"
            >
              <span class="ref-icon">📚</span>
              <span class="ref-text">参考来源</span>
              <span class="ref-count">({{ getReferenceSources(message).length }})</span>
            </div>
            
            <!-- 对话信息 -->
            <div v-if="message.conversationInfo && !message.isUser" class="conversation-info">
              <div class="info-item">
                <span class="info-label">🤖 模型：</span>
                <span class="info-value">{{ message.conversationInfo.model || '未知' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">🔢 Token：</span>
                <span class="info-value">{{ message.conversationInfo.tokens || 0 }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">⏰ 提问时间：</span>
                <span class="info-value">{{ formatTime(message.conversationInfo.questionTime) }}</span>
              </div>
              <div class="info-item" v-if="message.conversationInfo.answerTime">
                <span class="info-label">⏱️ 回答时间：</span>
                <span class="info-value">{{ formatTime(message.conversationInfo.answerTime) }}</span>
              </div>
              <div class="info-item" v-if="message.conversationInfo.duration">
                <span class="info-label">⚡ 耗时：</span>
                <span class="info-value">{{ formatDuration(message.conversationInfo.duration) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 加载状态：只有当正在加载的对话是当前选中的对话时才显示 -->
        <div v-if="isLoading && loadingConversationId === selectedConversationId" class="loading-message">
          <div class="loading-spinner"></div>
          <span>AI 正在思考...</span>
          <button 
            class="stop-button" 
            @click="stopChat"
            :disabled="isStopping"
          >
            {{ isStopping ? '终止中...' : '终止' }}
          </button>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="input-area">
        <!-- 对话模式选择器 -->
        <div class="conversation-mode-selector">
          <span class="mode-label">对话模式：</span>
          <div class="mode-options">
            <button
              :class="['mode-option', { 'active': conversationMode === 'fast_qa' }]"
              @click="conversationMode = 'fast_qa'"
            >
              ⚡ 快速问答
            </button>
            <button
              :class="['mode-option', { 'active': conversationMode === 'multi_round' }]"
              @click="conversationMode = 'multi_round'"
            >
              🔄 多轮对话
            </button>
          </div>
          <span v-if="conversationMode === 'multi_round'" class="mode-tip">（支持上下文记忆）</span>
        </div>
        
        <div class="input-wrapper" @click="focusInput">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="handleKeyDown"
            placeholder="输入您的问题，按 Enter 发送，Shift + Enter 换行..."
            class="message-input"
            rows="1"
            :disabled="isLoading && loadingConversationId === selectedConversationId"
            ref="inputRef"
          ></textarea>
          <button
            @click="sendMessage"
            :disabled="(isLoading && loadingConversationId === selectedConversationId) || !inputMessage.trim()"
            class="send-button"
          >
            <span v-if="isLoading && loadingConversationId === selectedConversationId">⏳</span>
            <span v-else>➤</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 参考来源侧边抽屉 -->
    <div 
      v-if="showReferenceDrawer" 
      class="reference-drawer-overlay"
      @click="closeReferenceDrawer"
    ></div>
    <div 
      v-if="showReferenceDrawer" 
      class="reference-drawer"
    >
      <div class="drawer-header">
        <h3 class="drawer-title">📚 参考来源</h3>
        <button class="drawer-close" @click="closeReferenceDrawer">✕</button>
      </div>
      <div class="drawer-content">
        <div 
          v-for="(source, index) in currentReferenceSources"
          :key="index"
          class="reference-item"
          @click="openDocument(source)"
        >
          <div class="ref-item-index">{{ index + 1 }}</div>
          <div class="ref-item-content">
            <div class="ref-item-title">{{ source.document_title || `文档 ${source.document_id}` }}</div>
            <div class="ref-item-preview">{{ source.chunk_content }}</div>
            <div class="ref-item-meta">
              <span class="ref-item-chunk">第 {{ source.chunk_index + 1 }} 段</span>
              <span class="ref-item-distance">相似度: {{ (source.distance !== undefined ? source.distance : source.similarity).toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAIService } from '@open/stores/ai'
import { ElMessageBox, ElMessage, ElInput } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'

// 为 keep-alive 组件设置名称
defineOptions({
  name: 'AIChat'
})

const router = useRouter()
const messages = ref([])
const inputMessage = ref('')
const conversationHistory = ref([])
const selectedConversationId = ref(null)
const selectedConversationUuid = ref(null) // 当前选中的对话UUID
const aiService = useAIService()
const messageList = ref(null)
const inputRef = ref(null)
const isLoading = ref(false)
const accessibleDocCount = ref(null)
const loadingConversationId = ref(null) // 跟踪当前正在加载的对话ID
const activeMenuUuid = ref(null) // 当前激活的菜单的conversation_uuid
const isStopping = ref(false) // 是否正在终止对话

// 参考来源相关状态
const showReferenceDrawer = ref(false)
const currentReferenceSources = ref([])

// 保存未完成的消息状态，按 conversationUuid 索引
const pendingMessages = ref({}) // { conversationUuid: { timestamp, messages } }

// 对话模式：fast_qa-快速问答，multi_round-多轮对话
const conversationMode = ref('fast_qa')

// 切换菜单显示
const toggleMenu = (conversationUuid) => {
  if (activeMenuUuid.value === conversationUuid) {
    activeMenuUuid.value = null
  } else {
    activeMenuUuid.value = conversationUuid
  }
}

// 关闭所有菜单
const closeMenu = () => {
  activeMenuUuid.value = null
}

// 点击外部关闭菜单
document.addEventListener('click', closeMenu)

// 保存步骤展开状态
const expandedSteps = ref({}) // { messageId: { step1: true, step2: false } }

// 切换步骤展开/折叠状态
const toggleStep = (messageId, step) => {
  if (!expandedSteps.value[messageId]) {
    expandedSteps.value[messageId] = {}
  }
  expandedSteps.value[messageId][step] = !expandedSteps.value[messageId][step]
}

// 检查步骤是否展开（默认展开）
const isStepExpanded = (messageId, step) => {
  if (!expandedSteps.value[messageId]) {
    expandedSteps.value[messageId] = {}
  }
  // 默认都展开
  if (expandedSteps.value[messageId][step] === undefined) {
    expandedSteps.value[messageId][step] = true
  }
  return expandedSteps.value[messageId][step]
}

const truncate = (text, length) => {
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

const formatTime = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatMarkdown = (content) => {
  if (!content) return ''
  
  return content
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

const formatDuration = (ms) => {
  if (!ms) return '0ms'
  if (ms < 1000) return `${ms}ms`
  const seconds = (ms / 1000).toFixed(2)
  return `${seconds}s`
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageList.value) {
      messageList.value.scrollTop = messageList.value.scrollHeight
    }
  })
}

const autoResizeInput = () => {
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
      inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 200) + 'px'
    }
  })
}

const focusInput = () => {
  if (inputRef.value && !(isLoading.value && loadingConversationId.value === selectedConversationId.value)) {
    inputRef.value.focus()
  }
}

watch(inputMessage, () => {
  autoResizeInput()
})

const handleKeyDown = (event) => {
  if (event.shiftKey) {
    return
  }
  sendMessage()
}

// 处理对话历史点击（AI思考时禁止切换到其他对话）
const handleHistoryClick = (history) => {
  // 如果AI正在思考且当前选中的对话不是目标对话，则禁止切换
  if (isLoading.value && loadingConversationId.value === selectedConversationId.value && selectedConversationId.value !== history.id) {
    ElMessage.warning('AI 正在思考中，请等待回答完成或点击"终止"按钮停止')
    return
  }
  loadConversation(history)
}

// 终止对话
const stopChat = async () => {
  if (!selectedConversationUuid.value) return
  
  isStopping.value = true
  try {
    await aiService.stopChatStream(selectedConversationUuid.value)
    ElMessage.info('对话已终止')
  } catch (error) {
    console.error('Failed to stop chat:', error)
    ElMessage.error('终止对话失败')
  } finally {
    isStopping.value = false
  }
}

const startNewChat = () => {
  messages.value = []
  selectedConversationId.value = null
  selectedConversationUuid.value = null // 重置 conversation_uuid
  scrollToBottom()
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || (isLoading.value && loadingConversationId.value === selectedConversationId.value)) return

  const newConversationId = Date.now()
  loadingConversationId.value = newConversationId
  selectedConversationId.value = newConversationId

  // 保存当前会话的 UUID（新对话为 null）
  const currentConversationUuid = selectedConversationUuid.value

  messages.value.push({
    id: Date.now(),
    content: message,
    isUser: true,
    steps: [],
    searchResults: [],
    referencedDocs: []
  })
  inputMessage.value = ''
  autoResizeInput()
  scrollToBottom()

  const aiMessageId = Date.now() + 1
  messages.value.push({
    id: aiMessageId,
    content: '',
    isUser: false,
    steps: [],
    searchResults: [],
    referencedDocs: [],
    conversationInfo: null,
    questionAnalysis: ''
  })
  isLoading.value = true
  
  // 触发AI聊天开始事件
  window.dispatchEvent(new Event('ai-chat-start'))

  try {
    // 保存未完成的消息状态
    const pendingKey = currentConversationUuid || `temp-${newConversationId}`
    pendingMessages.value[pendingKey] = {
      timestamp: Date.now(),
      messages: [...messages.value]
    }

    await aiService.chatStream(message, true, selectedConversationUuid.value, conversationMode.value, {
      onStep: (stepData) => {
        const aiMessage = messages.value.find(m => m.id === aiMessageId)
        if (aiMessage) {
          aiMessage.steps = aiMessage.steps.filter(s => s.step !== stepData.step)
          aiMessage.steps.push(stepData)
          scrollToBottom()
          // 更新未完成的消息状态
          if (pendingMessages.value[pendingKey]) {
            pendingMessages.value[pendingKey].messages = [...messages.value]
          }
        }
      },
      onSearchResult: (searchData) => {
        const aiMessage = messages.value.find(m => m.id === aiMessageId)
        if (aiMessage) {
          aiMessage.searchResults = searchData.results
          scrollToBottom()
          // 更新未完成的消息状态
          if (pendingMessages.value[pendingKey]) {
            pendingMessages.value[pendingKey].messages = [...messages.value]
          }
        }
      },
      onQuestionAnalysis: (analysisData) => {
        const aiMessage = messages.value.find(m => m.id === aiMessageId)
        if (aiMessage) {
          aiMessage.questionAnalysis += analysisData.content
          scrollToBottom()
          // 更新未完成的消息状态
          if (pendingMessages.value[pendingKey]) {
            pendingMessages.value[pendingKey].messages = [...messages.value]
          }
        }
      },
      onContent: (contentData) => {
        const aiMessage = messages.value.find(m => m.id === aiMessageId)
        if (aiMessage) {
          aiMessage.content += contentData.content
          scrollToBottom()
          // 更新未完成的消息状态
          if (pendingMessages.value[pendingKey]) {
            pendingMessages.value[pendingKey].messages = [...messages.value]
          }
        }
      },
      onDone: async (doneData) => {
        const aiMessage = messages.value.find(m => m.id === aiMessageId)
        if (aiMessage) {
          aiMessage.conversationId = doneData.conversation_id
          aiMessage.conversationUuid = doneData.conversation_uuid // 新增 conversation_uuid
          aiMessage.conversationInfo = {
            model: doneData.model,
            tokens: doneData.tokens,
            questionTime: doneData.question_time,
            answerTime: doneData.answer_time,
            duration: doneData.duration
          }
          aiMessage.processingSteps = doneData.processing_steps
          selectedConversationId.value = doneData.conversation_id
          selectedConversationUuid.value = doneData.conversation_uuid // 设置当前对话UUID
          loadingConversationId.value = doneData.conversation_id
        }
        // 清除未完成的消息状态
        delete pendingMessages.value[pendingKey]
        if (currentConversationUuid) {
          delete pendingMessages.value[`temp-${newConversationId}`]
        }
        await loadConversationHistory()
        isLoading.value = false
        loadingConversationId.value = null
        // 触发AI聊天结束事件
        window.dispatchEvent(new Event('ai-chat-end'))
      },
      onError: (error) => {
        const aiMessage = messages.value.find(m => m.id === aiMessageId)
        if (aiMessage) {
          aiMessage.content = `抱歉，出现错误：${error.message}`
        }
        // 清除未完成的消息状态
        delete pendingMessages.value[pendingKey]
        if (currentConversationUuid) {
          delete pendingMessages.value[`temp-${newConversationId}`]
        }
        isLoading.value = false
        loadingConversationId.value = null
        // 触发AI聊天结束事件
        window.dispatchEvent(new Event('ai-chat-end'))
      }
    })
  } catch (error) {
    const aiMessage = messages.value.find(m => m.id === aiMessageId)
    if (aiMessage) {
      aiMessage.content = `抱歉，出现错误：${error.message}`
    }
    // 清除未完成的消息状态
    const pendingKey = currentConversationUuid || `temp-${newConversationId}`
    delete pendingMessages.value[pendingKey]
    if (currentConversationUuid) {
      delete pendingMessages.value[`temp-${newConversationId}`]
    }
    isLoading.value = false
    loadingConversationId.value = null
    // 触发AI聊天结束事件
    window.dispatchEvent(new Event('ai-chat-end'))
  }
}

const loadConversation = async (conversation) => {
  selectedConversationId.value = conversation.id
  selectedConversationUuid.value = conversation.conversation_uuid // 设置 conversation_uuid
  
  // 检查是否有未完成的消息
  if (pendingMessages.value[conversation.conversation_uuid]) {
    console.log('Loading pending messages for conversation:', conversation.conversation_uuid)
    messages.value = [...pendingMessages.value[conversation.conversation_uuid].messages]
    scrollToBottom()
    return
  }
  
  // 使用新接口获取该会话的所有消息（最多50条）
  const sameConversationMessages = await aiService.getConversationByUuid(conversation.conversation_uuid)
  
  // 按时间排序
  sameConversationMessages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  
  // 构建消息列表
  const newMessages = []
  sameConversationMessages.forEach((conv, index) => {
    newMessages.push({
      id: conv.id,
      content: conv.question,
      isUser: true,
      steps: [],
      searchResults: [],
      referencedDocs: conv.referenced_docs || []
    })
    
    // 如果对话状态为pending（待处理），显示加载状态
    if (conv.status === 'pending') {
      newMessages.push({
        id: conv.id + 100000,
        content: '',
        isUser: false,
        steps: [],
        searchResults: [],
        referencedDocs: [],
        processingSteps: [],
        questionAnalysis: '',
        conversationInfo: null,
        status: 'pending'
      })
    } else {
      newMessages.push({
        id: conv.id + 100000, // 用一个偏移避免ID冲突
        content: conv.answer || (conv.status === 'error' ? '对话失败，请重试' : ''),
        isUser: false,
        steps: [],
        searchResults: [],
        referencedDocs: conv.referenced_docs || [],
        processingSteps: conv.processing_steps || [],
        questionAnalysis: conv.question_analysis || '',
        conversationInfo: {
          model: conv.model,
          tokens: conv.tokens,
          questionTime: conv.question_time,
          answerTime: conv.answer_time,
          duration: conv.duration
        }
      })
    }
  })
  
  messages.value = newMessages
  scrollToBottom()
}

const loadConversationHistory = async () => {
  try {
    console.log('Loading conversation history...')
    const history = await aiService.getConversationHistory()
    console.log('Conversation history loaded:', history)
    
    // 按 conversation_uuid 分组，每个对话只显示一次（取最早的一条作为标题）
    const groupedConversations = {}
    // 先按时间从旧到新排序
    history.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    
    history.forEach(conv => {
      if (!groupedConversations[conv.conversation_uuid]) {
        groupedConversations[conv.conversation_uuid] = conv
      }
    })
    
    // 转换为数组并按时间从新到旧排序（显示时最新的在最前面）
    const groupedArray = Object.values(groupedConversations)
    groupedArray.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    conversationHistory.value = groupedArray
    
    // 不自动加载历史对话，保持新对话状态
    console.log('Conversation list loaded, keeping new conversation state')
  } catch (error) {
    console.error('Failed to load conversation history:', error)
  }
}

// 参考来源相关函数
const getReferenceSources = (message) => {
  if (!message) return []
  
  // 从processingSteps的步骤2中获取
  if (message.processingSteps) {
    const step2 = message.processingSteps.find(s => s.step === 2)
    if (step2 && step2.search_results) {
      return step2.search_results
    }
  }
  
  // 从searchResults获取
  if (message.searchResults && message.searchResults.length > 0) {
    return message.searchResults
  }
  
  // 从referencedDocs获取
  if (message.referencedDocs && message.referencedDocs.length > 0) {
    return message.referencedDocs
  }
  
  return []
}

const openReferenceDrawer = (message) => {
  currentReferenceSources.value = getReferenceSources(message)
  showReferenceDrawer.value = true
}

const closeReferenceDrawer = () => {
  showReferenceDrawer.value = false
  currentReferenceSources.value = []
}

const openDocument = (source) => {
  // 使用 Vue Router 在同一个应用内打开文档
  if (source.document_id) {
    closeReferenceDrawer()
    router.push(`/documents/${source.document_id}`)
  }
}

const handleDeleteConversation = async (conversation) => {
    try {
      // 关闭菜单
      activeMenuUuid.value = null
      
      await ElMessageBox.confirm(
        '确定要删除这个对话吗？删除后将无法恢复。',
        '删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--danger'
        }
      )

      await aiService.deleteConversationSession(conversation.conversation_uuid)
      ElMessage.success('对话已删除')

      // 如果删除的是当前选中的对话，清空消息
      if (selectedConversationUuid.value === conversation.conversation_uuid) {
        messages.value = []
        selectedConversationId.value = null
        selectedConversationUuid.value = null
      }

      // 重新加载对话历史
      await loadConversationHistory()
    } catch (error) {
      if (error !== 'cancel') {
        console.error('Failed to delete conversation:', error)
        ElMessage.error('删除失败')
      }
    }
  }

  const handleEditTitle = async (conversation) => {
    try {
      // 关闭菜单
      activeMenuUuid.value = null
      
      const { value: newTitle } = await ElMessageBox.prompt(
        '请输入新的对话标题',
        '重命名对话',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputValue: conversation.title || conversation.question,
          inputPlaceholder: '请输入标题',
          inputPattern: /\S+/,
          inputErrorMessage: '标题不能为空'
        }
      )

      if (newTitle) {
        await aiService.updateConversationTitle(conversation.conversation_uuid, newTitle)
        ElMessage.success('标题已更新')
        
        // 重新加载对话历史以更新显示
        await loadConversationHistory()
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('Failed to update conversation title:', error)
        ElMessage.error('更新失败')
      }
    }
  }

onMounted(() => {
  loadConversationHistory()
  fetchAccessibleDocCount()
  
  // 刷新页面后，确保消息列表不为空时也能正确显示
  // 检查是否有未完成的消息状态（虽然刷新后会丢失，但做个保障）
  if (messages.value.length === 0 && selectedConversationId.value !== null) {
    console.log('Warning: selectedConversationId is set but messages is empty')
    selectedConversationId.value = null
  }
})

// 获取用户可访问的文档数量
const fetchAccessibleDocCount = async () => {
  try {
    const response = await fetch('/api/v1/ai/accessible-docs-count', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    })
    if (response.ok) {
      const data = await response.json()
      accessibleDocCount.value = data.count
    }
  } catch (error) {
    console.error('获取可访问文档数量失败:', error)
  }
}

onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
})
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  height: 100%;
  background: #f8fafc;
  overflow: hidden;
  border-radius: 8px;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  border-radius: 8px 0 0 8px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 20px 16px;
  border-bottom: none;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  position: relative;
}

.history-item:hover {
  background: #f1f5f9;
}

.history-item.active {
  background: #e0f2fe;
}

.history-content {
  flex: 1;
  overflow: hidden;
  min-width: 0;
}

.history-question {
  font-size: 14px;
  color: #1e293b;
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 400;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.history-time {
  font-size: 12px;
  color: #94a3b8;
}

.history-status {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.history-status.pending {
  background: #fef3c7;
  color: #d97706;
}

.history-status.error {
  background: #fee2e2;
  color: #dc2626;
}

.history-menu-wrapper {
  position: relative;
  flex-shrink: 0;
}

.history-menu-btn {
  display: none;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  padding: 0;
  transition: all 0.2s;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 2px;
}

.history-item:hover .history-menu-btn,
.history-menu-btn:focus {
  display: flex;
}

.history-menu-btn:hover {
  background: #e2e8f0;
}

.menu-dot {
  width: 4px;
  height: 4px;
  background: #64748b;
  border-radius: 50%;
}

.history-menu {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 4px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 120px;
  z-index: 100;
  overflow: hidden;
  animation: menuOpen 0.15s ease-out;
}

.history-menu.menu-up {
  top: auto;
  bottom: 100%;
  margin-top: 0;
  margin-bottom: 4px;
  animation: menuOpenUp 0.15s ease-out;
}

@keyframes menuOpen {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes menuOpenUp {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 14px;
  color: #1e293b;
}

.menu-item:hover {
  background: #f1f5f9;
}

.menu-item:last-child {
  color: #ef4444;
}

.menu-icon {
  font-size: 16px;
  line-height: 1;
}

.empty-history {
  text-align: center;
  color: #64748b;
  font-size: 12px;
  padding: 24px 12px;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.sidebar-footer {
  padding: 10px 16px;
  border-top: 1px solid #e2e8f0;
}

.new-chat-btn {
  width: 100%;
  padding: 12px 16px;
  background: white;
  color: #1e293b;
  border: 2px solid #e2e8f0;
  border-radius: 9999px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.new-chat-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.new-chat-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  border-radius: 0 8px 8px 0;
  min-width: 0;
}

.header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 10px 16px;
  flex-shrink: 0;
}

.header-title h2 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 2px 0;
}

.subtitle {
  color: #64748b;
  font-size: 12px;
  margin: 0;
}

/* 消息列表 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 欢迎区域 */
.welcome-section {
  text-align: center;
  padding: 30px 20px;
  margin: auto 0;
}

.welcome-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.welcome-section h3 {
  font-size: 18px;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.welcome-section p {
  color: #64748b;
  font-size: 13px;
  margin: 0 0 16px 0;
}

.welcome-tips {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.tip-item {
  background: white;
  padding: 8px 14px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  color: #475569;
  font-size: 12px;
}

.permission-notice {
  margin-top: 16px;
  padding: 12px 16px;
  background: #f0f9eb;
  border: 1px solid #c2e7b0;
  border-radius: 4px;
  color: #67c23a;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.permission-notice strong {
  color: #67c23a;
  font-weight: 600;
}

/* 消息样式 */
.message {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  max-width: 850px;
}

.user-message {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.user-message .message-avatar {
  background: #3b82f6;
  color: white;
}

.message-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-message .message-content-wrapper {
  align-items: flex-end;
}

/* 处理步骤 */
.processing-steps {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 0;
  width: 100%;
  overflow: hidden;
}

.step-item {
  display: flex;
  flex-direction: column;
  opacity: 0.6;
  border-bottom: 1px solid #f1f5f9;
}

.step-item:last-child {
  border-bottom: none;
}

.step-in-progress {
  opacity: 1;
  animation: pulse 1.5s ease-in-out infinite;
}

.step-completed {
  opacity: 1;
}

.step-error {
  opacity: 1;
  color: #ef4444;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.step-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.step-header:hover {
  background-color: #f8fafc;
}

.step-icon {
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 1px;
}

.step-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-title {
  font-weight: 600;
  font-size: 13px;
  color: #1e293b;
}

.step-description {
  font-size: 12px;
  color: #64748b;
}

.step-duration {
  font-size: 11px;
  color: #3b82f6;
  font-weight: 500;
}

.step-toggle {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  transition: transform 0.2s ease;
  color: #94a3b8;
  font-size: 14px;
}

.step-toggle.expanded {
  transform: rotate(180deg);
}

/* 步骤内容（子模块） */
.step-content {
  padding: 0 12px 12px 34px;
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 问题分析 */
.question-analysis {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px 12px;
  margin-top: 4px;
}

.analysis-content {
  font-size: 13px;
  color: #1e293b;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 内联搜索结果 */
.search-results-inline {
  margin-top: 4px;
}

.search-results-inline .search-result-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #475569;
}

.search-results-inline .search-result-item:last-child {
  margin-bottom: 0;
}

.search-results-inline .result-index {
  font-weight: 600;
  color: #3b82f6;
  font-size: 12px;
}

.search-results-inline .result-title {
  flex: 1;
  font-weight: 500;
  color: #1e293b;
}

/* 搜索结果 */
.search-results {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px;
  width: 100%;
}

.search-title {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 8px 0;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #64748b;
  margin-bottom: 4px;
  padding: 5px 8px;
  background: #f8fafc;
  border-radius: 4px;
}

.result-index {
  font-weight: 600;
}

.result-title {
  flex: 1;
  font-weight: 500;
  color: #3b82f6;
}

.result-chunk,
.result-distance {
  font-size: 10px;
  opacity: 0.8;
}

/* 消息文本 */
.message-text {
  background: white;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.user-message .message-text {
  background: #3b82f6;
  color: white;
  border: none;
}

.user-message .message-text strong {
  color: white;
}

/* 对话信息 */
.conversation-info {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.info-value {
  font-size: 11px;
  color: #1e293b;
  font-weight: 600;
}

/* 加载状态 */
.loading-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  color: #64748b;
  font-size: 12px;
  max-width: 850px;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 终止按钮 */
.stop-button {
  margin-left: 12px;
  padding: 4px 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.stop-button:hover:not(:disabled) {
  background: #dc2626;
}

.stop-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

/* 禁用状态的历史项 */
.history-item.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.history-content.disabled {
  cursor: not-allowed;
}

/* 输入区域 */
.input-area {
  /* padding: 12px 16px; */
  /* background: white; */
  /* border-top: 1px solid #e2e8f0; */
  flex-shrink: 0;
}

/* 对话模式选择器 */
.conversation-mode-selector {
  max-width: 850px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  /* background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0; */
}

.mode-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.mode-options {
  display: flex;
  gap: 8px;
}

.mode-option {
  padding: 4px 12px;
  font-size: 12px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-option:hover {
  background: #e2e8f0;
}

.mode-option.active {
  background: #3b82f6;
  color: white;
}

.mode-tip {
  font-size: 11px;
  color: #94a3b8;
}

.input-wrapper {
  max-width: 850px;
  margin: 0 auto;
  display: flex;
  gap: 8px;
  align-items: center;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px 12px;
  transition: all 0.2s;
  cursor: text;
}

.input-wrapper:focus-within {
  border-color: #3b82f6;
  background: white;
}

.message-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 13px;
  resize: none;
  outline: none;
  max-height: 100px;
  line-height: 1.5;
  min-height: 24px;
  display: flex;
  align-items: center;
}

.message-input::placeholder {
  color: #94a3b8;
}

.send-button {
  width: 32px;
  height: 32px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button:hover:not(:disabled) {
  background: #2563eb;
  transform: scale(1.05);
}

.send-button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* 参考来源按钮 */
.reference-sources-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  width: fit-content;
}

.reference-sources-btn:hover {
  background: #e0f2fe;
  border-color: #7dd3fc;
}

.ref-icon {
  font-size: 14px;
}

.ref-text {
  font-size: 12px;
  color: #0369a1;
  font-weight: 500;
}

.ref-count {
  font-size: 12px;
  color: #0369a1;
  font-weight: 600;
}

/* 参考来源抽屉 */
.reference-drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.reference-drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 400px;
  max-width: 90vw;
  background: white;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.drawer-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.drawer-close {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.drawer-close:hover {
  background: #e2e8f0;
  color: #1e293b;
}

.drawer-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.reference-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.reference-item:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateY(-1px);
}

.ref-item-index {
  width: 24px;
  height: 24px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.ref-item-content {
  flex: 1;
  min-width: 0;
}

.ref-item-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
  line-height: 1.4;
}

.ref-item-preview {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ref-item-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.ref-item-chunk {
  font-size: 11px;
  color: #94a3b8;
}

.ref-item-distance {
  font-size: 11px;
  color: #3b82f6;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -280px;
    top: 0;
    height: 100vh;
    z-index: 100;
    transition: left 0.3s;
  }
  
  .sidebar.open {
    left: 0;
  }
  
  .message {
    max-width: 100%;
  }
  
  .welcome-tips {
    flex-direction: column;
  }
}
</style>
