<template>
  <div class="dashboard">
    <!-- 统计卡片区域 -->
    <el-row :gutter="20" class="stats-section">
      <el-col :span="6">
        <el-card class="stat-card online" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon bg-success">
              <el-icon :size="30"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.onlineDevices }}</div>
              <div class="stat-label">在线设备</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card offline" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon bg-danger">
              <el-icon :size="30"><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.offlineDevices }}</div>
              <div class="stat-label">离线设备</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card alerts" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon bg-warning">
              <el-icon :size="30"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.unhandledAlarms }}</div>
              <div class="stat-label">未处理告警</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card performance" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon bg-info">
              <el-icon :size="30"><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.cpuUsage }}%</div>
              <div class="stat-label">CPU使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-section">
      <el-col :span="8">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>设备状态趋势</span>
            </div>
          </template>
          <div ref="statusChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>健康状况</span>
            </div>
          </template>
          <div ref="healthChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>网络流量</span>
            </div>
          </template>
          <div ref="trafficChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最新告警 -->
    <el-row :gutter="20" class="alerts-section">
      <el-col :span="24">
        <el-card class="alert-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>最新告警</span>
              <el-button type="primary" @click="viewAllAlerts" link>查看全部</el-button>
            </div>
          </template>
          <el-table 
            :data="alerts" 
            style="width: 100%"
            :row-class-name="getAlertRowClass"
            max-height="400"
            class="alerts-table"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="created_at" label="时间" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="device_name" label="设备" width="150" />
            <el-table-column prop="level" label="级别" width="120">
              <template #default="scope">
                <el-tag :type="getAlertTagType(scope.row.level)">
                  {{ getAlertLabel(scope.row.level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="告警详情" show-overflow-tooltip>
              <template #default="scope">
                <div v-if="scope.row.simple_details && Object.keys(scope.row.simple_details).length > 0">
                  <div v-if="scope.row.simple_details.alert_type">
                    <strong>{{ scope.row.simple_details.alert_type }}</strong>
                  </div>
                  <div v-if="scope.row.simple_details.conflict_ip || scope.row.simple_details.conflict_mac">
                    冲突IP: {{ scope.row.simple_details.conflict_ip || 'N/A' }} | 
                    冲突MAC: {{ scope.row.simple_details.conflict_mac || 'N/A' }}
                  </div>
                  <div v-if="scope.row.simple_details.conflict_interface || scope.row.simple_details.vlan_id">
                    接口: {{ scope.row.simple_details.conflict_interface || 'N/A' }} | 
                    VLAN: {{ scope.row.simple_details.vlan_id || 'N/A' }}
                  </div>
                  <div v-if="scope.row.simple_details.description">
                    描述: {{ scope.row.simple_details.description }}
                  </div>
                </div>
                <div v-else>
                  {{ scope.row.message || scope.row.title }}
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  SuccessFilled,
  CircleCloseFilled,
  Warning,
  DataAnalysis,
  DataLine,
  Monitor,
  UploadFilled
} from '@element-plus/icons-vue'
import { getDeviceOverview, getAlertStatistics, getDashboardData, getNewDashboardStats as getDashboardStats } from '@/api/dashboard'
import { getAlerts } from '@/api/alert'
// 导入设备API，以便启动状态检查
import { checkConnectivity } from '@/api/device'

// 路由实例
const router = useRouter()

// 响应式数据
const dashboardData = ref({
  stats: {
    totalDevices: 0,
    onlineDevices: 0,
    offlineDevices: 0,
    alertsCount: 0,
    cpuUsage: 0  // 添加CPU使用率字段
  },
  statusTrend: [],
  performanceData: {
    cpu: [],
    memory: [],
    bandwidth: []
  }
})

// 添加组件挂载状态变量
let isComponentMounted = true

// 定时器和WebSocket连接变量
let statusCheckTimer = null
let wsConnection = null
let reconnectAttempts = 0
const maxReconnectAttempts = 10
let reconnectDelay = 3000

// 启动WebSocket连接以接收实时状态更新
const initWebSocket = () => {
  // 检查浏览器是否支持WebSocket
  if (typeof WebSocket === 'undefined') {
    console.error('浏览器不支持WebSocket')
    return
  }
  
  // 检查是否已经有活动的WebSocket连接
  if (wsConnection) {
    console.log('已有WebSocket连接，跳过初始化')
    return
  }
  
  // 检查token是否存在
  const token = localStorage.getItem('access_token')
  if (!token) {
    console.warn('WebSocket连接：访问令牌不存在')
    return
  }
  
  // 构建WebSocket连接URL
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/device-status?token=${token}`
  
  console.log('仪表盘尝试连接WebSocket:', wsUrl)
  
  try {
    // 创建新的WebSocket连接
    wsConnection = new WebSocket(wsUrl)
    
    // 连接打开事件
    wsConnection.onopen = () => {
      console.log('仪表盘WebSocket连接已建立')
      reconnectAttempts = 0 // 重置重连尝试次数
      reconnectDelay = 3000 // 重置重连延迟
      ElMessage.success('仪表盘实时连接已建立')
    }
    
    // 消息接收事件
    wsConnection.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('仪表盘收到WebSocket消息:', data)
        
        // 根据消息类型处理不同的更新
        if (data.type === 'device_status_update' || 
            data.type === 'batch_device_status_update' || 
            data.type === 'device_list_update' ||
            data.type === 'connection_status') {
          // 这些类型的更新都需要刷新仪表盘数据
          loadDashboardStats()
          loadRecentAlerts() // 同时刷新告警数据
          
          // 触发一个自定义事件，通知其他组件更新
          window.dispatchEvent(new CustomEvent('device-status-change', {
            detail: { type: data.type, payload: data }
          }))
        } else {
          console.log('仪表盘收到未知类型的消息:', data.type)
        }
      } catch (error) {
        console.error('解析仪表盘WebSocket消息失败:', error)
      }
    }
    
    // 连接错误事件
    wsConnection.onerror = (error) => {
      console.error('仪表盘WebSocket连接错误:', error)
    }
    
    // 连接关闭事件
    wsConnection.onclose = (event) => {
      console.log(`仪表盘WebSocket连接已关闭: ${event.code} ${event.reason || ''}`)
      wsConnection = null // 清除连接引用
      
      // 只有在组件仍然挂载且不是主动关闭的情况下才尝试重连
      if (isComponentMounted && reconnectAttempts < maxReconnectAttempts) {
        console.log(`仪表盘尝试重连 (${reconnectAttempts + 1}/${maxReconnectAttempts})...`)
        
        // 增加重连延迟（指数退避），但不超过30秒
        reconnectDelay = Math.min(reconnectDelay * 1.5, 30000)
        reconnectAttempts++
        
        setTimeout(() => {
          // 在重试前再次检查组件是否仍处于挂载状态
          if (isComponentMounted) {
            initWebSocket()
          }
        }, reconnectDelay)
      } else if (!isComponentMounted) {
        console.log('组件已卸载，停止WebSocket重连')
      } else {
        console.error('仪表盘WebSocket重连次数已达上限')
        ElMessage.error({
          message: 'WebSocket连接已断开，无法重连，请刷新页面或检查网络连接',
          duration: 5000
        })
      }
    }
  } catch (error) {
    console.error('创建WebSocket连接失败:', error)
    wsConnection = null
  }
}

// 开始定时检查设备状态
const startStatusChecking = () => {
  console.log('仪表盘开始定时检查设备状态...')
  // 检查token是否存在
  const token = localStorage.getItem('access_token')
  console.log('仪表盘当前token状态:', token ? '存在' : '不存在')
  
  // 立即执行一次
  loadDashboardStats()
  
  // 在页面加载时立即触发一次设备状态检查
  triggerDeviceStatusCheck()
  
  // 每1分钟执行一次（更频繁地更新数据）
  statusCheckTimer = setInterval(() => {
    console.log('仪表盘定时器触发状态检查...')
    const currentToken = localStorage.getItem('access_token')
    console.log('仪表盘当前token状态:', currentToken ? '存在' : '不存在')
    if (currentToken) {
      loadDashboardStats()
    } else {
      console.warn('仪表盘定时检查：访问令牌不存在，停止定时器')
      stopStatusChecking()
    }
  }, 60000)  // 1分钟 = 60 * 1000毫秒
  
  console.log('仪表盘定时检查已启动')
  
  // 初始化WebSocket连接以接收实时状态更新
  initWebSocket()
}

// 触发设备状态检查的函数
const triggerDeviceStatusCheck = async () => {
  try {
    // 导入设备API以触发设备状态检查
    const deviceAPI = await import('@/api/device')
    
    // 获取设备列表
    const response = await deviceAPI.getDevices()
    
    if (response && response.data) {
      // 对每个设备触发连通性检查
      const checkPromises = response.data.map(async (device) => {
        if (device.management_ip) {
          try {
            const result = await deviceAPI.checkConnectivity(device.management_ip)
            // 更新设备状态到后端
            await deviceAPI.updateDevice(device.id, { 
              status: result.is_reachable ? 'online' : 'offline' 
            })
          } catch (error) {
            console.error(`检查设备 ${device.name} 连通性失败:`, error)
          }
        }
      })
      
      // 等待所有检查完成
      await Promise.all(checkPromises)
      console.log('所有设备状态检查完成')
      
      // 重新加载仪表盘数据以反映最新状态
      loadDashboardStats()
    }
  } catch (error) {
    console.error('触发设备状态检查失败:', error)
  }
}

// 停止定时检查
const stopStatusChecking = () => {
  if (statusCheckTimer) {
    clearInterval(statusCheckTimer)
    statusCheckTimer = null
    console.log('定时检查已停止')
  }
  
  if (wsConnection) {
    // 移除所有事件监听器
    wsConnection.onopen = null
    wsConnection.onmessage = null
    wsConnection.onerror = null
    wsConnection.onclose = null
    
    // 关闭连接
    wsConnection.close()
    wsConnection = null
    console.log('WebSocket连接已关闭')
  }
  
  reconnectAttempts = 0
  reconnectDelay = 3000
}

// 图表引用
const statusChartRef = ref()
const healthChartRef = ref()
const trafficChartRef = ref()

// 图表实例
let statusChart = null
let healthChart = null
let trafficChart = null
let echarts = null

// 从响应式数据中获取当前统计值
const stats = computed(() => {
  return {
    onlineDevices: dashboardData.value.stats.onlineDevices,
    offlineDevices: dashboardData.value.stats.offlineDevices,
    unhandledAlarms: dashboardData.value.stats.unhandledAlarms,
    cpuUsage: dashboardData.value.stats.cpuUsage
  };
});

// 添加一个强制刷新方法
const forceRefresh = async () => {
  console.log('仪表盘强制刷新数据...')
  await loadDashboardStats()
  await loadRecentAlerts()
}

// 告警数据
const alerts = ref([])

// 告警分页信息
const alertPagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 计算分页后的告警数据
const paginatedAlerts = computed(() => {
  const start = (alertPagination.currentPage - 1) * alertPagination.pageSize
  const end = start + alertPagination.pageSize
  return alerts.value.slice(start, end)
})

// 格式化时间显示
const formatTime = (timeString) => {
  if (!timeString) return '-'
  try {
    const date = new Date(timeString)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  } catch (e) {
    return timeString
  }
}

// 获取设备状态图表配置
const getStatusChartOption = (xAxisData = [], onlineData = [], offlineData = []) => {
  return {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['在线', '离线'],
      top: 'bottom'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData.length > 0 ? xAxisData : ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '在线',
        type: 'line',
        stack: '总量',
        data: onlineData.length > 0 ? onlineData : [1, 2, 3, 4, 5, 4, 3],
        smooth: true,
        areaStyle: {}
      },
      {
        name: '离线',
        type: 'line',
        stack: '总量',
        data: offlineData.length > 0 ? offlineData : [0, 0, 1, 0, 1, 0, 1],
        smooth: true,
        areaStyle: {}
      }
    ]
  }
}

// 获取设备健康图表配置
const getHealthChartOption = (xAxisData = [], cpuData = [], memoryData = []) => {
  return {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['CPU使用率', '内存使用率'],
      top: 'bottom'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData.length > 0 ? xAxisData : ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value} %'
      }
    },
    series: [
      {
        name: 'CPU使用率',
        type: 'line',
        data: cpuData.length > 0 ? cpuData : [20, 15, 30, 45, 40, 25],
        smooth: true,
        areaStyle: {}
      },
      {
        name: '内存使用率',
        type: 'line',
        data: memoryData.length > 0 ? memoryData : [40, 35, 50, 70, 65, 55],
        smooth: true,
        areaStyle: {}
      }
    ]
  }
}

// 获取流量图表配置
const getTrafficChartOption = (xAxisData = [], inboundData = [], outboundData = []) => {
  return {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['入站流量', '出站流量'],
      top: 'bottom'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData.length > 0 ? xAxisData : ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value} MB'
      }
    },
    series: [
      {
        name: '入站流量',
        type: 'line',
        data: inboundData.length > 0 ? inboundData : [10, 5, 30, 50, 45, 20],
        smooth: true,
        areaStyle: {}
      },
      {
        name: '出站流量',
        type: 'line',
        data: outboundData.length > 0 ? outboundData : [5, 2, 15, 30, 25, 10],
        smooth: true,
        areaStyle: {}
      }
    ]
  }
}

// 初始化图表
const initCharts = async () => {
  // 动态导入 echarts
  try {
    echarts = await import('echarts')
  } catch (error) {
    console.warn('ECharts 加载失败:', error)
    return
  }
  
  // 使用 nextTick 确保 DOM 已更新后再初始化图表
  await new Promise(resolve => setTimeout(resolve, 100))
  
  // 延迟初始化图表，确保DOM元素已渲染
  setTimeout(() => {
    // 检查DOM元素是否存在且有尺寸
    if (statusChartRef.value) {
      // 确保DOM元素已渲染并有尺寸
      if (statusChartRef.value.offsetWidth > 0 && statusChartRef.value.offsetHeight > 0) {
        statusChart = echarts.init(statusChartRef.value)
        statusChart.setOption(getStatusChartOption())
      } else {
        // 如果尺寸为0，尝试延迟初始化
        setTimeout(() => {
          if (statusChartRef.value && statusChartRef.value.offsetWidth > 0 && statusChartRef.value.offsetHeight > 0) {
            statusChart = echarts.init(statusChartRef.value)
            statusChart.setOption(getStatusChartOption())
          } else {
            // 再次尝试，确保图表容器有尺寸
            console.warn('状态趋势图表容器尺寸无效，尝试强制设置尺寸...')
            // 强制设置容器尺寸后再次尝试初始化
            statusChartRef.value.style.height = '400px'
            statusChartRef.value.style.width = '100%'
            if (statusChartRef.value.offsetWidth > 0 && statusChartRef.value.offsetHeight > 0) {
              statusChart = echarts.init(statusChartRef.value)
              statusChart.setOption(getStatusChartOption())
            } else {
              console.error('状态趋势图表容器初始化失败')
            }
          }
        }, 300)
      }
    } else {
      console.warn('状态趋势图表容器DOM元素不存在')
    }
    
    if (healthChartRef.value) {
      if (healthChartRef.value.offsetWidth > 0 && healthChartRef.value.offsetHeight > 0) {
        healthChart = echarts.init(healthChartRef.value)
        healthChart.setOption(getHealthChartOption())
      } else {
        // 如果尺寸为0，尝试延迟初始化
        setTimeout(() => {
          if (healthChartRef.value && healthChartRef.value.offsetWidth > 0 && healthChartRef.value.offsetHeight > 0) {
            healthChart = echarts.init(healthChartRef.value)
            healthChart.setOption(getHealthChartOption())
          } else {
            // 强制设置容器尺寸后再次尝试初始化
            console.warn('健康状况图表容器尺寸无效，尝试强制设置尺寸...')
            healthChartRef.value.style.height = '400px'
            healthChartRef.value.style.width = '100%'
            if (healthChartRef.value.offsetWidth > 0 && healthChartRef.value.offsetHeight > 0) {
              healthChart = echarts.init(healthChartRef.value)
              healthChart.setOption(getHealthChartOption())
            } else {
              console.error('健康状况图表容器初始化失败')
            }
          }
        }, 300)
      }
    } else {
      console.warn('健康状况图表容器DOM元素不存在')
    }
    
    if (trafficChartRef.value) {
      if (trafficChartRef.value.offsetWidth > 0 && trafficChartRef.value.offsetHeight > 0) {
        trafficChart = echarts.init(trafficChartRef.value)
        trafficChart.setOption(getTrafficChartOption())
      } else {
        // 如果尺寸为0，尝试延迟初始化
        setTimeout(() => {
          if (trafficChartRef.value && trafficChartRef.value.offsetWidth > 0 && trafficChartRef.value.offsetHeight > 0) {
            trafficChart = echarts.init(trafficChartRef.value)
            trafficChart.setOption(getTrafficChartOption())
          } else {
            // 强制设置容器尺寸后再次尝试初始化
            console.warn('流量图表容器尺寸无效，尝试强制设置尺寸...')
            trafficChartRef.value.style.height = '400px'
            trafficChartRef.value.style.width = '100%'
            if (trafficChartRef.value.offsetWidth > 0 && trafficChartRef.value.offsetHeight > 0) {
              trafficChart = echarts.init(trafficChartRef.value)
              trafficChart.setOption(getTrafficChartOption())
            } else {
              console.error('流量图表容器初始化失败')
            }
          }
        }, 300)
      }
    } else {
      console.warn('流量图表容器DOM元素不存在')
    }
    
    console.log('Charts initialized:', statusChart, healthChart, trafficChart);
  }, 100)
}

// 更新图表
const updateCharts = (performanceData, statusTrendData) => {
  console.log("Updating charts with data:", performanceData, statusTrendData);

  // 更新设备状态趋势图
  if (statusChart) {
    let dates = [];
    let onlineData = [];
    let offlineData = [];

    // 处理状态趋势数据
    if (statusTrendData && statusTrendData.trend) {
      dates = Array.isArray(statusTrendData.trend.dates) ? statusTrendData.trend.dates : [];
      onlineData = Array.isArray(statusTrendData.trend.online) ? statusTrendData.trend.online : [];
      offlineData = Array.isArray(statusTrendData.trend.offline) ? statusTrendData.trend.offline : [];
    } else if (statusTrendData && statusTrendData.status) {
      // 如果只有当前状态数据，创建一周的趋势数据
      dates = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
      const onlineCount = typeof statusTrendData.status.online === 'number' ? statusTrendData.status.online : 0;
      const offlineCount = typeof statusTrendData.status.offline === 'number' ? statusTrendData.status.offline : 0;
      onlineData = Array(7).fill(onlineCount);
      offlineData = Array(7).fill(offlineCount);
    }

    // 如果数据为空，提供默认数据
    if (dates.length === 0) {
      dates = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
      onlineData = Array(7).fill(typeof dashboardData.value.stats.onlineDevices === 'number' ? dashboardData.value.stats.onlineDevices : 0);
      offlineData = Array(7).fill(typeof dashboardData.value.stats.offlineDevices === 'number' ? dashboardData.value.stats.offlineDevices : 0);
    }

    console.log("Status trend data:", dates, onlineData, offlineData);

    const option = getStatusChartOption(dates, onlineData, offlineData);
    try {
      statusChart.setOption(option, true);
    } catch (error) {
      console.error("更新状态趋势图失败:", error);
    }
  }

  // 更新设备健康状况图
  if (healthChart) {
    let times = [];
    let cpuData = [];
    let memoryData = [];

    // 根据后端实际返回的数据结构处理 - 针对新的getDashboardData API
    if (performanceData && performanceData.health_data && performanceData.health_data.cpu_usage) {
      // 处理CPU数据
      if (Array.isArray(performanceData.health_data.cpu_usage) && performanceData.health_data.cpu_usage.length > 0) {
        times = performanceData.health_data.cpu_usage.map(item => {
          return item.time || item.timestamp || (item.date ? new Date(item.date).toLocaleTimeString() : '');
        });
        cpuData = performanceData.health_data.cpu_usage.map(item => {
          return typeof item.usage !== 'undefined' ? item.usage : (typeof item.value !== 'undefined' ? item.value : 0);
        });
      }

      // 处理内存数据
      if (performanceData.health_data.memory_usage && Array.isArray(performanceData.health_data.memory_usage) && performanceData.health_data.memory_usage.length > 0) {
        // 如果内存数据的时间点与CPU数据不一致，使用CPU的时间点
        if (times.length > 0) {
          memoryData = performanceData.health_data.memory_usage.map(item => {
            return typeof item.usage !== 'undefined' ? item.usage : (typeof item.value !== 'undefined' ? item.value : 0);
          });
        } else {
          // 如果CPU数据为空，使用内存数据的时间点
          times = performanceData.health_data.memory_usage.map(item => {
            return item.time || item.timestamp || (item.date ? new Date(item.date).toLocaleTimeString() : '');
          });
          memoryData = performanceData.health_data.memory_usage.map(item => {
            return typeof item.usage !== 'undefined' ? item.usage : (typeof item.value !== 'undefined' ? item.value : 0);
          });
        }
      } else {
        // 如果内存数据为空，使用CPU时间作为参考
        memoryData = Array(times.length).fill(0);
      }
    } else if (performanceData && performanceData.cpu_usage) {
      // 兼容旧的API数据结构
      if (Array.isArray(performanceData.cpu_usage) && performanceData.cpu_usage.length > 0) {
        times = performanceData.cpu_usage.map(item => {
          return item.time || item.timestamp || (item.date ? new Date(item.date).toLocaleTimeString() : '');
        });
        cpuData = performanceData.cpu_usage.map(item => {
          return typeof item.usage !== 'undefined' ? item.usage : (typeof item.value !== 'undefined' ? item.value : 0);
        });
      }

      // 处理内存数据
      if (performanceData.memory_usage && Array.isArray(performanceData.memory_usage) && performanceData.memory_usage.length > 0) {
        // 如果内存数据的时间点与CPU数据不一致，使用CPU的时间点
        if (times.length > 0) {
          memoryData = performanceData.memory_usage.map(item => {
            return typeof item.usage !== 'undefined' ? item.usage : (typeof item.value !== 'undefined' ? item.value : 0);
          });
        } else {
          // 如果CPU数据为空，使用内存数据的时间点
          times = performanceData.memory_usage.map(item => {
            return item.time || item.timestamp || (item.date ? new Date(item.date).toLocaleTimeString() : '');
          });
          memoryData = performanceData.memory_usage.map(item => {
            return typeof item.usage !== 'undefined' ? item.usage : (typeof item.value !== 'undefined' ? item.value : 0);
          });
        }
      } else {
        // 如果内存数据为空，使用CPU时间作为参考
        memoryData = Array(times.length).fill(0);
      }
    } else if (performanceData && performanceData.cpu) {
      // 更老的API数据结构
      if (Array.isArray(performanceData.cpu) && performanceData.cpu.length > 0) {
        times = performanceData.cpu.map(item => {
          return item.time || item.timestamp || (item.date ? new Date(item.date).toLocaleTimeString() : '');
        });
        cpuData = performanceData.cpu.map(item => {
          return typeof item.usage !== 'undefined' ? item.usage : (typeof item.value !== 'undefined' ? item.value : 0);
        });
      }

      // 处理内存数据
      if (performanceData.memory && Array.isArray(performanceData.memory) && performanceData.memory.length > 0) {
        // 如果内存数据的时间点与CPU数据不一致，使用CPU的时间点
        if (times.length > 0) {
          memoryData = performanceData.memory.map(item => {
            return typeof item.usage !== 'undefined' ? item.usage : (typeof item.value !== 'undefined' ? item.value : 0);
          });
        } else {
          // 如果CPU数据为空，使用内存数据的时间点
          times = performanceData.memory.map(item => {
            return item.time || item.timestamp || (item.date ? new Date(item.date).toLocaleTimeString() : '');
          });
          memoryData = performanceData.memory.map(item => {
            return typeof item.usage !== 'undefined' ? item.usage : (typeof item.value !== 'undefined' ? item.value : 0);
          });
        }
      } else {
        // 如果内存数据为空，使用CPU时间作为参考
        memoryData = Array(times.length).fill(0);
      }
    }

    // 如果数据为空，提供默认数据
    if (times.length === 0) {
      times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"];
      cpuData = [20, 15, 30, 45, 40, 25];
      memoryData = [40, 35, 50, 70, 65, 55];
    }

    console.log("Health chart data:", times, cpuData, memoryData);

    const option = getHealthChartOption(times, cpuData, memoryData);
    try {
      healthChart.setOption(option, true);
    } catch (error) {
      console.error("更新健康状况图失败:", error);
    }
  }

  // 更新网络流量图
  if (trafficChart) {
    let times = [];
    let inboundData = [];
    let outboundData = [];

    // 根据后端实际返回的数据结构处理 - 针对新的getDashboardData API
    if (performanceData && performanceData.traffic_data && performanceData.traffic_data.bandwidth_usage) {
      // 处理带宽数据
      if (Array.isArray(performanceData.traffic_data.bandwidth_usage) && performanceData.traffic_data.bandwidth_usage.length > 0) {
        times = performanceData.traffic_data.bandwidth_usage.map(item => {
          return item.time || item.timestamp || (item.date ? new Date(item.date).toLocaleTimeString() : '');
        });
        inboundData = performanceData.traffic_data.bandwidth_usage.map(item => {
          return typeof item.in !== 'undefined' ? item.in : (typeof item.value !== 'undefined' ? item.value : 0);
        });
        outboundData = performanceData.traffic_data.bandwidth_usage.map(item => {
          return typeof item.out !== 'undefined' ? item.out : (typeof item.value !== 'undefined' ? item.value : 0);
        });
      }
    } else if (performanceData && performanceData.bandwidth_usage) {
      // 兼容旧的API数据结构
      if (Array.isArray(performanceData.bandwidth_usage) && performanceData.bandwidth_usage.length > 0) {
        times = performanceData.bandwidth_usage.map(item => {
          return item.time || item.timestamp || (item.date ? new Date(item.date).toLocaleTimeString() : '');
        });
        inboundData = performanceData.bandwidth_usage.map(item => {
          return typeof item.in !== 'undefined' ? item.in : (typeof item.value !== 'undefined' ? item.value : 0);
        });
        outboundData = performanceData.bandwidth_usage.map(item => {
          return typeof item.out !== 'undefined' ? item.out : (typeof item.value !== 'undefined' ? item.value : 0);
        });
      }
    } else if (performanceData && performanceData.bandwidth) {
      // 更老的API数据结构
      if (Array.isArray(performanceData.bandwidth) && performanceData.bandwidth.length > 0) {
        times = performanceData.bandwidth.map(item => {
          return item.time || item.timestamp || (item.date ? new Date(item.date).toLocaleTimeString() : '');
        });
        inboundData = performanceData.bandwidth.map(item => {
          return typeof item.in !== 'undefined' ? item.in : (typeof item.value !== 'undefined' ? item.value : 0);
        });
        outboundData = performanceData.bandwidth.map(item => {
          return typeof item.out !== 'undefined' ? item.out : (typeof item.value !== 'undefined' ? item.value : 0);
        });
      }
    }

    // 如果数据为空，提供默认数据
    if (times.length === 0) {
      times = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"];
      inboundData = [10, 5, 30, 50, 45, 20];
      outboundData = [5, 2, 15, 30, 25, 10];
    }

    console.log("Traffic chart data:", times, inboundData, outboundData);

    const option = getTrafficChartOption(times, inboundData, outboundData);
    try {
      trafficChart.setOption(option, true);
    } catch (error) {
      console.error("更新流量图失败:", error);
    }
  }
}

// 带重试机制的API请求函数
async function fetchWithRetry(apiCallFn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await apiCallFn();
      return result;
    } catch (error) {
      console.warn(`API请求失败 (尝试 ${i+1}/${maxRetries}):`, error.message);
      
      // 如果是最后一次尝试，抛出错误
      if (i === maxRetries - 1) {
        // 如果是网络错误，返回默认值而不是抛出错误
        if (error.message && error.message.includes('Network Error')) {
          console.warn(`网络错误，返回默认值用于: ${apiCallFn.name}`);
          // 根据不同的API返回适当的默认值
          if (apiCallFn.name.includes('getDashboardData')) {
            return {
              status_distribution: {
                status: { online: 0, offline: 0, warning: 0, unknown: 0 },
                trend: {
                  dates: [],
                  online: [],
                  offline: []
                }
              },
              health_data: {
                cpu_usage: [],
                memory_usage: []
              },
              traffic_data: {
                bandwidth_usage: []
              }
            };
          } else if (apiCallFn.name.includes('getDeviceOverview')) {
            return { online_devices: 0, offline_devices: 0 };
          } else if (apiCallFn.name.includes('getAlertStatistics')) {
            return { new: 0 };
          } else if (apiCallFn.name.includes('getPerformanceData')) {
            // 返回包含空数组的性能数据结构，这样图表可以显示默认数据
            return { 
              cpu: [], 
              memory: [], 
              bandwidth: [],
              // 为兼容性添加可能的字段名
              cpu_data: [],
              memory_data: [],
              bandwidth_data: []
            };
          } else if (apiCallFn.name.includes('getDeviceStatusDistribution')) {
            return {
              status: { online: 0, offline: 0, warning: 0, unknown: 0 },
              vendor: {},
              type: {},
              trend: {
                dates: [],
                online: [],
                offline: []
              }
            };
          } else if (apiCallFn.name.includes('getAlerts')) {
            return { data: [] };  // 为告警API返回适当的数据结构
          } else {
            return {};
          }
        }
        throw error;
      }
      
      // 等待一段时间后重试
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))); // 递增延迟
    }
  }
}

// 获取仪表盘统计数据
const loadDashboardStats = async () => {
  try {
    // 使用新的统一API获取仪表盘数据，同时保留其他API用于补充数据
    const [dashboardDataRes, overviewRes, alertStatsRes] = await Promise.all([
      fetchWithRetry(getDashboardData),        // 从新的统一API获取状态趋势、健康和流量数据
      fetchWithRetry(getDeviceOverview),       // 从 /api/v1/device-stats/overview 获取设备概览
      fetchWithRetry(getAlertStatistics)       // 从 /api/v1/alerts/statistics 获取告警统计
    ])

    console.log('API Responses:', { 
      dashboardDataRes, 
      overviewRes, 
      alertStatsRes 
    });

    // 设置设备统计数据 - 优先使用设备概览API的数据
    if (overviewRes && typeof overviewRes.online_devices !== 'undefined') {
      dashboardData.value.stats.onlineDevices = typeof overviewRes.online_devices === 'number' ? overviewRes.online_devices : 0
      dashboardData.value.stats.offlineDevices = typeof overviewRes.offline_devices === 'number' ? overviewRes.offline_devices : 0
      dashboardData.value.stats.totalDevices = typeof overviewRes.total_devices === 'number' ? overviewRes.total_devices : 0
    } else if (overviewRes && overviewRes.data && typeof overviewRes.data.online_devices !== 'undefined') {
      // 如果响应包装在data字段中
      dashboardData.value.stats.onlineDevices = typeof overviewRes.data.online_devices === 'number' ? overviewRes.data.online_devices : 0
      dashboardData.value.stats.offlineDevices = typeof overviewRes.data.offline_devices === 'number' ? overviewRes.data.offline_devices : 0
      dashboardData.value.stats.totalDevices = typeof overviewRes.data.total_devices === 'number' ? overviewRes.data.total_devices : 0
    } else {
      // 如果设备概览API没有返回预期数据，使用仪表盘API的统计数据作为备选
      console.warn('设备概览API未返回预期数据结构，尝试其他数据源')
    }

    // 设置告警统计数据 - 优先使用告警统计API的数据
    if (alertStatsRes && typeof alertStatsRes.new !== 'undefined') {
      dashboardData.value.stats.unhandledAlarms = typeof alertStatsRes.new === 'number' ? alertStatsRes.new : 0
    } else if (alertStatsRes && alertStatsRes.data && typeof alertStatsRes.data.new !== 'undefined') {
      // 如果响应包装在data字段中
      dashboardData.value.stats.unhandledAlarms = typeof alertStatsRes.data.new === 'number' ? alertStatsRes.data.new : 0
    } else if (alertStatsRes && typeof alertStatsRes.unhandledAlarms !== 'undefined') {
      // 如果响应直接包含unhandledAlarms字段
      dashboardData.value.stats.unhandledAlarms = typeof alertStatsRes.unhandledAlarms === 'number' ? alertStatsRes.unhandledAlarms : 0
    } else {
      // 如果告警统计API没有返回预期数据，使用仪表盘API的统计数据作为备选
      console.warn('告警统计API未返回预期数据结构')
    }

    // 从新的统一API获取设备健康数据
    if (dashboardDataRes && dashboardDataRes.health_data) {
      // 设置CPU使用率（取最新数据点）
      if (dashboardDataRes.health_data.cpu_usage && Array.isArray(dashboardDataRes.health_data.cpu_usage) && dashboardDataRes.health_data.cpu_usage.length > 0) {
        const lastCpuData = dashboardDataRes.health_data.cpu_usage[dashboardDataRes.health_data.cpu_usage.length - 1]
        dashboardData.value.stats.cpuUsage = typeof lastCpuData.usage !== 'undefined' ? lastCpuData.usage : 0
      } else {
        // 如果后端返回空数组，尝试从其他API获取数据
        console.log('从后端获取的CPU使用率数据为空，尝试从stats API获取')
        try {
          const statsRes = await fetchWithRetry(getDeviceOverview)
          if (statsRes && typeof statsRes.cpuUsage !== 'undefined') {
            dashboardData.value.stats.cpuUsage = typeof statsRes.cpuUsage === 'number' ? statsRes.cpuUsage : 0
          } else if (statsRes && statsRes.data && typeof statsRes.data.cpuUsage !== 'undefined') {
            dashboardData.value.stats.cpuUsage = typeof statsRes.data.cpuUsage === 'number' ? statsRes.data.cpuUsage : 0
          } else {
            dashboardData.value.stats.cpuUsage = 0
          }
        } catch (error) {
          console.warn('获取CPU使用率失败，使用默认值0:', error)
          dashboardData.value.stats.cpuUsage = 0
        }
      }

      // 准备性能数据用于图表渲染
      dashboardData.value.performanceData = {
        cpu: Array.isArray(dashboardDataRes.health_data.cpu_usage) ? dashboardDataRes.health_data.cpu_usage : [],
        memory: Array.isArray(dashboardDataRes.health_data.memory_usage) ? dashboardDataRes.health_data.memory_usage : [],
        bandwidth: Array.isArray(dashboardDataRes.traffic_data.bandwidth_usage) ? dashboardDataRes.traffic_data.bandwidth_usage : []
      };

      // 准备状态趋势图表数据
      dashboardData.value.statusTrend = {
        status: dashboardDataRes.status_distribution ? dashboardDataRes.status_distribution.status : {},
        trend: dashboardDataRes.status_distribution ? dashboardDataRes.status_distribution.trend : {}
      };
    } else {
      console.warn('新的仪表盘API未返回预期数据结构，尝试使用旧API')
      
      // 如果新的API没有返回数据，使用旧的API获取数据
      const [deviceHealthRes, statusRes, trafficMonitoringRes] = await Promise.all([
        fetchWithRetry(getDeviceHealth),        // 从 /api/v1/device-stats/device-health 获取设备健康数据
        fetchWithRetry(getDeviceStatusDistribution), // 从 /api/v1/dashboard/device-status 获取设备状态分布
        fetchWithRetry(getTrafficMonitoring)    // 从 /api/v1/device-stats/traffic-monitoring 获取流量监控数据
      ])
      
      // 设置性能数据 (使用CPU使用率作为示例)
      if (deviceHealthRes && deviceHealthRes.cpu_usage && Array.isArray(deviceHealthRes.cpu_usage) && deviceHealthRes.cpu_usage.length > 0) {
        const lastCpuData = deviceHealthRes.cpu_usage[deviceHealthRes.cpu_usage.length - 1]
        dashboardData.value.stats.cpuUsage = typeof lastCpuData.value !== 'undefined' ? lastCpuData.value : 0
      } else if (deviceHealthRes && deviceHealthRes.data && deviceHealthRes.data.cpu_usage && Array.isArray(deviceHealthRes.data.cpu_usage) && deviceHealthRes.data.cpu_usage.length > 0) {
        // 如果响应包装在data字段中
        const lastCpuData = deviceHealthRes.data.cpu_usage[deviceHealthRes.data.cpu_usage.length - 1]
        dashboardData.value.stats.cpuUsage = typeof lastCpuData.value !== 'undefined' ? lastCpuData.value : 0
      } else {
        console.warn('设备健康数据API未返回预期数据结构')
        dashboardData.value.stats.cpuUsage = 0
      }

      // 准备状态趋势图表数据
      if (statusRes) {
        dashboardData.value.statusTrend = statusRes;
        if (statusRes && statusRes.data) {
          // 如果响应包装在data字段中
          dashboardData.value.statusTrend = statusRes.data;
        }
      }

      // 准备性能数据用于图表渲染
      dashboardData.value.performanceData = {
        cpu: [],
        memory: [],
        bandwidth: []
      };

      // 处理设备健康数据 - CPU和内存使用率
      if (deviceHealthRes && deviceHealthRes.cpu_usage && Array.isArray(deviceHealthRes.cpu_usage)) {
        dashboardData.value.performanceData.cpu = deviceHealthRes.cpu_usage;
      } else if (deviceHealthRes && deviceHealthRes.data && deviceHealthRes.data.cpu_usage && Array.isArray(deviceHealthRes.data.cpu_usage)) {
        dashboardData.value.performanceData.cpu = deviceHealthRes.data.cpu_usage;
      }

      if (deviceHealthRes && deviceHealthRes.memory_usage && Array.isArray(deviceHealthRes.memory_usage)) {
        dashboardData.value.performanceData.memory = deviceHealthRes.memory_usage;
      } else if (deviceHealthRes && deviceHealthRes.data && deviceHealthRes.data.memory_usage && Array.isArray(deviceHealthRes.data.memory_usage)) {
        dashboardData.value.performanceData.memory = deviceHealthRes.data.memory_usage;
      }

      // 处理流量监控数据 - 入站和出站流量
      if (trafficMonitoringRes && trafficMonitoringRes.inbound_traffic && Array.isArray(trafficMonitoringRes.inbound_traffic)) {
        // 转换流量数据格式以匹配图表期望的格式
        const inboundTraffic = trafficMonitoringRes.inbound_traffic;
        const outboundTraffic = Array.isArray(trafficMonitoringRes.outbound_traffic) ? trafficMonitoringRes.outbound_traffic : [];
        dashboardData.value.performanceData.bandwidth = inboundTraffic.map((item, index) => {
          const outItem = outboundTraffic[index] || { value: 0 };
          return {
            time: item.time || '',
            in: typeof item.value !== 'undefined' ? item.value : 0,
            out: typeof outItem.value !== 'undefined' ? outItem.value : 0
          };
        });
      } else if (trafficMonitoringRes && trafficMonitoringRes.data && trafficMonitoringRes.data.inbound_traffic && Array.isArray(trafficMonitoringRes.data.inbound_traffic)) {
        const inboundTraffic = trafficMonitoringRes.data.inbound_traffic;
        const outboundTraffic = Array.isArray(trafficMonitoringRes.data.outbound_traffic) ? trafficMonitoringRes.data.outbound_traffic : [];
        dashboardData.value.performanceData.bandwidth = inboundTraffic.map((item, index) => {
          const outItem = outboundTraffic[index] || { value: 0 };
          return {
            time: item.time || '',
            in: typeof item.value !== 'undefined' ? item.value : 0,
            out: typeof outItem.value !== 'undefined' ? outItem.value : 0
          };
        });
      }
    }

    // 确保图表已初始化后再更新数据
    setTimeout(() => {
      if (statusChart && healthChart && trafficChart) {
        updateCharts(
          dashboardData.value.performanceData,
          dashboardData.value.statusTrend
        );
      }
    }, 300);
  } catch (error) {
    console.error("获取仪表盘数据失败:", error);
    // 即使API失败，也确保页面有内容显示
    ElMessage.error("获取仪表盘数据失败: " + (error.message || "未知错误"));
    
    // 设置默认值，确保页面不会空白
    dashboardData.value.stats.onlineDevices = 0;
    dashboardData.value.stats.offlineDevices = 0;
    dashboardData.value.stats.unhandledAlarms = 0;
    dashboardData.value.stats.cpuUsage = 0;
    
    // 确保图表有默认数据
    setTimeout(() => {
      if (statusChart && healthChart && trafficChart) {
        updateCharts(
          {
            cpu: [],
            memory: [],
            bandwidth: []
          },
          {
            trend: {
              dates: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
              online: [0, 0, 0, 0, 0, 0, 0],
              offline: [0, 0, 0, 0, 0, 0, 0]
            }
          }
        );
      }
    }, 300);
  }
}

// 获取最新告警
const loadRecentAlerts = async () => {
  try {
    const response = await fetchWithRetry(() => getAlerts({ page: 1, pageSize: 10, search: '', severity: 'all', status: 'all' }))
    let data = []
    
    // 根据响应结构提取数据
    if (response.data?.data) {
      data = response.data.data
    } else if (Array.isArray(response.data)) {
      data = response.data
    } else if (response.data && Array.isArray(response)) {
      data = response
    } else {
      data = []
    }
    
    // 确保每个告警都有必要的字段，并适配告警管理页面的字段结构
    data = data.map(alert => ({
      ...alert,
      level: alert.level || alert.severity || 'INFO',
      created_at: alert.created_at || alert.time || alert.timestamp || '',
      device_name: alert.device_name || alert.device || alert.device_ip || 'N/A',
      message: alert.message || alert.title || alert.description || '',
      simple_details: alert.simple_details || alert.details || {}
    }))
    
    // 直接使用返回的数据，不需要额外转换，因为它们已经包含了simple_details等字段
    alerts.value = data
    
    // 更新分页总数
    alertPagination.total = alerts.value.length
    // 重置到第一页
    alertPagination.currentPage = 1
  } catch (error) {
    console.error('获取告警数据失败:', error)
    // 仅在不是网络错误的情况下显示错误消息
    if (error.message && !error.message.includes('Network Error')) {
      ElMessage.error('获取告警数据失败: ' + (error.message || '未知错误'))
    } else {
      console.warn("告警数据网络错误，保持现有数据")
    }
    // 保持现有数据，不替换为默认值
  }
}

// 查看所有告警
const viewAllAlerts = () => {
  router.push('/alerts')
}

// 获取告警标签类型，与告警管理页面保持一致
const getAlertTagType = (level) => {
  const severityMap = {
    'Critical': 'danger',
    'Major': 'warning',
    'Minor': 'info',
    'Warning': 'warning',
    'INFO': 'info',
    'WARNING': 'warning',
    'ERROR': 'danger',
    'CRITICAL': 'danger'
  }
  return severityMap[level] || 'info'
}

// 获取告警级别标签文本，与告警管理页面保持一致
const getAlertLabel = (level) => {
  const severityMap = {
    'Critical': '严重',
    'Major': '主要',
    'Minor': '次要',
    'Warning': '警告',
    'INFO': '信息',
    'WARNING': '警告',
    'ERROR': '错误',
    'CRITICAL': '严重'
  }
  return severityMap[level] || level
}

// 获取告警行类名
const getAlertRowClass = (row) => {
  const level = row.level || 'INFO';
  if (level === 'CRITICAL' || level === 'Critical' || level === 'ERROR') {
    return 'alert-row-error';
  } else if (level === 'WARNING' || level === 'Warning' || level === 'Major') {
    return 'alert-row-warning';
  }
  return '';
}

// 格式化日期时间
const formatDate = (dateString) => {
  if (!dateString) return ''
  return dateString
}

// 处理告警分页变化
const handleAlertPageChange = (page) => {
  alertPagination.currentPage = page
}

// 窗口大小改变时重置图表大小
const resizeCharts = () => {
  if (statusChart) statusChart.resize()
  if (healthChart) healthChart.resize()
  if (trafficChart) trafficChart.resize()
}

// 页面加载时获取数据
onMounted(async () => {
  // 设置组件挂载状态
  isComponentMounted = true
  
  // 先初始化图表
  await initCharts()
  
  // 确保图表初始化完成后再加载数据
  await loadDashboardStats()
  await loadRecentAlerts()
  
  // 启动设备状态检查和WebSocket连接
  startStatusChecking()
  
  // 添加窗口大小改变监听器
  window.addEventListener('resize', resizeCharts)
  
  // 添加事件监听器，监听设备状态变化
  window.addEventListener('device-status-change', forceRefresh)
})

// 组件卸载前清理事件监听器
onBeforeUnmount(() => {
  // 设置组件未挂载状态，防止组件卸载后继续重连
  isComponentMounted = false
  
  // 停止设备状态检查和WebSocket连接
  stopStatusChecking()
  
  window.removeEventListener('resize', resizeCharts)
  window.removeEventListener('device-status-change', forceRefresh)
  
  // 销毁图表实例
  if (statusChart) statusChart.dispose()
  if (healthChart) healthChart.dispose()
  if (trafficChart) trafficChart.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 84px);
}

.stats-section {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-card:hover {
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
  transition: all 0.3s ease;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  flex-shrink: 0;
}

.bg-success {
  background-color: #e8f7ef;
  color: #19a25e;
}

.bg-danger {
  background-color: #fcebeb;
  color: #ff4d4f;
}

.bg-warning {
  background-color: #fff3e6;
  color: #fa8c16;
}

.bg-info {
  background-color: #e6f4ff;
  color: #1890ff;
}

.stat-info {
  flex: 1;
}

.stat-info .stat-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 5px;
  color: #333;
}

.stat-info .stat-label {
  font-size: 14px;
  color: #666;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-container {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  height: 400px; /* 为图表容器设置固定高度 */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
}

.card-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.chart-wrapper {
  width: 100%;
  height: 300px;
}

.alerts-container {
  height: 426px;
  display: flex;
  flex-direction: column;
}

.alerts-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.alerts-table {
  flex: 1;
  overflow: auto;
}

.alerts-table :deep(.el-table__row) {
  /* 通过CSS类名设置不同级别的告警行样式 */
}

.alerts-table :deep(.alert-row-error) {
  background-color: #ffe6e6; /* 错误级别告警背景色 */
}

.alerts-table :deep(.alert-row-warning) {
  background-color: #fff7e6; /* 警告级别告警背景色 */
}

.alerts-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

.alerts-pagination {
  margin-top: 20px;
  text-align: center;
}

.time-text {
  font-family: 'Consolas', 'Monaco', monospace;
  color: #666;
}

.alert-message-cell {
  line-height: 1.4;
}

.alert-title {
  font-weight: bold;
  color: #333;
  margin-bottom: 2px;
}

.alert-details {
  font-size: 12px;
}

.detail-item {
  display: flex;
  margin-bottom: 1px;
}

.detail-label {
  color: #666;
  margin-right: 5px;
  flex-shrink: 0;
}

.detail-value {
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alert-message {
  color: #333;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-section {
    flex-direction: column;
  }
  
  .stats-section > .el-col {
    width: 100%;
    margin-bottom: 15px;
  }
  
  .charts-section .el-col {
    width: 100%;
    margin-bottom: 15px;
  }
}
</style>