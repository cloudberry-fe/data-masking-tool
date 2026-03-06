<template>
  <div class="dynamic-masking-list">
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
          <a-select-option value="ACTIVE">{{ t('dynamicMasking.active') }}</a-select-option>
          <a-select-option value="INACTIVE">{{ t('dynamicMasking.inactive') }}</a-select-option>
          <a-select-option value="ERROR">错误</a-select-option>
        </a-select>
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          {{ t('dynamicMasking.createRule') }}
        </a-button>
      </a-space>
    </div>

    <a-alert
      :message="t('dynamicMasking.title')"
      :description="t('dynamicMasking.warning')"
      type="info"
      show-icon
      style="margin-bottom: 16px"
    />

    <a-table
      :columns="columns"
      :data-source="ruleList"
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
        <template v-if="column.key === 'isEnabled'">
          <a-tag :color="record.isEnabled ? 'success' : 'default'">
            {{ record.isEnabled ? t('dynamicMasking.enabled') : t('dynamicMasking.disabled') }}
          </a-tag>
        </template>
        <template v-if="column.key === 'maskedRoles'">
          <a-tag v-for="role in record.maskedRoles" :key="role" color="orange" style="margin: 2px">
            {{ role }}
          </a-tag>
        </template>
        <template v-if="column.key === 'errorMessage'">
          <a-tooltip v-if="record.errorMessage" :title="record.errorMessage">
            <span style="color: #ff4d4f; cursor: pointer">{{ record.errorMessage.substring(0, 30) }}...</span>
          </a-tooltip>
          <span v-else>-</span>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="showDetailModal(record)">
              {{ t('dynamicMasking.configure') }}
            </a-button>
            <a-button type="link" size="small" @click="showEditModal(record)" v-if="!record.isEnabled">
              {{ t('common.edit') }}
            </a-button>
            <a-popconfirm
              v-if="!record.isEnabled"
              :title="t('dynamicMasking.enableConfirm')"
              @confirm="enableRule(record)"
            >
              <a-button type="primary" size="small">
                {{ t('dynamicMasking.enableRule') }}
              </a-button>
            </a-popconfirm>
            <a-popconfirm
              v-else
              :title="t('dynamicMasking.disableConfirm')"
              @confirm="disableRule(record)"
            >
              <a-button size="small">
                {{ t('dynamicMasking.disableRule') }}
              </a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="showPreviewSql(record)">
              {{ t('dynamicMasking.previewSQL') }}
            </a-button>
            <a-popconfirm
              v-if="!record.isEnabled"
              :title="t('messages.deleteConfirm')"
              @confirm="deleteRule(record.id)"
            >
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
      :title="isEdit ? t('common.edit') : t('dynamicMasking.createRule')"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      width="600px"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item :label="t('dynamicMasking.ruleName')" name="ruleName" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input v-model:value="formState.ruleName" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
        <a-form-item :label="t('datasource.title')" name="datasourceId" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select v-model:value="formState.datasourceId" :placeholder="t('common.pleaseSelect')" show-search :disabled="isEdit" @change="onFormDatasourceChange">
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
            :disabled="isEdit || !formState.datasourceId"
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
            :disabled="isEdit || !formState.datasourceId"
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
        <a-form-item :label="t('dynamicMasking.maskedRoles')" name="maskedRoles" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select
            v-model:value="formState.maskedRoles"
            mode="multiple"
            :placeholder="t('dynamicMasking.maskedRolesHint')"
            :loading="loadingRoles"
            :disabled="!formState.datasourceId"
            show-search
            allow-clear
            :filter-option="filterOption"
            @focus="loadRolesForForm"
          >
            <a-select-option v-for="role in roleList" :key="role" :value="role">
              {{ role }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('dynamicMasking.exemptedRoles')" name="exemptedRoles">
          <a-select
            v-model:value="formState.exemptedRoles"
            mode="multiple"
            :placeholder="t('dynamicMasking.exemptedRolesHint')"
            :loading="loadingRoles"
            :disabled="!formState.datasourceId"
            show-search
            allow-clear
            :filter-option="filterOption"
            @focus="loadRolesForForm"
          >
            <a-select-option v-for="role in roleList" :key="role" :value="role">
              {{ role }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('common.description')" name="description">
          <a-textarea v-model:value="formState.description" :rows="2" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Detail/Column Config Modal -->
    <a-modal
      :title="`${t('dynamicMasking.configure')}: ${currentRule?.ruleName || ''}`"
      v-model:open="detailModalVisible"
      width="800px"
      :footer="null"
    >
      <div v-if="currentRule">
        <!-- 错误信息显示 -->
        <a-alert
          v-if="currentRule.errorMessage"
          :message="'执行错误'"
          :description="currentRule.errorMessage"
          type="error"
          show-icon
          style="margin-bottom: 16px"
        />

        <a-descriptions :column="2" bordered size="small" style="margin-bottom: 16px">
          <a-descriptions-item label="Table">{{ currentRule.schemaName }}.{{ currentRule.tableName }}</a-descriptions-item>
          <a-descriptions-item :label="t('common.status')">
            <a-tag :color="getStatusColor(currentRule.status)">{{ getStatusText(currentRule.status) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item :label="t('dynamicMasking.maskedRoles')">
            <a-tag v-for="role in currentRule.maskedRoles" :key="role" color="orange">{{ role }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item :label="t('dynamicMasking.exemptedRoles')">
            <a-tag v-for="role in currentRule.exemptedRoles" :key="role" color="green">{{ role }}</a-tag>
          </a-descriptions-item>
        </a-descriptions>

        <a-divider>{{ t('masking.columnConfig') }}</a-divider>

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

        <div style="margin-top: 16px">
          <a-button type="dashed" block @click="showAddColumnModal" :disabled="currentRule.isEnabled">
            <PlusOutlined /> {{ t('masking.addColumn') }}
          </a-button>
        </div>
      </div>
    </a-modal>

    <!-- Add Column Rule Modal -->
    <a-modal
      :title="t('dynamicMasking.addColumnRule')"
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
        :message="t('dynamicMasking.previewSQLWarning')"
        type="warning"
        show-icon
        style="margin-bottom: 16px"
      />
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
const isEdit = ref(false)
const detailModalVisible = ref(false)
const addColumnModalVisible = ref(false)
const addColumnLoading = ref(false)
const previewSqlModalVisible = ref(false)
const columnLoading = ref(false)
const formRef = ref()
const addColumnFormRef = ref()

const ruleList = ref<any[]>([])
const datasourceList = ref<any[]>([])
const algorithms = ref<any[]>([])
const currentRule = ref<any>(null)
const columnRules = ref<any[]>([])
const previewSql = ref('')

// Schema, Table, Column 选择相关
const schemaList = ref<string[]>([])
const tableList = ref<any[]>([])
const columnList = ref<any[]>([])
const roleList = ref<string[]>([])
const loadingSchemas = ref(false)
const loadingTables = ref(false)
const loadingColumns = ref(false)
const loadingRoles = ref(false)

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
  dataType: '',
  maskingAlgorithm: '',
  algorithmParamsStr: ''
})

const columns = computed(() => [
  { title: t('dynamicMasking.ruleName'), dataIndex: 'ruleName', key: 'ruleName' },
  { title: t('datasource.title'), key: 'datasource', width: 120 },
  { title: t('masking.tableName'), key: 'table', width: 180 },
  { title: t('dynamicMasking.maskedRoles'), key: 'maskedRoles', width: 180 },
  { title: t('common.status'), key: 'status', width: 100 },
  { title: t('dynamicMasking.enabled'), key: 'isEnabled', width: 80 },
  { title: '错误信息', key: 'errorMessage', width: 120 },
  { title: t('common.actions'), key: 'actions', width: 350, fixed: 'right' as const }
])

const columnColumns = computed(() => [
  { title: t('masking.columnName'), dataIndex: 'columnName', key: 'columnName', width: 150 },
  { title: t('masking.algorithm'), dataIndex: 'maskingAlgorithm', key: 'maskingAlgorithm', width: 200 },
  { title: t('masking.algorithmParams'), key: 'algorithmParams', width: 150 },
  { title: t('common.actions'), key: 'actions', width: 100 }
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
    const data = await request.get('/dynamic-masking/rules', {
      params: {
        page: pagination.current,
        page_size: pagination.pageSize,
        datasource_id: search.datasourceId,
        status: search.status
      }
    })
    ruleList.value = data.items || []
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
    ruleName: '',
    datasourceId: undefined,
    schemaName: 'public',
    tableName: '',
    maskedRoles: [],
    exemptedRoles: [],
    description: ''
  })
  schemaList.value = []
  tableList.value = []
  roleList.value = []
  modalVisible.value = true
}

function showEditModal(record: any) {
  isEdit.value = true
  Object.assign(formState, {
    id: record.id,
    ruleName: record.ruleName,
    datasourceId: record.datasourceId,
    schemaName: record.schemaName || 'public',
    tableName: record.tableName,
    maskedRoles: record.maskedRoles || [],
    exemptedRoles: record.exemptedRoles || [],
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
  formState.maskedRoles = []
  formState.exemptedRoles = []
  schemaList.value = []
  tableList.value = []
  roleList.value = []
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

function filterOption(input: string, option: any) {
  const text = option.value || ''
  return text.toLowerCase().includes(input.toLowerCase())
}

async function loadRolesForForm() {
  if (!formState.datasourceId) return
  if (roleList.value.length > 0) return

  loadingRoles.value = true
  try {
    const data = await request.get(`/datasources/${formState.datasourceId}/roles`)
    roleList.value = data || []
  } catch (error) {
    console.error('加载角色列表失败', error)
    roleList.value = []
  } finally {
    loadingRoles.value = false
  }
}

async function handleModalOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    if (isEdit.value) {
      await request.put(`/dynamic-masking/rules/${formState.id}`, formState)
      message.success(t('messages.updateSuccess'))
    } else {
      await request.post('/dynamic-masking/rules', formState)
      message.success(t('messages.createSuccess'))
    }

    modalVisible.value = false
    loadData()
  } finally {
    modalLoading.value = false
  }
}

async function showDetailModal(record: any) {
  currentRule.value = record
  columnList.value = []
  detailModalVisible.value = true

  // 获取详情
  try {
    const data = await request.get(`/dynamic-masking/rules/${record.id}`)
    currentRule.value = data
    columnRules.value = data.columnRules || []
  } catch (error) {
    columnRules.value = []
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
  if (!currentRule.value?.datasourceId || !currentRule.value?.tableName) {
    message.warning(t('common.pleaseSelect'))
    return
  }
  if (columnList.value.length > 0) return

  loadingColumns.value = true
  try {
    const tableName = currentRule.value.schemaName
      ? `${currentRule.value.schemaName}.${currentRule.value.tableName}`
      : currentRule.value.tableName

    const data = await request.get(`/datasources/${currentRule.value.datasourceId}/tables/${tableName}/columns`, {
      params: { schema: currentRule.value.schemaName }
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

    await request.post(`/dynamic-masking/rules/${currentRule.value.id}/columns`, {
      columnName: addColumnForm.columnName,
      dataType: addColumnForm.dataType,
      maskingAlgorithm: addColumnForm.maskingAlgorithm,
      algorithmParams: params
    })
    message.success(t('messages.createSuccess'))
    addColumnModalVisible.value = false

    // 重新加载详情
    const data = await request.get(`/dynamic-masking/rules/${currentRule.value.id}`)
    currentRule.value = data
    columnRules.value = data.columnRules || []
  } finally {
    addColumnLoading.value = false
  }
}

async function deleteColumnRule(id: number) {
  try {
    await request.delete(`/dynamic-masking/rules/${currentRule.value.id}/columns/${id}`)
    message.success(t('messages.deleteSuccess'))

    // 重新加载详情
    const data = await request.get(`/dynamic-masking/rules/${currentRule.value.id}`)
    currentRule.value = data
    columnRules.value = data.columnRules || []
  } catch (error) {
    //
  }
}

async function enableRule(record: any) {
  try {
    const result = await request.post(`/dynamic-masking/rules/${record.id}/enable`)
    if (result.code === 500 || result.code === '500') {
      message.error(result.message || '启用失败')
      if (result.data?.hint) {
        message.warning(result.data.hint)
      }
    } else {
      message.success(t('dynamicMasking.enableSuccess'))
    }
    loadData()
  } catch (error: any) {
    // 处理 FastAPI HTTPException 返回的 detail 字段
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '启用失败'
    message.error(errorMsg, 5)  // 显示5秒让用户有时间阅读
  }
}

async function disableRule(record: any) {
  try {
    const result = await request.post(`/dynamic-masking/rules/${record.id}/disable`)
    if (result.code === 500 || result.code === '500') {
      message.error(result.message || '禁用失败')
    } else {
      message.success(t('dynamicMasking.disableSuccess'))
    }
    loadData()
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '禁用失败'
    message.error(errorMsg, 5)
  }
}

async function showPreviewSql(record: any) {
  try {
    const data = await request.get(`/dynamic-masking/rules/${record.id}/preview-sql`)
    previewSql.value = data.sql
    previewSqlModalVisible.value = true
  } catch (error: any) {
    const errorMsg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '获取SQL预览失败'
    message.error(errorMsg)
  }
}

async function deleteRule(id: number) {
  try {
    await request.delete(`/dynamic-masking/rules/${id}`)
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
    ACTIVE: 'success',
    INACTIVE: 'warning',
    ERROR: 'error'
  }
  return colors[status] || 'default'
}

function getStatusText(status: string): string {
  const texts: Record<string, Record<string, string>> = {
    DRAFT: { en: 'Draft', zh: '草稿' },
    ACTIVE: { en: 'Active', zh: '已激活' },
    INACTIVE: { en: 'Inactive', zh: '未激活' },
    ERROR: { en: 'Error', zh: '错误' }
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
</style>
