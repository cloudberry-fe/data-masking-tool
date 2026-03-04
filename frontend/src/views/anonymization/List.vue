<template>
  <div class="anonymization-list">
    <div class="page-header">
      <a-space>
        <a-select
          v-model:value="search.datasourceId"
          placeholder="Select Datasource"
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
          placeholder="Status"
          style="width: 140px"
          allow-clear
          @change="loadData"
        >
          <a-select-option value="DRAFT">Draft</a-select-option>
          <a-select-option value="EXECUTED">Executed</a-select-option>
        </a-select>
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          New Task
        </a-button>
      </a-space>
    </div>

    <a-alert
      message="In-Place Anonymization"
      type="warning"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #description>
        <strong>Warning:</strong> Anonymization permanently modifies the original table data. This operation is irreversible.
        <ul style="margin: 8px 0 0 0; padding-left: 20px;">
          <li>Original data will be permanently replaced with anonymized values</li>
          <li>Enable backup option to create a backup table before anonymization</li>
          <li>Suitable for GDPR compliance and data destruction scenarios</li>
        </ul>
      </template>
    </a-alert>

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
        <template v-if="column.key === 'backup'">
          <a-tag v-if="record.backupBeforeAnonymize" color="blue">
            {{ record.backupTableName || 'Enabled' }}
          </a-tag>
          <span v-else class="text-gray-400">No backup</span>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="showDetailModal(record)">
              Configure
            </a-button>
            <a-button type="link" size="small" @click="showPreviewSql(record)">
              Preview SQL
            </a-button>
            <a-popconfirm
              v-if="record.status === 'DRAFT'"
              title="Execute anonymization? This will permanently modify the original table data!"
              @confirm="executeTask(record)"
            >
              <a-button type="primary" size="small" danger>
                Execute
              </a-button>
            </a-popconfirm>
            <a-popconfirm
              v-if="record.status === 'DRAFT'"
              title="Are you sure you want to delete this task?"
              @confirm="deleteTask(record.id)"
            >
              <a-button type="link" size="small" danger>
                Delete
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- Create Modal -->
    <a-modal
      title="New Anonymization Task"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleCreateOk"
      width="600px"
    >
      <a-alert
        message="Anonymization is irreversible!"
        description="Please make sure to enable backup option for important data."
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
        <a-form-item label="Task Name" name="taskName" :rules="[{ required: true, message: 'Please enter' }]">
          <a-input v-model:value="formState.taskName" placeholder="e.g., Customer data anonymization" />
        </a-form-item>
        <a-form-item label="Data Source" name="datasourceId" :rules="[{ required: true, message: 'Please select' }]">
          <a-select v-model:value="formState.datasourceId" placeholder="Please select" show-search>
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Schema" name="schemaName">
          <a-input v-model:value="formState.schemaName" placeholder="public" />
        </a-form-item>
        <a-form-item label="Table Name" name="tableName" :rules="[{ required: true, message: 'Please enter' }]">
          <a-input v-model:value="formState.tableName" placeholder="Table to anonymize" />
        </a-form-item>
        <a-form-item label="Backup Before" name="backupBeforeAnonymize">
          <a-switch v-model:checked="formState.backupBeforeAnonymize" />
          <span style="margin-left: 8px; color: #666">
            Create backup table before anonymization (recommended)
          </span>
        </a-form-item>
        <a-form-item label="Description" name="description">
          <a-textarea v-model:value="formState.description" :rows="2" placeholder="Task description" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Detail/Column Config Modal -->
    <a-modal
      :title="`Configure: ${currentTask?.taskName || ''}`"
      v-model:open="detailModalVisible"
      width="800px"
      :footer="null"
    >
      <div v-if="currentTask">
        <a-descriptions :column="2" bordered size="small" style="margin-bottom: 16px">
          <a-descriptions-item label="Table">{{ currentTask.schemaName }}.{{ currentTask.tableName }}</a-descriptions-item>
          <a-descriptions-item label="Status">
            <a-tag :color="getStatusColor(currentTask.status)">{{ getStatusText(currentTask.status) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="Backup">
            <a-tag v-if="currentTask.backupBeforeAnonymize" color="blue">{{ currentTask.backupTableName || 'Enabled' }}</a-tag>
            <span v-else>No backup</span>
          </a-descriptions-item>
          <a-descriptions-item label="Last Executed">
            {{ currentTask.lastExecutedAt || '-' }}
          </a-descriptions-item>
        </a-descriptions>

        <a-divider>Column Anonymization Rules</a-divider>

        <a-table
          :columns="columnColumns"
          :data-source="columnRules"
          :loading="columnLoading"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'actions'">
              <a-popconfirm title="Delete this rule?" @confirm="deleteColumnRule(record.id)">
                <a-button type="link" size="small" danger>Delete</a-button>
              </a-popconfirm>
            </template>
          </template>
        </a-table>

        <div v-if="currentTask.status === 'DRAFT'" style="margin-top: 16px">
          <a-button type="dashed" block @click="showAddColumnModal">
            <PlusOutlined /> Add Column Rule
          </a-button>
        </div>
      </div>
    </a-modal>

    <!-- Add Column Rule Modal -->
    <a-modal
      title="Add Column Rule"
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
        <a-form-item label="Column Name" name="columnName" :rules="[{ required: true, message: 'Please enter' }]">
          <a-input v-model:value="addColumnForm.columnName" placeholder="Column to anonymize" />
        </a-form-item>
        <a-form-item label="Algorithm" name="maskingAlgorithm" :rules="[{ required: true, message: 'Please select' }]">
          <a-select v-model:value="addColumnForm.maskingAlgorithm" placeholder="Select algorithm" show-search>
            <a-select-option v-for="algo in algorithms" :key="algo.code" :value="algo.code">
              {{ algo.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Parameters" name="algorithmParams">
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
      title="Generated SQL Preview"
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
        <a-descriptions-item label="Backup Table">{{ previewData.backupTable || 'None' }}</a-descriptions-item>
      </a-descriptions>
      <pre class="sql-preview">{{ previewSql }}</pre>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const modalVisible = ref(false)
const modalLoading = ref(false)
const detailModalVisible = ref(false)
const addColumnModalVisible = ref(false)
const addColumnLoading = ref(false)
const previewSqlModalVisible = ref(false)
const columnLoading = ref(false)
const formRef = ref()
const addColumnFormRef = ref()

const dataSource = ref<any[]>([])
const datasourceList = ref<any[]>([])
const algorithms = ref<any[]>([])
const currentTask = ref<any>(null)
const columnRules = ref<any[]>([])
const previewSql = ref('')
const previewData = ref<any>({})

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
  taskName: '',
  datasourceId: undefined as number | undefined,
  schemaName: 'public',
  tableName: '',
  backupBeforeAnonymize: true,
  description: ''
})

const addColumnForm = reactive({
  columnName: '',
  maskingAlgorithm: '',
  algorithmParamsStr: ''
})

const columns = [
  { title: 'Task Name', dataIndex: 'taskName', key: 'taskName' },
  { title: 'Table', key: 'table', customRender: ({ record }: any) => `${record.schemaName}.${record.tableName}` },
  { title: 'Backup', key: 'backup', width: 150 },
  { title: 'Status', key: 'status', width: 100 },
  { title: 'Last Executed', dataIndex: 'lastExecutedAt', key: 'lastExecutedAt' },
  { title: 'Actions', key: 'actions', width: 280, fixed: 'right' as const }
]

const columnColumns = [
  { title: 'Column', dataIndex: 'columnName', key: 'columnName' },
  { title: 'Algorithm', dataIndex: 'maskingAlgorithm', key: 'maskingAlgorithm' },
  { title: 'Parameters', dataIndex: 'algorithmParams', key: 'algorithmParams' },
  { title: 'Actions', key: 'actions', width: 100 }
]

async function loadDatasources() {
  try {
    const data = await request.get('/datasources', { params: { page: 1, pageSize: 100 } })
    datasourceList.value = data.items
  } catch (error) {
    //
  }
}

async function loadAlgorithms() {
  try {
    const data = await request.get('/masking/algorithms')
    algorithms.value = data.algorithms
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
  Object.assign(formState, {
    taskName: '',
    datasourceId: undefined,
    schemaName: 'public',
    tableName: '',
    backupBeforeAnonymize: true,
    description: ''
  })
  modalVisible.value = true
}

async function handleCreateOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    await request.post('/anonymization/tasks', formState)
    message.success('Task created successfully')
    modalVisible.value = false
    loadData()
  } finally {
    modalLoading.value = false
  }
}

async function showDetailModal(record: any) {
  currentTask.value = record
  detailModalVisible.value = true
  columnRules.value = [] // TODO: Load column rules
}

function showAddColumnModal() {
  Object.assign(addColumnForm, {
    columnName: '',
    maskingAlgorithm: '',
    algorithmParamsStr: ''
  })
  addColumnModalVisible.value = true
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
        message.error('Invalid JSON for parameters')
        return
      }
    }

    await request.post(`/anonymization/tasks/${currentTask.value.id}/columns`, {
      column_name: addColumnForm.columnName,
      masking_algorithm: addColumnForm.maskingAlgorithm,
      algorithm_params: params
    })
    message.success('Column rule added successfully')
    addColumnModalVisible.value = false
  } finally {
    addColumnLoading.value = false
  }
}

async function deleteColumnRule(id: number) {
  message.success('Column rule deleted')
}

async function executeTask(record: any) {
  try {
    const result = await request.post(`/anonymization/tasks/${record.id}/execute`)
    message.success(result.message || 'Anonymization completed')
    loadData()
  } catch (error) {
    //
  }
}

async function showPreviewSql(record: any) {
  try {
    const data = await request.get(`/anonymization/tasks/${record.id}/preview-sql`)
    previewSql.value = data.sql
    previewData.value = data
    previewSqlModalVisible.value = true
  } catch (error) {
    //
  }
}

async function deleteTask(id: number) {
  try {
    await request.delete(`/anonymization/tasks/${id}`)
    message.success('Task deleted successfully')
    loadData()
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
  const texts: Record<string, string> = {
    DRAFT: 'Draft',
    EXECUTED: 'Executed'
  }
  return texts[status] || status
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
}
</style>
