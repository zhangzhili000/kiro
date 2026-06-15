<template>
  <div class="department-manage">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>部门管理</span>
          <el-button type="primary" @click="showDialog = true">新建部门</el-button>
        </div>
      </template>

      <el-tree :data="departmentTree" :props="treeProps" default-expand-all>
        <template #default="{ node, data }">
          <span class="tree-node">
            <span>{{ node.label }}</span>
            <span class="tree-actions">
              <el-button size="small" @click.stop="handleEdit(data)">编辑</el-button>
              <el-button size="small" type="danger" @click.stop="handleDelete(data.id)">删除</el-button>
            </span>
          </span>
        </template>
      </el-tree>
    </el-card>

    <el-dialog v-model="showDialog" :title="editingDepartment ? '编辑部门' : '新建部门'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="父部门">
          <el-select v-model="form.parent_id" placeholder="请选择父部门" clearable>
            <el-option 
              v-for="dept in departments" 
              :key="dept.id" 
              :label="dept.name" 
              :value="dept.id"
              :disabled="editingDepartment && dept.id === editingDepartment.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useDepartmentStore } from '@/stores/department'
import { ElMessage } from 'element-plus'

const departmentStore = useDepartmentStore()
const departments = ref([])
const departmentTree = ref([])
const showDialog = ref(false)
const editingDepartment = ref(null)

const form = reactive({
  name: '',
  description: '',
  parent_id: null
})

const treeProps = {
  children: 'children',
  label: 'name'
}

const fetchDepartments = async () => {
  await departmentStore.fetchDepartments()
  await departmentStore.fetchDepartmentTree()
  departments.value = departmentStore.departments
  departmentTree.value = departmentStore.departmentTree
}

const handleEdit = (dept) => {
  editingDepartment.value = dept
  form.name = dept.name
  form.description = dept.description
  form.parent_id = dept.parent_id
  showDialog.value = true
}

const handleSave = async () => {
  try {
    if (editingDepartment.value) {
      await departmentStore.updateDepartment(editingDepartment.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await departmentStore.createDepartment(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    editingDepartment.value = null
    fetchDepartments()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleDelete = async (id) => {
  try {
    await departmentStore.deleteDepartment(id)
    ElMessage.success('删除成功')
    fetchDepartments()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(fetchDepartments)
</script>

<style scoped>
.department-manage {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.tree-actions {
  display: flex;
  gap: 5px;
}
</style>
