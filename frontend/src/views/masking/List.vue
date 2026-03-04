<template>
  <div class="masking-list">
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
          v-model:value="search.status"
          :placeholder="t('common.status')"
          style="width: 140px"
          allow-clear
          @change="loadData"
        >
          <a-select-option value="DRAFT">{{ t('masking.statusDraft') }}</a-select-option>
          <a-select-option value="READY">{{ t('masking.statusReady') }}</a-select-option>
          <a-select-option value="RUNNING">{{ t('masking.statusRunning') }}</a-select-option>
          <a-select-option value="PAUSED">{{ t('masking.statusPaused') }}</a-select-option>
        </a-select>
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          {{ t('masking.createTask') }}
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
        <template v-if="column.key === 'maskingMode'">
          <a-tag :color="getModeColor(record.maskingMode)">
            {{ getModeText(record.maskingMode) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'lastExecution'">
          <a-tag v-if="record.lastExecutionStatus" :color="getExecutionStatusColor(record.lastExecutionStatus)">
            {{ getExecutionStatusText(record.lastExecutionStatus) }}
          </a-tag>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template v-if="column.key === 'scheduleType'">
          {{ record.scheduleType === 'CRON' ? t('masking.scheduleCron') : t('masking.scheduleManual') }}
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="goToDetail(record)">
              {{ t('common.edit') }}
            </a-button>
            <a-popconfirm
              v-if="record.status !== 'RUNNING'"
              :title="t('messages.executeConfirm')"
              @confirm="executeTask(record)"
            >
              <a-button type="primary" size="small">
                {{ t('masking.execute') }}
              </a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="showEditModal(record)">
              {{ t('common.edit') }}
            </a-button>
            <a-popconfirm :title="t('messages.deleteConfirm')" @confirm="deleteTask(record.id)">
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
      :title="isEdit ? t('masking.editTask') : t('masking.createTask')"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      width="650px"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item :label="t('masking.taskName')" name="taskName" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input v-model:value="formState.taskName" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
        <a-form-item label="Data Source" name="datasourceId" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select v-model:value="formState.datasourceId" :placeholder="t('common.pleaseSelect')" show-search>
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- Masking Mode Selection -->
        <a-form-item :label="t('masking.maskingMode')" name="maskingMode" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select v-model:value="formState.maskingMode" :placeholder="t('common.pleaseSelect')">
            <a-select-option value="STATIC">
              <div>
                <span style="font-weight: 500">{{ t('masking.modeStatic') }}</span>
                <span style="color: #999; margin-left: 8px; font-size: 12px">{{ t('masking.modeStaticDesc') }}</span>
              </div>
            </a-select-option>
            <a-select-option value="GENERALIZE">
              <div>
                <span style="font-weight: 500">{{ t('masking.modeGeneralize') }}</span>
                <span style="color: #999; margin-left: 8px; font-size: 12px">{{ t('masking.modeGeneralizeDesc') }}</span>
              </div>
            </a-select-option>
          </a-select>
          <div style="margin-top: 8px; color: #666; font-size: 12px">
            <template v-if="formState.maskingMode === 'STATIC'">
              <SafetyOutlined style="color: #1890ff" /> {{ t('masking.modeStaticDesc') }}
            </template>
            <template v-else-if="formState.maskingMode === 'GENERALIZE'">
              <LineChartOutlined style="color: #52c41a" /> {{ t('masking.modeGeneralizeDesc') }}
            </template>
          </div>
        </a-form-item>

        <a-form-item :label="t('masking.sourceSchema')" name="sourceSchema">
          <a-input v-model:value="formState.sourceSchema" placeholder="public" />
        </a-form-item>
        <a-form-item :label="t('masking.targetSchema')" name="targetSchema">
          <a-input v-model:value="formState.targetSchema" placeholder="public" />
        </a-form-item>
        <a-form-item :label="t('masking.scheduleType')" name="scheduleType">
          <a-select v-model:value="formState.scheduleType">
            <a-select-option value="MANUAL">{{ t('masking.scheduleManual') }}</a-select-option>
            <a-select-option value="CRON">{{ t('masking.scheduleCron') }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="formState.scheduleType === 'CRON'" :label="t('masking.cronExpression')" name="cronExpression">
          <a-input v-model:value="formState.cronExpression" placeholder="0 0 2 * * ?" />
        </a-form-item>
        <a-form-item :label="t('common.description')" name="description">
          <a-textarea v-model:value="formState.description" :rows="3" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined, SafetyOutlined, LineChartOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const { t } = useI18n()
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
  maskingMode: 'STATIC',
  sourceSchema: '',
  targetSchema: '',
  scheduleType: 'MANUAL',
  cronExpression: '',
  description: ''
})

const columns = computed(() => [
  { title: t('masking.taskName'), dataIndex: 'taskName', key: 'taskName' },
  { title: t('masking.maskingMode'), key: 'maskingMode', width: 120 },
  { title: t('common.status'), key: 'status', width: 100 },
  { title: t('masking.executionHistory'), key: 'lastExecution', width: 120 },
  { title: t('masking.scheduleType'), key: 'scheduleType', width: 100 },
  { title: t('common.createdAt'), dataIndex: 'createdAt', key: 'createdAt' },
  { title: t('common.actions'), key: 'actions', width: 280, fixed: 'right' as const }
])

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

    // Load last execution status for each task
    for (const task of dataSource.value) {
      try {
        const execData = await request.get(`/masking/tasks/${task.id}/executions`, {
          params: { page: 1, pageSize: 1 }
        })
        if (execData.items && execData.items.length > 0) {
          task.lastExecutionStatus = execData.items[0].status
          task.lastExecutionTime = execData.items[0].startTime
        }
      } catch (e) {
        // ignore
      }
    }

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
    maskingMode: 'STATIC',
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
    maskingMode: record.maskingMode || 'STATIC',
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
      message.success(t('messages.updateSuccess'))
    } else {
      await request.post('/masking/tasks', formState)
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

function goToDetail(record: any) {
  router.push(`/masking/${record.id}`)
}

async function executeTask(record: any) {
  try {
    await request.post(`/masking/tasks/${record.id}/execute`)
    message.success(t('messages.executeSuccess'))
    loadData()
  } catch (error) {
    //
  }
}

async function deleteTask(id: number) {
  try {
    await request.delete(`/masking/tasks/${id}`)
    message.success(t('messages.deleteSuccess'))
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
  const { locale } = useI18n()
  const texts: Record<string, Record<string, string>> = {
    DRAFT: { en: 'Draft', zh: '草稿' },
    READY: { en: 'Ready', zh: '就绪' },
    RUNNING: { en: 'Running', zh: '运行中' },
    PAUSED: { en: 'Paused', zh: '已暂停' },
    SUCCESS: { en: 'Success', zh: '成功' },
    FAILED: { en: 'Failed', zh: '失败' }
  }
  return texts[status]?.[locale.value] || status
}

function getModeColor(mode: string): string {
  const colors: Record<string, string> = {
    STATIC: 'blue',
    GENERALIZE: 'green'
  }
  return colors[mode] || 'default'
}

function getModeText(mode: string): string {
  const { locale } = useI18n()
  const texts: Record<string, Record<string, string>> = {
    STATIC: { en: 'Static', zh: '静态' },
    GENERALIZE: { en: 'Generalize', zh: '泛化' }
  }
  return texts[mode]?.[locale.value] || mode || 'Static'
}

function getExecutionStatusColor(status: string): string {
  const colors: Record<string, string> = {
    SUCCESS: 'success',
    FAILED: 'error',
    RUNNING: 'processing',
    PENDING: 'default'
  }
  return colors[status] || 'default'
}

function getExecutionStatusText(status: string): string {
  const { locale } = useI18n()
  const texts: Record<string, Record<string, string>> = {
    SUCCESS: { en: 'Success', zh: '成功' },
    FAILED: { en: 'Failed', zh: '失败' },
    RUNNING: { en: 'Running', zh: '运行中' },
    PENDING: { en: 'Pending', zh: '待执行' }
  }
  return texts[status]?.[locale.value] || status
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
.text-gray-400 {
  color: #9ca3af;
}
</style>
