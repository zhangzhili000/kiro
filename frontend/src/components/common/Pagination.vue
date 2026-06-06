<template>
  <div class="pagination">
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 20
  },
  total: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:page', 'update:pageSize', 'change'])

const currentPage = computed({
  get: () => props.page,
  set: (val) => emit('update:page', val)
})

const currentPageSize = computed({
  get: () => props.pageSize,
  set: (val) => emit('update:pageSize', val)
})

const handleSizeChange = (val) => {
  emit('change', { page: currentPage.value, pageSize: val })
}

const handleCurrentChange = (val) => {
  emit('change', { page: val, pageSize: currentPageSize.value })
}
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: flex-end;
  padding: 15px 0;
}
</style>
