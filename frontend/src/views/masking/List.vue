<template>
  <div class="masking-list">
    <div class="page-header">
      <a-space>
        <a-input-search
          v-model:value="search.keyword"
          placeholder="搜索任务名称"
          style="width: 240px"
          @search="loadData"
          allow-clear
        />
        <a-select
          v-model:value="search.status"
          placeholder="状态"
          style="width: 140px"
          allow-clear
          @change="loadData"
        >
          <a-select-option value="DRAFT">草稿</a-select-option>
          <a-select-option value="READY">就绪</a-select-option>
          <a-select-option value="RUNNING">执行中</a-select-option>
          <a-select-option value="PAUSED">已暂停</a-select-option>
        </a-select>
      </a-space>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <PlusOutlined />
          新建任务
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
        <template v-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'scheduleType'">
          {{ record.scheduleType === 'CRON' ? '定时调度' : '手动执行' }}
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" size="small" @click="goToDetail(record)">
              配置
            </a-button>
            <a-popconfirm
              v-if="record.status !== 'RUNNING'"
              title="确定要执行该任务吗？"
              @confirm="executeTask(record)"
            >
              <a-button type="link" size="small" type="primary">
                执行
              </a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="showEditModal(record)">
              编辑
            </a-button>
            <a-popconfirm title="确定要删除该任务吗？" @confirm="deleteTask(record.id)">
              <a-button type="link" size="small" danger>
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 新建/编辑弹窗 -->
    <a-modal
      :title="isEdit ? '编辑任务' : '新建任务'"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      width="600px"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="任务名称" name="taskName" :rules="[{ required: true, message: '请输入' }]">
          <a-input v-model:value="formState.taskName" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="数据源" name="datasourceId" :rules="[{ required: true, message: '请选择' }]">
          <a-select v-model:value="formState.datasourceId" placeholder="请选择" show-search>
            <a-select-option v-for="ds in datasourceList" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="源Schema" name="sourceSchema">
          <a-input v-model:value="formState.sourceSchema" placeholder="public" />
        </a-form-item>
        <a-form-item label="目标Schema" name="targetSchema">
          <a-input v-model:value="formState.targetSchema" placeholder="public" />
        </a-form-item>
        <a-form-item label="调度类型" name="scheduleType">
          <a-select v-model:value="formState.scheduleType">
            <a-select-option value="MANUAL">手动执行</a-select-option>
            <a-select-option value="CRON">定时调度</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="formState.scheduleType === 'CRON'" label="Cron表达式" name="cronExpression">
          <a-input v-model:value="formState.cronExpression" placeholder="0 0 2 * * ?" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="formState.description" :rows="3" placeholder="请输入" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const router = useRouter()

const loading = ref(false)
const modalVisible = ref(false)
const modalLoading = ref(false)
const isEdit = ref(false)
const formRef = ref()

const dataSource = ref<any[]>([])
const datasourceList = ref<any[]>([])
const search = reactive({
  keyword: '',
  status: undefined as string | undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const formState = reactive({
  id: undefined as number | undefined,
  taskName: '',
  datasourceId: undefined as number | undefined,
  sourceSchema: '',
  targetSchema: '',
  scheduleType: 'MANUAL',
  cronExpression: '',
  description: ''
})

const columns = [
  { title: '任务名称', dataIndex: 'taskName', key: 'taskName' },
  { title: '状态', key: 'status', width: 100 },
  { title: '调度类型', key: 'scheduleType', width: 100 },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt' },
  { title: '操作', key: 'actions', width: 280, fixed: 'right' as const }
]

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
    const data = await request.get('/masking/tasks', {
      params: {
        page: pagination.current,
        pageSize: pagination.pageSize,
        keyword: search.keyword,
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
  isEdit.value = false
  Object.assign(formState, {
    id: undefined,
    taskName: '',
    datasourceId: undefined,
    sourceSchema: '',
    targetSchema: '',
    scheduleType: 'MANUAL',
    cronExpression: '',
    description: ''
  })
  modalVisible.value = true
}

function showEditModal(record: any) {
  isEdit.value = true
  Object.assign(formState, {
    id: record.id,
    taskName: record.taskName,
    datasourceId: record.datasourceId,
    sourceSchema: record.sourceSchema,
    targetSchema: record.targetSchema,
    scheduleType: record.scheduleType,
    cronExpression: record.cronExpression,
    description: record.description
  })
  modalVisible.value = true
}

async function handleModalOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    if (isEdit.value) {
      await request.put(`/masking/tasks/${formState.id}`, formState)
      message.success('更新成功')
    } else {
      await request.post('/masking/tasks', formState)
      message.success('创建成功')
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

function goToDetail(record: any) {
  router.push(`/masking/${record.id}`)
}

async function executeTask(record: any) {
  try {
    await request.post(`/masking/tasks/${record.id}/execute`)
    message.success('任务已提交执行')
    loadData()
  } catch (error) {
    //
  }
}

async function deleteTask(id: number) {
  try {
    await request.delete(`/masking/tasks/${id}`)
    message.success('删除成功')
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
    PAUSED: 'warning',
    SUCCESS: 'success',
    FAILED: 'error'
  }
  return colors[status] || 'default'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    DRAFT: '草稿',
    READY: '就绪',
    RUNNING: '执行中',
    PAUSED: '已暂停',
    SUCCESS: '成功',
    FAILED: '失败'
  }
  return texts[status] || status
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
