<template>
  <div class="category-manage">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>分类管理</span>
          <el-button type="primary" @click="showDialog = true">新建分类</el-button>
        </div>
      </template>

      <el-table :data="categories" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="parent_id" label="父分类" width="120">
          <template #default="{ row }">
            {{ getParentName(row.parent_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" :title="editingCategory ? '编辑分类' : '新建分类'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="父分类">
          <el-select v-model="form.parent_id" placeholder="请选择父分类" clearable>
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
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
import { useCategoryStore } from '@open/stores/category'
import { ElMessage } from 'element-plus'

const categoryStore = useCategoryStore()
const categories = ref([])
const showDialog = ref(false)
const editingCategory = ref(null)

const form = reactive({
  name: '',
  description: '',
  parent_id: null,
  sort_order: 0
})

const fetchCategories = async () => {
  await categoryStore.fetchCategories()
  categories.value = categoryStore.categories
}

const getParentName = (parentId) => {
  if (!parentId) return '无'
  const parent = categories.value.find(c => c.id === parentId)
  return parent ? parent.name : '无'
}

const handleEdit = (category) => {
  editingCategory.value = category
  form.name = category.name
  form.description = category.description
  form.parent_id = category.parent_id
  form.sort_order = category.sort_order
  showDialog.value = true
}

const handleSave = async () => {
  try {
    if (editingCategory.value) {
      await categoryStore.updateCategory(editingCategory.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await categoryStore.createCategory(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    editingCategory.value = null
    fetchCategories()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleDelete = async (id) => {
  try {
    await categoryStore.deleteCategory(id)
    ElMessage.success('删除成功')
    fetchCategories()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(fetchCategories)
</script>

<style scoped>
.category-manage {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
