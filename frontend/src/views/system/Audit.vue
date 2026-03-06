<template>
  <div class="audit-page">
    <a-card>
      <template #title>Audit Logs</template>
      <a-form layout="inline" style="margin-bottom: 16px">
        <a-form-item label="Username">
          <a-input v-model:value="search.username" placeholder="Please enter" style="width: 160px" allow-clear />
        </a-form-item>
        <a-form-item label="Operation Type">
          <a-select v-model:value="search.operationType" placeholder="Please select" style="width: 140px" allow-clear>
            <a-select-option value="LOGIN">Login</a-select-option>
            <a-select-option value="LOGOUT">Logout</a-select-option>
            <a-select-option value="CREATE">Create</a-select-option>
            <a-select-option value="UPDATE">Update</a-select-option>
            <a-select-option value="DELETE">Delete</a-select-option>
            <a-select-option value="EXECUTE">Execute</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Module">
          <a-select v-model:value="search.operationModule" placeholder="Please select" style="width: 140px" allow-clear>
            <a-select-option value="auth">Auth</a-select-option>
            <a-select-option value="datasource">Data Sources</a-select-option>
            <a-select-option value="masking">Data Masking</a-select-option>
            <a-select-option value="lineage">Lineage Analysis</a-select-option>
            <a-select-option value="sync">Data Sync</a-select-option>
            <a-select-option value="system">System</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Result">
          <a-select v-model:value="search.responseResult" placeholder="Please select" style="width: 120px" allow-clear>
            <a-select-option value="SUCCESS">Success</a-select-option>
            <a-select-option value="FAILED">Failed</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Time Range">
          <a-range-picker v-model:value="timeRange" @change="handleTimeRangeChange" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="loadData">Search</a-button>
            <a-button @click="resetSearch">Reset</a-button>
          </a-space>
        </a-form-item>
      </a-form>

      <a-table
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
        size="small"
        :scroll="{ x: 1200 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'responseResult'">
            <a-tag :color="record.responseResult === 'SUCCESS' ? 'success' : 'error'">
              {{ record.responseResult === 'SUCCESS' ? 'Success' : 'Failed' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'errorMessage'">
            <template v-if="record.errorMessage">
              <a-tooltip :title="record.errorMessage">
                <span style="color: #ff4d4f" class="truncate">{{ record.errorMessage }}</span>
              </a-tooltip>
            </template>
            <span v-else style="color: #999">-</span>
          </template>
          <template v-if="column.key === 'operationDesc'">
            <a-tooltip :title="record.operationDesc">
              <span class="truncate">{{ record.operationDesc }}</span>
            </a-tooltip>
          </template>
          <template v-if="column.key === 'requestUrl'">
            <a-tooltip :title="record.requestUrl">
              <span class="truncate">{{ record.requestUrl }}</span>
            </a-tooltip>
          </template>
          <template v-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="showDetail(record)">
              Details
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Detail Modal -->
    <a-modal
      title="Log Details"
      v-model:open="detailModalVisible"
      :footer="null"
      width="700px"
    >
      <a-descriptions v-if="currentLog" bordered :column="2" size="small">
        <a-descriptions-item label="ID" :span="2">
          {{ currentLog.id }}
        </a-descriptions-item>
        <a-descriptions-item label="Username">
          {{ currentLog.username }}
        </a-descriptions-item>
        <a-descriptions-item label="Operation Type">
          {{ currentLog.operationType }}
        </a-descriptions-item>
        <a-descriptions-item label="Module">
          {{ currentLog.operationModule }}
        </a-descriptions-item>
        <a-descriptions-item label="Result">
          <a-tag :color="currentLog.responseResult === 'SUCCESS' ? 'success' : 'error'">
            {{ currentLog.responseResult === 'SUCCESS' ? 'Success' : 'Failed' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="Description" :span="2">
          {{ currentLog.operationDesc }}
        </a-descriptions-item>
        <a-descriptions-item label="Request Method">
          {{ currentLog.requestMethod }}
        </a-descriptions-item>
        <a-descriptions-item label="Request URL" :span="2">
          {{ currentLog.requestUrl }}
        </a-descriptions-item>
        <a-descriptions-item label="Request Params" :span="2">
          <pre style="max-height: 200px; overflow: auto;">{{ JSON.stringify(currentLog.requestParams, null, 2) }}</pre>
        </a-descriptions-item>
        <a-descriptions-item v-if="currentLog.errorMessage" label="Error Message" :span="2">
          {{ currentLog.errorMessage }}
        </a-descriptions-item>
        <a-descriptions-item label="IP Address">
          {{ currentLog.ipAddress }}
        </a-descriptions-item>
        <a-descriptions-item label="Created At">
          {{ currentLog.createdAt }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'
import type { Dayjs } from 'dayjs'

const loading = ref(false)
const detailModalVisible = ref(false)
const currentLog = ref<any>(null)
const timeRange = ref<[Dayjs, Dayjs]>()

const dataSource = ref<any[]>([])
const search = reactive({
  username: '',
  operationType: undefined as string | undefined,
  operationModule: undefined as string | undefined,
  responseResult: undefined as string | undefined,
  startTime: undefined as string | undefined,
  endTime: undefined as string | undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: 'Username', dataIndex: 'username', key: 'username', width: 100 },
  { title: 'Operation Type', dataIndex: 'operationType', key: 'operationType', width: 100 },
  { title: 'Module', dataIndex: 'operationModule', key: 'operationModule', width: 100 },
  { title: 'Description', key: 'operationDesc', width: 180 },
  { title: 'Request URL', key: 'requestUrl', width: 180 },
  { title: 'Result', key: 'responseResult', width: 80 },
  { title: 'Error', key: 'errorMessage', width: 200 },
  { title: 'IP Address', dataIndex: 'ipAddress', key: 'ipAddress', width: 100 },
  { title: 'Created At', dataIndex: 'createdAt', key: 'createdAt', width: 160 },
  { title: 'Actions', key: 'actions', width: 80, fixed: 'right' as const }
]

function handleTimeRangeChange(dates: any) {
  if (dates) {
    search.startTime = dates[0]?.toISOString()
    search.endTime = dates[1]?.toISOString()
  } else {
    search.startTime = undefined
    search.endTime = undefined
  }
}

async function loadData() {
  loading.value = true
  try {
    const data = await request.get('/audit/logs', {
      params: {
        page: pagination.current,
        pageSize: pagination.pageSize,
        ...search
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

function resetSearch() {
  Object.assign(search, {
    username: '',
    operationType: undefined,
    operationModule: undefined,
    responseResult: undefined,
    startTime: undefined,
    endTime: undefined
  })
  timeRange.value = undefined
  pagination.current = 1
  loadData()
}

function showDetail(record: any) {
  currentLog.value = record
  detailModalVisible.value = true
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.truncate {
  display: block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.ant-descriptions-item-label) {
  width: 100px;
}
</style>
