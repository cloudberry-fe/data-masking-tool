<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" :width="240" collapsible>
      <div class="logo">
        <h2 v-if="!collapsed">Cloudberry</h2>
        <h2 v-else>CLD</h2>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        mode="inline"
        theme="dark"
        :inline-collapsed="collapsed"
      >
        <template v-for="item in menuItems" :key="item.path">
          <a-sub-menu v-if="item.children" :key="item.path">
            <template #icon>
              <component :is="item.icon" />
            </template>
            <template #title>{{ item.title }}</template>
            <a-menu-item
              v-for="child in item.children"
              :key="child.path"
              @click="navigateTo(child.path)"
            >
              {{ child.title }}
            </a-menu-item>
          </a-sub-menu>
          <a-menu-item v-else :key="item.path" @click="navigateTo(item.path)">
            <template #icon>
              <component :is="item.icon" />
            </template>
            {{ item.title }}
          </a-menu-item>
        </template>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header class="header">
        <div class="header-left">
          <a-button type="text" @click="collapsed = !collapsed">
            <MenuUnfoldOutlined v-if="collapsed" />
            <MenuFoldOutlined v-else />
          </a-button>
        </div>
        <div class="header-right">
          <a-dropdown>
            <a class="user-dropdown">
              <UserOutlined />
              <span>{{ userStore.realName || userStore.username }}</span>
              <DownOutlined />
            </a>
            <template #overlay>
              <a-menu>
                <a-menu-item key="logout" @click="handleLogout">
                  <LogoutOutlined />
                  Logout
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  HomeOutlined,
  DatabaseOutlined,
  SafetyOutlined,
  BranchesOutlined,
  SwapOutlined,
  SettingOutlined,
  UserOutlined,
  DownOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>([])
const openKeys = ref<string[]>([])

const menuItems = [
  { path: '/dashboard', title: 'Dashboard', icon: HomeOutlined },
  { path: '/datasources', title: 'Data Sources', icon: DatabaseOutlined },
  { path: '/masking', title: 'Data Masking', icon: SafetyOutlined },
  { path: '/lineage', title: 'Lineage Analysis', icon: BranchesOutlined },
  { path: '/sync', title: 'Data Sync', icon: SwapOutlined },
  {
    path: '/system',
    title: 'System',
    icon: SettingOutlined,
    children: [
      { path: '/system/users', title: 'Users' },
      { path: '/system/roles', title: 'Roles' },
      { path: '/system/audit', title: 'Audit Logs' }
    ]
  }
]

function navigateTo(path: string) {
  router.push(path)
}

function handleLogout() {
  userStore.logout()
  message.success('Logged out successfully')
  router.push('/login')
}
</script>

<style scoped>
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.logo h2 {
  margin: 0;
  font-size: 16px;
  color: white;
  white-space: nowrap;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: white;
  border-bottom: 1px solid #f0f0f0;
}

.header-right .user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.content {
  margin: 24px;
  padding: 24px;
  background: white;
  min-height: calc(100vh - 112px);
  border-radius: 8px;
}
</style>
