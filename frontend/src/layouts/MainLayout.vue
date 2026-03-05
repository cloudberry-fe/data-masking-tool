<template>
  <a-layout style="min-height: 100vh; background: #F5F7FA;">
    <a-layout-sider v-model:collapsed="collapsed" :width="240" collapsible :theme="siderTheme">
      <div class="logo">
        <img v-if="!collapsed" src="/cloudberry-logo.svg" alt="Cloudberry" class="logo-icon" />
        <img v-else src="/cloudberry-logo-small.svg" alt="CLD" class="logo-icon-small" />
        <span v-if="!collapsed" class="logo-text">Cloudberry Data Studio</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        mode="inline"
        :theme="siderTheme"
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
          <!-- Language Switcher -->
          <a-dropdown class="lang-switcher">
            <a-button type="text">
              <GlobalOutlined />
              <span class="lang-text">{{ currentLangName }}</span>
            </a-button>
            <template #overlay>
              <a-menu @click="handleLocaleChange">
                <a-menu-item v-for="locale in locales" :key="locale.code" :class="{ 'ant-dropdown-menu-item-selected': locale.code === currentLocale }">
                  <span class="lang-flag">{{ locale.flag }}</span>
                  <span>{{ locale.name }}</span>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>

          <!-- User Dropdown -->
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
                  {{ t('common.logout') }}
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
import { useI18n } from 'vue-i18n'
import {
  HomeOutlined,
  DatabaseOutlined,
  SafetyOutlined,
  EyeOutlined,
  WarningOutlined,
  BranchesOutlined,
  SwapOutlined,
  SettingOutlined,
  UserOutlined,
  DownOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  GlobalOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { setLocale, LOCALES } from '@/locales'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>([])
const openKeys = ref<string[]>([])
const siderTheme = 'light' as const

// Locales
const locales = LOCALES
const currentLocale = computed(() => {
  const { locale } = useI18n()
  return locale.value
})
const currentLangName = computed(() => {
  const lang = locales.find(l => l.code === currentLocale.value)
  return lang ? `${lang.flag} ${lang.name}` : 'Language'
})

// Menu items with i18n
const menuItems = computed(() => [
  { path: '/dashboard', title: t('menu.dashboard'), icon: HomeOutlined },
  { path: '/datasources', title: t('menu.datasources'), icon: DatabaseOutlined },
  {
    path: '/masking',
    title: t('menu.masking'),
    icon: SafetyOutlined,
    children: [
      { path: '/masking', title: t('menu.staticMasking') },
      { path: '/dynamic-masking', title: t('menu.dynamicMasking') },
      { path: '/anonymization', title: t('menu.anonymization') }
    ]
  },
  { path: '/lineage', title: t('menu.lineage'), icon: BranchesOutlined },
  { path: '/sync', title: t('menu.sync'), icon: SwapOutlined },
  {
    path: '/system',
    title: t('menu.system'),
    icon: SettingOutlined,
    children: [
      { path: '/system/users', title: t('menu.users') },
      { path: '/system/roles', title: t('menu.roles') },
      { path: '/system/audit', title: t('menu.auditLogs') }
    ]
  }
])

function navigateTo(path: string) {
  router.push(path)
}

function handleLogout() {
  userStore.logout()
  message.success(t('messages.saveSuccess'))
  router.push('/login')
}

function handleLocaleChange(e: any) {
  const localeCode = e.key
  setLocale(localeCode)
  message.success(localeCode === 'zh' ? '已切换到中文' : 'Switched to English')
}
</script>

<style scoped>
/* Apache Style - Light theme with #2563eb primary */
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  background: #ffffff;
  padding: 0 12px;
  border-bottom: 2px solid #e2e8f0;
}

.logo-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.logo-icon-small {
  width: 32px;
  height: 32px;
}

.logo-text {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.2px;
  flex: 1;
  min-width: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-right .user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1e293b;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background 0.2s;
}

.header-right .user-dropdown:hover {
  background: #f8fafc;
}

.lang-switcher {
  cursor: pointer;
}

.lang-text {
  margin-left: 6px;
  color: #1e293b;
}

.lang-flag {
  margin-right: 8px;
}

.content {
  margin: 20px;
  padding: 28px;
  background: #ffffff;
  min-height: calc(100vh - 104px);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

/* Light theme menu styling - Apache blue */
:deep(.ant-menu-light) {
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
}

:deep(.ant-menu-item-selected) {
  background: rgba(37, 99, 235, 0.08) !important;
  color: #2563eb !important;
}

:deep(.ant-menu-item-selected::after) {
  border-right: 3px solid #2563eb;
}

:deep(.ant-menu-item:hover) {
  color: #2563eb;
}

:deep(.ant-menu-submenu-title:hover) {
  color: #2563eb;
}
</style>
