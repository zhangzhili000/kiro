import request from './request'

export const authAPI = {
  register: (data) => request.post('/auth/register', data),
  login: (data) => request.post('/auth/login', data),
  refresh: (data) => request.post('/auth/refresh', data),
  logout: () => request.post('/auth/logout')
}

export const userAPI = {
  getCurrentUser: () => request.get('/users/me'),
  updateCurrentUser: (data) => request.put('/users/me', data),
  changePassword: (data) => request.put('/users/password', data),
  uploadAvatar: (avatarUrl) => request.post('/users/avatar', null, { params: { avatar_url: avatarUrl } }),
  getUsers: () => request.get('/admin/users'),
  updateUserStatus: (userId, isActive) => request.put(`/admin/users/${userId}/status`, null, { params: { is_active: isActive } })
}

export const departmentAPI = {
  getDepartments: () => request.get('/departments'),
  getDepartmentTree: () => request.get('/departments/tree'),
  createDepartment: (data) => request.post('/departments', data),
  updateDepartment: (id, data) => request.put(`/departments/${id}`, data),
  deleteDepartment: (id) => request.delete(`/departments/${id}`)
}

export const documentAPI = {
  getDocuments: (params) => request.get('/documents', { params }),
  getDocument: (id) => request.get(`/documents/${id}`),
  createDocument: (data) => request.post('/documents', data),
  updateDocument: (id, data) => request.put(`/documents/${id}`, data),
  deleteDocument: (id) => request.delete(`/documents/${id}`),
  restoreDocument: (id) => request.post(`/documents/${id}/restore`),
  getTrash: () => request.get('/documents/trash'),
  getVersions: (id) => request.get(`/documents/${id}/versions`),
  getVersion: (id, versionNumber) => request.get(`/documents/${id}/versions/${versionNumber}`),
  toggleFavorite: (id) => request.post(`/documents/${id}/favorite`),
  toggleLike: (id) => request.post(`/documents/${id}/like`),
  shareDocument: (id) => request.post(`/documents/${id}/share`),
  getSharedDocument: (token) => request.get(`/documents/share/${token}`)
}

export const categoryAPI = {
  getCategories: () => request.get('/categories'),
  getCategoryTree: () => request.get('/categories/tree'),
  createCategory: (data) => request.post('/categories', data),
  updateCategory: (id, data) => request.put(`/categories/${id}`, data),
  deleteCategory: (id) => request.delete(`/categories/${id}`)
}

export const tagAPI = {
  getTags: () => request.get('/tags'),
  createTag: (data) => request.post('/tags', data),
  updateTag: (id, data) => request.put(`/tags/${id}`, data),
  deleteTag: (id) => request.delete(`/tags/${id}`)
}

export const searchAPI = {
  search: (params) => request.get('/search', { params }),
  getSuggestions: (q) => request.get('/search/suggestions', { params: { q } })
}

export const commentAPI = {
  getComments: (documentId) => request.get(`/comments/documents/${documentId}`),
  createComment: (documentId, data) => request.post(`/comments/documents/${documentId}`, data),
  updateComment: (id, data) => request.put(`/comments/${id}`, data),
  deleteComment: (id) => request.delete(`/comments/${id}`),
  replyComment: (id, data) => request.post(`/comments/${id}/reply`, data)
}

export const notificationAPI = {
  getNotifications: () => request.get('/notifications'),
  markAsRead: (id) => request.put(`/notifications/${id}/read`),
  markAllAsRead: () => request.put('/notifications/read-all')
}

export const subscriptionAPI = {
  getSubscriptions: () => request.get('/subscriptions'),
  createSubscription: (data) => request.post('/subscriptions', data),
  deleteSubscription: (id) => request.delete(`/subscriptions/${id}`)
}

export const auditAPI = {
  getAuditLogs: (params) => request.get('/admin/audit-logs', { params })
}

export const modelAPI = {
  getModels: () => request.get('/admin/models'),
  createModel: (data) => request.post('/admin/models', data),
  updateModel: (id, data) => request.put(`/admin/models/${id}`, data),
  deleteModel: (id) => request.delete(`/admin/models/${id}`),
  updateModelStatus: (id, data) => request.patch(`/admin/models/${id}/status`, data)
}
