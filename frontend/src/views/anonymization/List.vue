<template>
  <div class="anonymization-list">
    <div class="page-header">
      <a-space>
        <a-select
          v-model:value="search.datasourceId"
          :placeholder="t('common.pleaseSelect')"
          style="width: 200px"
          allow-clear
          @change="loadData"
        >
          <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
            {{ ds.datasourceName }}
          </a-select-option>
        </a-select>
        <a-select
          v-model:value="search.status"
          :placeholder="t('common.status')"
          style="width: 140px"
          allow-clear
          @change="loadData"
        >
          <a-select-option value="DRAFT">{{ t('masking.statusDraft') }}</a-select-option>
          <a-select-option value="EXECUTED">{{ t('anonymization.executed') }}</a-select-option>
        </a-select>
      </a-space>
      <a-space>
        <a-button @click="showExecutionsModal">
          {{ t('masking.executionHistory') }}
        </a-button>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          {{ t('anonymization.createTask') }}
        </a-button>
      </a-space>
    </div>

    <a-alert
      :message="t('anonymization.title')"
      type="warning"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #description>
        <strong>{{ t('anonymization.warning') }}</strong>
        <ul style="margin: 8px 0 0 0; padding-left: 20px;">
          <li>{{ t('anonymization.warningDesc1') }}</li>
          <li>{{ t('anonymization.warningDesc2') }}</li>
          <li>{{ t('anonymization.warningDesc3') }}</li>
        </ul>
      </template>
    </a-alert>

    <a-table
      :columns="columns"
      :data-source="taskList"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'datasource'">
          {{ getDatasourceName(record.datasourceId) }}
        </template>
        <template v-if="column.key === 'table'">
          {{ record.schemaName }}.{{ record.tableName }}
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'backup'">
          <a-tag v-if="record.backupBeforeAnonymize" color="blue">
            {{ record.backupTableName || t('common.yes') }}
          </a-tag>
          <span v-else class="text-gray-400">{{ t('anonymization.noBackup') }}</span>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="showDetailModal(record)">
              {{ t('common.dataConfig') }}
            </a-button>
            <a-button type="link" size="small" @click="showPreviewSql(record)">
              {{ t('dynamicMasking.previewSQL') }}
            </a-button>
            <a-button type="link" size="small" @click="showTaskExecutions(record)">
              {{ t('masking.executionHistory') }}
            </a-button>
            <a-popconfirm
              v-if="record.status === 'DRAFT'"
              :title="t('anonymization.executeConfirm')"
              @confirm="executeTask(record)"
            >
              <a-button type="primary" size="small" danger>
                {{ t('masking.execute') }}
              </a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="showEditModal(record)" v-if="record.status === 'DRAFT'">
              {{ t('common.edit') }}
            </a-button>
            <a-popconfirm
              v-if="record.status === 'DRAFT'"
              :title="t('messages.deleteConfirm')"
              @confirm="deleteTask(record.id)"
            >
              <a-button type="link" size="small" danger>
                {{ t('common.delete') }}
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- Create Modal -->
    <a-modal
      :title="isEdit ? t('common.edit') : t('anonymization.createTask')"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      width="600px"
    >
      <a-alert
        :message="t('anonymization.warningTitle')"
        :description="t('anonymization.warningHint')"
        type="warning"
        show-icon
        style="margin-bottom: 16px"
      />
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
          <a-select v-model:value="formState.datasourceId" :placeholder="t('common.pleaseSelect')" show-search @change="onFormDatasourceChange">
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Schema" name="schemaName">
          <a-select
            v-model:value="formState.schemaName"
            :placeholder="t('common.pleaseSelect')"
            :loading="loadingSchemas"
            :disabled="!formState.datasourceId"
            show-search
            allow-clear
            @change="onFormSchemaChange"
          >
            <a-select-option v-for="schema in schemaList" :key="schema" :value="schema">
              {{ schema }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('masking.tableName')" name="tableName" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select
            v-model:value="formState.tableName"
            :placeholder="t('common.pleaseSelect')"
            :loading="loadingTables"
            :disabled="!formState.datasourceId"
            show-search
            allow-clear
            @focus="loadTablesForForm"
          >
            <a-select-option v-for="table in tableList" :key="table.tableName" :value="table.tableName">
              {{ table.tableName }}
              <span v-if="table.tableComment" style="color: #999; margin-left: 8px; font-size: 12px">{{ table.tableComment }}</span>
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('anonymization.backupEnabled')" name="backupBeforeAnonymize">
          <a-switch v-model:checked="formState.backupBeforeAnonymize" />
          <span style="margin-left: 8px; color: #666">
            {{ t('anonymization.backupHint') }}
          </span>
        </a-form-item>
        <a-form-item :label="t('common.description')" name="description">
          <a-textarea v-model:value="formState.description" :rows="2" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Detail/Column Config Modal -->
    <a-modal
      :title="`${t('anonymization.configure')}: ${currentTask?.taskName || ''}`"
      v-model:open="detailModalVisible"
      width="800px"
      :footer="null"
    >
      <div v-if="currentTask">
        <a-descriptions :column="2" bordered size="small" style="margin-bottom: 16px">
          <a-descriptions-item label="Table">{{ currentTask.schemaName }}.{{ currentTask.tableName }}</a-descriptions-item>
          <a-descriptions-item :label="t('common.status')">
            <a-tag :color="getStatusColor(currentTask.status)">{{ getStatusText(currentTask.status) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item :label="t('anonymization.backupTable')">
            <a-tag v-if="currentTask.backupBeforeAnonymize" color="blue">{{ currentTask.backupTableName || t('common.yes') }}</a-tag>
            <span v-else>{{ t('anonymization.noBackup') }}</span>
          </a-descriptions-item>
          <a-descriptions-item :label="t('anonymization.lastExecuted')">
            {{ currentTask.lastExecutedAt || '-' }}
          </a-descriptions-item>
        </a-descriptions>

        <a-divider>{{ t('anonymization.columnRules') }}</a-divider>

        <a-table
          :columns="columnColumns"
          :data-source="columnRules"
          :loading="columnLoading"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'algorithmParams'">
              <code v-if="record.algorithmParams">{{ JSON.stringify(record.algorithmParams) }}</code>
              <span v-else>-</span>
            </template>
            <template v-if="column.key === 'actions'">
              <a-popconfirm :title="t('messages.deleteConfirm')" @confirm="deleteColumnRule(record.id)">
                <a-button type="link" size="small" danger>{{ t('common.delete') }}</a-button>
              </a-popconfirm>
            </template>
          </template>
        </a-table>

        <div v-if="currentTask.status === 'DRAFT'" style="margin-top: 16px">
          <a-button type="dashed" block @click="showAddColumnModal">
            <PlusOutlined /> {{ t('masking.addColumn') }}
          </a-button>
        </div>
      </div>
    </a-modal>

    <!-- Add Column Rule Modal -->
    <a-modal
      :title="t('anonymization.addColumnRule')"
      v-model:open="addColumnModalVisible"
      :confirm-loading="addColumnLoading"
      @ok="handleAddColumnOk"
    >
      <a-form
        ref="addColumnFormRef"
        :model="addColumnForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item :label="t('masking.columnName')" name="columnName" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select
            v-model:value="addColumnForm.columnName"
            :placeholder="t('common.pleaseSelect')"
            :loading="loadingColumns"
            show-search
            allow-clear
            @focus="loadColumnsForRule"
            @change="onColumnSelect"
          >
            <a-select-option v-for="col in columnList" :key="col.columnName" :value="col.columnName">
              {{ col.columnName }}
              <a-tag size="small" style="margin-left: 8px">{{ col.dataType }}</a-tag>
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('masking.dataType')" name="dataType">
          <a-input v-model:value="addColumnForm.dataType" disabled />
        </a-form-item>
        <a-form-item :label="t('masking.algorithm')" name="maskingAlgorithm" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select v-model:value="addColumnForm.maskingAlgorithm" :placeholder="t('common.pleaseSelect')" show-search>
            <a-select-option v-for="algo in algorithms" :key="algo.code" :value="algo.code">
              {{ algo.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('masking.algorithmParams')" name="algorithmParams">
          <a-textarea
            v-model:value="addColumnForm.algorithmParamsStr"
            placeholder='{"show_first": 2, "show_last": 2}'
            :rows="2"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Preview SQL Modal -->
    <a-modal
      :title="t('dynamicMasking.previewSQL')"
      v-model:open="previewSqlModalVisible"
      width="700px"
      :footer="null"
    >
      <a-alert
        :message="previewData.warning"
        type="error"
        show-icon
        style="margin-bottom: 16px"
      />
      <a-descriptions :column="2" size="small" style="margin-bottom: 16px">
        <a-descriptions-item label="Table">{{ previewData.tableName }}</a-descriptions-item>
        <a-descriptions-item :label="t('anonymization.backupTable')">{{ previewData.backupTable || t('anonymization.noBackup') }}</a-descriptions-item>
      </a-descriptions>
      <pre class="sql-preview">{{ previewSql }}</pre>
    </a-modal>

    <!-- Executions Modal -->
    <a-modal
      :title="t('masking.executionHistory')"
      v-model:open="executionsModalVisible"
      width="900px"
      :footer="null"
    >
      <a-table
        :columns="executionColumns"
        :data-source="executionList"
        :loading="executionsLoading"
        :pagination="executionPagination"
        @change="handleExecutionTableChange"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getExecutionStatusColor(record.status)">{{ record.status }}</a-tag>
          </template>
          <template v-if="column.key === 'duration'">
            {{ record.duration?.formatted || '-' }}
          </template>
          <template v-if="column.key === 'errorMessage'">
            <a-tooltip v-if="record.errorMessage" :title="record.errorMessage">
              <span class="error-text">{{ record.errorMessage.substring(0, 50) }}...</span>
            </a-tooltip>
            <span v-else>-</span>
          </template>
          <template v-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="showExecutionDetail(record)">
              {{ t('common.detail') || '详情' }}
            </a-button>
          </template>
        </template>
      </a-table>
    </a-modal>

    <!-- Execution Detail Modal -->
    <a-modal
      :title="`${t('common.detail') || '详情'}: ${currentExecution?.executionNo || ''}`"
      v-model:open="executionDetailModalVisible"
      width="600px"
      :footer="null"
    >
      <a-descriptions :column="1" bordered size="small" v-if="currentExecution">
        <a-descriptions-item :label="t('masking.executionNo')">{{ currentExecution.executionNo }}</a-descriptions-item>
        <a-descriptions-item :label="t('common.status')">
          <a-tag :color="getExecutionStatusColor(currentExecution.status)">{{ currentExecution.status }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item :label="t('masking.startTime')">{{ currentExecution.startTime }}</a-descriptions-item>
        <a-descriptions-item :label="t('masking.endTime')">{{ currentExecution.endTime || '-' }}</a-descriptions-item>
        <a-descriptions-item :label="t('masking.duration')">{{ currentExecution.duration?.formatted || '-' }}</a-descriptions-item>
        <a-descriptions-item :label="t('masking.totalRecords')">{{ currentExecution.totalRecords || 0 }}</a-descriptions-item>
        <a-descriptions-item v-if="currentExecution.errorMessage" :label="t('masking.errorMessage')">
          <pre class="error-message">{{ currentExecution.errorMessage }}</pre>
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const { t, locale } = useI18n()

const loading = ref(false)
const modalVisible = ref(false)
const modalLoading = ref(false)
const isEdit = ref(false)
const detailModalVisible = ref(false)
const addColumnModalVisible = ref(false)
const addColumnLoading = ref(false)
const previewSqlModalVisible = ref(false)
const columnLoading = ref(false)
const formRef = ref()
const addColumnFormRef = ref()

const taskList = ref<any[]>([])
const datasourceList = ref<any[]>([])
const algorithms = ref<any[]>([])
const currentTask = ref<any>(null)
const columnRules = ref<any[]>([])
const previewSql = ref('')
const previewData = ref<any>({})

// Schema, Table, Column 选择相关
const schemaList = ref<string[]>([])
const tableList = ref<any[]>([])
const columnList = ref<any[]>([])
const loadingSchemas = ref(false)
const loadingTables = ref(false)
const loadingColumns = ref(false)

// Executions
const executionsModalVisible = ref(false)
const executionsLoading = ref(false)
const executionList = ref<any[]>([])
const executionPagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})
const currentTaskIdForExecutions = ref<number | null>(null)
const executionDetailModalVisible = ref(false)
const currentExecution = ref<any>(null)

const search = reactive({
  datasourceId: undefined as number | undefined,
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
  schemaName: 'public',
  tableName: '',
  backupBeforeAnonymize: true,
  description: ''
})

const addColumnForm = reactive({
  columnName: '',
  dataType: '',
  maskingAlgorithm: '',
  algorithmParamsStr: ''
})

const columns = computed(() => [
  { title: t('masking.taskName'), dataIndex: 'taskName', key: 'taskName' },
  { title: t('datasource.title'), key: 'datasource', width: 120 },
  { title: t('masking.tableName'), key: 'table', width: 180 },
  { title: t('anonymization.backupTable'), key: 'backup', width: 150 },
  { title: t('common.status'), key: 'status', width: 100 },
  { title: t('anonymization.lastExecuted'), dataIndex: 'lastExecutedAt', key: 'lastExecutedAt', width: 160 },
  { title: t('common.actions'), key: 'actions', width: 350, fixed: 'right' as const }
])

const columnColumns = computed(() => [
  { title: t('masking.columnName'), dataIndex: 'columnName', key: 'columnName', width: 150 },
  { title: t('masking.algorithm'), dataIndex: 'maskingAlgorithm', key: 'maskingAlgorithm', width: 200 },
  { title: t('masking.algorithmParams'), key: 'algorithmParams', width: 150 },
  { title: t('common.actions'), key: 'actions', width: 100 }
])

const executionColumns = computed(() => [
  { title: t('masking.executionNo'), dataIndex: 'executionNo', key: 'executionNo', width: 200 },
  { title: t('masking.taskName'), dataIndex: 'taskName', key: 'taskName', width: 150 },
  { title: t('common.status'), key: 'status', width: 100 },
  { title: t('masking.startTime'), dataIndex: 'startTime', key: 'startTime', width: 160 },
  { title: t('masking.duration'), key: 'duration', width: 100 },
  { title: t('masking.totalRecords'), dataIndex: 'totalRecords', key: 'totalRecords', width: 100 },
  { title: t('masking.errorMessage'), key: 'errorMessage', width: 150 },
  { title: t('common.actions'), key: 'actions', width: 80 }
])

function getDatasourceName(id: number): string {
  const ds = datasourceList.value.find(d => d.id === id)
  return ds?.datasourceName || '-'
}

async function loadDatasources() {
  try {
    const data = await request.get('/datasources', { params: { page: 1, pageSize: 100 } })
    datasourceList.value = data.items || []
  } catch (error) {
    //
  }
}

async function loadAlgorithms() {
  try {
    const data = await request.get('/masking/algorithms')
    algorithms.value = data.algorithms || []
  } catch (error) {
    //
  }
}

async function loadData() {
  loading.value = true
  try {
    const data = await request.get('/anonymization/tasks', {
      params: {
        page: pagination.current,
        page_size: pagination.pageSize,
        datasource_id: search.datasourceId,
        status: search.status
      }
    })
    taskList.value = data.items || []
    pagination.total = data.total || 0
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
    schemaName: 'public',
    tableName: '',
    backupBeforeAnonymize: true,
    description: ''
  })
  schemaList.value = []
  tableList.value = []
  modalVisible.value = true
}

function showEditModal(record: any) {
  isEdit.value = true
  Object.assign(formState, {
    id: record.id,
    taskName: record.taskName,
    datasourceId: record.datasourceId,
    schemaName: record.schemaName || 'public',
    tableName: record.tableName,
    backupBeforeAnonymize: record.backupBeforeAnonymize,
    description: record.description || ''
  })
  // 编辑时加载 schema 和表列表
  if (record.datasourceId) {
    loadSchemasForForm()
    if (record.schemaName) {
      loadTablesForForm()
    }
  }
  modalVisible.value = true
}

async function onFormDatasourceChange(datasourceId: number) {
  formState.schemaName = ''
  formState.tableName = ''
  schemaList.value = []
  tableList.value = []
  if (datasourceId) {
    await loadSchemasForForm()
  }
}

async function onFormSchemaChange(schema: string) {
  formState.tableName = ''
  tableList.value = []
  if (schema) {
    await loadTablesForForm()
  }
}

async function loadSchemasForForm() {
  if (!formState.datasourceId) return
  loadingSchemas.value = true
  try {
    const data = await request.get(`/datasources/${formState.datasourceId}/schemas`)
    schemaList.value = data || ['public']
    // 如果只有一个 schema，自动选中
    if (schemaList.value.length === 1 && !formState.schemaName) {
      formState.schemaName = schemaList.value[0]
    }
  } catch (error) {
    console.error('加载Schema列表失败', error)
    schemaList.value = ['public']
  } finally {
    loadingSchemas.value = false
  }
}

async function loadTablesForForm() {
  if (!formState.datasourceId || !formState.schemaName) return
  loadingTables.value = true
  try {
    const data = await request.get(`/datasources/${formState.datasourceId}/tables`, {
      params: { schema: formState.schemaName }
    })
    tableList.value = (data || []).map((t: any) => ({
      tableName: t.tableName || t.table_name,
      tableComment: t.tableComment || t.table_comment || ''
    }))
  } catch (error) {
    console.error('加载表列表失败', error)
    tableList.value = []
  } finally {
    loadingTables.value = false
  }
}

async function handleModalOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    if (isEdit.value) {
      await request.put(`/anonymization/tasks/${formState.id}`, formState)
      message.success(t('messages.updateSuccess'))
    } else {
      await request.post('/anonymization/tasks', formState)
      message.success(t('messages.createSuccess'))
    }

    modalVisible.value = false
    loadData()
  } finally {
    modalLoading.value = false
  }
}

async function showDetailModal(record: any) {
  currentTask.value = record
  columnList.value = []
  detailModalVisible.value = true
  columnLoading.value = true

  try {
    // 获取任务详情
    const detail = await request.get(`/anonymization/tasks/${record.id}`)
    currentTask.value = detail
    columnRules.value = detail.columnRules || []
  } catch (error) {
    columnRules.value = []
  } finally {
    columnLoading.value = false
  }
}

function showAddColumnModal() {
  Object.assign(addColumnForm, {
    columnName: '',
    dataType: '',
    maskingAlgorithm: '',
    algorithmParamsStr: ''
  })
  columnList.value = []
  addColumnModalVisible.value = true
}

async function loadColumnsForRule() {
  if (!currentTask.value?.datasourceId || !currentTask.value?.tableName) {
    message.warning(t('common.pleaseSelect'))
    return
  }
  if (columnList.value.length > 0) return

  loadingColumns.value = true
  try {
    const tableName = currentTask.value.schemaName
      ? `${currentTask.value.schemaName}.${currentTask.value.tableName}`
      : currentTask.value.tableName

    const data = await request.get(`/datasources/${currentTask.value.datasourceId}/tables/${tableName}/columns`, {
      params: { schema: currentTask.value.schemaName }
    })
    columnList.value = (data || []).map((c: any) => ({
      columnName: c.columnName || c.column_name,
      dataType: c.dataType || c.data_type,
      isNullable: c.isNullable ?? c.is_nullable ?? true
    }))
  } catch (error) {
    console.error('加载字段列表失败', error)
    message.error(t('testData.loadColumnsFailed'))
    columnList.value = []
  } finally {
    loadingColumns.value = false
  }
}

function onColumnSelect(columnName: string) {
  const col = columnList.value.find(c => c.columnName === columnName)
  if (col) {
    addColumnForm.dataType = col.dataType
  }
}

async function handleAddColumnOk() {
  try {
    await addColumnFormRef.value?.validate()
    addColumnLoading.value = true

    let params = {}
    if (addColumnForm.algorithmParamsStr) {
      try {
        params = JSON.parse(addColumnForm.algorithmParamsStr)
      } catch {
        message.error(t('dynamicMasking.invalidJson'))
        return
      }
    }

    await request.post(`/anonymization/tasks/${currentTask.value.id}/columns`, {
      columnName: addColumnForm.columnName,
      dataType: addColumnForm.dataType,
      maskingAlgorithm: addColumnForm.maskingAlgorithm,
      algorithmParams: params
    })
    message.success(t('messages.createSuccess'))
    addColumnModalVisible.value = false

    // 重新加载任务详情
    const detail = await request.get(`/anonymization/tasks/${currentTask.value.id}`)
    columnRules.value = detail.columnRules || []
  } finally {
    addColumnLoading.value = false
  }
}

async function deleteColumnRule(id: number) {
  try {
    await request.delete(`/anonymization/tasks/${currentTask.value.id}/columns/${id}`)
    message.success(t('messages.deleteSuccess'))

    // 重新加载任务详情
    const detail = await request.get(`/anonymization/tasks/${currentTask.value.id}`)
    columnRules.value = detail.columnRules || []
  } catch (error) {
    //
  }
}

async function executeTask(record: any) {
  try {
    const result = await request.post(`/anonymization/tasks/${record.id}/execute`)
    message.success(result.message || t('messages.executeSuccess'))
    loadData()
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '执行失败'
    message.error(errorMsg, 5)
  }
}

async function showPreviewSql(record: any) {
  try {
    const data = await request.get(`/anonymization/tasks/${record.id}/preview-sql`)
    previewSql.value = data.sql
    previewData.value = data
    previewSqlModalVisible.value = true
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '获取SQL预览失败'
    message.error(errorMsg)
  }
}

async function deleteTask(id: number) {
  try {
    await request.delete(`/anonymization/tasks/${id}`)
    message.success(t('messages.deleteSuccess'))
    loadData()
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '删除失败'
    message.error(errorMsg)
  }
}

// Executions
async function showExecutionsModal() {
  currentTaskIdForExecutions.value = null
  executionsModalVisible.value = true
  await loadExecutions()
}

async function showTaskExecutions(record: any) {
  currentTaskIdForExecutions.value = record.id
  executionsModalVisible.value = true
  await loadExecutions()
}

async function loadExecutions() {
  executionsLoading.value = true
  try {
    const params: any = {
      page: executionPagination.current,
      page_size: executionPagination.pageSize
    }

    let data
    if (currentTaskIdForExecutions.value) {
      data = await request.get(`/anonymization/tasks/${currentTaskIdForExecutions.value}/executions`, { params })
    } else {
      data = await request.get('/anonymization/executions', { params })
    }

    executionList.value = data.items || []
    executionPagination.total = data.total || 0
  } finally {
    executionsLoading.value = false
  }
}

function handleExecutionTableChange(pag: any) {
  executionPagination.current = pag.current
  executionPagination.pageSize = pag.pageSize
  loadExecutions()
}

async function showExecutionDetail(record: any) {
  try {
    const data = await request.get(`/anonymization/executions/${record.id}`)
    currentExecution.value = data
    executionDetailModalVisible.value = true
  } catch (error) {
    //
  }
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    DRAFT: 'default',
    EXECUTED: 'success'
  }
  return colors[status] || 'default'
}

function getStatusText(status: string): string {
  const texts: Record<string, Record<string, string>> = {
    DRAFT: { en: 'Draft', zh: '草稿' },
    EXECUTED: { en: 'Executed', zh: '已执行' }
  }
  return texts[status]?.[locale.value] || status
}

function getExecutionStatusColor(status: string): string {
  const colors: Record<string, string> = {
    RUNNING: 'processing',
    SUCCESS: 'success',
    FAILED: 'error'
  }
  return colors[status] || 'default'
}

onMounted(() => {
  loadDatasources()
  loadAlgorithms()
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
.sql-preview {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  white-space: pre-wrap;
  max-height: 400px;
}
.error-text {
  color: #ff4d4f;
  cursor: pointer;
}
.error-message {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  padding: 8px;
  border-radius: 4px;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}
</style>
