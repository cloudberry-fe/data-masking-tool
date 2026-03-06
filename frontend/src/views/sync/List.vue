<template>
  <div class="test-data-list">
    <div class="page-header">
      <a-space>
        <a-input-search
          v-model:value="search.keyword"
          :placeholder="t('common.search')"
          style="width: 240px"
          @search="loadData"
          allow-clear
        />
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          {{ t('testData.createTask') }}
        </a-button>
      </a-space>
    </div>

    <a-table
      :columns="columns"
      :data-source="taskList"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'dataRatio'">
          {{ (record.dataRatio * 100).toFixed(0) }}%
        </template>
        <template v-if="column.key === 'sourceDatasource'">
          {{ getDatasourceName(record.sourceDatasourceId) }}
        </template>
        <template v-if="column.key === 'targetDatasource'">
          {{ getDatasourceName(record.targetDatasourceId) }}
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button size="small" @click="showConfigModal(record)">
              {{ t('testData.config') }}
            </a-button>
            <a-button type="primary" size="small" @click="analyzeTask(record)">
              {{ t('testData.analyze') }}
            </a-button>
            <a-popconfirm :title="t('messages.executeConfirm')" @confirm="executeTask(record)">
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
      :title="isEdit ? t('testData.editTask') : t('testData.createTask')"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      width="700px"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item :label="t('testData.taskName')" name="taskName" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input v-model:value="formState.taskName" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
        <a-form-item :label="t('testData.sourceDatasource')" name="sourceDatasourceId" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select v-model:value="formState.sourceDatasourceId" :placeholder="t('common.pleaseSelect')" show-search @change="onSourceDatasourceChange">
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('testData.targetDatasource')" name="targetDatasourceId" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select v-model:value="formState.targetDatasourceId" :placeholder="t('common.pleaseSelect')" show-search>
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('testData.dataRatio')" name="dataRatio">
          <a-slider v-model:value="formState.dataRatioSlider" :min="1" :max="100" :marks="{ 10: '10%', 50: '50%', 100: '100%' }" />
        </a-form-item>
        <a-form-item :label="t('testData.keepRelations')" name="keepRelations">
          <a-switch v-model:checked="formState.keepRelations" />
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
      </a-form>
    </a-modal>

    <!-- Table Config Modal -->
    <a-modal
      :title="t('testData.tableConfig')"
      v-model:open="configModalVisible"
      width="1000px"
      :footer="null"
    >
      <a-alert
        :message="t('testData.configHint')"
        type="info"
        show-icon
        style="margin-bottom: 16px"
      />

      <a-tabs v-model:activeKey="configActiveTab">
        <a-tab-pane key="tables" :tab="t('testData.tableList')">
          <div style="margin-bottom: 16px">
            <a-space wrap>
              <a-select
                v-model:value="selectedSchema"
                :placeholder="t('common.pleaseSelect') + ' Schema'"
                style="width: 150px"
                show-search
                allow-clear
                :loading="loadingSchemas"
                :disabled="!currentTask?.sourceDatasourceId"
                @change="onSchemaChange"
              >
                <a-select-option v-for="schema in schemaList" :key="schema" :value="schema">
                  {{ schema }}
                </a-select-option>
              </a-select>
              <a-select
                v-model:value="addTableForm.sourceTable"
                :placeholder="t('testData.selectSourceTable')"
                style="width: 200px"
                show-search
                :loading="loadingTables"
                :disabled="!currentTask?.sourceDatasourceId || !selectedSchema"
                @focus="loadSourceTablesIfNeeded"
                @change="onSourceTableChange"
              >
                <a-select-option v-for="table in sourceTableList" :key="table" :value="table">
                  {{ table }}
                </a-select-option>
              </a-select>
              <a-select
                v-model:value="addTableForm.targetSchema"
                :placeholder="'目标 Schema'"
                style="width: 150px"
                show-search
                allow-clear
                :loading="loadingTargetSchemas"
                :disabled="!currentTask?.targetDatasourceId"
                @focus="loadTargetSchemasIfNeeded"
              >
                <a-select-option v-for="schema in targetSchemaList" :key="schema" :value="schema">
                  {{ schema }}
                </a-select-option>
              </a-select>
              <a-input
                v-model:value="addTableForm.targetTable"
                :placeholder="t('testData.targetTablePlaceholder')"
                style="width: 180px"
              />
              <a-input-number
                v-model:value="addTableForm.rowCount"
                :min="1"
                :max="1000000"
                :placeholder="t('testData.rowCount')"
                style="width: 100px"
              />
              <a-button type="primary" @click="addTableToConfig" :disabled="!addTableForm.sourceTable">
                {{ t('testData.addTable') }}
              </a-button>
            </a-space>
          </div>

          <a-table
            :columns="tableColumns"
            :data-source="tableConfigs"
            size="small"
            row-key="sourceTable"
            :pagination="false"
          >
            <template #bodyCell="{ column, record, index }">
              <template v-if="column.key === 'rowCount'">
                <a-input-number v-model:value="record.rowCount" :min="1" :max="1000000" style="width: 100px" />
              </template>
              <template v-if="column.key === 'columns'">
                <a-tag v-if="record.columns?.length">{{ record.columns.length }} {{ t('testData.columns') }}</a-tag>
                <span v-else style="color: #999">-</span>
              </template>
              <template v-if="column.key === 'actions'">
                <a-space>
                  <a-button type="link" size="small" @click="showColumnConfig(index)">
                    {{ t('testData.columnConfig') }}
                  </a-button>
                  <a-button type="link" size="small" danger @click="removeTable(index)">
                    {{ t('common.delete') }}
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
        <a-tab-pane key="preview" :tab="t('masking.preview')">
          <a-button @click="previewData" :loading="previewLoading" style="margin-bottom: 16px">
            {{ t('testData.generatePreview') }}
          </a-button>
          <a-spin :spinning="previewLoading">
            <div v-if="previewDataResult">
              <div v-for="(tableData, tableName) in previewDataResult" :key="tableName">
                <h4>{{ tableName }}</h4>
                <a-table
                  :columns="getTableColumns(tableData)"
                  :data-source="tableData.rows"
                  size="small"
                  :pagination="false"
                  :scroll="{ x: 'max-content' }"
                />
              </div>
            </div>
            <a-empty v-else :description="t('testData.clickToPreview')" />
          </a-spin>
        </a-tab-pane>
      </a-tabs>
      <div style="margin-top: 16px; text-align: right">
        <a-space>
          <a-button @click="configModalVisible = false">{{ t('common.cancel') }}</a-button>
          <a-button type="primary" @click="saveTableConfig" :loading="saveConfigLoading">{{ t('common.save') }}</a-button>
        </a-space>
      </div>
    </a-modal>

    <!-- Column Config Drawer -->
    <a-drawer
      :title="t('testData.columnConfig') + ': ' + (tableConfigs[currentTableIndex]?.sourceTable || '')"
      :open="columnDrawerVisible"
      :width="700"
      @close="columnDrawerVisible = false"
    >
      <a-button type="primary" @click="loadTableColumns" :loading="loadingColumns" style="margin-bottom: 16px">
        {{ t('testData.loadColumns') }}
      </a-button>

      <a-table
        :columns="columnConfigColumns"
        :data-source="currentTableColumns"
        size="small"
        row-key="name"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'generator'">
            <a-select v-model:value="record.generator" style="width: 160px">
              <a-select-option v-for="(label, key) in generatorTypes" :key="key" :value="key">
                {{ label }}
              </a-select-option>
            </a-select>
          </template>
        </template>
      </a-table>
      <template #footer>
        <a-space>
          <a-button @click="columnDrawerVisible = false">{{ t('common.cancel') }}</a-button>
          <a-button type="primary" @click="saveColumnConfig">{{ t('common.save') }}</a-button>
        </a-space>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const { t, locale } = useI18n()

const loading = ref(false)
const modalVisible = ref(false)
const modalLoading = ref(false)
const isEdit = ref(false)
const formRef = ref()

const taskList = ref<any[]>([])
const datasourceList = ref<any[]>([])
const search = reactive({
  keyword: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const formState = reactive({
  id: undefined as number | undefined,
  taskName: '',
  sourceDatasourceId: undefined as number | undefined,
  targetDatasourceId: undefined as number | undefined,
  dataRatioSlider: 100,
  keepRelations: true,
  scheduleType: 'MANUAL',
  cronExpression: ''
})

const configModalVisible = ref(false)
const configActiveTab = ref('tables')
const saveConfigLoading = ref(false)
const currentTask = ref<any>(null)
const tableConfigs = ref<any[]>([])
const generatorTypes = ref<Record<string, string>>({})

// 表选择相关
const sourceTableList = ref<string[]>([])
const loadingTables = ref(false)
const schemaList = ref<string[]>([])
const loadingSchemas = ref(false)
const selectedSchema = ref('public')
const targetSchemaList = ref<string[]>([])
const loadingTargetSchemas = ref(false)
const addTableForm = reactive({
  sourceTable: '',
  targetSchema: '',
  targetTable: '',
  rowCount: 100
})

const columnDrawerVisible = ref(false)
const currentTableIndex = ref(0)
const currentTableColumns = ref<any[]>([])
const loadingColumns = ref(false)
const previewLoading = ref(false)
const previewDataResult = ref<any>(null)

const columns = computed(() => [
  { title: t('testData.taskName'), dataIndex: 'taskName', key: 'taskName' },
  { title: t('testData.sourceDatasource'), key: 'sourceDatasource', width: 150 },
  { title: t('testData.targetDatasource'), key: 'targetDatasource', width: 150 },
  { title: t('testData.dataRatio'), key: 'dataRatio', width: 80 },
  { title: t('common.status'), key: 'status', width: 100 },
  { title: t('common.createdAt'), dataIndex: 'createdAt', key: 'createdAt', width: 160 },
  { title: t('common.actions'), key: 'actions', width: 300, fixed: 'right' as const }
])

const tableColumns = computed(() => [
  { title: t('testData.sourceTable'), dataIndex: 'sourceTable', key: 'sourceTable', width: 180 },
  { title: '目标 Schema', dataIndex: 'targetSchema', key: 'targetSchema', width: 120 },
  { title: t('testData.targetTable'), dataIndex: 'targetTable', key: 'targetTable', width: 180 },
  { title: t('testData.rowCount'), key: 'rowCount', width: 100 },
  { title: t('testData.columns'), key: 'columns', width: 100 },
  { title: t('common.actions'), key: 'actions', width: 150 }
])

const columnConfigColumns = computed(() => [
  { title: t('testData.columnName'), dataIndex: 'name', key: 'name', width: 150 },
  { title: t('testData.dataType'), dataIndex: 'dataType', key: 'dataType', width: 100 },
  { title: t('testData.generator'), key: 'generator', width: 180 }
])

function getDatasourceName(id: number): string {
  const ds = datasourceList.value.find(d => d.id === id)
  return ds?.datasourceName || '-'
}

function getTableColumns(tableData: any) {
  if (!tableData?.columns) return []
  return tableData.columns.map((c: string) => ({ title: c, dataIndex: c, key: c }))
}

async function loadDatasources() {
  try {
    const data = await request.get('/datasources', { params: { page: 1, pageSize: 100 } })
    datasourceList.value = data.items || []
  } catch (error) {
    console.error('加载数据源失败', error)
  }
}

async function loadGeneratorTypes() {
  try {
    const data = await request.get('/test-data/generators')
    generatorTypes.value = data || {}
  } catch (error) {
    generatorTypes.value = {
      'fake_name': '姓名',
      'fake_email': '邮箱',
      'fake_phone': '电话',
      'fake_address': '地址',
      'fake_company': '公司',
      'random_string': '随机字符串',
      'random_int': '随机整数',
      'random_float': '随机浮点数',
      'sequence': '序列',
      'uuid': 'UUID'
    }
  }
}

async function loadData() {
  loading.value = true
  try {
    const data = await request.get('/test-data/tasks', {
      params: {
        page: pagination.current,
        pageSize: pagination.pageSize,
        keyword: search.keyword
      }
    })
    taskList.value = data.items || []
    pagination.total = data.total || 0
  } catch (error) {
    console.error('加载任务列表失败', error)
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
    sourceDatasourceId: undefined,
    targetDatasourceId: undefined,
    dataRatioSlider: 100,
    keepRelations: true,
    scheduleType: 'MANUAL',
    cronExpression: ''
  })
  modalVisible.value = true
}

function showEditModal(record: any) {
  isEdit.value = true
  Object.assign(formState, {
    id: record.id,
    taskName: record.taskName,
    sourceDatasourceId: record.sourceDatasourceId,
    targetDatasourceId: record.targetDatasourceId,
    dataRatioSlider: Math.round((record.dataRatio || 1) * 100),
    keepRelations: record.keepRelations,
    scheduleType: record.scheduleType || 'MANUAL',
    cronExpression: record.cronExpression
  })
  modalVisible.value = true
}

async function handleModalOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    const submitData: any = {
      taskName: formState.taskName,
      sourceDatasourceId: formState.sourceDatasourceId,
      targetDatasourceId: formState.targetDatasourceId,
      dataRatio: formState.dataRatioSlider / 100,
      keepRelations: formState.keepRelations,
      scheduleType: formState.scheduleType,
      cronExpression: formState.cronExpression
    }

    if (isEdit.value) {
      await request.put(`/test-data/tasks/${formState.id}`, submitData)
      message.success(t('messages.updateSuccess'))
    } else {
      await request.post('/test-data/tasks', submitData)
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

function onSourceDatasourceChange() {
  // 清空表列表和 schema
  sourceTableList.value = []
  schemaList.value = []
  selectedSchema.value = 'public'
  addTableForm.sourceTable = ''
  loadSchemas()
}

async function loadSchemas() {
  const dsId = currentTask.value?.sourceDatasourceId || formState.sourceDatasourceId
  if (!dsId) return

  loadingSchemas.value = true
  try {
    const data = await request.get(`/datasources/${dsId}/schemas`)
    schemaList.value = data || ['public']
    // 如果只有一个 schema，自动选中
    if (schemaList.value.length === 1 && !selectedSchema.value) {
      selectedSchema.value = schemaList.value[0]
    }
  } catch (error) {
    console.error('加载Schema列表失败', error)
    schemaList.value = ['public']
  } finally {
    loadingSchemas.value = false
  }
}

function onSchemaChange(schema: string) {
  addTableForm.sourceTable = ''
  sourceTableList.value = []
  if (schema) {
    loadSourceTables()
  }
}

function loadSourceTablesIfNeeded() {
  if (sourceTableList.value.length === 0 && selectedSchema.value) {
    loadSourceTables()
  }
}

async function loadSourceTables() {
  if (!currentTask.value?.sourceDatasourceId && !formState.sourceDatasourceId) {
    return
  }

  if (!selectedSchema.value) {
    return
  }

  const dsId = currentTask.value?.sourceDatasourceId || formState.sourceDatasourceId
  loadingTables.value = true

  try {
    const data = await request.get(`/datasources/${dsId}/tables`, {
      params: { schema: selectedSchema.value }
    })
    // API 返回 { code: 0, data: [...] }，request 已解包到 data
    sourceTableList.value = (data || []).map((t: any) => t.tableName || t.table_name || t)
  } catch (error) {
    message.error(t('testData.loadTablesFailed'))
    sourceTableList.value = []
  } finally {
    loadingTables.value = false
  }
}

function loadTargetSchemasIfNeeded() {
  if (targetSchemaList.value.length === 0 && currentTask.value?.targetDatasourceId) {
    loadTargetSchemas()
  }
}

async function loadTargetSchemas() {
  if (!currentTask.value?.targetDatasourceId) return
  if (targetSchemaList.value.length > 0) return

  loadingTargetSchemas.value = true
  try {
    const data = await request.get(`/datasources/${currentTask.value.targetDatasourceId}/schemas`)
    targetSchemaList.value = data || ['public']
    // 默认选中 public
    if (targetSchemaList.value.includes('public') && !addTableForm.targetSchema) {
      addTableForm.targetSchema = 'public'
    }
  } catch (error) {
    console.error('加载目标Schema列表失败', error)
    targetSchemaList.value = ['public']
  } finally {
    loadingTargetSchemas.value = false
  }
}

function onSourceTableChange(tableName: string) {
  // 自动生成目标表名：源表名_flipping
  if (tableName) {
    addTableForm.targetTable = `${tableName}_flipping`
  }
}

async function showConfigModal(record: any) {
  currentTask.value = record
  selectedSchema.value = 'public'
  sourceTableList.value = []
  schemaList.value = []
  targetSchemaList.value = []

  // 重置表单
  addTableForm.sourceTable = ''
  addTableForm.targetSchema = ''
  addTableForm.targetTable = ''
  addTableForm.rowCount = 100

  // 获取任务详情
  try {
    const detail = await request.get(`/test-data/tasks/${record.id}`)
    currentTask.value = detail
    tableConfigs.value = detail.tableConfigs?.tables || []
  } catch (error) {
    tableConfigs.value = []
  }

  previewDataResult.value = null
  configModalVisible.value = true
  configActiveTab.value = 'tables'

  // 加载源 schema 列表
  if (record.sourceDatasourceId) {
    await loadSchemas()
    if (selectedSchema.value) {
      loadSourceTables()
    }
  }
}

function addTableToConfig() {
  if (!addTableForm.sourceTable) {
    message.warning(t('testData.selectSourceTableFirst'))
    return
  }

  // 构建完整的源表名（包含 schema）
  const fullSourceTable = selectedSchema.value
    ? `${selectedSchema.value}.${addTableForm.sourceTable}`
    : addTableForm.sourceTable

  // 检查是否已存在
  if (tableConfigs.value.some(t => t.sourceTable === fullSourceTable)) {
    message.warning(t('testData.tableAlreadyExists'))
    return
  }

  // 默认目标表名：源表名_flipping
  const defaultTargetTable = `${addTableForm.sourceTable}_flipping`

  tableConfigs.value.push({
    sourceTable: fullSourceTable,
    sourceSchema: selectedSchema.value,
    targetSchema: addTableForm.targetSchema || 'public',
    targetTable: addTableForm.targetTable || defaultTargetTable,
    rowCount: addTableForm.rowCount || 100,
    columns: []
  })

  // 重置表单（保留 targetSchema）
  addTableForm.sourceTable = ''
  addTableForm.targetTable = ''
  addTableForm.rowCount = 100
}

function removeTable(index: number) {
  tableConfigs.value.splice(index, 1)
}

async function showColumnConfig(index: number) {
  currentTableIndex.value = index
  currentTableColumns.value = tableConfigs.value[index]?.columns || []
  columnDrawerVisible.value = true
}

async function loadTableColumns() {
  const table = tableConfigs.value[currentTableIndex.value]
  if (!table?.sourceTable || !currentTask.value?.sourceDatasourceId) {
    message.warning(t('testData.selectSourceTableFirst'))
    return
  }

  loadingColumns.value = true
  try {
    // 解析 schema 和表名
    let schema = table.schema
    let tableName = table.sourceTable

    if (tableName.includes('.')) {
      const parts = tableName.split('.')
      schema = parts[0]
      tableName = parts[1]
    }

    const cols = await request.get(`/datasources/${currentTask.value.sourceDatasourceId}/tables/${tableName}/columns`, {
      params: { schema }
    })
    currentTableColumns.value = (cols || []).map((c: any) => ({
      name: c.columnName || c.name,
      dataType: c.dataType || c.type,
      generator: 'random_string'
    }))
  } catch (error) {
    message.error(t('testData.loadColumnsFailed'))
  } finally {
    loadingColumns.value = false
  }
}

function saveColumnConfig() {
  if (tableConfigs.value[currentTableIndex.value]) {
    tableConfigs.value[currentTableIndex.value].columns = [...currentTableColumns.value]
  }
  columnDrawerVisible.value = false
  message.success(t('messages.saveSuccess'))
}

async function saveTableConfig() {
  if (!currentTask.value?.id) return

  saveConfigLoading.value = true
  try {
    await request.put(`/test-data/tasks/${currentTask.value.id}`, {
      tableConfigs: {
        tables: tableConfigs.value,
        relations: []
      },
      status: 'READY'
    })
    message.success(t('messages.saveSuccess') + '，任务已就绪')
    configModalVisible.value = false
    loadData()
  } catch (error) {
    message.error(t('messages.saveFailed'))
  } finally {
    saveConfigLoading.value = false
  }
}

async function analyzeTask(record: any) {
  try {
    message.loading(t('testData.analyzing'), 0)
    const result = await request.post(`/test-data/tasks/${record.id}/analyze`)
    message.destroy()

    if (result && result.length > 0) {
      message.success(t('testData.analyzeSuccess'))
      // 更新任务详情
      const detail = await request.get(`/test-data/tasks/${record.id}`)
      if (detail?.tableConfigs?.tables) {
        tableConfigs.value = detail.tableConfigs.tables
      }
      loadData()
    }
  } catch (error: any) {
    message.destroy()
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || t('testData.analyzeFailed')
    message.error(errorMsg, 5)
  }
}

async function previewData() {
  if (!currentTask.value?.id) return

  previewLoading.value = true
  try {
    const result = await request.get(`/test-data/tasks/${currentTask.value.id}/preview`, {
      params: { rows: 10 }
    })
    previewDataResult.value = result
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || t('testData.previewFailed')
    message.error(errorMsg)
  } finally {
    previewLoading.value = false
  }
}

async function executeTask(record: any) {
  try {
    await request.post(`/test-data/tasks/${record.id}/execute`)
    message.success(t('messages.executeSuccess'))
    loadData()
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '执行失败'
    message.error(errorMsg, 5)
  }
}

async function deleteTask(id: number) {
  try {
    await request.delete(`/test-data/tasks/${id}`)
    message.success(t('messages.deleteSuccess'))
    loadData()
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '删除失败'
    message.error(errorMsg)
  }
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    DRAFT: 'default',
    READY: 'blue',
    RUNNING: 'processing',
    SUCCESS: 'success',
    FAILED: 'error'
  }
  return colors[status] || 'default'
}

function getStatusText(status: string): string {
  const texts: Record<string, Record<string, string>> = {
    DRAFT: { en: 'Draft', zh: '草稿' },
    READY: { en: 'Ready', zh: '就绪' },
    RUNNING: { en: 'Running', zh: '运行中' },
    SUCCESS: { en: 'Success', zh: '成功' },
    FAILED: { en: 'Failed', zh: '失败' }
  }
  return texts[status]?.[locale.value] || status
}

onMounted(() => {
  loadDatasources()
  loadGeneratorTypes()
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
