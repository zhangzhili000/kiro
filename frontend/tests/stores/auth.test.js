import { describe, it, expect } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should have initial state', () => {
    const authStore = useAuthStore()

    expect(authStore.user).toBeNull()
    expect(authStore.isAuthenticated).toBe(false)
  })

  it('should be authenticated when token exists', () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const authStore = useAuthStore()

    localStorage.setItem('access_token', 'test_token')
    authStore.accessToken = 'test_token'

    expect(authStore.isAuthenticated).toBe(true)
  })

  it('should not be authenticated when token is null', () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const authStore = useAuthStore()

    authStore.accessToken = null

    expect(authStore.isAuthenticated).toBe(false)
  })

  it('should be admin when role is admin', () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const authStore = useAuthStore()

    authStore.user = { role: 'admin' }

    expect(authStore.isAdmin).toBe(true)
  })

  it('should not be admin when role is user', () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const authStore = useAuthStore()

    authStore.user = { role: 'user' }

    expect(authStore.isAdmin).toBe(false)
  })
})
