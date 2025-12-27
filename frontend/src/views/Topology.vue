<template>
  <div class="topology-container">
    <div class="topology-header">
      <h2>网络拓扑</h2>
      <div class="actions">
        <el-button type="primary" @click="refreshTopology" :loading="loading">刷新</el-button>
        <el-button @click="autoLayout" :disabled="!d3Loaded">自动布局</el-button>
        <el-button @click="resetView" :disabled="!d3Loaded">重置视图</el-button>
        <el-button @click="autoRefreshTopology" :type="autoRefresh ? 'danger' : 'default'">
          {{ autoRefresh ? '停止自动刷新' : '自动刷新' }}
        </el-button>
      </div>
    </div>
    

    
    <div class="topology-main">
      <div class="topology-content">
        <div ref="topologyCanvas" class="topology-canvas">
          <div v-if="!d3Loaded && loading" class="loading-placeholder">
            <el-skeleton animated>
              <template #template>
                <el-skeleton-item variant="rect" style="width: 100%; height: 500px;" />
              </template>
            </el-skeleton>
          </div>
          
          <!-- 添加数据加载提示 -->
          <div v-if="d3Loaded && devices.length === 0" class="no-data-tip">
            <el-alert
              title="暂无设备数据"
              description="正在收集网络设备信息，请稍后刷新查看..."
              type="info"
              show-icon
              :closable="false"
            />
          </div>
          
          <div v-show="d3Loaded && devices.length > 0" class="topology-controls">
            <el-button-group>
              <el-button @click="zoomIn" :icon="Plus" circle size="small" title="放大"></el-button>
              <el-button @click="zoomOut" :icon="Minus" circle size="small" title="缩小"></el-button>
              <el-button @click="resetView" :icon="Refresh" circle size="small" title="重置视图"></el-button>
            </el-button-group>
          </div>
        </div>
      </div>
      
      <div class="topology-sidebar">
        <el-tabs type="border-card">
          <el-tab-pane label="设备列表">
            <div class="device-filter">
              <el-input
                v-model="deviceFilter"
                placeholder="搜索设备..."
                clearable
                size="small"
                @input="filterDevices"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
            
            <!-- 添加设备列表加载状态 -->
            <div v-if="loading && filteredDevices.length === 0" class="device-list-loading">
              <el-skeleton animated>
                <template #template>
                  <el-skeleton-item variant="text" style="width: 80%; margin-bottom: 10px;" />
                  <el-skeleton-item variant="text" style="width: 60%; margin-bottom: 10px;" />
                  <el-skeleton-item variant="text" style="width: 90%; margin-bottom: 10px;" />
                </template>
              </el-skeleton>
            </div>
            
            <el-table 
              v-else
              :data="filteredDevices" 
              style="width: 100%" 
              max-height="350"
              :empty-text="loading ? '加载中...' : '暂无设备数据'"
            >
              <el-table-column prop="name" label="设备名称" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="device-name" @click="highlightDevice(row.id)">{{ row.name }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="management_ip" label="管理IP" width="120" />
              <el-table-column prop="vendor" label="厂商" width="100" />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          
          <el-tab-pane label="连接详情">
            <div v-if="links.length === 0" class="no-links">
              <el-empty description="暂无连接信息" />
            </div>
            <el-table v-else :data="links" style="width: 100%" max-height="350">
              <el-table-column prop="source_interface" label="源接口" />
              <el-table-column prop="target_interface" label="目标接口" />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'up' ? 'success' : 'danger'">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          
        </el-tabs>
            <!-- 添加统计信息展示 -->
    <div class="topology-stats" v-if="devices.length > 0 || links.length > 0">
      <el-card class="stat-card">
        <div class="stat-item">
          <span class="stat-label">设备总数:</span>
          <span class="stat-value">{{ devices.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">连接数:</span>
          <span class="stat-value">{{ links.length }}</span>
        </div>
      </el-card>
    </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, onBeforeUnmount, onUnmounted } from 'vue'
import { ElMessage, ElEmpty, ElSkeleton, ElSkeletonItem } from 'element-plus'
import { Search, Plus, Minus, Refresh, ArrowRight } from '@element-plus/icons-vue'
import { 
  getTopologyDevices, 
  getTopologyLinks, 
  refreshTopology as refreshTopologyApi 
} from '@/api/topology'

const topologyCanvas = ref(null)
const loading = ref(false)
const d3Loaded = ref(false)
const deviceFilter = ref('')

// 设备数据
const devices = ref([])
const filteredDevices = ref([])
const links = ref([])

// D3相关变量
let svg = null
let g = null
let simulation = null
let d3 = null
let zoom = null

// 计算在线设备数量
const onlineDevicesCount = computed(() => {
  return devices.value.filter(device => device.status === 'online').length
})

// 获取设备状态类型
const getStatusType = (status) => {
  const statusMap = {
    'online': 'success',
    'offline': 'danger',
    'warning': 'warning',
    'unknown': 'info'
  }
  return statusMap[status] || 'info'
}

// 获取设备状态文本
const getStatusText = (status) => {
  const statusMap = {
    'online': '在线',
    'offline': '离线',
    'warning': '警告',
    'unknown': '未知'
  }
  return statusMap[status] || status
}

// 根据设备ID获取设备名称
const getDeviceNameById = (id) => {
  if (!id) return '未知设备'
  const device = devices.value.find(d => d.id === id)
  return device ? device.name : '未知设备'
}

// 过滤设备
const filterDevices = () => {
  if (!deviceFilter.value) {
    filteredDevices.value = [...devices.value]
  } else {
    filteredDevices.value = devices.value.filter(device => 
      device.name.toLowerCase().includes(deviceFilter.value.toLowerCase()) ||
      device.management_ip.includes(deviceFilter.value)
    )
  }
}

// 高亮设备
const highlightDevice = (deviceId) => {
  if (!d3 || !g) return
  
  // 移除之前的高亮
  g.selectAll('.node').classed('highlighted', false)
  g.selectAll('.link').classed('highlighted', false)
  
  // 高亮选中的设备
  g.selectAll(`.node-${deviceId}`).classed('highlighted', true)
  
  // 高亮连接到该设备的连线
  g.selectAll('.link')
    .filter(d => d.source.id === deviceId || d.target.id === deviceId)
    .classed('highlighted', true)
}

// 初始化D3拓扑图
const initTopology = async () => {
  // 如果已经初始化过，先清理
  cleanupTopology()
  
  if (!topologyCanvas.value) return

  // 动态导入D3.js
  try {
    d3 = await import('d3')
    d3Loaded.value = true
  } catch (error) {
    console.error('D3.js 加载失败:', error)
    ElMessage.error('拓扑图库加载失败，请检查网络连接或联系管理员')
    return
  }

  // 清空画布
  topologyCanvas.value.innerHTML = ''

  const width = topologyCanvas.value.clientWidth
  const height = topologyCanvas.value.clientHeight

  // 创建SVG元素
  svg = d3.select(topologyCanvas.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  // 创建缩放行为
  zoom = d3.zoom()
    .scaleExtent([0.1, 5])
    .on('zoom', (event) => {
      if (g) {
        g.attr('transform', event.transform)
      }
    })

  // 应用缩放行为到SVG
  svg.call(zoom)

  // 创建包含所有元素的组
  g = svg.append('g')

  // 创建连线容器
  const linkGroup = g.append('g').attr('class', 'links')
  // 创建节点容器
  const nodeGroup = g.append('g').attr('class', 'nodes')

  // 创建力导向图模拟
  simulation = d3.forceSimulation(devices.value)
    .force('link', d3.forceLink(links.value).id(d => d.id).distance(150))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(60))

  // 绘制连线
  const linkElements = linkGroup.selectAll('line')
    .data(links.value)
    .enter()
    .append('line')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', 2)

  // 绘制节点
  const nodeElements = nodeGroup.selectAll('g')
    .data(devices.value)
    .enter()
    .append('g')
    .attr('class', d => `node node-${d.id}`)
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended)
    )
    .on('click', (event, d) => {
      highlightDevice(d.id)
    })
    .on('mouseover', function(event, d) {
      // 高亮显示连接线
      linkElements
        .filter(link => link.source.id === d.id || link.target.id === d.id)
        .attr('stroke', '#409EFF')
        .attr('stroke-width', 3)
    })
    .on('mouseout', function(event, d) {
      // 恢复连接线样式
      linkElements
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 2)
    })

  // 添加圆形
  nodeElements.append('circle')
    .attr('r', 30)
    .attr('fill', d => {
      const colorMap = {
        'online': '#67C23A',
        'offline': '#F56C6C',
        'warning': '#E6A23C',
        'unknown': '#909399'
      }
      return colorMap[d.status] || '#409EFF'
    })
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('cursor', 'pointer')

  // 添加设备图标（根据设备类型）
  nodeElements.append('text')
    .attr('dy', 5)
    .attr('text-anchor', 'middle')
    .attr('font-family', 'FontAwesome')
    .attr('font-size', '20px')
    .attr('fill', '#fff')
    .text(d => {
      const iconMap = {
        'switch': '\uf234', // fa-server
        'router': '\uf0e8', // fa-sitemap
        'firewall': '\uf132', // fa-shield
        'access_point': '\uf1eb' // fa-wifi
      }
      return iconMap[d.device_type] || '\uf233' // fa-server as default
    })

  // 添加设备名称
  nodeElements.append('text')
    .text(d => d.name)
    .attr('text-anchor', 'middle')
    .attr('dy', 45)
    .attr('font-size', '12px')
    .attr('fill', '#333')
    .attr('font-weight', 'bold')

  // 添加IP地址
  nodeElements.append('text')
    .text(d => d.management_ip)
    .attr('text-anchor', 'middle')
    .attr('dy', 58)
    .attr('font-size', '10px')
    .attr('fill', '#666')

  // 更新位置
  simulation.on('tick', () => {
    if (linkElements) {
      linkElements
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)
    }

    if (nodeElements) {
      nodeElements
        .attr('transform', d => {
          if (typeof d.x !== 'undefined' && typeof d.y !== 'undefined') {
            return `translate(${d.x},${d.y})`
          }
          return ''
        })
    }
  })
}

// 清理拓扑图资源
const cleanupTopology = () => {
  console.log('Cleaning up topology resources...')
  
  try {
    // 停止力导向图模拟
    if (simulation) {
      simulation.stop()
      simulation = null
      console.log('Simulation stopped')
    }
    
    // 移除SVG元素
    if (svg) {
      svg.remove()
      svg = null
      console.log('SVG removed')
    }
    
    // 清空画布
    if (topologyCanvas.value) {
      topologyCanvas.value.innerHTML = ''
      console.log('Canvas cleared')
    }
    
    // 清空引用
    g = null
    d3 = null
    zoom = null
    
    console.log('Topology resources cleaned up successfully')
  } catch (error) {
    console.error('Error cleaning up topology resources:', error)
  }
}

// 拖拽开始
const dragstarted = (event, d) => {
  if (!event.active && simulation) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

// 拖拽中
const dragged = (event, d) => {
  d.fx = event.x
  d.fy = event.y
}

// 拖拽结束
const dragended = (event, d) => {
  if (!event.active && simulation) simulation.alphaTarget(0)
  // 保留固定位置
}

// 自动布局
const autoLayout = () => {
  if (simulation) {
    // 重置所有节点的固定位置
    devices.value.forEach(d => {
      d.fx = null
      d.fy = null
    })
    
    simulation.alpha(0.3).restart()
  }
}

// 放大
const zoomIn = () => {
  if (svg && zoom) {
    svg.transition().duration(300).call(zoom.scaleBy, 1.2)
  }
}

// 缩小
const zoomOut = () => {
  if (svg && zoom) {
    svg.transition().duration(300).call(zoom.scaleBy, 0.8)
  }
}

// 重置视图
const resetView = () => {
  if (svg && zoom) {
    svg.transition().duration(300).call(zoom.translateTo, 0, 0)
    svg.transition().duration(300).call(zoom.scaleTo, 1)
  }
  
  if (simulation) {
    simulation.alpha(0.3).restart()
  }
}

// 刷新拓扑
const refreshTopology = async () => {
  loading.value = true
  try {
    const response = await refreshTopologyApi()
    ElMessage.success(response.data.message || '拓扑数据刷新请求已发送')
    
    // 等待一段时间后重新加载数据
    setTimeout(async () => {
      await loadData()
    }, 5000)
  } catch (error) {
    // 特别处理认证错误
    if (error.response && error.response.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      // 清除本地存储并跳转到登录页
      localStorage.removeItem('access_token')
      localStorage.removeItem('username')
      localStorage.removeItem('systemName')
      if (window.location.hash !== '#/login') {
        window.location.hash = '#/login'
      }
      return
    }
    
    console.error('刷新拓扑失败:', error)
    ElMessage.error(`刷新拓扑失败: ${error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

// 加载数据
const loadData = async () => {
  try {
    // 并行获取设备和连接数据
    const [devicesRes, linksRes] = await Promise.all([
      getTopologyDevices(),
      getTopologyLinks()
    ])

    devices.value = devicesRes.devices || []
    links.value = linksRes.links || []
    
    // 初始化过滤设备列表
    filterDevices()

    // 等待DOM更新后再初始化拓扑图
    await nextTick()
    initTopology()
  } catch (error) {
    // 特别处理认证错误
    if (error.response && error.response.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      // 清除本地存储并跳转到登录页
      localStorage.removeItem('access_token')
      localStorage.removeItem('username')
      localStorage.removeItem('systemName')
      if (window.location.hash !== '#/login') {
        window.location.hash = '#/login'
      }
      return
    }
    
    console.error('加载拓扑数据失败:', error)
    ElMessage.error('加载拓扑数据失败: ' + (error.message || '未知错误'))
  }
}

// 自动刷新相关
const autoRefresh = ref(false)
let autoRefreshInterval = null

// 自动刷新拓扑
const autoRefreshTopology = () => {
  if (autoRefresh.value) {
    // 停止自动刷新
    clearInterval(autoRefreshInterval)
    autoRefreshInterval = null
    autoRefresh.value = false
    ElMessage.info('已停止自动刷新')
  } else {
    // 开始自动刷新
    autoRefresh.value = true
    autoRefreshInterval = setInterval(() => {
      refreshTopology()
    }, 30000) // 每30秒刷新一次
    ElMessage.success('已开启自动刷新，每30秒刷新一次')
  }
}

// 组件销毁前清理资源
onBeforeUnmount(() => {
  console.log('Topology component before unmount')
  cleanupTopology()
  
  // 移除窗口大小变化监听器
  if (typeof window !== 'undefined' && window.handleResize) {
    window.removeEventListener('resize', window.handleResize)
    console.log('Resize listener removed')
  }
})

// 组件卸载时清理资源
onUnmounted(() => {
  cleanupTopology()
  // 清理自动刷新定时器
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
    autoRefreshInterval = null
  }
})

onMounted(() => {
  loadData()
  
  // 监听窗口大小变化
  const handleResize = () => {
    if (simulation && topologyCanvas.value) {
      const width = topologyCanvas.value.clientWidth
      const height = topologyCanvas.value.clientHeight
      
      if (svg) {
        svg.attr('width', width).attr('height', height)
      }
      
      if (simulation) {
        simulation.force('center', d3.forceCenter(width / 2, height / 2))
        simulation.alpha(0.3).restart()
      }
    }
  }
  
  window.addEventListener('resize', handleResize)
  
  // 保存handleResize函数的引用，以便在组件卸载时移除
  window.handleResize = handleResize
})
</script>

<style scoped>
.topology-container {
  padding: 20px;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
}

.topology-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.topology-header h2 {
  margin: 0;
}

.actions {
  display: flex;
  gap: 10px;
}

/* 添加统计信息样式 */
.topology-stats {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: inline-block;
  margin-right: 30px;
}

.stat-label {
  font-weight: bold;
  margin-right: 5px;
  color: #606266;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #409EFF;
}

.topology-main {
  flex: 1;
  display: flex;
  gap: 20px;
}

.topology-content {
  flex: 1;
  position: relative;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.topology-canvas {
  width: 100%;
  height: 100%;
  min-height: 500px;
}

.loading-placeholder {
  padding: 20px;
}

.topology-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.topology-sidebar {
  width: 400px;
  display: flex;
  flex-direction: column;
}

.device-filter {
  margin-bottom: 15px;
}

.device-name {
  color: #409EFF;
  cursor: pointer;
}

.device-name:hover {
  text-decoration: underline;
}

.connections-list {
  max-height: 350px;
  overflow-y: auto;
}

.connection-card {
  margin-bottom: 10px;
}

.connection-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
}

.device {
  font-weight: 500;
}

.interface-info {
  font-size: 12px;
  color: #909399;
  text-align: center;
  margin: 5px 0;
}

.link-status {
  text-align: right;
}

.stats-container {
  padding: 10px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #666;
}

.stat-value {
  font-weight: bold;
  font-size: 16px;
}

/* D3样式 */
.node.highlighted circle {
  stroke: #409eff;
  stroke-width: 3px;
  filter: drop-shadow(0 0 3px rgba(64, 158, 255, 0.5));
}

.link.highlighted {
  stroke: #409eff;
  stroke-width: 3px;
}
</style>