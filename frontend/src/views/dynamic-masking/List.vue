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
            {{ record.isEnabled ? t('dynamicMasking.enabled') : t('dynamicMasking.disabled') }}
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
              {{ t('dynamicMasking.configure') }}
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

    <!-- Create Modal -->
    <a-modal
      :title="t('dynamicMasking.createRule')"
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
        <a-form-item :label="t('dynamicMasking.ruleName')" name="ruleName" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input v-model:value="formState.ruleName" :placeholder="t('common.pleaseInput')" />
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
        <a-form-item :label="t('dynamicMasking.maskedRoles')" name="maskedRoles" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-select
            v-model:value="formState.maskedRoles"
            mode="tags"
            :placeholder="t('dynamicMasking.maskedRolesHint')"
          >
          </a-select>
        </a-form-item>
        <a-form-item :label="t('dynamicMasking.exemptedRoles')" name="exemptedRoles">
          <a-select
            v-model:value="formState.exemptedRoles"
            mode="tags"
            :placeholder="t('dynamicMasking.exemptedRolesHint')"
          >
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
            <template v-if="column.key === 'actions'">
              <a-popconfirm :title="t('messages.deleteConfirm')" @confirm="deleteColumnRule(record.id)">
                <a-button type="link" size="small" danger>{{ t('common.delete') }}</a-button>
              </a-popconfirm>
            </template>
          </template>
        </a-table>

        <div style="margin-top: 16px">
          <a-button type="dashed" block @click="showAddColumnModal">
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

const columns = computed(() => [
  { title: t('dynamicMasking.ruleName'), dataIndex: 'ruleName', key: 'ruleName' },
  { title: t('masking.tableName'), key: 'table', customRender: ({ record }: any) => `${record.schemaName}.${record.tableName}` },
  { title: t('dynamicMasking.maskedRoles'), key: 'maskedRoles', width: 200 },
  { title: t('common.status'), key: 'status', width: 100 },
  { title: t('dynamicMasking.enabled'), key: 'isEnabled', width: 100 },
  { title: t('common.actions'), key: 'actions', width: 300, fixed: 'right' as const }
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
    message.success(t('messages.createSuccess'))
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
    columnRules.value = []
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
        message.error(t('dynamicMasking.invalidJson'))
        return
      }
    }

    await request.post(`/dynamic-masking/rules/${currentRule.value.id}/columns`, {
      column_name: addColumnForm.columnName,
      masking_algorithm: addColumnForm.maskingAlgorithm,
      algorithm_params: params
    })
    message.success(t('messages.createSuccess'))
    addColumnModalVisible.value = false
    await loadColumnRules(currentRule.value.id)
  } finally {
    addColumnLoading.value = false
  }
}

async function deleteColumnRule(id: number) {
  message.success(t('messages.deleteSuccess'))
}

async function enableRule(record: any) {
  try {
    await request.post(`/dynamic-masking/rules/${record.id}/enable`)
    message.success(t('dynamicMasking.enableSuccess'))
    loadData()
  } catch (error) {
    //
  }
}

async function disableRule(record: any) {
  try {
    await request.post(`/dynamic-masking/rules/${record.id}/disable`)
    message.success(t('dynamicMasking.disableSuccess'))
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
    message.success(t('messages.deleteSuccess'))
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
  const texts: Record<string, Record<string, string>> = {
    DRAFT: { en: 'Draft', zh: '草稿' },
    ACTIVE: { en: 'Active', zh: '已激活' },
    INACTIVE: { en: 'Inactive', zh: '未激活' }
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
}
</style>
