<template>
  <div class="knowledge-graph">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>知识图谱</span>
          <div class="controls">
            <div class="checkbox-group">
              <el-checkbox v-model="selectAll" @change="handleSelectAll">全部</el-checkbox>
              <el-checkbox-group v-model="selectedNodeTypes">
                <el-checkbox label="document">文档</el-checkbox>
                <el-checkbox label="category">分类</el-checkbox>
                <el-checkbox label="tag">标签</el-checkbox>
                <el-checkbox label="user">用户</el-checkbox>
              </el-checkbox-group>
            </div>
            <el-button @click="handleRefresh" :loading="loading">刷新</el-button>
            <el-button @click="handleResetZoom">重置视图</el-button>
          </div>
        </div>
      </template>

      <div class="graph-container" ref="graphContainer">
        <svg ref="svgRef" width="100%" height="600"></svg>
      </div>

      <div class="legend">
        <div class="legend-item">
          <span class="legend-color document"></span>
          <span>文档</span>
        </div>
        <div class="legend-item">
          <span class="legend-color category"></span>
          <span>分类</span>
        </div>
        <div class="legend-item">
          <span class="legend-color tag"></span>
          <span>标签</span>
        </div>
        <div class="legend-item">
          <span class="legend-color user"></span>
          <span>用户</span>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="nodeDetailVisible" :title="`节点详情 - ${selectedNode?.label}`" width="500px">
      <div v-if="selectedNode" class="node-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="类型">{{ selectedNode.type }}</el-descriptions-item>
          <el-descriptions-item label="ID">{{ selectedNode.id }}</el-descriptions-item>
          <el-descriptions-item v-for="(value, key) in selectedNode.properties" :key="key" :label="key">
            {{ value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as d3 from 'd3'
import request from '@open/api/request'

const graphContainer = ref(null)
const svgRef = ref(null)
const loading = ref(false)
const selectAll = ref(true)
const selectedNodeTypes = ref(['document', 'category', 'tag', 'user'])
const nodeDetailVisible = ref(false)
const selectedNode = ref(null)
const currentScale = ref(1)

let svg = null
let g = null
let zoom = null
let simulation = null
let scaleBarLabels = null

const nodeColors = {
  document: '#409eff',
  category: '#67c23a',
  tag: '#e6a23c',
  user: '#f56c6c'
}

const fetchGraphData = async () => {
  loading.value = true
  try {
    const data = await request.get('/knowledge-graph')
    return data
  } catch (error) {
    ElMessage.error('获取图谱数据失败')
    return null
  } finally {
    loading.value = false
  }
}

const renderGraph = (data) => {
  if (!data || !svgRef.value) return

  const width = svgRef.value.clientWidth
  const height = 600

  svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  svg.selectAll('*').remove()

  g = svg.append('g')

  zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
      currentScale.value = event.transform.k
      updateScaleBar(event.transform.k)
    })

  svg.call(zoom)

  simulation = d3.forceSimulation(data.nodes)
    .force('link', d3.forceLink(data.edges).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(30))

  const link = g.append('g')
    .selectAll('line')
    .data(data.edges)
    .enter()
    .append('line')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', 1)

  const node = g.append('g')
    .selectAll('g')
    .data(data.nodes)
    .enter()
    .append('g')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))

  node.append('circle')
    .attr('r', 20)
    .attr('fill', d => nodeColors[d.type] || '#999')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .on('click', (event, d) => {
      event.stopPropagation()
      selectedNode.value = d
      nodeDetailVisible.value = true
    })

  node.append('text')
    .attr('dy', -25)
    .attr('text-anchor', 'middle')
    .text(d => d.label)
    .attr('font-size', '12px')
    .attr('fill', '#333')
    .style('pointer-events', 'none')

  const tickCount = ref(0)
  simulation.on('tick', () => {
    tickCount.value++
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    node.attr('transform', d => `translate(${d.x},${d.y})`)

    if (tickCount.value === 100) {
      simulation.stop()
      fitToScreen(data, width, height)
    }
  })

  addScaleBar(width, height)

  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }

  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }
}

const fitToScreen = (data, width, height) => {
  if (!data.nodes || data.nodes.length === 0) return

  const padding = 50
  const bounds = d3.extent(data.nodes, d => d.x)
  const xRange = bounds[1] - bounds[0] || 100
  const yBounds = d3.extent(data.nodes, d => d.y)
  const yRange = yBounds[1] - yBounds[0] || 100

  const scaleX = (width - padding * 2) / xRange
  const scaleY = (height - padding * 2) / yRange
  const scale = Math.min(scaleX, scaleY, 1)

  const centerX = (bounds[0] + bounds[1]) / 2
  const centerY = (yBounds[0] + yBounds[1]) / 2

  const transform = d3.zoomIdentity
    .translate(width / 2, height / 2)
    .scale(scale)
    .translate(-centerX, -centerY)

  svg.transition().duration(500).call(zoom.transform, transform)
}

const addScaleBar = (width, height) => {
  const scaleBarHeight = 20
  const scaleBarWidth = 100
  const scaleBarX = width - scaleBarWidth - 20
  const scaleBarY = height - scaleBarHeight - 20

  const scaleBar = svg.append('g')
    .attr('class', 'scale-bar')
    .attr('transform', `translate(${scaleBarX}, ${scaleBarY})`)
    .style('pointer-events', 'none')

  scaleBar.append('rect')
    .attr('width', scaleBarWidth)
    .attr('height', 4)
    .attr('fill', '#666')

  scaleBar.append('rect')
    .attr('width', scaleBarWidth)
    .attr('height', 1)
    .attr('y', -6)
    .attr('fill', '#666')

  scaleBar.append('rect')
    .attr('width', 1)
    .attr('height', 8)
    .attr('y', -6)
    .attr('fill', '#666')

  scaleBar.append('rect')
    .attr('width', 1)
    .attr('height', 8)
    .attr('x', scaleBarWidth / 2)
    .attr('y', -6)
    .attr('fill', '#666')

  scaleBar.append('rect')
    .attr('width', 1)
    .attr('height', 8)
    .attr('x', scaleBarWidth)
    .attr('y', -6)
    .attr('fill', '#666')

  scaleBarLabels = {
    left: scaleBar.append('text')
      .attr('x', 0)
      .attr('y', -8)
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .text('0'),
    middle: scaleBar.append('text')
      .attr('x', scaleBarWidth / 2)
      .attr('y', -8)
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .attr('text-anchor', 'middle')
      .text('50'),
    right: scaleBar.append('text')
      .attr('x', scaleBarWidth)
      .attr('y', -8)
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .attr('text-anchor', 'middle')
      .text('100'),
    unit: scaleBar.append('text')
      .attr('x', scaleBarWidth / 2)
      .attr('y', 15)
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .attr('text-anchor', 'middle')
      .text('单位: 像素')
  }
}

const updateScaleBar = (scale) => {
  if (!scaleBarLabels) return
  
  const actualLength = Math.round(100 / scale)
  const halfLength = Math.round(actualLength / 2)
  
  scaleBarLabels.left.text('0')
  scaleBarLabels.middle.text(halfLength.toString())
  scaleBarLabels.right.text(actualLength.toString())
}

const handleRefresh = async () => {
  const data = await fetchGraphData()
  if (data) {
    renderGraph(data)
  }
}

const handleResetZoom = () => {
  if (svg && zoom) {
    svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity)
  }
}

const handleSelectAll = (val) => {
  if (val) {
    selectedNodeTypes.value = ['document', 'category', 'tag', 'user']
  } else {
    selectedNodeTypes.value = []
  }
}

watch(selectedNodeTypes, async (newTypes) => {
  const data = await fetchGraphData()
  if (data && newTypes.length > 0) {
    const filteredNodes = data.nodes.filter(n => newTypes.includes(n.type))
    const nodeIds = new Set(filteredNodes.map(n => n.id))
    const filteredEdges = data.edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))
    renderGraph({ nodes: filteredNodes, edges: filteredEdges })
  } else if (data) {
    renderGraph(data)
  }
}, { deep: true })

onMounted(async () => {
  const data = await fetchGraphData()
  if (data) {
    renderGraph(data)
  }
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
  }
})
</script>

<style scoped>
.knowledge-graph {
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.graph-container {
  width: 100%;
  height: 600px;
  border: 1px solid #e6e6e6;
  border-radius: 4px;
  overflow: hidden;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-top: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
}

.legend-color.document {
  background: #409eff;
}

.legend-color.category {
  background: #67c23a;
}

.legend-color.tag {
  background: #e6a23c;
}

.legend-color.user {
  background: #f56c6c;
}

.node-detail {
  padding: 10px;
}
</style>