import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

export interface UserInfo {
  user_id: number
  username: string
  real_name?: string
  roles: Array<{ id: number; code: string; name: string }>
  permissions: string[]
}

export interface LoginResponse extends UserInfo {
  access_token: string
  token_type: string
  expires_in: number
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const realName = computed(() => userInfo.value?.real_name || '')
  const roles = computed(() => userInfo.value?.roles || [])
  const permissions = computed(() => userInfo.value?.permissions || [])

  async function login(username: string, password: string): Promise<UserInfo> {
    const data = await request.post<LoginResponse>('/auth/login', { username, password })
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    userInfo.value = {
      user_id: data.user_id,
      username: data.username,
      real_name: data.real_name,
      roles: data.roles,
      permissions: data.permissions
    }
    return userInfo.value
  }

  async function fetchCurrentUser() {
    if (!token.value) return null
    try {
      const data = await request.get('/auth/current-user')
      userInfo.value = data
      return data
    } catch (error) {
      logout()
      throw error
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  function hasAnyPermission(perms: string[]): boolean {
    return perms.some(p => permissions.value.includes(p))
  }

  function hasAllPermissions(perms: string[]): boolean {
    return perms.every(p => permissions.value.includes(p))
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    realName,
    roles,
    permissions,
    login,
    fetchCurrentUser,
    logout,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions
  }
})
