<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>数据脱敏系统</h1>
        <p>恒丰银行 - 血缘分析、MPP数据脱敏、翻数工具</p>
      </div>
      <a-form
        :model="formState"
        :rules="rules"
        @finish="handleLogin"
        class="login-form"
        autocomplete="off"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="formState.username"
            size="large"
            placeholder="请输入用户名"
            :prefix-icon="UserOutlined"
          />
        </a-form-item>
        <a-form-item name="password">
          <a-input-password
            v-model:value="formState.password"
            size="large"
            placeholder="请输入密码"
            :prefix-icon="LockOutlined"
            @pressEnter="handleLogin"
          />
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            size="large"
            html-type="submit"
            block
            :loading="loading"
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>
      <div class="login-footer">
        <p>默认账号: admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const formState = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  if (!formState.username || !formState.password) {
    return
  }

  loading.value = true
  try {
    await userStore.login(formState.username, formState.password)
    message.success('登录成功')
    router.push('/')
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 420px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-header h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 14px;
  color: #999;
}

.login-form {
  margin-top: 30px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
}

.login-footer p {
  font-size: 12px;
  color: #999;
}
</style>
