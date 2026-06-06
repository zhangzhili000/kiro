<template>
  <div class="confirm-dialog">
    <el-button type="danger" plain @click="handleClick">
      {{ text }}
    </el-button>
  </div>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'

const props = defineProps({
  text: {
    type: String,
    default: '删除'
  },
  title: {
    type: String,
    default: '确认操作'
  },
  message: {
    type: String,
    default: '确定要执行此操作吗？此操作不可恢复！'
  },
  confirmText: {
    type: String,
    default: '确定'
  },
  cancelText: {
    type: String,
    default: '取消'
  }
})

const emit = defineEmits(['confirm'])

const handleClick = async () => {
  try {
    await ElMessageBox.confirm(props.message, props.title, {
      confirmButtonText: props.confirmText,
      cancelButtonText: props.cancelText,
      type: 'warning'
    })
    emit('confirm')
  } catch (error) {
  }
}
</script>

<style scoped>
.confirm-dialog {
  display: inline-block;
}
</style>
