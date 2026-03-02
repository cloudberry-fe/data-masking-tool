<template>
  <div class="dashboard">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="数据源数量" :value="stats.datasourceCount">
            <template #prefix>
              <DatabaseOutlined style="color: #1890ff" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="脱敏任务数" :value="stats.maskingTaskCount">
            <template #prefix>
              <SafetyOutlined style="color: #52c41a" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="翻数任务数" :value="stats.syncTaskCount">
            <template #prefix>
              <SwapOutlined style="color: #722ed1" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="今日执行次数" :value="stats.todayExecutionCount">
            <template #prefix>
              <PlayCircleOutlined style="color: #fa8c16" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 24px">
      <a-col :span="16">
        <a-card title="快捷操作">
          <a-space wrap>
            <a-button type="primary" @click="$router.push('/datasources')">
              <PlusOutlined />
              新增数据源
            </a-button>
            <a-button type="primary" @click="$router.push('/masking')">
              <PlusOutlined />
              新建脱敏任务
            </a-button>
            <a-button @click="$router.push('/lineage')">
              <BranchesOutlined />
              血缘分析
            </a-button>
            <a-button @click="$router.push('/sync')">
              <SwapOutlined />
              翻数工具
            </a-button>
          </a-space>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="系统信息">
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="系统名称">数据脱敏系统</a-descriptions-item>
            <a-descriptions-item label="版本号">1.0.0</a-descriptions-item>
            <a-descriptions-item label="当前用户">{{ userStore.realName || userStore.username }}</a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="最近执行">
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
  { id: 1, taskName: '客户信息脱敏', status: 'SUCCESS', startTime: '2024-01-15 09:00:00', duration: '5分钟' },
  { id: 2, taskName: '订单数据同步', status: 'SUCCESS', startTime: '2024-01-15 08:30:00', duration: '12分钟' },
  { id: 3, taskName: '交易记录脱敏', status: 'FAILED', startTime: '2024-01-14 18:00:00', duration: '-' }
])

const executionColumns = [
  { title: '任务名称', dataIndex: 'taskName', key: 'taskName' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '开始时间', dataIndex: 'startTime', key: 'startTime' },
  { title: '耗时', dataIndex: 'duration', key: 'duration' }
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
    SUCCESS: '成功',
    FAILED: '失败',
    RUNNING: '执行中',
    PENDING: '等待中'
  }
  return texts[status] || status
}

onMounted(() => {
  // 模拟数据加载
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
