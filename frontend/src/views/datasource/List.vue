<template>
  <div class="datasource-list">
    <div class="page-header">
      <a-space>
        <a-input-search
          v-model:value="search.keyword"
          placeholder="Search data source name"
          style="width: 240px"
          @search="loadData"
          allow-clear
        />
        <a-select
          v-model:value="search.datasourceType"
          placeholder="Data source type"
          style="width: 160px"
          allow-clear
          @change="loadData"
        >
          <a-select-option v-for="t in datasourceTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </a-select-option>
        </a-select>
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          Add Data Source
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
        <template v-if="column.key === 'datasourceType'">
          <a-tag :color="getTypeColor(record.datasourceType)">
            {{ getTypeText(record.datasourceType) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="record.status === 1 ? 'success' : 'default'">
            {{ record.status === 1 ? 'Enabled' : 'Disabled' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="testConnection(record)">
              Test Connection
            </a-button>
            <a-button type="link" size="small" @click="showEditModal(record)">
              Edit
            </a-button>
            <a-popconfirm title="Are you sure you want to delete this data source?" @confirm="deleteDatasource(record.id)">
              <a-button type="link" size="small" danger>
                Delete
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- Create/Edit Modal -->
    <a-modal
      :title="isEdit ? 'Edit Data Source' : 'Add Data Source'"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      width="600px"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="Data Source Name" name="datasourceName" :rules="[{ required: true, message: 'Please enter' }]">
          <a-input v-model:value="formState.datasourceName" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Data Source Type" name="datasourceType" :rules="[{ required: true, message: 'Please select' }]">
          <a-select v-model:value="formState.datasourceType" placeholder="Please select">
            <a-select-option v-for="t in datasourceTypes" :key="t.value" :value="t.value">
              {{ t.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Host" name="host" :rules="[{ required: true, message: 'Please enter' }]">
          <a-input v-model:value="formState.host" placeholder="localhost" />
        </a-form-item>
        <a-form-item label="Port" name="port" :rules="[{ required: true, message: 'Please enter' }]">
          <a-input-number v-model:value="formState.port" :min="1" :max="65535" style="width: 100%" />
        </a-form-item>
        <a-form-item label="Database Name" name="databaseName">
          <a-input v-model:value="formState.databaseName" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Username" name="username">
          <a-input v-model:value="formState.username" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Password" name="password">
          <a-input-password v-model:value="formState.password" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Enable Account Mapping" name="enableAccountMapping">
          <a-switch v-model:checked="formState.enableAccountMapping" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const modalVisible = ref(false)
const modalLoading = ref(false)
const isEdit = ref(false)
const formRef = ref()

const dataSource = ref<any[]>([])
const search = reactive({
  keyword: '',
  datasourceType: undefined as string | undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const datasourceTypes = [
  { label: 'HashData Lightning (MPP)', value: 'MPP' },
  { label: 'PostgreSQL', value: 'POSTGRESQL' },
  { label: 'Oracle', value: 'ORACLE' },
  { label: 'MySQL', value: 'MYSQL' },
  { label: 'GoldenDB', value: 'GOLDENDB' },
  { label: 'DM', value: 'DM' }
]

const formState = reactive({
  id: undefined as number | undefined,
  datasourceName: '',
  datasourceType: '',
  host: '',
  port: 5432,
  databaseName: '',
  username: '',
  password: '',
  enableAccountMapping: false
})

const columns = [
  { title: 'Data Source Name', dataIndex: 'datasourceName', key: 'datasourceName' },
  { title: 'Type', key: 'datasourceType', width: 160 },
  { title: 'Host', dataIndex: 'host', key: 'host' },
  { title: 'Port', dataIndex: 'port', key: 'port', width: 80 },
  { title: 'Database', dataIndex: 'databaseName', key: 'databaseName' },
  { title: 'Status', key: 'status', width: 80 },
  { title: 'Created At', dataIndex: 'createdAt', key: 'createdAt' },
  { title: 'Actions', key: 'actions', width: 200, fixed: 'right' as const }
]

async function loadData() {
  loading.value = true
  try {
    const data = await request.get('/datasources', {
      params: {
        page: pagination.current,
        pageSize: pagination.pageSize,
        keyword: search.keyword,
        datasourceType: search.datasourceType
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
    datasourceName: '',
    datasourceType: '',
    host: '',
    port: 5432,
    databaseName: '',
    username: '',
    password: '',
    enableAccountMapping: false
  })
  modalVisible.value = true
}

function showEditModal(record: any) {
  isEdit.value = true
  Object.assign(formState, {
    id: record.id,
    datasourceName: record.datasourceName,
    datasourceType: record.datasourceType,
    host: record.host,
    port: record.port,
    databaseName: record.databaseName,
    username: record.username,
    password: '',
    enableAccountMapping: record.enableAccountMapping
  })
  modalVisible.value = true
}

async function handleModalOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    if (isEdit.value) {
      await request.put(`/datasources/${formState.id}`, formState)
      message.success('Updated successfully')
    } else {
      await request.post('/datasources', formState)
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

async function testConnection(record: any) {
  try {
    const result = await request.post('/datasources/test-connection', {
      datasourceType: record.datasourceType,
      host: record.host,
      port: record.port,
      databaseName: record.databaseName,
      username: record.username,
      password: '' // User needs to enter password
    })

    if (result.success) {
      message.success(`Connection successful! ${result.version || ''}`)
    } else {
      message.error(result.message)
    }
  } catch (error) {
    // Error handled in interceptor
  }
}

async function deleteDatasource(id: number) {
  try {
    await request.delete(`/datasources/${id}`)
    message.success('Deleted successfully')
    loadData()
  } catch (error) {
    // Error handled in interceptor
  }
}

function getTypeColor(type: string): string {
  const colors: Record<string, string> = {
    MPP: 'blue',
    POSTGRESQL: 'cyan',
    ORACLE: 'orange',
    MYSQL: 'green',
    GOLDENDB: 'purple',
    DM: 'geekblue'
  }
  return colors[type] || 'default'
}

function getTypeText(type: string): string {
  const item = datasourceTypes.find(t => t.value === type)
  return item?.label || type
}

onMounted(() => {
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
