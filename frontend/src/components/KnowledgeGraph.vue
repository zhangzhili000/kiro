<template>
  <div class="knowledge-graph-container">
    <div class="graph-header">
      <h2>知识图谱</h2>
      <div class="graph-controls">
        <el-input
          v-model="searchQuery"
          placeholder="搜索节点..."
          class="search-input"
          @keyup.enter="searchNode"
        />
        <el-select v-model="centralNodeId" placeholder="选择中心节点">
          <el-option
            v-for="node in nodeOptions"
            :key="node.value"
            :label="node.label"
            :value="node.value"
          />
        </el-select>
        <el-button @click="refreshGraph">刷新图谱</el-button>
      </div>
    </div>
    
    <div ref="graphCanvas" class="graph-canvas">
      <svg :width="canvasWidth" :height="canvasHeight">
        <defs>
          <marker
            v-for="relType in relationTypes"
            :key="relType"
            :id="`arrow-${relType}`"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L0,6 L9,3 z" :fill="getRelationColor(relType)" />
          </marker>
        </defs>
        
        <!-- 连线 -->
        <g class="edges">
          <line
            v-for="(edge, index) in edges"
            :key="'edge-' + index"
            :x1="getNodePosition(edge.source_node_id).x"
            :y1="getNodePosition(edge.source_node_id).y"
            :x2="getNodePosition(edge.target_node_id).x"
            :y2="getNodePosition(edge.target_node_id).y"
            :stroke="getRelationColor(edge.relation_type)"
            stroke-width="2"
            :marker-end="`url(#arrow-${edge.relation_type})`"
            class="edge-line"
          />
          <text
            v-for="(edge, index) in edges"
            :key="'label-' + index"
            :x="(getNodePosition(edge.source_node_id).x + getNodePosition(edge.target_node_id).x) / 2"
            :y="(getNodePosition(edge.source_node_id).y + getNodePosition(edge.target_node_id).y) / 2 - 5"
            fill="#666"
            font-size="12"
            text-anchor="middle"
            class="edge-label"
          >
            {{ getRelationLabel(edge.relation_type) }}
          </text>
        </g>
        
        <!-- 节点 -->
        <g
          v-for="node in nodes"
          :key="'node-' + node.id"
          class="node-group"
          :class="{ 'node-selected': selectedNode?.id === node.id }"
          @click="selectNode(node)"
          @mousedown="startDrag($event, node)"
        >
          <circle
            :cx="getNodePosition(node.id).x"
            :cy="getNodePosition(node.id).y"
            :r="getNodeSize(node)"
            :fill="getNodeColor(node)"
            class="node-circle"
          />
          <text
            :x="getNodePosition(node.id).x"
            :y="getNodePosition(node.id).y + getNodeSize(node) + 15"
            fill="#333"
            font-size="12"
            text-anchor="middle"
            class="node-label"
          >
            {{ truncateTitle(node.title) }}
          </text>
        </g>
      </svg>
    </div>
    
    <div v-if="selectedNode" class="node-detail-panel">
      <div class="panel-header">
        <h3>{{ selectedNode.title }}</h3>
        <el-button @click="selectedNode = null">关闭</el-button>
      </div>
      <div class="panel-content">
        <p><strong>类型：</strong>{{ getNodeTypeLabel(selectedNode.node_type) }}</p>
        <p v-if="selectedNode.description"><strong>描述：</strong>{{ selectedNode.description }}</p>
        <p v-if="selectedNode.document_id"><strong>关联文档：</strong>{{ selectedNode.document_id }}</p>
        <div class="panel-actions">
          <el-button @click="viewDocument(selectedNode)">查看文档</el-button>
          <el-button @click="expandNode(selectedNode)">展开关联</el-button>
        </div>
      </div>
    </div>
    
    <div class="legend">
      <div class="legend-title">图例</div>
      <div v-for="(color, type) in nodeTypeColors" :key="type" class="legend-item">
        <span class="legend-color" :style="{ backgroundColor: color }"></span>
        <span>{{ getNodeTypeLabel(type) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>import { ref, reactive, onMounted, computed, watch } from 'vue';
import { getKnowledgeGraphData, getNodeDetail, recommendDocuments } from '@/api/knowledgeGraph';
const graphCanvas = ref(null);
const canvasWidth = ref(1000);
const canvasHeight = ref(600);
const nodes = ref([]);
const edges = ref([]);
const selectedNode = ref(null);
const searchQuery = ref('');
const centralNodeId = ref(null);
const nodePositions = reactive({});
const draggingNode = ref(null);
const dragOffset = reactive({ x: 0, y: 0 });
const nodeTypeColors = {
 document: '#42b983',
 concept: '#3b82f6',
 entity: '#f59e0b',
 event: '#ef4444'
};
const relationTypes = ['related_to', 'contains', 'references', 'derived_from', 'similar_to'];
const relationColors = {
 related_to: '#9ca3af',
 contains: '#10b981',
 references: '#3b82f6',
 derived_from: '#8b5cf6',
 similar_to: '#f59e0b'
};
const relationLabels = {
 related_to: '相关',
 contains: '包含',
 references: '引用',
 derived_from: '派生',
 similar_to: '相似'
};
const nodeOptions = computed(() => {
 return nodes.value.map(node => ({
 value: node.id,
 label: node.title
 }));
});
const getNodePosition = (nodeId) => {
 return nodePositions[nodeId] || { x: canvasWidth.value / 2, y: canvasHeight.value / 2 };
};
const getNodeColor = (node) => {
 return nodeTypeColors[node.node_type] || '#6b7280';
};
const getNodeSize = (node) => {
 return node.node_type === 'document' ? 25 : 20;
};
const getRelationColor = (relType) => {
 return relationColors[relType] || '#9ca3af';
};
const getRelationLabel = (relType) => {
 return relationLabels[relType] || relType;
};
const getNodeTypeLabel = (type) => {
 const labels = {
 document: '文档',
 concept: '概念',
 entity: '实体',
 event: '事件'
 };
 return labels[type] || type;
};
const truncateTitle = (title) => {
 return title.length > 10 ? title.slice(0, 10) + '...' : title;
};
const refreshGraph = async () => {
 await loadGraphData();
};
const loadGraphData = async () => {
 try {
 const params = centralNodeId.value ? { central_node_id: centralNodeId.value } : {};
 const response = await getKnowledgeGraphData(params);
 nodes.value = response.nodes;
 edges.value = response.edges;
 // 初始化节点位置（力导向布局）
 initializeLayout();
 }
 catch (error) {
 console.error('加载图谱数据失败:', error);
 }
};
const initializeLayout = () => {
 const centerX = canvasWidth.value / 2;
 const centerY = canvasHeight.value / 2;
 const radius = 150;
 nodes.value.forEach((node, index) => {
 const angle = (index / nodes.value.length) * Math.PI * 2;
 nodePositions[node.id] = {
 x: centerX + Math.cos(angle) * radius * (1 + Math.random() * 0.3),
 y: centerY + Math.sin(angle) * radius * (1 + Math.random() * 0.3)
 };
 });
};
const selectNode = (node) => {
 selectedNode.value = node;
};
const searchNode = async () => {
 if (!searchQuery.value)
 return;
 const found = nodes.value.find(n => n.title.toLowerCase().includes(searchQuery.value.toLowerCase()));
 if (found) {
 selectedNode.value = found;
 }
};
const viewDocument = (node) => {
 if (node.document_id) {
 window.open(`/documents/${node.document_id}`, '_blank');
 }
};
const expandNode = async (node) => {
 centralNodeId.value = node.id;
 await loadGraphData();
};
const startDrag = (event, node) => {
 draggingNode.value = node;
 const rect = graphCanvas.value.getBoundingClientRect();
 dragOffset.x = event.clientX - rect.left - nodePositions[node.id].x;
 dragOffset.y = event.clientY - rect.top - nodePositions[node.id].y;
 document.addEventListener('mousemove', onDrag);
 document.addEventListener('mouseup', stopDrag);
};
const onDrag = (event) => {
 if (!draggingNode.value || !graphCanvas.value)
 return;
 const rect = graphCanvas.value.getBoundingClientRect();
 nodePositions[draggingNode.value.id] = {
 x: event.clientX - rect.left - dragOffset.x,
 y: event.clientY - rect.top - dragOffset.y
 };
};
const stopDrag = () => {
 draggingNode.value = null;
 document.removeEventListener('mousemove', onDrag);
 document.removeEventListener('mouseup', stopDrag);
};
watch(centralNodeId, async () => {
 await loadGraphData();
});
onMounted(() => {
 loadGraphData();
});
</script>

<style scoped>
.knowledge-graph-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.graph-header h2 {
  margin: 0;
  font-size: 18px;
}

.graph-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 200px;
}

.graph-canvas {
  flex: 1;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
  position: relative;
}

.graph-canvas svg {
  display: block;
}

.node-group {
  cursor: pointer;
  transition: opacity 0.2s;
}

.node-group:hover {
  opacity: 0.8;
}

.node-circle {
  transition: r 0.2s, fill 0.2s;
}

.node-group:hover .node-circle {
  r: 30;
}

.node-selected .node-circle {
  stroke: #3b82f6;
  stroke-width: 3;
}

.edge-line {
  transition: stroke 0.2s;
}

.edge-line:hover {
  stroke-width: 3;
}

.node-detail-panel {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 300px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 100;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #3b82f6;
  color: #fff;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
}

.panel-content {
  padding: 16px;
}

.panel-content p {
  margin: 8px 0;
  font-size: 13px;
  color: #666;
}

.panel-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}

.legend {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(255, 255, 255, 0.95);
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.legend-title {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
</style>
