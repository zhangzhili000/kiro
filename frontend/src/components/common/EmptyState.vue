<template>
  <div class="empty-state">
    <el-empty :description="description" :image-size="imageSize">
      <slot></slot>
    </el-empty>
  </div>
</template>

<script setup>
defineProps({
  description: {
    type: String,
    default: '暂无数据'
  },
  imageSize: {
    type: Number,
    default: 100
  }
})
</script>

<style scoped>
.empty-state {
  padding: 40px 0;
}
</style>
