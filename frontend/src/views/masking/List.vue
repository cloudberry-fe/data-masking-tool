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
              {{ t('common.dataConfig') }}
            </a-button>
            <a-button type="link" size="small" @click="showPreviewSql(record)">
              {{ t('dynamicMasking.previewSQL') }}
            </a-button>
            <a-button type="link" size="small" @click="showExecutionsModal(record)">
              {{ t('masking.executionHistory') }}
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
        <a-form-item :label="t('datasource.title')" name="datasourceId" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select
            v-model:value="formState.datasourceId"
            :placeholder="t('common.pleaseSelect')"
            show-search
            @change="onDatasourceChange"
          >
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
          <a-select
            v-model:value="formState.sourceSchema"
            :placeholder="t('common.pleaseSelect')"
            :loading="loadingSchemas"
            :disabled="!formState.datasourceId"
            allow-clear
            show-search
            @focus="loadSchemasIfNeeded"
          >
            <a-select-option v-for="schema in schemaList" :key="schema" :value="schema">
              {{ schema }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('masking.targetSchema')" name="targetSchema">
          <a-select
            v-model:value="formState.targetSchema"
            :placeholder="t('common.pleaseSelect')"
            :loading="loadingSchemas"
            :disabled="!formState.datasourceId"
            allow-clear
            show-search
            @focus="loadSchemasIfNeeded"
          >
            <a-select-option v-for="schema in schemaList" :key="schema" :value="schema">
              {{ schema }}
            </a-select-option>
          </a-select>
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

    <!-- Execution History Modal -->
    <a-modal
      :title="t('masking.executionHistory')"
      v-model:open="executionsModalVisible"
      :footer="null"
      width="800px"
    >
      <a-table
        :columns="executionColumns"
        :data-source="executions"
        :loading="loadingExecutions"
        :pagination="false"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getExecutionStatusColor(record.status)">
              {{ getExecutionStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'duration'">
            <span v-if="record.startTime && record.endTime">
              {{ formatDuration(record.startTime, record.endTime) }}
            </span>
            <span v-else>-</span>
          </template>
          <template v-if="column.key === 'records'">
            <span v-if="record.successRecords !== undefined">
              {{ record.successRecords }} / {{ record.totalRecords || 0 }}
            </span>
            <span v-else>-</span>
          </template>
        </template>
      </a-table>
    </a-modal>

    <!-- SQL Preview Modal -->
    <a-modal
      :title="t('dynamicMasking.previewSQL')"
      v-model:open="sqlPreviewModalVisible"
      :footer="null"
      width="800px"
    >
      <a-spin :spinning="loadingSqlPreview">
        <pre style="max-height: 500px; overflow: auto; background: #f5f5f5; padding: 16px; border-radius: 4px; white-space: pre-wrap; word-break: break-all;">{{ sqlPreviewContent }}</pre>
      </a-spin>
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

// Execution history
const executionsModalVisible = ref(false)
const loadingExecutions = ref(false)
const executions = ref<any[]>([])
const currentTaskId = ref<number | null>(null)

// SQL Preview
const sqlPreviewModalVisible = ref(false)
const loadingSqlPreview = ref(false)
const sqlPreviewContent = ref('')

const dataSource = ref<any[]>([])
const datasourceList = ref<any[]>([])
const schemaList = ref<string[]>([])
const loadingSchemas = ref(false)
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
  { title: t('common.actions'), key: 'actions', width: 380, fixed: 'right' as const }
])

const executionColumns = [
  { title: 'ID', dataIndex: 'executionNo', key: 'executionNo', width: 150 },
  { title: t('common.status'), key: 'status', width: 100 },
  { title: t('masking.records'), key: 'records', width: 100 },
  { title: t('masking.duration'), key: 'duration', width: 100 },
  { title: t('common.createdAt'), dataIndex: 'startTime', key: 'startTime', width: 160 }
]

async function loadDatasources() {
  try {
    const data = await request.get('/datasources', { params: { page: 1, pageSize: 100 } })
    datasourceList.value = data.items
  } catch (error) {
    //
  }
}

async function loadSchemasIfNeeded() {
  if (!formState.datasourceId) return
  if (schemaList.value.length > 0) return

  loadingSchemas.value = true
  try {
    const data = await request.get(`/datasources/${formState.datasourceId}/schemas`)
    schemaList.value = data || []
    // 如果只有一个schema，自动选中
    if (schemaList.value.length === 1) {
      if (!formState.sourceSchema) formState.sourceSchema = schemaList.value[0]
      if (!formState.targetSchema) formState.targetSchema = schemaList.value[0]
    }
  } catch (error) {
    console.error('加载Schema列表失败', error)
    schemaList.value = ['public']
  } finally {
    loadingSchemas.value = false
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
  schemaList.value = []
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
  // 编辑时加载schema列表
  if (record.datasourceId) {
    loadSchemasForDatasource(record.datasourceId)
  }
  modalVisible.value = true
}

async function loadSchemasForDatasource(datasourceId: number) {
  loadingSchemas.value = true
  try {
    const data = await request.get(`/datasources/${datasourceId}/schemas`)
    schemaList.value = data || []
  } catch (error) {
    console.error('加载Schema列表失败', error)
    schemaList.value = ['public']
  } finally {
    loadingSchemas.value = false
  }
}

function onDatasourceChange(datasourceId: number) {
  // 清空已选择的schema
  formState.sourceSchema = ''
  formState.targetSchema = ''
  // 加载新的schema列表
  if (datasourceId) {
    loadSchemasForDatasource(datasourceId)
  } else {
    schemaList.value = []
  }
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
    DRAFT: { en: 'Configuring', zh: '配置中' },
    READY: { en: 'Ready', zh: '就绪' },
    RUNNING: { en: 'Running', zh: '执行中' },
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

async function showExecutionsModal(record: any) {
  currentTaskId.value = record.id
  executionsModalVisible.value = true
  loadingExecutions.value = true

  try {
    const data = await request.get(`/masking/tasks/${record.id}/executions`, {
      params: { page: 1, page_size: 20 }
    })
    executions.value = data.items || []
  } catch (error) {
    executions.value = []
  } finally {
    loadingExecutions.value = false
  }
}

function formatDuration(start: string, end: string): string {
  if (!start || !end) return '-'
  const startTime = new Date(start).getTime()
  const endTime = new Date(end).getTime()
  const diff = Math.floor((endTime - startTime) / 1000)

  if (diff < 60) return `${diff}秒`
  if (diff < 3600) return `${Math.floor(diff / 60)}分${diff % 60}秒`
  return `${Math.floor(diff / 3600)}时${Math.floor((diff % 3600) / 60)}分`
}

async function showPreviewSql(record: any) {
  sqlPreviewModalVisible.value = true
  loadingSqlPreview.value = true
  sqlPreviewContent.value = ''

  try {
    const data = await request.post(`/masking/tasks/${record.id}/generate-sql`)
    sqlPreviewContent.value = data.sql || '-- No SQL generated --'
  } catch (error: any) {
    sqlPreviewContent.value = `-- Error: ${error?.message || 'Failed to generate SQL'}`
  } finally {
    loadingSqlPreview.value = false
  }
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
