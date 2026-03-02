<template>
  <div class="audit-page">
    <a-card>
      <template #title>审计日志</template>
      <a-form layout="inline" style="margin-bottom: 16px">
        <a-form-item label="用户名">
          <a-input v-model:value="search.username" placeholder="请输入" style="width: 160px" allow-clear />
        </a-form-item>
        <a-form-item label="操作类型">
          <a-select v-model:value="search.operationType" placeholder="请选择" style="width: 140px" allow-clear>
            <a-select-option value="LOGIN">登录</a-select-option>
            <a-select-option value="LOGOUT">登出</a-select-option>
            <a-select-option value="CREATE">创建</a-select-option>
            <a-select-option value="UPDATE">更新</a-select-option>
            <a-select-option value="DELETE">删除</a-select-option>
            <a-select-option value="EXECUTE">执行</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="操作模块">
          <a-select v-model:value="search.operationModule" placeholder="请选择" style="width: 140px" allow-clear>
            <a-select-option value="auth">认证</a-select-option>
            <a-select-option value="datasource">数据源</a-select-option>
            <a-select-option value="masking">数据脱敏</a-select-option>
            <a-select-option value="lineage">血缘分析</a-select-option>
            <a-select-option value="sync">翻数工具</a-select-option>
            <a-select-option value="system">系统管理</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="结果">
          <a-select v-model:value="search.responseResult" placeholder="请选择" style="width: 120px" allow-clear>
            <a-select-option value="SUCCESS">成功</a-select-option>
            <a-select-option value="FAIL">失败</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="时间范围">
          <a-range-picker v-model:value="timeRange" @change="handleTimeRangeChange" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="loadData">查询</a-button>
            <a-button @click="resetSearch">重置</a-button>
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
              {{ record.responseResult === 'SUCCESS' ? '成功' : '失败' }}
            </a-tag>
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
              详情
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 详情弹窗 -->
    <a-modal
      title="日志详情"
      v-model:open="detailModalVisible"
      :footer="null"
      width="700px"
    >
      <a-descriptions v-if="currentLog" bordered :column="2" size="small">
        <a-descriptions-item label="ID" :span="2">
          {{ currentLog.id }}
        </a-descriptions-item>
        <a-descriptions-item label="用户名">
          {{ currentLog.username }}
        </a-descriptions-item>
        <a-descriptions-item label="操作类型">
          {{ currentLog.operationType }}
        </a-descriptions-item>
        <a-descriptions-item label="操作模块">
          {{ currentLog.operationModule }}
        </a-descriptions-item>
        <a-descriptions-item label="结果">
          <a-tag :color="currentLog.responseResult === 'SUCCESS' ? 'success' : 'error'">
            {{ currentLog.responseResult === 'SUCCESS' ? '成功' : '失败' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="操作描述" :span="2">
          {{ currentLog.operationDesc }}
        </a-descriptions-item>
        <a-descriptions-item label="请求方法">
          {{ currentLog.requestMethod }}
        </a-descriptions-item>
        <a-descriptions-item label="请求URL" :span="2">
          {{ currentLog.requestUrl }}
        </a-descriptions-item>
        <a-descriptions-item label="请求参数" :span="2">
          <pre style="max-height: 200px; overflow: auto;">{{ JSON.stringify(currentLog.requestParams, null, 2) }}</pre>
        </a-descriptions-item>
        <a-descriptions-item v-if="currentLog.errorMessage" label="错误信息" :span="2">
          {{ currentLog.errorMessage }}
        </a-descriptions-item>
        <a-descriptions-item label="IP地址">
          {{ currentLog.ipAddress }}
        </a-descriptions-item>
        <a-descriptions-item label="操作时间">
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
  { title: '用户名', dataIndex: 'username', key: 'username', width: 120 },
  { title: '操作类型', dataIndex: 'operationType', key: 'operationType', width: 100 },
  { title: '操作模块', dataIndex: 'operationModule', key: 'operationModule', width: 120 },
  { title: '操作描述', key: 'operationDesc', width: 200 },
  { title: '请求URL', key: 'requestUrl', width: 200 },
  { title: '结果', key: 'responseResult', width: 80 },
  { title: 'IP地址', dataIndex: 'ipAddress', key: 'ipAddress', width: 120 },
  { title: '操作时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 },
  { title: '操作', key: 'actions', width: 80, fixed: 'right' as const }
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
