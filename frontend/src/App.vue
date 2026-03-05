<template>
  <a-config-provider :locale="enUS" :theme="themeConfig">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import enUS from 'ant-design-vue/es/locale/en_US'
import { themeConfig } from './theme'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
}

/* PPT Style Theme */
:root {
  --primary-color: #00319F;
  --primary-light: #156082;
  --primary-dark: #0E2841;
  --accent-blue: #0F9ED5;
  --accent-orange: #E97132;
  --accent-green: #196B24;
  --accent-purple: #A02B93;
  --bg-light: #F5F7FA;
  --bg-white: #FFFFFF;
  --text-dark: #0E2841;
  --text-gray: #666666;
  --text-light: #999999;
  --border-color: #E8E8E8;
}

/* Global PPT-style elements */
.ppt-title {
  color: var(--primary-color);
  font-weight: 600;
}

.ppt-underline {
  position: relative;
}

.ppt-underline::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 3px;
  background: var(--primary-color);
}
</style>
