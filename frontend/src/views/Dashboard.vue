<template>
  <div class="dashboard">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="Data Sources" :value="stats.datasourceCount">
            <template #prefix>
              <DatabaseOutlined style="color: #1890ff" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="Masking Tasks" :value="stats.maskingTaskCount">
            <template #prefix>
              <SafetyOutlined style="color: #52c41a" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="Sync Tasks" :value="stats.syncTaskCount">
            <template #prefix>
              <SwapOutlined style="color: #722ed1" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
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
        <a-card title="Recent Executions">
          <a-table :columns="executionColumns" :data-source="recentExecutions" :pagination="false" size="small">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">
                  {{ getStatusText(record.status) }}
                </a-tag>
              </template>
            </template>
          </a-table>
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

const userStore = useUserStore()

const stats = reactive({
  datasourceCount: 0,
  maskingTaskCount: 0,
  syncTaskCount: 0,
  todayExecutionCount: 0
})

const recentExecutions = ref([
  { id: 1, taskName: 'Customer Info Masking', status: 'SUCCESS', startTime: '2024-01-15 09:00:00', duration: '5 min' },
  { id: 2, taskName: 'Order Data Sync', status: 'SUCCESS', startTime: '2024-01-15 08:30:00', duration: '12 min' },
  { id: 3, taskName: 'Transaction Masking', status: 'FAILED', startTime: '2024-01-14 18:00:00', duration: '-' }
])

const executionColumns = [
  { title: 'Task Name', dataIndex: 'taskName', key: 'taskName' },
  { title: 'Status', dataIndex: 'status', key: 'status' },
  { title: 'Start Time', dataIndex: 'startTime', key: 'startTime' },
  { title: 'Duration', dataIndex: 'duration', key: 'duration' }
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

onMounted(() => {
  // Mock data loading
  stats.datasourceCount = 5
  stats.maskingTaskCount = 12
  stats.syncTaskCount = 8
  stats.todayExecutionCount = 25
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}
</style>
