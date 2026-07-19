import { defineStore } from 'pinia'
import { documentAPI } from '@open/api'

export const useDocumentStore = defineStore('document', {
  state: () => ({
    documents: [],
    currentDocument: null,
    trashDocuments: [],
    versions: [],
    total: 0,
    page: 1,
    pageSize: 20
  }),

  actions: {
    async fetchDocuments(params = {}) {
      const res = await documentAPI.getDocuments({ ...params, page: this.page, page_size: this.pageSize })
      this.documents = res
      return res
    },

    async fetchDocument(id) {
      this.currentDocument = await documentAPI.getDocument(id)
      return this.currentDocument
    },

    async createDocument(data) {
      return await documentAPI.createDocument(data)
    },

    async updateDocument(id, data) {
      return await documentAPI.updateDocument(id, data)
    },

    async deleteDocument(id) {
      await documentAPI.deleteDocument(id)
      this.documents = this.documents.filter(d => d.id !== id)
    },

    async restoreDocument(id) {
      await documentAPI.restoreDocument(id)
      this.trashDocuments = this.trashDocuments.filter(d => d.id !== id)
    },

    async fetchTrash() {
      this.trashDocuments = await documentAPI.getTrash()
    },

    async fetchVersions(id) {
      this.versions = await documentAPI.getVersions(id)
    },

    async toggleFavorite(id) {
      return await documentAPI.toggleFavorite(id)
    },

    async toggleLike(id) {
      return await documentAPI.toggleLike(id)
    },

    async shareDocument(id) {
      return await documentAPI.shareDocument(id)
    }
  }
})
