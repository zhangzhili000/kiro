import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@open/api/request'

export const useAIService = defineStore('ai', () => {
  const conversations = ref([])
  const isLoading = ref(false)

  const chat = async (question, useContext = true) => {
    isLoading.value = true
    try {
      const response = await request.post('/ai/chat', {
        question,
        use_context: useContext
      })
      return response.data
    } finally {
      isLoading.value = false
    }
  }

  const chatStream = async (question, useContext = true, conversationUuid = null, conversationMode = 'fast_qa', callbacks = {}) => {
    isLoading.value = true
    
    const {
      onStep,
      onSearchResult,
      onContent,
      onQuestionAnalysis,
      onDone,
      onError
    } = callbacks

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('/api/v1/ai/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          question,
          use_context: useContext,
          conversation_uuid: conversationUuid,
          conversation_mode: conversationMode
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const processEvent = (eventData) => {
        try {
          const data = JSON.parse(eventData)
          
          switch (data.type) {
            case 'step':
              onStep && onStep(data.data)
              break
            case 'search_result':
              onSearchResult && onSearchResult(data.data)
              break
            case 'content':
              onContent && onContent(data.data)
              break
            case 'question_analysis':
              onQuestionAnalysis && onQuestionAnalysis(data.data)
              break
            case 'done':
              onDone && onDone(data.data)
              break
            case 'error':
              onError && onError(new Error(data.data.message))
              break
          }
        } catch (e) {
          console.error('Failed to parse SSE event:', e, eventData)
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          if (buffer.trim()) {
            const dataMatch = buffer.match(/data: (.+)/)
            if (dataMatch) {
              processEvent(dataMatch[1])
            }
          }
          break
        }

        buffer += decoder.decode(value, { stream: true })
        
        let eventBoundary
        while ((eventBoundary = buffer.indexOf('\n\n')) !== -1) {
          const rawEvent = buffer.slice(0, eventBoundary)
          buffer = buffer.slice(eventBoundary + 2)
          
          const dataMatch = rawEvent.match(/data: (.+)/)
          if (dataMatch) {
            processEvent(dataMatch[1])
          }
        }
      }
    } catch (error) {
      console.error('Stream chat error:', error)
      onError && onError(error)
    } finally {
      isLoading.value = false
    }
  }

  const getConversationHistory = async () => {
    try {
      console.log('Fetching conversation history from API...')
      const response = await request.get('/ai/chat/history')
      console.log('API response:', response)
      console.log('Conversations data:', response.conversations)
      conversations.value = response.conversations
      return conversations.value
    } catch (error) {
      console.error('Failed to get conversation history:', error)
      return []
    }
  }

  const getConversationByUuid = async (conversationUuid) => {
    try {
      // request拦截器会直接返回response.data，所以response其实就是data
      const response = await request.get(`/ai/chat/conversation/${conversationUuid}`)
      
      // 添加空值检查
      if (!response) {
        console.error('Response is undefined')
        return []
      }
      console.log('Conversations array:', response.conversations)
      return response.conversations || []
    } catch (error) {
      console.error('Failed to get conversation by UUID:', error)
      console.error('Error message:', error.message)
      console.error('Error response:', error.response)
      return []
    }
  }

  const deleteConversation = async (conversationId) => {
    try {
      await request.delete(`/ai/chat/history/${conversationId}`)
      conversations.value = conversations.value.filter(c => c.id !== conversationId)
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  const deleteConversationSession = async (conversationUuid) => {
    try {
      await request.delete(`/ai/chat/conversation/${conversationUuid}`)
      // 移除所有具有该conversation_uuid的对话
      conversations.value = conversations.value.filter(c => c.conversation_uuid !== conversationUuid)
    } catch (error) {
      console.error('Failed to delete conversation session:', error)
      throw error
    }
  }

  const updateConversationTitle = async (conversationUuid, title) => {
    try {
      const response = await request.put('/ai/chat/conversation/title', {
        conversation_uuid: conversationUuid,
        title: title
      })
      // 更新本地状态
      conversations.value = conversations.value.map(c => {
        if (c.conversation_uuid === conversationUuid) {
          return { ...c, title: title }
        }
        return c
      })
      return response
    } catch (error) {
      console.error('Failed to update conversation title:', error)
      throw error
    }
  }

  const stopChatStream = async (conversationUuid) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/v1/ai/chat/stream/stop/${conversationUuid}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        }
      })
      return response.json()
    } catch (error) {
      console.error('Failed to stop chat stream:', error)
      throw error
    }
  }

  const getDocumentSummary = async (documentId) => {
    try {
      const response = await request.get(`/ai/documents/${documentId}/summary`)
      return response.data
    } catch (error) {
      console.error('Failed to get document summary:', error)
      throw error
    }
  }

  // AI配置管理
  const getAIConfig = async () => {
    try {
      const response = await request.get('/ai/config')
      return response
    } catch (error) {
      console.error('Failed to get AI config:', error)
      return {
        roleDefinition: {
          name: '企业知识助手',
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
      }
    }
  }

  const updateAIConfig = async (config) => {
    try {
      const response = await request.put('/ai/config', config)
      return response
    } catch (error) {
      console.error('Failed to update AI config:', error)
      throw error
    }
  }

  const updateRoleDefinition = async (roleDefinition) => {
    try {
      const response = await request.put('/ai/config/role-definition', roleDefinition)
      return response
    } catch (error) {
      console.error('Failed to update role definition:', error)
      throw error
    }
  }

  const updateRules = async (rules) => {
    try {
      const response = await request.put('/ai/config/rules', rules)
      return response
    } catch (error) {
      console.error('Failed to update rules:', error)
      throw error
    }
  }

  const addPromptTemplate = async (template) => {
    try {
      const response = await request.post('/ai/prompt-templates', template)
      return response
    } catch (error) {
      console.error('Failed to add prompt template:', error)
      throw error
    }
  }

  const updatePromptTemplate = async (template) => {
    try {
      const response = await request.put(`/ai/prompt-templates/${template.id}`, template)
      return response
    } catch (error) {
      console.error('Failed to update prompt template:', error)
      throw error
    }
  }

  const deletePromptTemplate = async (templateId) => {
    try {
      const response = await request.delete(`/ai/prompt-templates/${templateId}`)
      return response
    } catch (error) {
      console.error('Failed to delete prompt template:', error)
      throw error
    }
  }

  const getDocumentKeywords = async (documentId) => {
    try {
      const response = await request.get(`/ai/documents/${documentId}/keywords`)
      return response.data
    } catch (error) {
      console.error('Failed to get document keywords:', error)
      throw error
    }
  }

  const processDocument = async (documentId) => {
    isLoading.value = true
    try {
      const response = await request.post(`/ai/documents/${documentId}/process`)
      return response.data
    } finally {
      isLoading.value = false
    }
  }

  const searchVectors = async (query, topK = 5) => {
    try {
      const response = await request.post('/ai/vectors/search', {
        query,
        top_k: topK
      })
      return response.data
    } catch (error) {
      console.error('Failed to search vectors:', error)
      throw error
    }
  }

  const buildVectorIndex = async () => {
    isLoading.value = true
    try {
      const response = await request.post('/ai/vectors/index')
      return response.data
    } finally {
      isLoading.value = false
    }
  }

  return {
    conversations,
    isLoading,
    chat,
    chatStream,
    stopChatStream,
    getConversationHistory,
    getConversationByUuid,
    deleteConversation,
    deleteConversationSession,
    updateConversationTitle,
    getDocumentSummary,
    getDocumentKeywords,
    processDocument,
    searchVectors,
    buildVectorIndex,
    getAIConfig,
    updateAIConfig,
    updateRoleDefinition,
    updateRules,
    addPromptTemplate,
    updatePromptTemplate,
    deletePromptTemplate
  }
})
