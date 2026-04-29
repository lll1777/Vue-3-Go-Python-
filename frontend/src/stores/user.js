import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getCurrentUser } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const currentUser = ref(null)
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value && !!currentUser.value)

  const login = async (credentials) => {
    const res = await loginApi(credentials)
    token.value = res.data.token
    localStorage.setItem('token', res.data.token)
    await fetchCurrentUser()
    return res
  }

  const fetchCurrentUser = async () => {
    try {
      const res = await getCurrentUser()
      currentUser.value = res.data
    } catch (error) {
      console.error('Failed to fetch current user:', error)
      logout()
    }
  }

  const logout = () => {
    currentUser.value = null
    token.value = ''
    localStorage.removeItem('token')
  }

  const initialize = async () => {
    if (token.value) {
      try {
        await fetchCurrentUser()
      } catch (error) {
        logout()
      }
    }
  }

  return {
    currentUser,
    token,
    isLoggedIn,
    login,
    logout,
    initialize,
    fetchCurrentUser
  }
})
