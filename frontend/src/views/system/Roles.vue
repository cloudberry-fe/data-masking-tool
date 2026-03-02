<template>
  <div class="roles-page">
    <a-row :gutter="24">
      <a-col :span="8">
        <a-card title="角色列表">
          <template #extra>
            <a-button type="primary" size="small" @click="showCreateModal">
              <PlusOutlined />
              新增
            </a-button>
          </template>
          <a-list
            :data-source="roles"
            :loading="loading"
            size="small"
          >
            <template #renderItem="{ item }">
              <a-list-item
                :class="{ active: selectedRole?.id === item.id }"
                @click="selectRole(item)"
              >
                <a-list-item-meta :title="item.roleName" :description="item.roleCode" />
                <template #extra>
                  <a-space>
                    <a-button type="text" size="small" @click.stop="showEditModal(item)">
                      <EditOutlined />
                    </a-button>
                    <a-popconfirm title="确定删除？" @confirm.stop="deleteRole(item.id)">
                      <a-button type="text" size="small" danger>
                        <DeleteOutlined />
                      </a-button>
                    </a-popconfirm>
                  </a-space>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      <a-col :span="16">
        <a-card v-if="selectedRole" title="角色详情">
          <a-descriptions :column="2" bordered size="small">
            <a-descriptions-item label="角色编码">
              {{ selectedRole.roleCode }}
            </a-descriptions-item>
            <a-descriptions-item label="角色名称">
              {{ selectedRole.roleName }}
            </a-descriptions-item>
            <a-descriptions-item label="描述" :span="2">
              {{ selectedRole.description || '-' }}
            </a-descriptions-item>
          </a-descriptions>

          <a-divider />

          <div class="permissions-section">
            <div class="section-header">
              <span>权限配置</span>
              <a-button type="primary" size="small" @click="savePermissions">
                保存
              </a-button>
            </div>
            <a-checkbox-group v-model:value="selectedPermissionIds">
              <a-row>
                <a-col :span="8" v-for="group in groupedPermissions" :key="group.type">
                  <a-divider orientation="left">{{ group.label }}</a-divider>
                  <a-space direction="vertical" style="width: 100%">
                    <a-checkbox v-for="perm in group.permissions" :key="perm.id" :value="perm.id">
                      {{ perm.permissionName }}
                    </a-checkbox>
                  </a-space>
                </a-col>
              </a-row>
            </a-checkbox-group>
          </div>
        </a-card>
        <a-empty v-else description="请选择一个角色" />
      </a-col>
    </a-row>

    <!-- 新建/编辑角色弹窗 -->
    <a-modal
      :title="isEdit ? '编辑角色' : '新增角色'"
      v-model:open="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      width="500px"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="角色编码" name="roleCode" :rules="[{ required: true }]">
          <a-input v-model:value="formState.roleCode" placeholder="请输入" :disabled="isEdit" />
        </a-form-item>
        <a-form-item label="角色名称" name="roleName" :rules="[{ required: true }]">
          <a-input v-model:value="formState.roleName" placeholder="请输入" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="formState.description" :rows="3" placeholder="请输入" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const modalVisible = ref(false)
const modalLoading = ref(false)
const isEdit = ref(false)
const formRef = ref()

const roles = ref<any[]>([])
const permissions = ref<any[]>([])
const selectedRole = ref<any>(null)
const selectedPermissionIds = ref<number[]>([])

const formState = reactive({
  id: undefined as number | undefined,
  roleCode: '',
  roleName: '',
  description: ''
})

const groupedPermissions = computed(() => {
  const groups: Record<string, any> = {}
  const typeLabels: Record<string, string> = {
    datasource: '数据源管理',
    masking: '数据脱敏',
    lineage: '血缘分析',
    sync: '翻数工具',
    system: '系统管理'
  }

  permissions.value.forEach(p => {
    const type = p.resourceType || 'other'
    if (!groups[type]) {
      groups[type] = {
        type,
        label: typeLabels[type] || type,
        permissions: []
      }
    }
    groups[type].permissions.push(p)
  })

  return Object.values(groups)
})

async function loadRoles() {
  loading.value = true
  try {
    roles.value = await request.get('/system/roles')
  } finally {
    loading.value = false
  }
}

async function loadPermissions() {
  try {
    permissions.value = await request.get('/system/permissions')
  } catch (error) {
    //
  }
}

function selectRole(role: any) {
  selectedRole.value = role
  selectedPermissionIds.value = (role.permissions || []).map((p: any) => p.id)
}

function showCreateModal() {
  isEdit.value = false
  Object.assign(formState, {
    id: undefined,
    roleCode: '',
    roleName: '',
    description: ''
  })
  modalVisible.value = true
}

function showEditModal(role: any) {
  isEdit.value = true
  Object.assign(formState, {
    id: role.id,
    roleCode: role.roleCode,
    roleName: role.roleName,
    description: role.description
  })
  modalVisible.value = true
}

async function handleModalOk() {
  try {
    await formRef.value?.validate()
    modalLoading.value = true

    if (isEdit.value) {
      await request.put(`/system/roles/${formState.id}`, formState)
      message.success('更新成功')
    } else {
      await request.post('/system/roles', formState)
      message.success('创建成功')
    }

    modalVisible.value = false
    loadRoles()
  } finally {
    modalLoading.value = false
  }
}

function handleModalCancel() {
  modalVisible.value = false
}

async function savePermissions() {
  if (!selectedRole.value) return

  try {
    await request.put(`/system/roles/${selectedRole.value.id}/permissions`, {
      roleId: selectedRole.value.id,
      permissionIds: selectedPermissionIds.value
    })
    message.success('保存成功')
    loadRoles()
  } catch (error) {
    //
  }
}

async function deleteRole(id: number) {
  try {
    await request.delete(`/system/roles/${id}`)
    message.success('删除成功')
    if (selectedRole.value?.id === id) {
      selectedRole.value = null
    }
    loadRoles()
  } catch (error) {
    //
  }
}

onMounted(() => {
  loadRoles()
  loadPermissions()
})
</script>

<style scoped>
.roles-page {
  height: 100%;
}

:deep(.ant-list-item) {
  cursor: pointer;
}

:deep(.ant-list-item:hover) {
  background: #f5f5f5;
}

:deep(.ant-list-item.active) {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.permissions-section {
  margin-top: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
