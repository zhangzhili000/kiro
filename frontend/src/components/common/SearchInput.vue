<template>
  <div class="search-input">
    <el-input
      v-model="keyword"
      :placeholder="placeholder"
      :prefix-icon="Search"
      clearable
      @keyup.enter="handleSearch"
      @input="handleInput"
    >
      <template #append v-if="showButton">
        <el-button :icon="Search" @click="handleSearch" />
      </template>
    </el-input>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '搜索...'
  },
  showButton: {
    type: Boolean,
    default: true
  },
  debounce: {
    type: Boolean,
    default: false
  },
  debounceTime: {
    type: Number,
    default: 300
  }
})

const emit = defineEmits(['update:modelValue', 'search'])

const keyword = ref(props.modelValue)
let debounceTimer = null

const handleInput = () => {
  if (props.debounce) {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      emit('update:modelValue', keyword.value)
    }, props.debounceTime)
  } else {
    emit('update:modelValue', keyword.value)
  }
}

const handleSearch = () => {
  clearTimeout(debounceTimer)
  emit('update:modelValue', keyword.value)
  emit('search', keyword.value)
}
</script>

<style scoped>
.search-input {
  width: 100%;
  max-width: 400px;
}
</style>
