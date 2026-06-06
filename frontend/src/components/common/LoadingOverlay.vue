<template>
  <div class="loading-overlay" v-if="loading">
    <el-icon class="loading-icon" :size="size">
      <Loading />
    </el-icon>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'

defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  size: {
    type: Number,
    default: 30
  },
  text: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  z-index: 1000;
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

.loading-text {
  margin-top: 10px;
  color: #666;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
