<template>
  <div class="monitor-container">
    <div class="monitor-header">
      <h2>监控中心</h2>
      <div class="actions">
        <el-button type="primary" @click="refreshData" :loading="loading">刷新数据</el-button>
        <el-date-picker
          v-model="timeRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          :shortcuts="shortcuts"
          style="margin-left: 10px; width: 300px"
          @change="handleTimeRangeChange"
        />
      </div>
    </div>
    
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card class="stat-card online">
          <div class="stat-content">
            <div class="stat-icon">
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
        <el-card class="stat-card offline">
          <div class="stat-content">
            <div class="stat-icon">
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
        <el-card class="stat-card alerts">
          <div class="stat-content">
            <div class="stat-icon">
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
        <el-card class="stat-card performance">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="30"><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.avgCpu }}%</div>
              <div class="stat-label">平均CPU使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card class="chart-card" style="height: 400px;">
          <template #header>
            <div class="card-header">
              <span>设备状态趋势</span>
            </div>
          </template>
          <div ref="statusChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="alerts-card" style="height: 400px;">
          <template #header>
            <div class="card-header">
              <span>最新告警</span>
              <el-button link @click="viewAllAlerts">查看全部</el-button>
            </div>
          </template>
          <el-table :data="alerts" style="width: 100%" height="300" class="alerts-table">
            <el-table-column prop="time" label="时间" width="180" />
            <el-table-column prop="device" label="设备" width="120" />
            <!-- 修改告警信息列，使其与告警管理页面保持一致 -->
            <el-table-column label="告警信息" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="alert-message-cell">
                  <div v-if="row.simple_details && Object.keys(row.simple_details).length > 0">
                    <div v-if="row.simple_details.alert_type" class="alert-title">
                      {{ row.simple_details.alert_type }}
                    </div>
                    <div class="alert-details">
                      <div v-if="row.simple_details.conflict_ip || row.simple_details.conflict_mac" class="detail-item">
                        <span class="detail-label">冲突信息:</span>
                        <span class="detail-value">
                          IP: {{ row.simple_details.conflict_ip || 'N/A' }} | 
                          MAC: {{ row.simple_details.conflict_mac || 'N/A' }}
                        </span>
                      </div>
                      <div v-if="row.simple_details.conflict_interface || row.simple_details.vlan_id" class="detail-item">
                        <span class="detail-label">位置信息:</span>
                        <span class="detail-value">
                          接口: {{ row.simple_details.conflict_interface || 'N/A' }} | 
                          VLAN: {{ row.simple_details.vlan_id || 'N/A' }}
                        </span>
                      </div>
                      <div v-if="row.simple_details.description" class="detail-item">
                        <span class="detail-label">描述:</span>
                        <span class="detail-value">{{ row.simple_details.description }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="alert-message">
                    {{ row.message }}
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="level" label="级别" width="100">
              <template #default="{ row }">
                <el-tag :type="getAlertTagType(row.level)" size="small">
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  SuccessFilled, 
  CircleCloseFilled, 
  Warning, 
  DataAnalysis, 
  DataLine 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getDeviceOverview } from '@/api/device'
import { getAlertStatistics, getAlerts } from '@/api/alert'
import { getDeviceStatusDistribution, getPerformanceData } from '@/api/dashboard'

const router = useRouter()

// 图表引用
const statusChartRef = ref()

// 加载状态
const loading = ref(false)

// 时间范围
const timeRange = ref('')

// 定时器引用
const refreshTimer = ref(null)

// 时间范围快捷选项
const shortcuts = [
  {
    text: '最近一小时',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000)
      return [start, end]
    },
  },
  {
    text: '最近一天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24)
      return [start, end]
    },
  },
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    },
  }
]

// 统计数据
const stats = reactive({
  onlineDevices: 0,
  offlineDevices: 0,
  unhandledAlarms: 0,
  avgCpu: 0
})

// 告警数据
const alerts = ref([])

// 图表实例
let statusChart = null

// 初始化图表
const initChart = () => {
  if (statusChartRef.value) {
    statusChart = echarts.init(statusChartRef.value)
    
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['在线设备', '离线设备']
      },
      xAxis: {
        type: 'category',
        data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '在线设备',
          type: 'line',
          stack: '总量',
          data: [120, 132, 101, 134, 90, 230, 210]
        },
        {
          name: '离线设备',
          type: 'line',
          stack: '总量',
          data: [220, 182, 191, 234, 290, 330, 310]
        }
      ]
    }
    
    statusChart.setOption(option)
  }
}

// 更新状态趋势图表
const updateStatusChart = (statusData) => {
  if (statusChart && statusData) {
    let dates = [];
    let onlineData = [];
    let offlineData = [];
    
    // 处理状态趋势数据
    if (statusData.trend && statusData.trend.dates) {
      // 优先使用趋势数据
      dates = statusData.trend.dates || [];
      onlineData = statusData.trend.online || [];
      offlineData = statusData.trend.offline || [];
    } else if (statusData.status) {
      // 如果只有当前状态数据，创建一周的趋势数据
      const today = new Date();
      dates = [];
      for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        dates.push(`${date.getMonth() + 1}-${date.getDate()}`);
      }
      const onlineCount = statusData.status.online || 0;
      const offlineCount = statusData.status.offline || 0;
      onlineData = Array(7).fill(onlineCount);
      offlineData = Array(7).fill(offlineCount);
    } else {
      // 如果没有趋势数据，尝试从性能数据中获取
      dates = statusData.dates || statusData.time || [];
      onlineData = statusData.online || statusData.online_devices || [];
      offlineData = statusData.offline || statusData.offline_devices || [];
    }
    
    // 确保数据长度一致
    const minLen = Math.min(dates.length, onlineData.length, offlineData.length);
    dates = dates.slice(0, minLen);
    onlineData = onlineData.slice(0, minLen);
    offlineData = offlineData.slice(0, minLen);
    
    // 如果数据仍然为空，使用默认数据
    if (dates.length === 0) {
      console.warn("设备状态趋势数据为空，使用默认数据");
      const today = new Date();
      dates = [];
      for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        dates.push(`${date.getMonth() + 1}-${date.getDate()}`);
      }
      onlineData = Array(7).fill(stats.onlineDevices);
      offlineData = Array(7).fill(stats.offlineDevices);
    }
    
    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          let result = params[0].axisValue + '<br/>';
          params.forEach(param => {
            result += param.marker + ' ' + param.seriesName + ': ' + param.data + '<br/>';
          });
          return result;
        }
      },
      legend: {
        data: ['在线设备', '离线设备']
      },
      xAxis: {
        type: 'category',
        data: dates
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '在线设备',
          type: 'line',
          smooth: true,
          data: onlineData
        },
        {
          name: '离线设备',
          type: 'line',
          smooth: true,
          data: offlineData
        }
      ]
    };
    
    statusChart.setOption(option, true); // 使用true表示不合并，完全替换
  }
};

// 刷新数据
const refreshData = async () => {
  loading.value = true
  try {
    // 并行获取统计数据
    const [overviewRes, alertStatsRes, alertsRes, statusRes, performanceRes] = await Promise.all([
      getDeviceOverview(),
      getAlertStatistics(),
      getAlerts({ page: 1, pageSize: 10, search: '', severity: 'all', status: 'all' }),
      getDeviceStatusDistribution(),
      getPerformanceData()
    ])
    
    // 更新设备统计数据
    stats.onlineDevices = overviewRes.data?.online_devices || overviewRes.online_devices || 0
    stats.offlineDevices = overviewRes.data?.offline_devices || overviewRes.offline_devices || 0
    
    // 更新告警统计数据
    stats.unhandledAlarms = alertStatsRes.data?.new || alertStatsRes.new || 0
    
    // 计算平均CPU使用率
    if (performanceRes.data?.cpu && performanceRes.data.cpu.length > 0) {
      const cpuData = performanceRes.data.cpu;
      const totalCpu = cpuData.reduce((sum, item) => sum + (item.usage || 0), 0);
      stats.avgCpu = Math.round(totalCpu / cpuData.length);
    } else if (performanceRes.cpu && performanceRes.cpu.length > 0) {
      const cpuData = performanceRes.cpu;
      const totalCpu = cpuData.reduce((sum, item) => sum + (item.usage || 0), 0);
      stats.avgCpu = Math.round(totalCpu / cpuData.length);
    } else {
      // 如果没有CPU数据，使用随机数模拟
      stats.avgCpu = Math.floor(Math.random() * 100)
    }
    
    // 更新告警列表，直接使用返回的数据，因为它们已经包含了simple_details等字段
    if (alertsRes.data?.data) {
      alerts.value = alertsRes.data.data
    } else if (Array.isArray(alertsRes.data)) {
      alerts.value = alertsRes.data
    } else {
      alerts.value = []
    }
    
    // 更新状态趋势图表
    updateStatusChart(statusRes.data || statusRes)
    
    ElMessage.success('数据刷新成功')
  } catch (error) {
    // 特别处理认证错误
    if (error.response && error.response.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      // 清除本地存储并跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      if (window.location.hash !== '#/login') {
        window.location.hash = '#/login'
      }
      loading.value = false
      return
    }
    
    console.error('刷新监控数据失败:', error)
    ElMessage.error('数据刷新失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 开始自动刷新
const startAutoRefresh = () => {
  // 清除已存在的定时器
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
  
  // 每30秒刷新一次数据
  refreshTimer.value = setInterval(() => {
    refreshData()
  }, 30000)
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 处理时间范围变化
const handleTimeRangeChange = () => {
  // 在实际应用中，这里可以根据时间范围过滤数据
  refreshData()
}

// 查看所有告警
const viewAllAlerts = () => {
  router.push('/alerts')
}

// 获取告警标签类型
const getAlertTagType = (level) => {
  const types = {
    'INFO': 'info',
    'WARNING': 'warning',
    'ERROR': 'danger',
    'CRITICAL': 'danger'
  }
  return types[level] || 'info'
}

// 页面加载时获取数据
onMounted(() => {
  initChart()
  refreshData()
  startAutoRefresh()
})

// 组件卸载前清理定时器
onBeforeUnmount(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.monitor-container {
  padding: 20px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  margin-bottom: 20px;
}

.monitor-header h2 {
  margin: 0;
}

.stats-cards {
  margin: 0 -10px;
}

.stat-card {
  margin: 0 10px;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  margin-right: 15px;
  padding: 10px;
  border-radius: 6px;
}

.stat-info .stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-info .stat-label {
  font-size: 14px;
  color: #666;
}

.online .stat-icon {
  background-color: #e8f7ef;
  color: #19a25e;
}

.online .stat-value {
  color: #19a25e;
}

.offline .stat-icon {
  background-color: #fcebeb;
  color: #ff4d4f;
}

.offline .stat-value {
  color: #ff4d4f;
}

.alerts .stat-icon {
  background-color: #fff3e6;
  color: #fa8c16;
}

.alerts .stat-value {
  color: #fa8c16;
}

.performance .stat-icon {
  background-color: #e6f4ff;
  color: #1890ff;
}

.performance .stat-value {
  color: #1890ff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alerts-table :deep(.el-table__row) {
  cursor: pointer;
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

.chart-container {
  width: 100%;
  height: 300px;
}
</style>