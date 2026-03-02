<template>
  <div class="users-page">
    <div class="page-header">
      <a-space>
        <a-input-search
          v-model:value="search.keyword"
          placeholder="搜索用户名或姓名"
          style="width: 240px"
          @search="loadData"
          allow-clear
        />
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          新增用户
        </a-button>
      </a-space>
    </div>

    <a-table
      :columns="columns"
      :data-source="dataSource"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="record.status === 1 ? 'success' : 'default'">
            {{ record.status === 1 ? '启用' : '禁用' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'roles'">
          <a-tag v-for="role in record.roles" :key="role.id" style="margin-right: 4px">
            {{ role.roleName }}
          </a-tag>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="showRoleModal(record)">
              分配角色
            </a-button>
            <a-button type="link" size="small" @click="showEditModal(record)">
              编辑
            </a-button>
            <a-popconfirm v-if="record.id !== currentUserId" title="确定要删除该用户吗？" @confirm="deleteUser(record.id)">
              <a-button type="link" size="small" danger>
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 新建/编辑用户弹窗 -->
    <a-modal
      :title="isEdit ? '编辑用户' : '新增用户'"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      width="500px"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item v-if="!isEdit" label="用户名" name="username" :rules="[{ required: true }]">
          <a-input v-model:value="formState.username" placeholder="请输入" />
        </a-form-item>
        <a-form-item v-if="!isEdit" label="密码" name="password" :rules="isEdit ? [] : [{ required: true }]">
          <a-input-password v-model:value="formState.password" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="真实姓名" name="realName">
          <a-input v-model:value="formState.realName" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="formState.email" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="手机号" name="phone">
          <a-input v-model:value="formState.phone" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-select v-model:value="formState.status">
            <a-select-option :value="1">启用</a-select-option>
            <a-select-option :value="0">禁用</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 分配角色弹窗 -->
    <a-modal
      title="分配角色"
      v-model:open="roleModalVisible"
      @ok="handleRoleModalOk"
      @cancel="roleModalVisible = false"
      width="500px"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="用户">
          <span>{{ roleFormUser?.username }}</span>
        </a-form-item>
        <a-form-item label="选择角色">
          <a-checkbox-group v-model:value="selectedRoleIds">
            <a-checkbox v-for="role in allRoles" :key="role.id" :value="role.id">
              {{ role.roleName }}
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const currentUserId = computed(() => userStore.userInfo?.user_id)

const loading = ref(false)
const modalVisible = ref(false)
const modalLoading = ref(false)
const roleModalVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

const dataSource = ref<any[]>([])
const allRoles = ref<any[]>([])
const search = reactive({
  keyword: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const formState = reactive({
  id: undefined as number | undefined,
  username: '',
  password: '',
  realName: '',
  email: '',
  phone: '',
  status: 1
})

const roleFormUser = ref<any>(null)
const selectedRoleIds = ref<number[]>([])

const columns = [
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '真实姓名', dataIndex: 'realName', key: 'realName' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '角色', key: 'roles' },
  { title: '状态', key: 'status', width: 80 },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt' },
  { title: '操作', key: 'actions', width: 220, fixed: 'right' as const }
]

async function loadRoles() {
  try {
    allRoles.value = await request.get('/system/roles')
  } catch (error) {
    //
  }
}

async function loadData() {
  loading.value = true
  try {
    const data = await request.get('/system/users', {
      params: {
        page: pagination.current,
        pageSize: pagination.pageSize,
        keyword: search.keyword
      }
    })
    dataSource.value = data.items
    pagination.total = data.total
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadData()
}

function showCreateModal() {
  isEdit.value = false
  Object.assign(formState, {
    id: undefined,
    username: '',
    password: '',
    realName: '',
    email: '',
    phone: '',
    status: 1
  })
  modalVisible.value = true
}

function showEditModal(record: any) {
  isEdit.value = true
  Object.assign(formState, {
    id: record.id,
    username: record.username,
    password: '',
    realName: record.realName,
    email: record.email,
    phone: record.phone,
    status: record.status
  })
  modalVisible.value = true
}

async function handleModalOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    if (isEdit.value) {
      await request.put(`/system/users/${formState.id}`, formState)
      message.success('更新成功')
    } else {
      await request.post('/system/users', formState)
      message.success('创建成功')
    }

    modalVisible.value = false
    loadData()
  } finally {
    modalLoading.value = false
  }
}

function handleModalCancel() {
  modalVisible.value = false
}

function showRoleModal(record: any) {
  roleFormUser.value = record
  selectedRoleIds.value = (record.roles || []).map((r: any) => r.id)
  roleModalVisible.value = true
}

async function handleRoleModalOk() {
  try {
    await request.put(`/system/users/${roleFormUser.value.id}/roles`, {
      userId: roleFormUser.value.id,
      roleIds: selectedRoleIds.value
    })
    message.success('分配成功')
    roleModalVisible.value = false
    loadData()
  } catch (error) {
    //
  }
}

async function deleteUser(id: number) {
  try {
    await request.delete(`/system/users/${id}`)
    message.success('删除成功')
    loadData()
  } catch (error) {
    //
  }
}

onMounted(() => {
  loadRoles()
  loadData()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
