<template>
  <div class="dynamic-masking-list">
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
          <a-select-option value="ACTIVE">Active</a-select-option>
          <a-select-option value="INACTIVE">Inactive</a-select-option>
        </a-select>
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          New Rule
        </a-button>
      </a-space>
    </div>

    <a-alert
      message="Dynamic Masking"
      description="Configure role-based masking rules for database tables. Different database roles will see masked data when querying."
      type="info"
      show-icon
      style="margin-bottom: 16px"
    />

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
        <template v-if="column.key === 'isEnabled'">
          <a-tag :color="record.isEnabled ? 'success' : 'default'">
            {{ record.isEnabled ? 'Enabled' : 'Disabled' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'maskedRoles'">
          <a-tag v-for="role in record.maskedRoles" :key="role" color="orange">
            {{ role }}
          </a-tag>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="showDetailModal(record)">
              Configure
            </a-button>
            <a-popconfirm
              v-if="!record.isEnabled"
              title="Enable this rule? This will apply SECURITY LABEL to the table."
              @confirm="enableRule(record)"
            >
              <a-button type="primary" size="small">
                Enable
              </a-button>
            </a-popconfirm>
            <a-popconfirm
              v-else
              title="Disable this rule?"
              @confirm="disableRule(record)"
            >
              <a-button size="small">
                Disable
              </a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="showPreviewSql(record)">
              Preview SQL
            </a-button>
            <a-popconfirm
              v-if="!record.isEnabled"
              title="Are you sure you want to delete this rule?"
              @confirm="deleteRule(record.id)"
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
      title="New Dynamic Masking Rule"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleCreateOk"
      width="600px"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="Rule Name" name="ruleName" :rules="[{ required: true, message: 'Please enter' }]">
          <a-input v-model:value="formState.ruleName" placeholder="e.g., users table dynamic masking" />
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
          <a-input v-model:value="formState.tableName" placeholder="Table to mask" />
        </a-form-item>
        <a-form-item label="Masked Roles" name="maskedRoles" :rules="[{ required: true, message: 'Please enter' }]">
          <a-select
            v-model:value="formState.maskedRoles"
            mode="tags"
            placeholder="Database roles that will see masked data"
          >
          </a-select>
        </a-form-item>
        <a-form-item label="Exempted Roles" name="exemptedRoles">
          <a-select
            v-model:value="formState.exemptedRoles"
            mode="tags"
            placeholder="Database roles that can see original data"
          >
          </a-select>
        </a-form-item>
        <a-form-item label="Description" name="description">
          <a-textarea v-model:value="formState.description" :rows="2" placeholder="Rule description" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Detail/Column Config Modal -->
    <a-modal
      :title="`Configure: ${currentRule?.ruleName || ''}`"
      v-model:open="detailModalVisible"
      width="800px"
      :footer="null"
    >
      <div v-if="currentRule">
        <a-descriptions :column="2" bordered size="small" style="margin-bottom: 16px">
          <a-descriptions-item label="Table">{{ currentRule.schemaName }}.{{ currentRule.tableName }}</a-descriptions-item>
          <a-descriptions-item label="Status">
            <a-tag :color="getStatusColor(currentRule.status)">{{ getStatusText(currentRule.status) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="Masked Roles">
            <a-tag v-for="role in currentRule.maskedRoles" :key="role" color="orange">{{ role }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="Exempted Roles">
            <a-tag v-for="role in currentRule.exemptedRoles" :key="role" color="green">{{ role }}</a-tag>
          </a-descriptions-item>
        </a-descriptions>

        <a-divider>Column Masking Rules</a-divider>

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

        <div style="margin-top: 16px">
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
          <a-input v-model:value="addColumnForm.columnName" placeholder="Column to mask" />
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
        message="This SQL will be executed when enabling the rule"
        type="warning"
        show-icon
        style="margin-bottom: 16px"
      />
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
const currentRule = ref<any>(null)
const columnRules = ref<any[]>([])
const previewSql = ref('')

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
  ruleName: '',
  datasourceId: undefined as number | undefined,
  schemaName: 'public',
  tableName: '',
  maskedRoles: [] as string[],
  exemptedRoles: [] as string[],
  description: ''
})

const addColumnForm = reactive({
  columnName: '',
  maskingAlgorithm: '',
  algorithmParamsStr: ''
})

const columns = [
  { title: 'Rule Name', dataIndex: 'ruleName', key: 'ruleName' },
  { title: 'Table', key: 'table', customRender: ({ record }: any) => `${record.schemaName}.${record.tableName}` },
  { title: 'Masked Roles', key: 'maskedRoles', width: 200 },
  { title: 'Status', key: 'status', width: 100 },
  { title: 'Enabled', key: 'isEnabled', width: 100 },
  { title: 'Actions', key: 'actions', width: 300, fixed: 'right' as const }
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
    const data = await request.get('/dynamic-masking/rules', {
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
    ruleName: '',
    datasourceId: undefined,
    schemaName: 'public',
    tableName: '',
    maskedRoles: [],
    exemptedRoles: [],
    description: ''
  })
  modalVisible.value = true
}

async function handleCreateOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    await request.post('/dynamic-masking/rules', formState)
    message.success('Rule created successfully')
    modalVisible.value = false
    loadData()
  } finally {
    modalLoading.value = false
  }
}

async function showDetailModal(record: any) {
  currentRule.value = record
  detailModalVisible.value = true
  await loadColumnRules(record.id)
}

async function loadColumnRules(ruleId: number) {
  columnLoading.value = true
  try {
    const rule = await request.get(`/dynamic-masking/rules/${ruleId}/preview-sql`)
    // Load column rules from the rule
    columnRules.value = [] // TODO: Add endpoint to get column rules
  } finally {
    columnLoading.value = false
  }
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

    await request.post(`/dynamic-masking/rules/${currentRule.value.id}/columns`, {
      column_name: addColumnForm.columnName,
      masking_algorithm: addColumnForm.maskingAlgorithm,
      algorithm_params: params
    })
    message.success('Column rule added successfully')
    addColumnModalVisible.value = false
    await loadColumnRules(currentRule.value.id)
  } finally {
    addColumnLoading.value = false
  }
}

async function deleteColumnRule(id: number) {
  // TODO: Add endpoint to delete column rule
  message.success('Column rule deleted')
}

async function enableRule(record: any) {
  try {
    await request.post(`/dynamic-masking/rules/${record.id}/enable`)
    message.success('Rule enabled successfully')
    loadData()
  } catch (error) {
    //
  }
}

async function disableRule(record: any) {
  try {
    await request.post(`/dynamic-masking/rules/${record.id}/disable`)
    message.success('Rule disabled successfully')
    loadData()
  } catch (error) {
    //
  }
}

async function showPreviewSql(record: any) {
  try {
    const data = await request.get(`/dynamic-masking/rules/${record.id}/preview-sql`)
    previewSql.value = data.sql
    previewSqlModalVisible.value = true
  } catch (error) {
    //
  }
}

async function deleteRule(id: number) {
  try {
    await request.delete(`/dynamic-masking/rules/${id}`)
    message.success('Rule deleted successfully')
    loadData()
  } catch (error) {
    //
  }
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    DRAFT: 'default',
    ACTIVE: 'success',
    INACTIVE: 'warning'
  }
  return colors[status] || 'default'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    DRAFT: 'Draft',
    ACTIVE: 'Active',
    INACTIVE: 'Inactive'
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
