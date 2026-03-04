<template>
  <div class="sync-list">
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
          {{ t('sync.createTask') }}
        </a-button>
      </a-space>
    </div>

    <a-table
      :columns="columns"
      :data-source="dataSource"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'syncMode'">
          {{ record.syncMode === 'FULL' ? t('sync.fullSync') : t('sync.incrementalSync') }}
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
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
      :title="isEdit ? t('sync.editTask') : t('sync.createTask')"
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
        <a-form-item :label="t('sync.taskName')" name="taskName" :rules="[{ required: true, message: t('common.pleaseInput') }]">
          <a-input v-model:value="formState.taskName" :placeholder="t('common.pleaseInput')" />
        </a-form-item>
        <a-form-item :label="t('sync.sourceDatasource')" name="sourceDatasourceId" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select v-model:value="formState.sourceDatasourceId" :placeholder="t('common.pleaseSelect')" show-search>
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('sync.targetDatasource')" name="targetDatasourceId" :rules="[{ required: true, message: t('common.pleaseSelect') }]">
          <a-select v-model:value="formState.targetDatasourceId" :placeholder="t('common.pleaseSelect')" show-search>
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('sync.syncMode')" name="syncMode">
          <a-select v-model:value="formState.syncMode">
            <a-select-option value="FULL">{{ t('sync.fullSync') }}</a-select-option>
            <a-select-option value="INCREMENTAL">{{ t('sync.incrementalSync') }}</a-select-option>
          </a-select>
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
const formRef = ref()

const dataSource = ref<any[]>([])
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
  syncMode: 'FULL',
  scheduleType: 'MANUAL',
  cronExpression: ''
})

const columns = computed(() => [
  { title: t('sync.taskName'), dataIndex: 'taskName', key: 'taskName' },
  { title: t('sync.syncMode'), key: 'syncMode', width: 120 },
  { title: t('masking.scheduleType'), dataIndex: 'scheduleType', key: 'scheduleType', width: 100 },
  { title: t('common.status'), key: 'status', width: 100 },
  { title: t('common.createdAt'), dataIndex: 'createdAt', key: 'createdAt' },
  { title: t('common.actions'), key: 'actions', width: 220, fixed: 'right' as const }
])

async function loadDatasources() {
  try {
    const data = await request.get('/datasources', { params: { page: 1, pageSize: 100 } })
    datasourceList.value = data.items
  } catch (error) {
    //
  }
}

async function loadData() {
  loading.value = true
  try {
    const data = await request.get('/sync/tasks', {
      params: {
        page: pagination.current,
        pageSize: pagination.pageSize,
        keyword: search.keyword
      }
    })
    dataSource.value = data.items || []
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
    sourceDatasourceId: undefined,
    targetDatasourceId: undefined,
    syncMode: 'FULL',
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
    syncMode: record.syncMode,
    scheduleType: record.scheduleType,
    cronExpression: record.cronExpression
  })
  modalVisible.value = true
}

async function handleModalOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    if (isEdit.value) {
      await request.put(`/sync/tasks/${formState.id}`, formState)
      message.success(t('messages.updateSuccess'))
    } else {
      await request.post('/sync/tasks', formState)
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

async function executeTask(record: any) {
  try {
    await request.post(`/sync/tasks/${record.id}/execute`)
    message.success(t('messages.executeSuccess'))
  } catch (error) {
    //
  }
}

async function deleteTask(id: number) {
  try {
    await request.delete(`/sync/tasks/${id}`)
    message.success(t('messages.deleteSuccess'))
    loadData()
  } catch (error) {
    //
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
