<template>
  <div class="datasource-selector">
    <!-- Schema 选择 -->
    <a-form-item :label="labels.schema || 'Schema'" :name="formFieldName.schema">
      <a-select
        v-model:value="selectedSchema"
        :placeholder="placeholders.schema || '请选择Schema'"
        :loading="loadingSchemas"
        :disabled="disabled || !datasourceId"
        show-search
        allow-clear
        @change="onSchemaChange"
      >
        <a-select-option v-for="schema in schemaList" :key="schema" :value="schema">
          {{ schema }}
        </a-select-option>
      </a-select>
    </a-form-item>

    <!-- 表选择 -->
    <a-form-item :label="labels.table || '表名'" :name="formFieldName.table" :rules="tableRequired ? [{ required: true, message: '请选择表' }] : []">
      <a-select
        v-model:value="selectedTable"
        :placeholder="placeholders.table || '请选择表'"
        :loading="loadingTables"
        :disabled="disabled || !datasourceId"
        show-search
        allow-clear
        :filter-option="filterOption"
        @change="onTableChange"
        @focus="loadTablesIfNeeded"
      >
        <a-select-option v-for="table in tableList" :key="table.tableName" :value="table.tableName">
          <span>{{ table.tableName }}</span>
          <span v-if="table.tableComment" style="color: #999; margin-left: 8px; font-size: 12px">{{ table.tableComment }}</span>
        </a-select-option>
      </a-select>
    </a-form-item>

    <!-- 字段选择（可选） -->
    <a-form-item v-if="showColumnSelect" :label="labels.column || '字段名'" :name="formFieldName.column" :rules="columnRequired ? [{ required: true, message: '请选择字段' }] : []">
      <a-select
        v-model:value="selectedColumn"
        :placeholder="placeholders.column || '请选择字段'"
        :loading="loadingColumns"
        :disabled="disabled || !datasourceId || !selectedTable"
        show-search
        allow-clear
        :filter-option="filterOption"
        @change="onColumnChange"
        @focus="loadColumnsIfNeeded"
      >
        <a-select-option v-for="col in columnList" :key="col.columnName" :value="col.columnName">
          <span>{{ col.columnName }}</span>
          <a-tag size="small" style="margin-left: 8px">{{ col.dataType }}</a-tag>
          <span v-if="col.columnComment" style="color: #999; margin-left: 8px; font-size: 12px">{{ col.columnComment }}</span>
        </a-select-option>
      </a-select>
    </a-form-item>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'

interface Props {
  datasourceId?: number
  schema?: string
  table?: string
  column?: string
  disabled?: boolean
  showColumnSelect?: boolean
  tableRequired?: boolean
  columnRequired?: boolean
  labels?: {
    schema?: string
    table?: string
    column?: string
  }
  placeholders?: {
    schema?: string
    table?: string
    column?: string
  }
  formFieldName?: {
    schema?: string
    table?: string
    column?: string
  }
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  showColumnSelect: false,
  tableRequired: true,
  columnRequired: false,
  labels: () => ({}),
  placeholders: () => ({}),
  formFieldName: () => ({ schema: 'schemaName', table: 'tableName', column: 'columnName' })
})

const emit = defineEmits<{
  (e: 'update:schema', value: string): void
  (e: 'update:table', value: string): void
  (e: 'update:column', value: string): void
  (e: 'schemaChange', value: string): void
  (e: 'tableChange', value: string, tableInfo: any): void
  (e: 'columnChange', value: string, columnInfo: any): void
}>()

const selectedSchema = ref<string>(props.schema || '')
const selectedTable = ref<string>(props.table || '')
const selectedColumn = ref<string>(props.column || '')

const schemaList = ref<string[]>([])
const tableList = ref<any[]>([])
const columnList = ref<any[]>([])

const loadingSchemas = ref(false)
const loadingTables = ref(false)
const loadingColumns = ref(false)

// 监听外部 props 变化
watch(() => props.schema, (val) => {
  if (val !== selectedSchema.value) {
    selectedSchema.value = val || ''
  }
})

watch(() => props.table, (val) => {
  if (val !== selectedTable.value) {
    selectedTable.value = val || ''
  }
})

watch(() => props.column, (val) => {
  if (val !== selectedColumn.value) {
    selectedColumn.value = val || ''
  }
})

// 监听数据源变化，重置选择
watch(() => props.datasourceId, (newId, oldId) => {
  if (newId !== oldId) {
    selectedSchema.value = ''
    selectedTable.value = ''
    selectedColumn.value = ''
    schemaList.value = []
    tableList.value = []
    columnList.value = []
    emit('update:schema', '')
    emit('update:table', '')
    emit('update:column', '')
    if (newId) {
      loadSchemas()
    }
  }
})

function filterOption(input: string, option: any) {
  const text = option.label || option.value || ''
  return text.toLowerCase().includes(input.toLowerCase())
}

async function loadSchemas() {
  if (!props.datasourceId) return

  loadingSchemas.value = true
  try {
    const data = await request.get(`/datasources/${props.datasourceId}/schemas`)
    schemaList.value = data || ['public']
    // 如果只有一个 schema，自动选中
    if (schemaList.value.length === 1 && !selectedSchema.value) {
      selectedSchema.value = schemaList.value[0]
      emit('update:schema', selectedSchema.value)
    }
  } catch (error) {
    console.error('加载Schema列表失败', error)
    schemaList.value = ['public']
  } finally {
    loadingSchemas.value = false
  }
}

async function loadTables() {
  if (!props.datasourceId || !selectedSchema.value) {
    tableList.value = []
    return
  }

  loadingTables.value = true
  try {
    const data = await request.get(`/datasources/${props.datasourceId}/tables`, {
      params: { schema: selectedSchema.value }
    })
    tableList.value = (data || []).map((t: any) => ({
      tableName: t.tableName || t.table_name,
      tableComment: t.tableComment || t.table_comment || ''
    }))
  } catch (error) {
    console.error('加载表列表失败', error)
    tableList.value = []
  } finally {
    loadingTables.value = false
  }
}

function loadTablesIfNeeded() {
  if (tableList.value.length === 0 && props.datasourceId && selectedSchema.value) {
    loadTables()
  }
}

async function loadColumns() {
  if (!props.datasourceId || !selectedTable.value) {
    columnList.value = []
    return
  }

  loadingColumns.value = true
  try {
    const tableName = selectedSchema.value ? `${selectedSchema.value}.${selectedTable.value}` : selectedTable.value
    const data = await request.get(`/datasources/${props.datasourceId}/tables/${tableName}/columns`, {
      params: { schema: selectedSchema.value }
    })
    columnList.value = (data || []).map((c: any) => ({
      columnName: c.columnName || c.column_name,
      dataType: c.dataType || c.data_type,
      isNullable: c.isNullable ?? c.is_nullable ?? true,
      columnComment: c.columnComment || c.column_comment || ''
    }))
  } catch (error) {
    console.error('加载字段列表失败', error)
    columnList.value = []
  } finally {
    loadingColumns.value = false
  }
}

function loadColumnsIfNeeded() {
  if (columnList.value.length === 0 && props.datasourceId && selectedTable.value) {
    loadColumns()
  }
}

function onSchemaChange(value: string) {
  emit('update:schema', value)
  emit('schemaChange', value)
  // 清空表和字段选择
  selectedTable.value = ''
  selectedColumn.value = ''
  tableList.value = []
  columnList.value = []
  emit('update:table', '')
  emit('update:column', '')
  // 加载新 schema 的表
  if (value) {
    loadTables()
  }
}

function onTableChange(value: string) {
  emit('update:table', value)
  const tableInfo = tableList.value.find(t => t.tableName === value)
  emit('tableChange', value, tableInfo)
  // 清空字段选择
  selectedColumn.value = ''
  columnList.value = []
  emit('update:column', '')
  // 加载字段
  if (value && props.showColumnSelect) {
    loadColumns()
  }
}

function onColumnChange(value: string) {
  emit('update:column', value)
  const colInfo = columnList.value.find(c => c.columnName === value)
  emit('columnChange', value, colInfo)
}

// 初始化
onMounted(() => {
  if (props.datasourceId) {
    loadSchemas()
    if (props.schema) {
      loadTables()
    }
    if (props.table && props.showColumnSelect) {
      loadColumns()
    }
  }
})

// 暴露方法供父组件调用
defineExpose({
  loadSchemas,
  loadTables,
  loadColumns,
  validateTable: async () => {
    if (!props.datasourceId || !selectedTable.value) return false
    try {
      const data = await request.get(`/datasources/${props.datasourceId}/tables`, {
        params: { schema: selectedSchema.value }
      })
      const tables = data || []
      return tables.some((t: any) => (t.tableName || t.table_name) === selectedTable.value)
    } catch {
      return false
    }
  },
  validateColumn: async () => {
    if (!props.datasourceId || !selectedTable.value || !selectedColumn.value) return false
    try {
      const tableName = selectedSchema.value ? `${selectedSchema.value}.${selectedTable.value}` : selectedTable.value
      const data = await request.get(`/datasources/${props.datasourceId}/tables/${tableName}/columns`, {
        params: { schema: selectedSchema.value }
      })
      const columns = data || []
      return columns.some((c: any) => (c.columnName || c.column_name) === selectedColumn.value)
    } catch {
      return false
    }
  }
})
</script>

<style scoped>
.datasource-selector {
  /* 可根据需要添加样式 */
}
</style>
