<template>
  <div class="masking-detail">
    <a-page-header
      :title="task?.taskName"
      sub-title="Masking Task Configuration"
      @back="$router.back()"
    >
      <template #extra>
        <a-space>
          <a-button @click="previewMasking" :loading="previewing">
            <EyeOutlined />
            Preview
          </a-button>
          <a-button @click="generateSQL">
            <CodeOutlined />
            Generate SQL
          </a-button>
          <a-button type="primary" @click="executeTask" :loading="executing">
            <PlayCircleOutlined />
            Execute Task
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="tables" tab="Table Configuration">
        <div class="tab-content">
          <div class="action-bar">
            <a-button type="primary" @click="showTableModal">
              <PlusOutlined />
              Add Table
            </a-button>
          </div>

          <a-table
            :columns="tableColumns"
            :data-source="tables"
            :pagination="false"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="record.enabled ? 'success' : 'default'">
                  {{ record.enabled ? 'Enabled' : 'Disabled' }}
                </a-tag>
              </template>
              <template v-if="column.key === 'actions'">
                <a-space>
                  <a-button type="link" size="small" @click="manageColumns(record)">
                    Columns ({{ record.columns?.length || 0 }})
                  </a-button>
                  <a-button type="link" size="small" @click="showTableModal(record)">
                    Edit
                  </a-button>
                  <a-popconfirm title="Are you sure you want to delete?" @confirm="deleteTable(record.id)">
                    <a-button type="link" size="small" danger>
                      Delete
                    </a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </div>
      </a-tab-pane>

      <a-tab-pane key="executions" tab="Execution History">
        <div class="tab-content">
          <a-table
            :columns="executionColumns"
            :data-source="executions"
            :pagination="true"
            row-key="id"
            size="small"
            @row-click="showExecutionDetail"
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
              <template v-if="column.key === 'actions'">
                <a-button type="link" size="small" @click.stop="showExecutionDetail(record)">
                  View Details
                </a-button>
              </template>
            </template>
          </a-table>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- Table Configuration Modal -->
    <a-modal
      :title="editingTable ? 'Edit Table' : 'Add Table'"
      v-model:open="tableModalVisible"
      @ok="handleTableModalOk"
      @cancel="tableModalVisible = false"
      width="650px"
    >
      <a-form ref="tableFormRef" :model="tableFormState" :label-col="{ span: 7 }">
        <a-divider>Source Table</a-divider>
        <a-form-item label="Source Schema" name="sourceSchema">
          <a-select
            v-model:value="tableFormState.sourceSchema"
            placeholder="Select schema"
            show-search
            allow-clear
            :loading="loadingSchemas"
            @change="onSourceSchemaChange"
          >
            <a-select-option v-for="schema in schemaList" :key="schema" :value="schema">
              {{ schema }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Source Table" name="sourceTable" :rules="[{ required: true }]">
          <a-select
            v-model:value="tableFormState.sourceTable"
            placeholder="Select source table"
            show-search
            :loading="loadingTables"
            @focus="loadTablesForSchema('source')"
            @change="onSourceTableChange"
          >
            <a-select-option v-for="table in sourceTableList" :key="table" :value="table">
              {{ table }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-divider>Target Table</a-divider>
        <a-form-item label="Target Schema" name="targetSchema">
          <a-select
            v-model:value="tableFormState.targetSchema"
            placeholder="Select or type new schema"
            show-search
            allow-clear
            :loading="loadingSchemas"
          >
            <a-select-option v-for="schema in schemaList" :key="schema" :value="schema">
              {{ schema }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Target Table" name="targetTable" :rules="[{ required: true }]">
          <a-input v-model:value="tableFormState.targetTable" placeholder="Target table name (e.g., users_masked)" />
        </a-form-item>

        <a-divider>Options</a-divider>
        <a-form-item label="Config Name" name="tableName">
          <a-input v-model:value="tableFormState.tableName" placeholder="Optional: custom name for this configuration" />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            Optional identifier. If empty, source table name will be used.
          </div>
        </a-form-item>
        <a-form-item label="Order" name="orderNo">
          <a-input-number v-model:value="tableFormState.orderNo" style="width: 100%" min="0" />
        </a-form-item>
        <a-form-item label="Enabled" name="enabled">
          <a-switch v-model:checked="tableFormState.enabled" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Column Configuration Drawer -->
    <a-drawer
      title="Column Configuration"
      :width="900"
      v-model:open="columnDrawerVisible"
    >
      <div v-if="currentTable" class="column-config">
        <div class="action-bar">
          <a-space>
            <a-button type="primary" size="small" @click="loadTableColumnsFromDB" :loading="loadingColumns">
              <PlusOutlined />
              Select from Database
            </a-button>
            <a-button size="small" @click="showColumnModal">
              <PlusOutlined />
              Add Manually
            </a-button>
          </a-space>
        </div>

        <a-table
          :columns="columnColumns"
          :data-source="columns"
          :pagination="false"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'algorithm'">
              <a-tag color="blue">{{ getAlgorithmName(record.maskingAlgorithm) }}</a-tag>
            </template>
            <template v-if="column.key === 'params'">
              <span v-if="record.algorithmParams && Object.keys(record.algorithmParams).length > 0">
                <a-tag v-for="(value, key) in record.algorithmParams" :key="key" size="small">
                  {{ key }}: {{ value }}
                </a-tag>
              </span>
              <span v-else class="text-gray-400">-</span>
            </template>
            <template v-if="column.key === 'actions'">
              <a-space>
                <a-button type="link" size="small" @click="showColumnModal(record)">
                  Edit
                </a-button>
                <a-popconfirm title="Are you sure you want to delete?" @confirm="deleteColumn(record.id)">
                  <a-button type="link" size="small" danger>
                    Delete
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>
    </a-drawer>

    <!-- Select Columns Modal -->
    <a-modal
      title="Select Columns from Database"
      v-model:open="selectColumnsModalVisible"
      @ok="handleSelectColumnsOk"
      @cancel="selectColumnsModalVisible = false"
      width="700px"
    >
      <a-alert
        v-if="dbColumns.length === 0 && !loadingColumns"
        message="No columns found. Please check if the table exists in the database."
        type="warning"
        class="mb-4"
      />
      <a-checkbox-group v-model:value="selectedColumnNames" style="width: 100%">
        <a-table
          :columns="dbColumnTableColumns"
          :data-source="dbColumns"
          :pagination="false"
          :loading="loadingColumns"
          row-key="columnName"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'select'">
              <a-checkbox :value="record.columnName" />
            </template>
            <template v-if="column.key === 'columnName'">
              <span class="font-bold">{{ record.columnName }}</span>
            </template>
            <template v-if="column.key === 'dataType'">
              <a-tag size="small">{{ record.dataType }}</a-tag>
            </template>
          </template>
        </a-table>
      </a-checkbox-group>
    </a-modal>

    <!-- Column Configuration Modal -->
    <a-modal
      :title="editingColumn ? 'Edit Column' : 'Add Column'"
      v-model:open="columnModalVisible"
      @ok="handleColumnModalOk"
      @cancel="columnModalVisible = false"
      width="700px"
    >
      <a-form ref="columnFormRef" :model="columnFormState" :label-col="{ span: 6 }">
        <a-form-item label="Column Name" name="columnName" :rules="[{ required: true }]">
          <a-input v-model:value="columnFormState.columnName" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Data Type" name="dataType">
          <a-input v-model:value="columnFormState.dataType" placeholder="varchar, int, etc." />
        </a-form-item>

        <!-- Algorithm Category Selection -->
        <a-form-item label="Category" name="algorithmCategory">
          <a-select
            v-model:value="selectedCategory"
            placeholder="Select category"
            @change="onCategoryChange"
          >
            <a-select-option value="">All Categories</a-select-option>
            <a-select-option v-for="cat in algorithmCategories" :key="cat.code" :value="cat.code">
              {{ cat.name }} - {{ cat.description }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- Algorithm Selection -->
        <a-form-item label="Algorithm" name="maskingAlgorithm" :rules="[{ required: true }]">
          <a-select
            v-model:value="columnFormState.maskingAlgorithm"
            placeholder="Please select"
            show-search
            :filter-option="filterAlgorithm"
            @change="onAlgorithmChange"
          >
            <a-select-option
              v-for="algo in filteredAlgorithms"
              :key="algo.code"
              :value="algo.code"
            >
              <div>
                <span class="font-bold">{{ algo.name }}</span>
                <span class="text-gray-400 ml-2">{{ algo.description }}</span>
              </div>
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- Algorithm Description -->
        <a-form-item v-if="selectedAlgorithm" label="Description">
          <div class="text-gray-500">
            {{ selectedAlgorithm.description }}
            <a-tag size="small" class="ml-2">{{ selectedAlgorithm.returnType }}</a-tag>
          </div>
        </a-form-item>

        <!-- Dynamic Algorithm Parameters -->
        <template v-if="selectedAlgorithm && selectedAlgorithm.params && selectedAlgorithm.params.length > 0">
          <a-divider>Algorithm Parameters</a-divider>
          <a-form-item
            v-for="param in selectedAlgorithm.params"
            :key="param.name"
            :label="param.name"
            :required="param.required"
          >
            <div class="flex items-center gap-2">
              <!-- Integer input -->
              <a-input-number
                v-if="param.type === 'int' || param.type === 'bigint'"
                v-model:value="columnFormState.algorithmParams[param.name]"
                :placeholder="param.description"
                style="width: 200px"
              />
              <!-- Float input -->
              <a-input-number
                v-else-if="param.type === 'float'"
                v-model:value="columnFormState.algorithmParams[param.name]"
                :placeholder="param.description"
                :step="0.1"
                style="width: 200px"
              />
              <!-- Boolean switch -->
              <a-switch
                v-else-if="param.type === 'bool'"
                v-model:checked="columnFormState.algorithmParams[param.name]"
              />
              <!-- Array input -->
              <a-input
                v-else-if="param.type === 'array'"
                v-model:value="columnFormState.algorithmParams[param.name]"
                :placeholder="param.description + ' (comma separated)'"
                style="width: 300px"
              />
              <!-- Text input (default) -->
              <a-input
                v-else
                v-model:value="columnFormState.algorithmParams[param.name]"
                :placeholder="param.description"
                style="width: 300px"
              />
              <span class="text-gray-400 text-xs">{{ param.description }}</span>
              <span v-if="param.default !== undefined && param.default !== null" class="text-gray-400 text-xs">
                (default: {{ param.default }})
              </span>
            </div>
          </a-form-item>
        </template>

        <a-form-item label="Description" name="description">
          <a-textarea v-model:value="columnFormState.description" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- SQL Preview Modal -->
    <a-modal
      title="Generated SQL"
      v-model:open="sqlModalVisible"
      :footer="null"
      width="800px"
    >
      <pre class="sql-preview">{{ generatedSQL }}</pre>
      <div class="mt-4">
        <a-button type="primary" @click="copySQL">
          <CopyOutlined />
          Copy to Clipboard
        </a-button>
      </div>
    </a-modal>

    <!-- Preview Modal -->
    <a-modal
      title="Masking Preview"
      v-model:open="previewModalVisible"
      :footer="null"
      width="800px"
    >
      <a-table
        v-if="previewData.columns"
        :columns="previewData.columns.map((c: string) => ({ title: c, dataIndex: c, key: c }))"
        :data-source="previewData.rows?.map((row: any[], idx: number) => {
          const obj: any = { key: idx }
          previewData.columns.forEach((c: string, i: number) => obj[c] = row[i])
          return obj
        })"
        size="small"
        :pagination="false"
      />
    </a-modal>

    <!-- Execution Detail Modal -->
    <a-modal
      title="Execution Details"
      v-model:open="executionDetailVisible"
      :footer="null"
      width="700px"
    >
      <a-descriptions v-if="selectedExecution" :column="2" bordered size="small">
        <a-descriptions-item label="Execution No" :span="2">
          {{ selectedExecution.executionNo }}
        </a-descriptions-item>
        <a-descriptions-item label="Status">
          <a-tag :color="getExecutionStatusColor(selectedExecution.status)">
            {{ getExecutionStatusText(selectedExecution.status) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="Trigger Type">
          {{ selectedExecution.triggerType }}
        </a-descriptions-item>
        <a-descriptions-item label="Start Time">
          {{ selectedExecution.startTime || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="End Time">
          {{ selectedExecution.endTime || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="Duration">
          {{ selectedExecution.duration?.formatted || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="Total Records">
          {{ selectedExecution.totalRecords }}
        </a-descriptions-item>
        <a-descriptions-item label="Success Records">
          <span class="text-green-600">{{ selectedExecution.successRecords }}</span>
        </a-descriptions-item>
        <a-descriptions-item label="Failed Records">
          <span :class="selectedExecution.failedRecords > 0 ? 'text-red-600' : ''">
            {{ selectedExecution.failedRecords }}
          </span>
        </a-descriptions-item>
      </a-descriptions>

      <a-divider v-if="selectedExecution?.errorMessage">Error Message</a-divider>
      <a-alert
        v-if="selectedExecution?.errorMessage"
        type="error"
        :message="selectedExecution.errorMessage"
        show-icon
        class="mt-4"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  CodeOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()

const taskId = computed(() => parseInt(route.params.id as string))
const task = ref<any>(null)
const activeTab = ref('tables')
const executing = ref(false)
const previewing = ref(false)

// Table related
const tables = ref<any[]>([])
const tableModalVisible = ref(false)
const tableFormRef = ref()
const editingTable = ref<any>(null)
const tableFormState = reactive({
  id: undefined as number | undefined,
  tableName: '',
  sourceSchema: '',
  sourceTable: '',
  targetSchema: '',
  targetTable: '',
  orderNo: 0,
  enabled: true
})

// Schema and table selection
const schemaList = ref<string[]>([])
const sourceTableList = ref<string[]>([])
const loadingSchemas = ref(false)
const loadingTables = ref(false)

// Column related
const columnDrawerVisible = ref(false)
const columnModalVisible = ref(false)
const columnFormRef = ref()
const currentTable = ref<any>(null)
const columns = ref<any[]>([])
const editingColumn = ref<any>(null)
const algorithms = ref<any[]>([])
const algorithmCategories = ref<any[]>([])
const selectedCategory = ref('')
const selectedAlgorithm = ref<any>(null)
const columnFormState = reactive({
  id: undefined as number | undefined,
  columnName: '',
  dataType: '',
  maskingAlgorithm: '',
  algorithmParams: {} as Record<string, any>,
  description: ''
})

// Database columns selection
const selectColumnsModalVisible = ref(false)
const loadingColumns = ref(false)
const dbColumns = ref<any[]>([])
const selectedColumnNames = ref<string[]>([])

const dbColumnTableColumns = [
  { title: 'Select', key: 'select', width: 60 },
  { title: 'Column Name', key: 'columnName', width: 200 },
  { title: 'Data Type', key: 'dataType', width: 120 },
  { title: 'Nullable', dataIndex: 'isNullable', key: 'isNullable', width: 80 }
]

// Execution history
const executions = ref<any[]>([])

// SQL Preview
const sqlModalVisible = ref(false)
const generatedSQL = ref('')
const previewModalVisible = ref(false)
const previewData = ref<any>({ columns: [], rows: [] })

// Execution detail
const executionDetailVisible = ref(false)
const selectedExecution = ref<any>(null)

const tableColumns = [
  { title: 'Config Name', dataIndex: 'tableName', key: 'tableName' },
  { title: 'Source Table', dataIndex: 'sourceTable', key: 'sourceTable' },
  { title: 'Target Table', dataIndex: 'targetTable', key: 'targetTable' },
  { title: 'Order', dataIndex: 'orderNo', key: 'orderNo', width: 80 },
  { title: 'Status', key: 'status', width: 80 },
  { title: 'Actions', key: 'actions', width: 200 }
]

const columnColumns = [
  { title: 'Column Name', dataIndex: 'columnName', key: 'columnName' },
  { title: 'Type', dataIndex: 'dataType', key: 'dataType', width: 120 },
  { title: 'Masking Algorithm', key: 'algorithm', width: 180 },
  { title: 'Parameters', key: 'params', width: 200 },
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Actions', key: 'actions', width: 140 }
]

const executionColumns = [
  { title: 'Execution ID', dataIndex: 'executionNo', key: 'executionNo' },
  { title: 'Trigger Type', dataIndex: 'triggerType', key: 'triggerType' },
  { title: 'Status', key: 'status', width: 100 },
  { title: 'Start Time', dataIndex: 'startTime', key: 'startTime' },
  { title: 'Duration', key: 'duration', width: 100 },
  { title: 'Total Records', dataIndex: 'totalRecords', key: 'totalRecords' },
  { title: 'Success', dataIndex: 'successRecords', key: 'successRecords' },
  { title: 'Failed', dataIndex: 'failedRecords', key: 'failedRecords' },
  { title: 'Actions', key: 'actions', width: 120 }
]

// Filtered algorithms based on category
const filteredAlgorithms = computed(() => {
  if (!selectedCategory.value) {
    return algorithms.value
  }
  return algorithms.value.filter(a => a.category === selectedCategory.value)
})

async function loadTask() {
  try {
    const data = await request.get(`/masking/tasks/${taskId.value}`)
    task.value = data
    tables.value = data.tables || []
  } catch (error) {
    message.error('Failed to load task')
  }
}

async function loadAlgorithms() {
  try {
    const data = await request.get('/masking/algorithms')
    algorithmCategories.value = data.categories || []
    algorithms.value = data.algorithms || []
  } catch (error) {
    console.error('Failed to load algorithms', error)
  }
}

async function loadExecutions() {
  try {
    const data = await request.get(`/masking/tasks/${taskId.value}/executions`)
    executions.value = data.items || []
  } catch (error) {
    //
  }
}

function getAlgorithmName(code: string): string {
  const algo = algorithms.value.find(a => a.code === code)
  return algo?.name || code
}

function filterAlgorithm(input: string, option: any): boolean {
  const algo = algorithms.value.find(a => a.code === option.value)
  if (!algo) return false
  return algo.name.toLowerCase().includes(input.toLowerCase()) ||
         algo.description.toLowerCase().includes(input.toLowerCase())
}

function onCategoryChange() {
  // Reset algorithm selection when category changes
  // columnFormState.maskingAlgorithm = ''
}

function onAlgorithmChange(code: string) {
  selectedAlgorithm.value = algorithms.value.find(a => a.code === code) || null
  // Initialize params with defaults
  if (selectedAlgorithm.value?.params) {
    const params: Record<string, any> = {}
    selectedAlgorithm.value.params.forEach((p: any) => {
      if (p.default !== undefined) {
        params[p.name] = p.default
      }
    })
    columnFormState.algorithmParams = params
  } else {
    columnFormState.algorithmParams = {}
  }
}

function showTableModal(record?: any) {
  // Load schemas when opening modal
  loadSchemas()

  if (record) {
    editingTable.value = record
    // Parse source table if it contains schema (e.g., "tpcds_1g.catalog_returns")
    let sourceSchema = ''
    let sourceTable = record.sourceTable || record.tableName

    if (sourceTable && sourceTable.includes('.')) {
      const parts = sourceTable.split('.')
      sourceSchema = parts[0]
      sourceTable = parts[1]
    }

    // Parse target table if it contains schema
    let targetSchema = ''
    let targetTable = record.targetTable || ''

    if (targetTable && targetTable.includes('.')) {
      const parts = targetTable.split('.')
      targetSchema = parts[0]
      targetTable = parts[1]
    }

    Object.assign(tableFormState, {
      id: record.id,
      tableName: record.tableName,
      sourceSchema: sourceSchema,
      sourceTable: sourceTable,
      targetSchema: targetSchema,
      targetTable: targetTable,
      orderNo: record.orderNo,
      enabled: record.enabled
    })
  } else {
    editingTable.value = null
    Object.assign(tableFormState, {
      id: undefined,
      tableName: '',
      sourceSchema: task.value?.sourceSchema || '',
      sourceTable: '',
      targetSchema: task.value?.targetSchema || '',
      targetTable: '',
      orderNo: 0,
      enabled: true
    })
  }
  tableModalVisible.value = true
}

async function loadSchemas() {
  if (!task.value?.datasourceId) return

  try {
    loadingSchemas.value = true
    const data = await request.get(`/datasources/${task.value.datasourceId}/schemas`)
    schemaList.value = data || ['public']
  } catch (error) {
    console.error('Failed to load schemas', error)
    schemaList.value = ['public']
  } finally {
    loadingSchemas.value = false
  }
}

async function loadTablesForSchema(type: 'source' | 'target') {
  if (!task.value?.datasourceId) return

  const schema = type === 'source' ? tableFormState.sourceSchema : tableFormState.targetSchema
  if (!schema) {
    sourceTableList.value = []
    return
  }

  try {
    loadingTables.value = true
    const data = await request.get(`/datasources/${task.value.datasourceId}/tables`, {
      params: { schema }
    })

    if (Array.isArray(data)) {
      sourceTableList.value = data.map((t: any) => {
        const tableName = t.tableName || t.table_name
        // Remove schema prefix if present
        if (tableName && tableName.includes('.')) {
          return tableName.split('.')[1]
        }
        return tableName
      }).filter(Boolean)
    }
  } catch (error) {
    console.error('Failed to load tables', error)
  } finally {
    loadingTables.value = false
  }
}

// When source schema changes, reset table selection
function onSourceSchemaChange() {
  tableFormState.sourceTable = undefined
  sourceTableList.value = []
}

// When source table changes, auto-fill config name and target table
function onSourceTableChange(value: string) {
  // Auto-fill config name if empty
  if (!tableFormState.tableName && value) {
    tableFormState.tableName = value
  }
  // Auto-fill target table name with "_masked" suffix
  if (!tableFormState.targetTable && value) {
    tableFormState.targetTable = `${value}_masked`
  }
}

async function handleTableModalOk() {
  try {
    // Build full table names with schema prefix
    const fullSourceTable = tableFormState.sourceSchema
      ? `${tableFormState.sourceSchema}.${tableFormState.sourceTable}`
      : tableFormState.sourceTable

    const fullTargetTable = tableFormState.targetSchema
      ? `${tableFormState.targetSchema}.${tableFormState.targetTable}`
      : tableFormState.targetTable

    // If tableName is empty, use source table name
    const tableName = tableFormState.tableName || tableFormState.sourceTable

    const payload = {
      ...tableFormState,
      tableName,
      sourceTable: fullSourceTable,
      targetTable: fullTargetTable
    }

    if (editingTable.value && editingTable.value.id) {
      await request.put(`/masking/tables/${editingTable.value.id}`, payload)
      message.success('Updated successfully')
    } else {
      await request.post(`/masking/tasks/${taskId.value}/tables`, {
        taskId: taskId.value,
        ...payload
      })
      message.success('Added successfully')
    }
    tableModalVisible.value = false
    loadTask()
  } catch (error) {
    //
  }
}

async function deleteTable(id: number) {
  try {
    await request.delete(`/masking/tables/${id}`)
    message.success('Deleted successfully')
    loadTask()
  } catch (error) {
    //
  }
}

async function manageColumns(record: any) {
  currentTable.value = record
  columns.value = record.columns || []
  columnDrawerVisible.value = true
}

function showColumnModal(record?: any) {
  if (record) {
    editingColumn.value = record
    Object.assign(columnFormState, {
      id: record.id,
      columnName: record.columnName,
      dataType: record.dataType,
      maskingAlgorithm: record.maskingAlgorithm,
      algorithmParams: record.algorithmParams || {},
      description: record.description
    })
    selectedAlgorithm.value = algorithms.value.find(a => a.code === record.maskingAlgorithm) || null
  } else {
    editingColumn.value = null
    Object.assign(columnFormState, {
      id: undefined,
      columnName: '',
      dataType: '',
      maskingAlgorithm: '',
      algorithmParams: {},
      description: ''
    })
    selectedAlgorithm.value = null
  }
  columnModalVisible.value = true
}

async function handleColumnModalOk() {
  try {
    // Clean up empty params
    const cleanParams: Record<string, any> = {}
    Object.entries(columnFormState.algorithmParams).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        cleanParams[key] = value
      }
    })

    const payload = {
      ...columnFormState,
      algorithmParams: Object.keys(cleanParams).length > 0 ? cleanParams : null
    }

    if (editingColumn.value) {
      await request.put(`/masking/columns/${columnFormState.id}`, payload)
      message.success('Updated successfully')
    } else {
      await request.post(`/masking/tables/${currentTable.value.id}/columns`, {
        tableId: currentTable.value.id,
        ...payload
      })
      message.success('Added successfully')
    }
    columnModalVisible.value = false
    // Refresh task data and update columns list
    await loadTask()
    // Update columns in drawer from refreshed data
    if (currentTable.value) {
      const updatedTable = tables.value.find(t => t.id === currentTable.value.id)
      if (updatedTable) {
        columns.value = updatedTable.columns || []
      }
    }
  } catch (error) {
    //
  }
}

async function deleteColumn(id: number) {
  try {
    await request.delete(`/masking/columns/${id}`)
    message.success('Deleted successfully')
    await loadTask()
    // Update columns in drawer from refreshed data
    if (currentTable.value) {
      const updatedTable = tables.value.find(t => t.id === currentTable.value.id)
      if (updatedTable) {
        columns.value = updatedTable.columns || []
      }
    }
  } catch (error) {
    //
  }
}

async function loadTableColumnsFromDB() {
  if (!currentTable.value || !task.value?.datasourceId) {
    message.warning('Please configure table and datasource first')
    return
  }

  try {
    loadingColumns.value = true
    dbColumns.value = []
    selectedColumnNames.value = []

    // 解析表名，支持 schema.table 格式
    let tableName = currentTable.value.sourceTable || currentTable.value.tableName
    const data = await request.get(`/datasources/${task.value.datasourceId}/tables/${tableName}/columns`)

    // 转换字段名
    dbColumns.value = (data || []).map((col: any) => ({
      columnName: col.columnName || col.column_name,
      dataType: col.dataType || col.data_type,
      isNullable: col.isNullable ?? col.is_nullable ?? true,
      columnComment: col.columnComment || col.column_comment || ''
    }))

    // 预选已有的字段
    const existingColumnNames = columns.value.map(c => c.columnName)
    selectedColumnNames.value = existingColumnNames

    selectColumnsModalVisible.value = true
  } catch (error) {
    message.error('Failed to load columns from database')
  } finally {
    loadingColumns.value = false
  }
}

async function handleSelectColumnsOk() {
  if (selectedColumnNames.value.length === 0) {
    message.warning('Please select at least one column')
    return
  }

  try {
    // 获取现有字段名
    const existingColumnNames = columns.value.map(c => c.columnName)

    // 添加新选择的字段（排除已存在的）
    const newColumns = selectedColumnNames.value.filter(name => !existingColumnNames.includes(name))

    if (newColumns.length === 0) {
      message.info('All selected columns already exist')
      selectColumnsModalVisible.value = false
      return
    }

    // 批量添加字段（使用默认脱敏算法）
    for (const colName of newColumns) {
      const colInfo = dbColumns.value.find(c => c.columnName === colName)
      try {
        await request.post(`/masking/tables/${currentTable.value.id}/columns`, {
          tableId: currentTable.value.id,
          columnName: colName,
          dataType: colInfo?.dataType || 'text',
          maskingAlgorithm: 'MASK',  // 默认使用掩码算法
          algorithmParams: { prefix_length: 2, mask_char: '*', suffix_length: 2 },
          description: colInfo?.columnComment || ''
        })
      } catch (error) {
        console.error(`Failed to add column ${colName}:`, error)
      }
    }

    message.success(`Added ${newColumns.length} columns successfully`)
    selectColumnsModalVisible.value = false
    loadTask()

    // Refresh columns in drawer
    if (currentTable.value) {
      const updatedTable = tables.value.find(t => t.id === currentTable.value.id)
      if (updatedTable) {
        columns.value = updatedTable.columns || []
      }
    }
  } catch (error) {
    message.error('Failed to add columns')
  }
}

function showQuickAddColumns() {
  loadTableColumnsFromDB()
}

async function executeTask() {
  try {
    executing.value = true
    await request.post(`/masking/tasks/${taskId.value}/execute`)
    message.success('Task submitted for execution')
    activeTab.value = 'executions'
    loadExecutions()
  } finally {
    executing.value = false
  }
}

async function generateSQL() {
  try {
    // Call backend API to generate real SQL
    const data = await request.post(`/masking/tasks/${taskId.value}/generate-sql`)
    generatedSQL.value = data.sql
    sqlModalVisible.value = true
  } catch (error: any) {
    message.error(error.response?.data?.detail || 'Failed to generate SQL')
  }
}

async function previewMasking() {
  try {
    previewing.value = true
    message.info('Preview feature will execute masking on a sample of data')
    // This would call the backend preview endpoint
    previewModalVisible.value = true
  } finally {
    previewing.value = false
  }
}

function copySQL() {
  navigator.clipboard.writeText(generatedSQL.value)
  message.success('SQL copied to clipboard')
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
  const texts: Record<string, string> = {
    SUCCESS: 'Success',
    FAILED: 'Failed',
    RUNNING: 'Running',
    PENDING: 'Pending'
  }
  return texts[status] || status
}

function formatDuration(startTime: string, endTime: string): string {
  if (!startTime || !endTime) return '-'
  const start = new Date(startTime).getTime()
  const end = new Date(endTime).getTime()
  const seconds = Math.floor((end - start) / 1000)
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
}

async function showExecutionDetail(record: any) {
  try {
    const data = await request.get(`/masking/executions/${record.id}/logs`)
    selectedExecution.value = data.execution
    executionDetailVisible.value = true
  } catch (error) {
    // If the new API fails, show basic info
    selectedExecution.value = record
    executionDetailVisible.value = true
  }
}

onMounted(() => {
  loadTask()
  loadAlgorithms()
  loadExecutions()
})
</script>

<style scoped>
.tab-content {
  padding-top: 16px;
}

.action-bar {
  margin-bottom: 16px;
}

.sql-preview {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  white-space: pre-wrap;
  max-height: 500px;
  overflow: auto;
}

.text-gray-400 {
  color: #9ca3af;
}

.text-gray-500 {
  color: #6b7280;
}

.font-bold {
  font-weight: 600;
}

.ml-2 {
  margin-left: 8px;
}

.mt-4 {
  margin-top: 16px;
}

.text-green-600 {
  color: #16a34a;
}

.text-red-600 {
  color: #dc2626;
}
</style>
