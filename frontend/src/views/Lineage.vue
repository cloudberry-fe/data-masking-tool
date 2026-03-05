<template>
  <div class="lineage-page">
    <a-card>
      <template #title>{{ t('lineage.title') }}</template>
      <template #extra>
        <a-space>
          <a-select v-model:value="selectedDatasource" style="width: 240px" :placeholder="t('lineage.selectDatasource')">
            <a-select-option v-for="ds in datasources" :key="ds.id" :value="ds.id">
              {{ ds.datasourceName }}
            </a-select-option>
          </a-select>
          <a-button type="primary" @click="scanLineage" :loading="scanLoading">
            {{ t('lineage.scan') }}
          </a-button>
          <a-button @click="loadLineage" :loading="loading">
            {{ t('lineage.analyze') }}
          </a-button>
        </a-space>
      </template>

      <div class="lineage-controls" v-if="graphData.nodes.length > 0">
        <a-space>
          <a-input-search
            v-model:value="searchNode"
            :placeholder="t('lineage.searchNode')"
            style="width: 200px"
            @search="filterNode"
            allow-clear
          />
          <a-select v-model:value="searchDirection" style="width: 120px">
            <a-select-option value="BOTH">{{ t('lineage.both') }}</a-select-option>
            <a-select-option value="UPSTREAM">{{ t('lineage.upstream') }}</a-select-option>
            <a-select-option value="DOWNSTREAM">{{ t('lineage.downstream') }}</a-select-option>
          </a-select>
          <a-button @click="resetFilter">{{ t('common.reset') }}</a-button>
        </a-space>
      </div>

      <div ref="graphContainer" class="graph-container"></div>

      <div v-if="graphData.nodes.length === 0 && !loading" class="empty-hint">
        <a-empty :description="t('lineage.emptyHint')" />
      </div>
    </a-card>

    <!-- Add Relation Modal -->
    <a-modal
      :title="t('lineage.addRelation')"
      v-model:open="relationModalVisible"
      :confirm-loading="relationLoading"
      @ok="handleAddRelation"
    >
      <a-form :model="relationForm" :label-col="{ span: 6 }">
        <a-form-item :label="t('lineage.sourceNode')">
          <a-input v-model:value="relationForm.sourceNode" />
        </a-form-item>
        <a-form-item :label="t('lineage.targetNode')">
          <a-input v-model:value="relationForm.targetNode" />
        </a-form-item>
        <a-form-item :label="t('lineage.relationType')">
          <a-select v-model:value="relationForm.relationType">
            <a-select-option value="TRANSFORM">Transform</a-select-option>
            <a-select-option value="VIEW">View</a-select-option>
            <a-select-option value="FOREIGN_KEY">Foreign Key</a-select-option>
            <a-select-option value="MANUAL">Manual</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('lineage.transformLogic')">
          <a-textarea v-model:value="relationForm.transformLogic" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import request from '@/utils/request'

const { t, locale } = useI18n()

const graphContainer = ref<HTMLElement>()
const selectedDatasource = ref<number>()
const datasources = ref<any[]>([])
const loading = ref(false)
const scanLoading = ref(false)
const searchNode = ref('')
const searchDirection = ref('BOTH')
const relationModalVisible = ref(false)
const relationLoading = ref(false)

const graphData = reactive({
  nodes: [] as any[],
  edges: [] as any[]
})

const relationForm = reactive({
  sourceNode: '',
  targetNode: '',
  relationType: 'TRANSFORM',
  transformLogic: ''
})

let graph: any = null

async function loadDatasources() {
  try {
    const data = await request.get('/datasources', { params: { page: 1, pageSize: 100 } })
    datasources.value = data.items
  } catch (error) {
    //
  }
}

async function scanLineage() {
  if (!selectedDatasource.value) {
    message.warning(t('lineage.selectDatasourceHint'))
    return
  }

  scanLoading.value = true
  try {
    const result = await request.post('/lineage/scan', null, {
      params: { datasource_id: selectedDatasource.value }
    })
    if (result.success) {
      message.success(t('lineage.scanSuccess', { count: result.relationsSaved }))
      await loadLineage()
    } else {
      message.error(t('lineage.scanFailed'))
    }
  } finally {
    scanLoading.value = false
  }
}

async function loadLineage() {
  if (!selectedDatasource.value) {
    message.warning(t('lineage.selectDatasourceHint'))
    return
  }

  loading.value = true
  try {
    const data = await request.get('/lineage/graph', {
      params: {
        datasource_id: selectedDatasource.value,
        depth: 5
      }
    })
    graphData.nodes = data.nodes || []
    graphData.edges = data.edges || []
    renderGraph(data)
  } finally {
    loading.value = false
  }
}

async function filterNode() {
  if (!searchNode.value || !selectedDatasource.value) return

  loading.value = true
  try {
    const data = await request.get('/lineage/graph', {
      params: {
        datasource_id: selectedDatasource.value,
        node_name: searchNode.value,
        direction: searchDirection.value,
        depth: 3
      }
    })
    graphData.nodes = data.nodes || []
    graphData.edges = data.edges || []
    renderGraph(data)
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  searchNode.value = ''
  searchDirection.value = 'BOTH'
  if (selectedDatasource.value) {
    loadLineage()
  }
}

async function handleAddRelation() {
  if (!selectedDatasource.value) return

  relationLoading.value = true
  try {
    await request.post('/lineage/relations', {
      datasource_id: selectedDatasource.value,
      source_node: relationForm.sourceNode,
      target_node: relationForm.targetNode,
      relation_type: relationForm.relationType,
      transform_logic: relationForm.transformLogic
    })
    message.success(t('messages.createSuccess'))
    relationModalVisible.value = false
    loadLineage()
  } finally {
    relationLoading.value = false
  }
}

async function renderGraph(data: any) {
  try {
    // Dynamically import G6
    const G6 = await import('@antv/g6')

    if (graph) {
      graph.destroy()
    }

    if (!graphContainer.value) return

    const containerWidth = graphContainer.value.clientWidth
    const containerHeight = 500

    if (!data.nodes || data.nodes.length === 0) {
      return
    }

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
    console.error('Failed to render lineage graph:', error)
    message.info(t('lineage.g6Required'))
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

.lineage-controls {
  margin-bottom: 16px;
}

.graph-container {
  width: 100%;
  height: 500px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}

.empty-hint {
  height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
