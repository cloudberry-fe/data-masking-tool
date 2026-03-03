<template>
  <div class="dashboard">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-card class="stat-card" :loading="loading">
          <a-statistic title="Data Sources" :value="stats.datasourceCount">
            <template #prefix>
              <DatabaseOutlined style="color: #1890ff" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card" :loading="loading">
          <a-statistic title="Masking Tasks" :value="stats.maskingTaskCount">
            <template #prefix>
              <SafetyOutlined style="color: #52c41a" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card" :loading="loading">
          <a-statistic title="Sync Tasks" :value="stats.syncTaskCount">
            <template #prefix>
              <SwapOutlined style="color: #722ed1" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card" :loading="loading">
          <a-statistic title="Today's Executions" :value="stats.todayExecutionCount">
            <template #prefix>
              <PlayCircleOutlined style="color: #fa8c16" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 24px">
      <a-col :span="16">
        <a-card title="Quick Actions">
          <a-space wrap>
            <a-button type="primary" @click="$router.push('/datasources')">
              <PlusOutlined />
              Add Data Source
            </a-button>
            <a-button type="primary" @click="$router.push('/masking')">
              <PlusOutlined />
              New Masking Task
            </a-button>
            <a-button @click="$router.push('/lineage')">
              <BranchesOutlined />
              Lineage Analysis
            </a-button>
            <a-button @click="$router.push('/sync')">
              <SwapOutlined />
              Data Sync
            </a-button>
          </a-space>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="System Info">
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="System Name">Cloudberry Data Management Console</a-descriptions-item>
            <a-descriptions-item label="Version">1.0.0</a-descriptions-item>
            <a-descriptions-item label="Current User">{{ userStore.realName || userStore.username }}</a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="Recent Executions" :loading="loading">
          <a-table
            :columns="executionColumns"
            :data-source="recentExecutions"
            :pagination="false"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>
              <template v-if="column.key === 'taskType'">
                <a-tag :color="record.taskType === 'MASKING' ? 'blue' : 'purple'">
                  {{ record.taskType === 'MASKING' ? 'Masking' : 'Sync' }}
                </a-tag>
              </template>
              <template v-if="column.key === 'records'">
                <span v-if="record.totalRecords">
                  {{ record.successRecords || 0 }} / {{ record.totalRecords }}
                </span>
                <span v-else>-</span>
              </template>
            </template>
          </a-table>
          <a-empty v-if="!loading && recentExecutions.length === 0" description="No recent executions" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import {
  DatabaseOutlined,
  SafetyOutlined,
  SwapOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  BranchesOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const userStore = useUserStore()
const loading = ref(false)

const stats = reactive({
  datasourceCount: 0,
  maskingTaskCount: 0,
  syncTaskCount: 0,
  todayExecutionCount: 0
})

const recentExecutions = ref<any[]>([])

const executionColumns = [
  { title: 'Task Name', dataIndex: 'taskName', key: 'taskName' },
  { title: 'Type', dataIndex: 'taskType', key: 'taskType', width: 100 },
  { title: 'Status', dataIndex: 'status', key: 'status', width: 100 },
  { title: 'Records (Success/Total)', key: 'records', width: 150 },
  { title: 'Start Time', dataIndex: 'startTime', key: 'startTime' },
  { title: 'Duration', dataIndex: 'duration', key: 'duration', width: 100 }
]

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    SUCCESS: 'success',
    FAILED: 'error',
    RUNNING: 'processing',
    PENDING: 'default'
  }
  return colors[status] || 'default'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    SUCCESS: 'Success',
    FAILED: 'Failed',
    RUNNING: 'Running',
    PENDING: 'Pending'
  }
  return texts[status] || status
}

async function loadDashboardStats() {
  try {
    loading.value = true
    const data = await request.get('/system/dashboard/stats')

    stats.datasourceCount = data.datasourceCount || 0
    stats.maskingTaskCount = data.maskingTaskCount || 0
    stats.syncTaskCount = data.syncTaskCount || 0
    stats.todayExecutionCount = data.todayExecutionCount || 0

    recentExecutions.value = (data.recentExecutions || []).map((item: any) => ({
      key: item.id,
      ...item
    }))
  } catch (error) {
    console.error('Failed to load dashboard stats', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboardStats()
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}
</style>
