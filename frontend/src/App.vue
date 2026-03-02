<template>
  <a-config-provider :locale="enUS">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import enUS from 'ant-design-vue/es/locale/en_US'
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
}
</style>
