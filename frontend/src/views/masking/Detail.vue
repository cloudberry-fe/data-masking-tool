<template>
  <div class="masking-detail">
    <a-page-header
      :title="task?.taskName"
      sub-title="Masking Task Configuration"
      @back="$router.back()"
    >
      <template #extra>
        <a-space>
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
                    Columns
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
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="getExecutionStatusColor(record.status)">
                  {{ getExecutionStatusText(record.status) }}
                </a-tag>
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
    >
      <a-form ref="tableFormRef" :model="tableFormState" :label-col="{ span: 6 }">
        <a-form-item label="Table Name" name="tableName" :rules="[{ required: true }]">
          <a-input v-model:value="tableFormState.tableName" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Source Table" name="sourceTable">
          <a-input v-model:value="tableFormState.sourceTable" placeholder="Same as table name" />
        </a-form-item>
        <a-form-item label="Target Table" name="targetTable">
          <a-input v-model:value="tableFormState.targetTable" placeholder="table_name_masked" />
        </a-form-item>
        <a-form-item label="Order" name="orderNo">
          <a-input-number v-model:value="tableFormState.orderNo" style="width: 100%" />
        </a-form-item>
        <a-form-item label="Enabled" name="enabled">
          <a-switch v-model:checked="tableFormState.enabled" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Column Configuration Drawer -->
    <a-drawer
      title="Column Configuration"
      :width="720"
      v-model:open="columnDrawerVisible"
    >
      <div v-if="currentTable" class="column-config">
        <div class="action-bar">
          <a-space>
            <a-button type="primary" size="small" @click="showQuickAddColumns">
              <PlusOutlined />
              Select from Table
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
              <a-tag>{{ record.maskingAlgorithm }}</a-tag>
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

    <!-- Column Configuration Modal -->
    <a-modal
      :title="editingColumn ? 'Edit Column' : 'Add Column'"
      v-model:open="columnModalVisible"
      @ok="handleColumnModalOk"
      @cancel="columnModalVisible = false"
      width="560px"
    >
      <a-form ref="columnFormRef" :model="columnFormState" :label-col="{ span: 6 }">
        <a-form-item label="Column Name" name="columnName" :rules="[{ required: true }]">
          <a-input v-model:value="columnFormState.columnName" placeholder="Please enter" />
        </a-form-item>
        <a-form-item label="Data Type" name="dataType">
          <a-input v-model:value="columnFormState.dataType" placeholder="varchar, int, etc." />
        </a-form-item>
        <a-form-item label="Masking Algorithm" name="maskingAlgorithm" :rules="[{ required: true }]">
          <a-select v-model:value="columnFormState.maskingAlgorithm" placeholder="Please select">
            <a-select-option v-for="algo in algorithms" :key="algo.code" :value="algo.code">
              {{ algo.name }} - {{ algo.description }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Description" name="description">
          <a-textarea v-model:value="columnFormState.description" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  PlayCircleOutlined
} from '@ant-design/icons-vue'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()

const taskId = computed(() => parseInt(route.params.id as string))
const task = ref<any>(null)
const activeTab = ref('tables')
const executing = ref(false)

// Table related
const tables = ref<any[]>([])
const tableModalVisible = ref(false)
const tableFormRef = ref()
const editingTable = ref<any>(null)
const tableFormState = reactive({
  id: undefined as number | undefined,
  tableName: '',
  sourceTable: '',
  targetTable: '',
  orderNo: 0,
  enabled: true
})

// Column related
const columnDrawerVisible = ref(false)
const columnModalVisible = ref(false)
const columnFormRef = ref()
const currentTable = ref<any>(null)
const columns = ref<any[]>([])
const editingColumn = ref<any>(null)
const algorithms = ref<any[]>([])
const columnFormState = reactive({
  id: undefined as number | undefined,
  columnName: '',
  dataType: '',
  maskingAlgorithm: '',
  description: ''
})

// Execution history
const executions = ref<any[]>([])

const tableColumns = [
  { title: 'Table Name', dataIndex: 'tableName', key: 'tableName' },
  { title: 'Source Table', dataIndex: 'sourceTable', key: 'sourceTable' },
  { title: 'Target Table', dataIndex: 'targetTable', key: 'targetTable' },
  { title: 'Order', dataIndex: 'orderNo', key: 'orderNo', width: 80 },
  { title: 'Status', key: 'status', width: 80 },
  { title: 'Actions', key: 'actions', width: 200 }
]

const columnColumns = [
  { title: 'Column Name', dataIndex: 'columnName', key: 'columnName' },
  { title: 'Type', dataIndex: 'dataType', key: 'dataType', width: 120 },
  { title: 'Masking Algorithm', key: 'algorithm', width: 120 },
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Actions', key: 'actions', width: 140 }
]

const executionColumns = [
  { title: 'Execution ID', dataIndex: 'executionNo', key: 'executionNo' },
  { title: 'Trigger Type', dataIndex: 'triggerType', key: 'triggerType' },
  { title: 'Status', key: 'status', width: 100 },
  { title: 'Start Time', dataIndex: 'startTime', key: 'startTime' },
  { title: 'Total Records', dataIndex: 'totalRecords', key: 'totalRecords' },
  { title: 'Success', dataIndex: 'successRecords', key: 'successRecords' },
  { title: 'Failed', dataIndex: 'failedRecords', key: 'failedRecords' }
]

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
    algorithms.value = await request.get('/masking/algorithms')
  } catch (error) {
    //
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

function showTableModal(record?: any) {
  if (record) {
    editingTable.value = record
    Object.assign(tableFormState, {
      id: record.id,
      tableName: record.tableName,
      sourceTable: record.sourceTable,
      targetTable: record.targetTable,
      orderNo: record.orderNo,
      enabled: record.enabled
    })
  } else {
    editingTable.value = null
    Object.assign(tableFormState, {
      id: undefined,
      tableName: '',
      sourceTable: '',
      targetTable: '',
      orderNo: 0,
      enabled: true
    })
  }
  tableModalVisible.value = true
}

async function handleTableModalOk() {
  try {
    if (editingTable.value) {
      await request.put(`/masking/tables/${tableFormState.id}`, tableFormState)
      message.success('Updated successfully')
    } else {
      await request.post(`/masking/tasks/${taskId.value}/tables`, {
        taskId: taskId.value,
        ...tableFormState
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
      description: record.description
    })
  } else {
    editingColumn.value = null
    Object.assign(columnFormState, {
      id: undefined,
      columnName: '',
      dataType: '',
      maskingAlgorithm: '',
      description: ''
    })
  }
  columnModalVisible.value = true
}

async function handleColumnModalOk() {
  try {
    if (editingColumn.value) {
      await request.put(`/masking/columns/${columnFormState.id}`, columnFormState)
      message.success('Updated successfully')
    } else {
      await request.post(`/masking/tables/${currentTable.value.id}/columns`, {
        tableId: currentTable.value.id,
        ...columnFormState
      })
      message.success('Added successfully')
    }
    columnModalVisible.value = false
    loadTask()
  } catch (error) {
    //
  }
}

async function deleteColumn(id: number) {
  try {
    await request.delete(`/masking/columns/${id}`)
    message.success('Deleted successfully')
    loadTask()
  } catch (error) {
    //
  }
}

function showQuickAddColumns() {
  message.info('Select columns from data source table feature coming soon')
}

async function executeTask() {
  try {
    executing.value = true
    await request.post(`/masking/tasks/${taskId.value}/execute`)
    message.success('Task submitted for execution')
    loadExecutions()
  } finally {
    executing.value = false
  }
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
</style>
