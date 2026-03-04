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
            {{ record.backupTableName || t('common.yes') }}
          </a-tag>
          <span v-else class="text-gray-400">{{ t('anonymization.noBackup') }}</span>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="showDetailModal(record)">
              {{ t('anonymization.configure') }}
            </a-button>
            <a-button type="link" size="small" @click="showPreviewSql(record)">
              {{ t('dynamicMasking.previewSQL') }}
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
      :title="t('anonymization.createTask')"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleCreateOk"
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
          <a-select v-model:value="formState.datasourceId" :placeholder="t('common.pleaseSelect')" show-search>
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Schema" name="schemaName">
          <a-input v-model:value="formState.schemaName" placeholder="public" />
        </a-form-item>
        <a-form-item :label="t('masking.tableName')" name="tableName" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input v-model:value="formState.tableName" :placeholder="t('common.pleaseInput')" />
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
        <a-form-item :label="t('masking.columnName')" name="columnName" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input v-model:value="addColumnForm.columnName" :placeholder="t('common.pleaseInput')" />
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

const columns = computed(() => [
  { title: t('masking.taskName'), dataIndex: 'taskName', key: 'taskName' },
  { title: t('masking.tableName'), key: 'table', customRender: ({ record }: any) => `${record.schemaName}.${record.tableName}` },
  { title: t('anonymization.backupTable'), key: 'backup', width: 150 },
  { title: t('common.status'), key: 'status', width: 100 },
  { title: t('anonymization.lastExecuted'), dataIndex: 'lastExecutedAt', key: 'lastExecutedAt' },
  { title: t('common.actions'), key: 'actions', width: 280, fixed: 'right' as const }
])

const columnColumns = computed(() => [
  { title: t('masking.columnName'), dataIndex: 'columnName', key: 'columnName' },
  { title: t('masking.algorithm'), dataIndex: 'maskingAlgorithm', key: 'maskingAlgorithm' },
  { title: t('masking.algorithmParams'), dataIndex: 'algorithmParams', key: 'algorithmParams' },
  { title: t('common.actions'), key: 'actions', width: 100 }
])

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
    message.success(t('messages.createSuccess'))
    modalVisible.value = false
    loadData()
  } finally {
    modalLoading.value = false
  }
}

async function showDetailModal(record: any) {
  currentTask.value = record
  detailModalVisible.value = true
  columnRules.value = []
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
        message.error(t('dynamicMasking.invalidJson'))
        return
      }
    }

    await request.post(`/anonymization/tasks/${currentTask.value.id}/columns`, {
      column_name: addColumnForm.columnName,
      masking_algorithm: addColumnForm.maskingAlgorithm,
      algorithm_params: params
    })
    message.success(t('messages.createSuccess'))
    addColumnModalVisible.value = false
  } finally {
    addColumnLoading.value = false
  }
}

async function deleteColumnRule(id: number) {
  message.success(t('messages.deleteSuccess'))
}

async function executeTask(record: any) {
  try {
    const result = await request.post(`/anonymization/tasks/${record.id}/execute`)
    message.success(result.message || t('messages.executeSuccess'))
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
    message.success(t('messages.deleteSuccess'))
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
  const texts: Record<string, Record<string, string>> = {
    DRAFT: { en: 'Draft', zh: '草稿' },
    EXECUTED: { en: 'Executed', zh: '已执行' }
  }
  return texts[status]?.[locale.value] || status
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
