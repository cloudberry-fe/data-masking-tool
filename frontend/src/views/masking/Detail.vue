<template>
  <div class="masking-detail">
    <a-page-header
      :title="task?.taskName"
      sub-title="脱敏任务配置"
      @back="$router.back()"
    >
      <template #extra>
        <a-space>
          <a-button type="primary" @click="executeTask" :loading="executing">
            <PlayCircleOutlined />
            执行任务
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="tables" tab="表配置">
        <div class="tab-content">
          <div class="action-bar">
            <a-button type="primary" @click="showTableModal">
              <PlusOutlined />
              添加表
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
                  {{ record.enabled ? '启用' : '禁用' }}
                </a-tag>
              </template>
              <template v-if="column.key === 'actions'">
                <a-space>
                  <a-button type="link" size="small" @click="manageColumns(record)">
                    字段配置
                  </a-button>
                  <a-button type="link" size="small" @click="showTableModal(record)">
                    编辑
                  </a-button>
                  <a-popconfirm title="确定删除？" @confirm="deleteTable(record.id)">
                    <a-button type="link" size="small" danger>
                      删除
                    </a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </div>
      </a-tab-pane>

      <a-tab-pane key="executions" tab="执行历史">
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

    <!-- 表配置弹窗 -->
    <a-modal
      :title="editingTable ? '编辑表' : '添加表'"
      v-model:open="tableModalVisible"
      @ok="handleTableModalOk"
      @cancel="tableModalVisible = false"
    >
      <a-form ref="tableFormRef" :model="tableFormState" :label-col="{ span: 6 }">
        <a-form-item label="表名" name="tableName" :rules="[{ required: true }]">
          <a-input v-model:value="tableFormState.tableName" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="源表名" name="sourceTable">
          <a-input v-model:value="tableFormState.sourceTable" placeholder="默认同表名" />
        </a-form-item>
        <a-form-item label="目标表名" name="targetTable">
          <a-input v-model:value="tableFormState.targetTable" placeholder="默认表名_masked" />
        </a-form-item>
        <a-form-item label="执行顺序" name="orderNo">
          <a-input-number v-model:value="tableFormState.orderNo" style="width: 100%" />
        </a-form-item>
        <a-form-item label="启用" name="enabled">
          <a-switch v-model:checked="tableFormState.enabled" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 字段配置抽屉 -->
    <a-drawer
      title="字段配置"
      :width="720"
      v-model:open="columnDrawerVisible"
    >
      <div v-if="currentTable" class="column-config">
        <div class="action-bar">
          <a-space>
            <a-button type="primary" size="small" @click="showQuickAddColumns">
              <PlusOutlined />
              从表选择
            </a-button>
            <a-button size="small" @click="showColumnModal">
              <PlusOutlined />
              手动添加
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
                  编辑
                </a-button>
                <a-popconfirm title="确定删除？" @confirm="deleteColumn(record.id)">
                  <a-button type="link" size="small" danger>
                    删除
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>
    </a-drawer>

    <!-- 字段配置弹窗 -->
    <a-modal
      :title="editingColumn ? '编辑字段' : '添加字段'"
      v-model:open="columnModalVisible"
      @ok="handleColumnModalOk"
      @cancel="columnModalVisible = false"
      width="560px"
    >
      <a-form ref="columnFormRef" :model="columnFormState" :label-col="{ span: 6 }">
        <a-form-item label="字段名" name="columnName" :rules="[{ required: true }]">
          <a-input v-model:value="columnFormState.columnName" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="数据类型" name="dataType">
          <a-input v-model:value="columnFormState.dataType" placeholder="varchar, int等" />
        </a-form-item>
        <a-form-item label="脱敏算法" name="maskingAlgorithm" :rules="[{ required: true }]">
          <a-select v-model:value="columnFormState.maskingAlgorithm" placeholder="请选择">
            <a-select-option v-for="algo in algorithms" :key="algo.code" :value="algo.code">
              {{ algo.name }} - {{ algo.description }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="说明" name="description">
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

// 表相关
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

// 字段相关
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

// 执行历史
const executions = ref<any[]>([])

const tableColumns = [
  { title: '表名', dataIndex: 'tableName', key: 'tableName' },
  { title: '源表', dataIndex: 'sourceTable', key: 'sourceTable' },
  { title: '目标表', dataIndex: 'targetTable', key: 'targetTable' },
  { title: '顺序', dataIndex: 'orderNo', key: 'orderNo', width: 80 },
  { title: '状态', key: 'status', width: 80 },
  { title: '操作', key: 'actions', width: 200 }
]

const columnColumns = [
  { title: '字段名', dataIndex: 'columnName', key: 'columnName' },
  { title: '类型', dataIndex: 'dataType', key: 'dataType', width: 120 },
  { title: '脱敏算法', key: 'algorithm', width: 120 },
  { title: '说明', dataIndex: 'description', key: 'description' },
  { title: '操作', key: 'actions', width: 140 }
]

const executionColumns = [
  { title: '执行编号', dataIndex: 'executionNo', key: 'executionNo' },
  { title: '触发类型', dataIndex: 'triggerType', key: 'triggerType' },
  { title: '状态', key: 'status', width: 100 },
  { title: '开始时间', dataIndex: 'startTime', key: 'startTime' },
  { title: '总记录数', dataIndex: 'totalRecords', key: 'totalRecords' },
  { title: '成功', dataIndex: 'successRecords', key: 'successRecords' },
  { title: '失败', dataIndex: 'failedRecords', key: 'failedRecords' }
]

async function loadTask() {
  try {
    const data = await request.get(`/masking/tasks/${taskId.value}`)
    task.value = data
    tables.value = data.tables || []
  } catch (error) {
    message.error('加载任务失败')
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
      message.success('更新成功')
    } else {
      await request.post(`/masking/tasks/${taskId.value}/tables`, {
        taskId: taskId.value,
        ...tableFormState
      })
      message.success('添加成功')
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
    message.success('删除成功')
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
      message.success('更新成功')
    } else {
      await request.post(`/masking/tables/${currentTable.value.id}/columns`, {
        tableId: currentTable.value.id,
        ...columnFormState
      })
      message.success('添加成功')
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
    message.success('删除成功')
    loadTask()
  } catch (error) {
    //
  }
}

function showQuickAddColumns() {
  message.info('从数据源表选择字段功能待实现')
}

async function executeTask() {
  try {
    executing.value = true
    await request.post(`/masking/tasks/${taskId.value}/execute`)
    message.success('任务已提交执行')
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
    SUCCESS: '成功',
    FAILED: '失败',
    RUNNING: '执行中',
    PENDING: '等待中'
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
