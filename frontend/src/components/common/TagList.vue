<template>
  <div class="tag-list">
    <el-tag
      v-for="tag in tags"
      :key="tag.id"
      :color="tag.color"
      : closable="closable"
      :disable-transitions="false"
      @close="handleClose(tag)"
    >
      {{ tag.name }}
    </el-tag>
    <el-input
      v-if="inputVisible"
      ref="InputRef"
      v-model="inputValue"
      size="small"
      class="tag-input"
      @keyup.enter="handleInputConfirm"
      @blur="handleInputConfirm"
    />
    <el-button v-else-if="addable" class="add-tag-btn" size="small" @click="showInput">
      + New Tag
    </el-button>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({
  tags: {
    type: Array,
    default: () => []
  },
  closable: {
    type: Boolean,
    default: false
  },
  addable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:tags', 'add', 'remove'])

const inputVisible = ref(false)
const inputValue = ref('')
const InputRef = ref(null)

const handleClose = (tag) => {
  emit('remove', tag)
}

const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    InputRef.value?.focus()
  })
}

const handleInputConfirm = () => {
  if (inputValue.value) {
    emit('add', inputValue.value)
  }
  inputVisible.value = false
  inputValue.value = ''
}
</script>

<style scoped>
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tag-input {
  width: 100px;
}

.add-tag-btn {
  height: 24px;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
