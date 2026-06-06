<template>
  <div class="tag-manage">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>标签管理</span>
          <el-button type="primary" @click="showDialog = true">新建标签</el-button>
        </div>
      </template>

      <el-table :data="tags" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="color" label="颜色" width="120">
          <template #default="{ row }">
            <el-tag :color="row.color" effect="dark">{{ row.color }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" :title="editingTag ? '编辑标签' : '新建标签'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" />
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
import { useTagStore } from '@/stores/tag'
import { ElMessage } from 'element-plus'

const tagStore = useTagStore()
const tags = ref([])
const showDialog = ref(false)
const editingTag = ref(null)

const form = reactive({
  name: '',
  color: '#409eff'
})

const fetchTags = async () => {
  await tagStore.fetchTags()
  tags.value = tagStore.tags
}

const handleEdit = (tag) => {
  editingTag.value = tag
  form.name = tag.name
  form.color = tag.color || '#409eff'
  showDialog.value = true
}

const handleSave = async () => {
  try {
    if (editingTag.value) {
      await tagStore.updateTag(editingTag.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await tagStore.createTag(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    editingTag.value = null
    fetchTags()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleDelete = async (id) => {
  try {
    await tagStore.deleteTag(id)
    ElMessage.success('删除成功')
    fetchTags()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(fetchTags)
</script>

<style scoped>
.tag-manage {
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
