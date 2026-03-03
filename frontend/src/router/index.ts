import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页', icon: 'home' }
      },
      {
        path: 'datasources',
        name: 'Datasources',
        component: () => import('@/views/datasource/List.vue'),
        meta: { title: '数据源管理', icon: 'database' }
      },
      {
        path: 'masking',
        name: 'Masking',
        component: () => import('@/views/masking/List.vue'),
        meta: { title: '数据脱敏', icon: 'safety' }
      },
      {
        path: 'masking/:id',
        name: 'MaskingDetail',
        component: () => import('@/views/masking/Detail.vue'),
        meta: { title: '脱敏任务详情', hidden: true }
      },
      {
        path: 'lineage',
        name: 'Lineage',
        component: () => import('@/views/Lineage.vue'),
        meta: { title: '血缘分析', icon: 'branches' }
      },
      {
        path: 'sync',
        name: 'Sync',
        component: () => import('@/views/sync/List.vue'),
        meta: { title: '翻数工具', icon: 'swap' }
      },
      {
        path: 'system',
        name: 'System',
        redirect: '/system/users',
        meta: { title: '系统管理', icon: 'setting' },
        children: [
          {
            path: 'users',
            name: 'Users',
            component: () => import('@/views/system/Users.vue'),
            meta: { title: '用户管理' }
          },
          {
            path: 'roles',
            name: 'Roles',
            component: () => import('@/views/system/Roles.vue'),
            meta: { title: '角色管理' }
          },
          {
            path: 'audit',
            name: 'Audit',
            component: () => import('@/views/system/Audit.vue'),
            meta: { title: '审计日志' }
          }
        ]
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/')
  } else {
    if (requiresAuth && !userStore.userInfo) {
      try {
        await userStore.fetchCurrentUser()
      } catch (error) {
        next('/login')
        return
      }
    }
    next()
  }
})

export default router
