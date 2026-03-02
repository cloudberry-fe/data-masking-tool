<template>
  <div class="users-page">
    <div class="page-header">
      <a-space>
        <a-input-search
          v-model:value="search.keyword"
          placeholder="Search username or name"
          style="width: 240px"
          @search="loadData"
          allow-clear
        />
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          Add User
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
            {{ record.status === 1 ? 'Enabled' : 'Disabled' }}
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
              Assign Roles
            </a-button>
            <a-button type="link" size="small" @click="showEditModal(record)">
              Edit
            </a-button>
            <a-popconfirm v-if="record.id !== currentUserId" title="Are you sure you want to delete this user?" @confirm="deleteUser(record.id)">
              <a-button type="link" size="small" danger>
                Delete
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- Create/Edit User Modal -->
    <a-modal
      :title="isEdit ? 'Edit User' : 'Add User'"
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
        <a-form-item v-if="!isEdit" label="Username" name="username" :rules="[{ required: true }]">
          <a-input v-model:value="formState.username" placeholder="Please enter" />
        </a-form-item>
        <a-form-item v-if="!isEdit" label="Password" name="password" :rules="isEdit ? [] : [{ required: true }]">
          <a-input-password v-model:value="formState.password" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Real Name" name="realName">
          <a-input v-model:value="formState.realName" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Email" name="email">
          <a-input v-model:value="formState.email" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Phone" name="phone">
          <a-input v-model:value="formState.phone" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Status" name="status">
          <a-select v-model:value="formState.status">
            <a-select-option :value="1">Enabled</a-select-option>
            <a-select-option :value="0">Disabled</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Assign Roles Modal -->
    <a-modal
      title="Assign Roles"
      v-model:open="roleModalVisible"
      @ok="handleRoleModalOk"
      @cancel="roleModalVisible = false"
      width="500px"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="User">
          <span>{{ roleFormUser?.username }}</span>
        </a-form-item>
        <a-form-item label="Select Roles">
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
  { title: 'Username', dataIndex: 'username', key: 'username' },
  { title: 'Real Name', dataIndex: 'realName', key: 'realName' },
  { title: 'Email', dataIndex: 'email', key: 'email' },
  { title: 'Roles', key: 'roles' },
  { title: 'Status', key: 'status', width: 80 },
  { title: 'Created At', dataIndex: 'createdAt', key: 'createdAt' },
  { title: 'Actions', key: 'actions', width: 220, fixed: 'right' as const }
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
      message.success('Updated successfully')
    } else {
      await request.post('/system/users', formState)
      message.success('Created successfully')
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
    message.success('Assigned successfully')
    roleModalVisible.value = false
    loadData()
  } catch (error) {
    //
  }
}

async function deleteUser(id: number) {
  try {
    await request.delete(`/system/users/${id}`)
    message.success('Deleted successfully')
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
