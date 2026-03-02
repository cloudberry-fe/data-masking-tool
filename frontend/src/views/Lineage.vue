<template>
  <div class="lineage-page">
    <a-card>
      <template #title>血缘分析</template>
      <template #extra>
        <a-space>
          <a-select v-model:value="selectedDatasource" style="width: 240px" placeholder="选择数据源">
            <a-select-option v-for="ds in datasources" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
          <a-button type="primary" @click="loadLineage" :loading="loading">
            分析
          </a-button>
        </a-space>
      </template>

      <div ref="graphContainer" class="graph-container"></div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'

const graphContainer = ref<HTMLElement>()
const selectedDatasource = ref<number>()
const datasources = ref<any[]>([])
const loading = ref(false)
let graph: any = null

async function loadDatasources() {
  try {
    const data = await request.get('/datasources', { params: { page: 1, pageSize: 100 } })
    datasources.value = data.items
  } catch (error) {
    //
  }
}

async function loadLineage() {
  if (!selectedDatasource.value) {
    message.warning('请选择数据源')
    return
  }

  loading.value = true
  try {
    const data = await request.get('/lineage/graph', {
      params: { datasourceId: selectedDatasource.value }
    })
    renderGraph(data)
  } finally {
    loading.value = false
  }
}

async function renderGraph(data: any) {
  try {
    // 动态导入 G6
    const G6 = await import('@antv/g6')

    if (graph) {
      graph.destroy()
    }

    if (!graphContainer.value) return

    const containerWidth = graphContainer.value.clientWidth
    const containerHeight = 500

    graph = new G6.Graph({
      container: graphContainer.value,
      width: containerWidth,
      height: containerHeight,
      fitView: true,
      modes: {
        default: ['drag-canvas', 'zoom-canvas', 'drag-node']
      },
      defaultNode: {
        type: 'rect',
        size: [160, 60],
        style: {
          radius: 8,
          fill: '#C6E5FF',
          stroke: '#5B8FF9',
          lineWidth: 2
        },
        labelCfg: {
          style: {
            fill: '#000',
            fontSize: 14
          }
        }
      },
      defaultEdge: {
        type: 'cubic-horizontal',
        style: {
          stroke: '#A3B1BF',
          lineWidth: 2
        }
      },
      layout: {
        type: 'dagre',
        rankdir: 'LR',
        nodesep: 40,
        ranksep: 80
      }
    })

    const nodes = (data.nodes || []).map((node: any) => ({
      id: node.id,
      label: node.name,
      ...node
    }))

    const edges = (data.edges || []).map((edge: any) => ({
      source: edge.source,
      target: edge.target,
      label: edge.type,
      ...edge
    }))

    graph.data({ nodes, edges })
    graph.render()
  } catch (error) {
    console.error('渲染血缘图失败:', error)
    message.info('血缘图谱需要安装 @antv/g6 依赖')
  }
}

onMounted(() => {
  loadDatasources()
})

onUnmounted(() => {
  if (graph) {
    graph.destroy()
  }
})
</script>

<style scoped>
.lineage-page {
  height: 100%;
}

.graph-container {
  width: 100%;
  height: 500px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}
</style>
