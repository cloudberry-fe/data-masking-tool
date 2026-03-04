<template>
  <div class="datasource-list">
    <div class="page-header">
      <a-space>
        <a-input-search
          v-model:value="search.keyword"
          :placeholder="t('common.search')"
          style="width: 240px"
          @search="loadData"
          allow-clear
        />
        <a-select
          v-model:value="search.datasourceType"
          :placeholder="t('datasource.datasourceType')"
          style="width: 160px"
          allow-clear
          @change="loadData"
        >
          <a-select-option v-for="dt in datasourceTypes" :key="dt.value" :value="dt.value">
            {{ dt.label }}
          </a-select-option>
        </a-select>
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          {{ t('datasource.create') }}
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
            {{ record.status === 1 ? t('common.yes') : t('common.no') }}
          </a-tag>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="testConnection(record)">
              {{ t('datasource.testConnection') }}
            </a-button>
            <a-button type="link" size="small" @click="showEditModal(record)">
              {{ t('common.edit') }}
            </a-button>
            <a-popconfirm :title="t('messages.deleteConfirm')" @confirm="deleteDatasource(record.id)">
              <a-button type="link" size="small" danger>
                {{ t('common.delete') }}
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- Create/Edit Modal -->
    <a-modal
      :title="isEdit ? t('datasource.edit') : t('datasource.create')"
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
        <a-form-item :label="t('datasource.datasourceName')" name="datasourceName" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input v-model:value="formState.datasourceName" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
        <a-form-item :label="t('datasource.datasourceType')" name="datasourceType" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select v-model:value="formState.datasourceType" :placeholder="t('common.pleaseSelect')">
            <a-select-option v-for="dt in datasourceTypes" :key="dt.value" :value="dt.value">
              {{ dt.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('datasource.host')" name="host" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input v-model:value="formState.host" placeholder="localhost" />
        </a-form-item>
        <a-form-item :label="t('datasource.port')" name="port" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input-number v-model:value="formState.port" :min="1" :max="65535" style="width: 100%" />
        </a-form-item>
        <a-form-item :label="t('datasource.database')" name="databaseName">
          <a-input v-model:value="formState.databaseName" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
        <a-form-item :label="t('datasource.username')" name="username">
          <a-input v-model:value="formState.username" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
        <a-form-item :label="t('datasource.password')" name="password">
          <a-input-password v-model:value="formState.password" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
        <a-form-item :label="t('datasource.enableAccountMapping')" name="enableAccountMapping">
          <a-switch v-model:checked="formState.enableAccountMapping" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const { t, locale } = useI18n()

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

const datasourceTypes = computed(() => [
  { label: locale.value === 'zh' ? 'HashData Lightning (MPP)' : 'HashData Lightning (MPP)', value: 'MPP' },
  { label: 'PostgreSQL', value: 'POSTGRESQL' },
  { label: 'Oracle', value: 'ORACLE' },
  { label: 'MySQL', value: 'MYSQL' },
  { label: locale.value === 'zh' ? 'GoldenDB' : 'GoldenDB', value: 'GOLDENDB' },
  { label: locale.value === 'zh' ? '达梦' : 'DM', value: 'DM' }
])

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

const columns = computed(() => [
  { title: t('datasource.datasourceName'), dataIndex: 'datasourceName', key: 'datasourceName' },
  { title: t('datasource.datasourceType'), key: 'datasourceType', width: 160 },
  { title: t('datasource.host'), dataIndex: 'host', key: 'host' },
  { title: t('datasource.port'), dataIndex: 'port', key: 'port', width: 80 },
  { title: t('datasource.database'), dataIndex: 'databaseName', key: 'databaseName' },
  { title: t('common.status'), key: 'status', width: 80 },
  { title: t('common.createdAt'), dataIndex: 'createdAt', key: 'createdAt' },
  { title: t('common.actions'), key: 'actions', width: 200, fixed: 'right' as const }
])

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
      message.success(t('messages.updateSuccess'))
    } else {
      await request.post('/datasources', formState)
      message.success(t('messages.createSuccess'))
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
    const result = await request.post(`/datasources/${record.id}/test-connection`)

    if (result.success) {
      message.success(`${t('datasource.connectionSuccess')}! ${result.version || ''}`)
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
    message.success(t('messages.deleteSuccess'))
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
  const item = datasourceTypes.value.find(t => t.value === type)
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
