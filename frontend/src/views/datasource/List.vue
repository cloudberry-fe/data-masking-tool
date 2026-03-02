<template>
  <div class="datasource-list">
    <div class="page-header">
      <a-space>
        <a-input-search
          v-model:value="search.keyword"
          placeholder="搜索数据源名称"
          style="width: 240px"
          @search="loadData"
          allow-clear
        />
        <a-select
          v-model:value="search.datasourceType"
          placeholder="数据源类型"
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
          新增数据源
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
            {{ record.status === 1 ? '启用' : '禁用' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="testConnection(record)">
              测试连接
            </a-button>
            <a-button type="link" size="small" @click="showEditModal(record)">
              编辑
            </a-button>
            <a-popconfirm title="确定要删除该数据源吗？" @confirm="deleteDatasource(record.id)">
              <a-button type="link" size="small" danger>
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 新增/编辑弹窗 -->
    <a-modal
      :title="isEdit ? '编辑数据源' : '新增数据源'"
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
        <a-form-item label="数据源名称" name="datasourceName" :rules="[{ required: true, message: '请输入' }]">
          <a-input v-model:value="formState.datasourceName" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="数据源类型" name="datasourceType" :rules="[{ required: true, message: '请选择' }]">
          <a-select v-model:value="formState.datasourceType" placeholder="请选择">
            <a-select-option v-for="t in datasourceTypes" :key="t.value" :value="t.value">
              {{ t.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="主机地址" name="host" :rules="[{ required: true, message: '请输入' }]">
          <a-input v-model:value="formState.host" placeholder="localhost" />
        </a-form-item>
        <a-form-item label="端口" name="port" :rules="[{ required: true, message: '请输入' }]">
          <a-input-number v-model:value="formState.port" :min="1" :max="65535" style="width: 100%" />
        </a-form-item>
        <a-form-item label="数据库名" name="databaseName">
          <a-input v-model:value="formState.databaseName" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="formState.username" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="密码" name="password">
          <a-input-password v-model:value="formState.password" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="启用账号映射" name="enableAccountMapping">
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
  { label: '达梦', value: 'DM' }
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
  { title: '数据源名称', dataIndex: 'datasourceName', key: 'datasourceName' },
  { title: '类型', key: 'datasourceType', width: 160 },
  { title: '主机', dataIndex: 'host', key: 'host' },
  { title: '端口', dataIndex: 'port', key: 'port', width: 80 },
  { title: '数据库', dataIndex: 'databaseName', key: 'databaseName' },
  { title: '状态', key: 'status', width: 80 },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt' },
  { title: '操作', key: 'actions', width: 200, fixed: 'right' as const }
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
      message.success('更新成功')
    } else {
      await request.post('/datasources', formState)
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

async function testConnection(record: any) {
  try {
    const result = await request.post('/datasources/test-connection', {
      datasourceType: record.datasourceType,
      host: record.host,
      port: record.port,
      databaseName: record.databaseName,
      username: record.username,
      password: '' // 需要用户输入密码
    })

    if (result.success) {
      message.success(`连接成功！${result.version || ''}`)
    } else {
      message.error(result.message)
    }
  } catch (error) {
    // 错误已在拦截器处理
  }
}

async function deleteDatasource(id: number) {
  try {
    await request.delete(`/datasources/${id}`)
    message.success('删除成功')
    loadData()
  } catch (error) {
    // 错误已在拦截器处理
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
