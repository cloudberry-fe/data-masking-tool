<template>
  <div class="masking-list">
    <div class="page-header">
      <a-space>
        <a-input-search
          v-model:value="search.keyword"
          placeholder="Search task name"
          style="width: 240px"
          @search="loadData"
          allow-clear
        />
        <a-select
          v-model:value="search.status"
          placeholder="Status"
          style="width: 140px"
          allow-clear
          @change="loadData"
        >
          <a-select-option value="DRAFT">Draft</a-select-option>
          <a-select-option value="READY">Ready</a-select-option>
          <a-select-option value="RUNNING">Running</a-select-option>
          <a-select-option value="PAUSED">Paused</a-select-option>
        </a-select>
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          New Task
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
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'scheduleType'">
          {{ record.scheduleType === 'CRON' ? 'Scheduled' : 'Manual' }}
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="goToDetail(record)">
              Configure
            </a-button>
            <a-popconfirm
              v-if="record.status !== 'RUNNING'"
              title="Are you sure you want to execute this task?"
              @confirm="executeTask(record)"
            >
              <a-button type="link" size="small" type="primary">
                Execute
              </a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="showEditModal(record)">
              Edit
            </a-button>
            <a-popconfirm title="Are you sure you want to delete this task?" @confirm="deleteTask(record.id)">
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
      :title="isEdit ? 'Edit Task' : 'New Task'"
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
        <a-form-item label="Task Name" name="taskName" :rules="[{ required: true, message: 'Please enter' }]">
          <a-input v-model:value="formState.taskName" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Data Source" name="datasourceId" :rules="[{ required: true, message: 'Please select' }]">
          <a-select v-model:value="formState.datasourceId" placeholder="Please select" show-search>
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Source Schema" name="sourceSchema">
          <a-input v-model:value="formState.sourceSchema" placeholder="public" />
        </a-form-item>
        <a-form-item label="Target Schema" name="targetSchema">
          <a-input v-model:value="formState.targetSchema" placeholder="public" />
        </a-form-item>
        <a-form-item label="Schedule Type" name="scheduleType">
          <a-select v-model:value="formState.scheduleType">
            <a-select-option value="MANUAL">Manual</a-select-option>
            <a-select-option value="CRON">Scheduled</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="formState.scheduleType === 'CRON'" label="Cron Expression" name="cronExpression">
          <a-input v-model:value="formState.cronExpression" placeholder="0 0 2 * * ?" />
        </a-form-item>
        <a-form-item label="Description" name="description">
          <a-textarea v-model:value="formState.description" :rows="3" placeholder="Please enter" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const router = useRouter()

const loading = ref(false)
const modalVisible = ref(false)
const modalLoading = ref(false)
const isEdit = ref(false)
const formRef = ref()

const dataSource = ref<any[]>([])
const datasourceList = ref<any[]>([])
const search = reactive({
  keyword: '',
  status: undefined as string | undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const formState = reactive({
  id: undefined as number | undefined,
  taskName: '',
  datasourceId: undefined as number | undefined,
  sourceSchema: '',
  targetSchema: '',
  scheduleType: 'MANUAL',
  cronExpression: '',
  description: ''
})

const columns = [
  { title: 'Task Name', dataIndex: 'taskName', key: 'taskName' },
  { title: 'Status', key: 'status', width: 100 },
  { title: 'Schedule Type', key: 'scheduleType', width: 100 },
  { title: 'Created At', dataIndex: 'createdAt', key: 'createdAt' },
  { title: 'Actions', key: 'actions', width: 280, fixed: 'right' as const }
]

async function loadDatasources() {
  try {
    const data = await request.get('/datasources', { params: { page: 1, pageSize: 100 } })
    datasourceList.value = data.items
  } catch (error) {
    //
  }
}

async function loadData() {
  loading.value = true
  try {
    const data = await request.get('/masking/tasks', {
      params: {
        page: pagination.current,
        pageSize: pagination.pageSize,
        keyword: search.keyword,
        status: search.status
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
    taskName: '',
    datasourceId: undefined,
    sourceSchema: '',
    targetSchema: '',
    scheduleType: 'MANUAL',
    cronExpression: '',
    description: ''
  })
  modalVisible.value = true
}

function showEditModal(record: any) {
  isEdit.value = true
  Object.assign(formState, {
    id: record.id,
    taskName: record.taskName,
    datasourceId: record.datasourceId,
    sourceSchema: record.sourceSchema,
    targetSchema: record.targetSchema,
    scheduleType: record.scheduleType,
    cronExpression: record.cronExpression,
    description: record.description
  })
  modalVisible.value = true
}

async function handleModalOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    if (isEdit.value) {
      await request.put(`/masking/tasks/${formState.id}`, formState)
      message.success('Updated successfully')
    } else {
      await request.post('/masking/tasks', formState)
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

function goToDetail(record: any) {
  router.push(`/masking/${record.id}`)
}

async function executeTask(record: any) {
  try {
    await request.post(`/masking/tasks/${record.id}/execute`)
    message.success('Task submitted for execution')
    loadData()
  } catch (error) {
    //
  }
}

async function deleteTask(id: number) {
  try {
    await request.delete(`/masking/tasks/${id}`)
    message.success('Deleted successfully')
    loadData()
  } catch (error) {
    //
  }
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    DRAFT: 'default',
    READY: 'blue',
    RUNNING: 'processing',
    PAUSED: 'warning',
    SUCCESS: 'success',
    FAILED: 'error'
  }
  return colors[status] || 'default'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    DRAFT: 'Draft',
    READY: 'Ready',
    RUNNING: 'Running',
    PAUSED: 'Paused',
    SUCCESS: 'Success',
    FAILED: 'Failed'
  }
  return texts[status] || status
}

onMounted(() => {
  loadDatasources()
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
