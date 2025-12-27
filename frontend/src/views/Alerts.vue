<template>
  <div class="alerts-container">
    <div class="alerts-header">
      <h2>告警管理</h2>
      <div class="actions">
        <el-button type="primary" @click="fetchAlerts">刷新</el-button>
        <el-button @click="clearFilters">清空条件</el-button>
      </div>
    </div>
    
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input 
            v-model="filters.search" 
            placeholder="关键字搜索" 
            clearable
            @clear="fetchAlerts"
            @keyup.enter="fetchAlerts"
          />
        </el-col>
        <el-col :span="6">
          <el-select 
            v-model="filters.severity" 
            placeholder="告警级别" 
            clearable 
            style="width: 100%"
            @change="fetchAlerts"
          >
            <el-option label="全部" value="" />
            <el-option label="严重(Critical)" value="Critical" />
            <el-option label="主要(Major)" value="Major" />
            <el-option label="次要(Minor)" value="Minor" />
            <el-option label="警告(Warning)" value="Warning" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select 
            v-model="filters.status" 
            placeholder="告警状态" 
            clearable 
            style="width: 100%"
            @change="fetchAlerts"
          >
            <el-option label="全部" value="" />
            <el-option label="新建(New)" value="New" />
            <el-option label="已确认(Acknowledged)" value="Acknowledged" />
            <el-option label="已解决(Resolved)" value="Resolved" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>
    
    <el-card class="alerts-card">
      <template #header>
        <div class="card-header">
          <span>告警列表</span>
        </div>
      </template>
      
      <el-table 
        :data="alerts" 
        v-loading="loading"
        style="width: 100%"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="time" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.time) }}
          </template>
        </el-table-column>
        <el-table-column prop="device" label="设备" width="150" />
        <el-table-column prop="level" label="级别" width="120">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.level)">
              {{ getSeverityLabel(row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- 简化信息展示 -->
        <el-table-column label="告警详情" show-overflow-tooltip>
          <template #default="{ row }">
            <div v-if="row.simple_details && Object.keys(row.simple_details).length > 0">
              <div v-if="row.simple_details.alert_type">
                <strong>{{ row.simple_details.alert_type }}</strong>
              </div>
              <div v-if="row.simple_details.conflict_ip || row.simple_details.conflict_mac">
                冲突IP: {{ row.simple_details.conflict_ip || 'N/A' }} | 
                冲突MAC: {{ row.simple_details.conflict_mac || 'N/A' }}
              </div>
              <div v-if="row.simple_details.conflict_interface || row.simple_details.vlan_id">
                接口: {{ row.simple_details.conflict_interface || 'N/A' }} | 
                VLAN: {{ row.simple_details.vlan_id || 'N/A' }}
              </div>
              <div v-if="row.simple_details.description">
                描述: {{ row.simple_details.description }}
              </div>
            </div>
            <div v-else>
              {{ row.message }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="acknowledgeAlert(row)">确认</el-button>
            <el-button size="small" @click="resolveAlert(row)">解决</el-button>
            <el-button size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 告警详情对话框 -->
    <el-dialog v-model="dialogVisible" title="告警详情" width="60%">
      <el-card v-if="selectedAlert">
        <div v-if="selectedAlert.simple_details && Object.keys(selectedAlert.simple_details).length > 0">
          <el-descriptions title="告警信息" :column="1" border>
            <el-descriptions-item label="告警类型">{{ selectedAlert.simple_details.alert_type }}</el-descriptions-item>
            <el-descriptions-item label="冲突IP地址">{{ selectedAlert.simple_details.conflict_ip }}</el-descriptions-item>
            <el-descriptions-item label="冲突MAC地址">{{ selectedAlert.simple_details.conflict_mac }}</el-descriptions-item>
            <el-descriptions-item label="冲突接口">{{ selectedAlert.simple_details.conflict_interface }}</el-descriptions-item>
            <el-descriptions-item label="VLAN ID">{{ selectedAlert.simple_details.vlan_id }}</el-descriptions-item>
            <el-descriptions-item label="描述">{{ selectedAlert.simple_details.description }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <div v-else>
          <h3>告警内容</h3>
          <pre>{{ selectedAlert.message }}</pre>
        </div>
      </el-card>
    </el-dialog>
  </div>
</template>

<script>
import { getAlerts } from '@/api/alert'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'Alerts',
  data() {
    return {
      filters: {
        search: '',
        severity: '',
        status: ''
      },
      loading: false,
      alerts: [],
      pagination: {
        page: 1,
        pageSize: 10,
        total: 0,
        totalPages: 0
      },
      dialogVisible: false,
      selectedAlert: null
    }
  },
  mounted() {
    this.fetchAlerts()
  },
  methods: {
    async fetchAlerts() {
      this.loading = true
      try {
        const params = {
          page: this.pagination.page,
          pageSize: this.pagination.pageSize,
          search: this.filters.search,
          severity: this.filters.severity || 'all',
          status: this.filters.status || 'all'
        }
        
        const response = await getAlerts(params)
        
        if (response && response.data) {
          this.alerts = response.data
        } else {
          this.alerts = []
        }
        
        if (response && response.pagination) {
          this.pagination.total = response.pagination.total || 0
          this.pagination.totalPages = response.pagination.totalPages || 0
        } else {
          this.pagination.total = 0
          this.pagination.totalPages = 0
        }
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
          this.alerts = []
          this.pagination.total = 0
          this.pagination.totalPages = 0
          this.loading = false
          return
        }
        
        ElMessage.error('获取告警失败: ' + (error.message || '未知错误'))
        console.error('获取告警失败:', error)
        this.alerts = []
        this.pagination.total = 0
        this.pagination.totalPages = 0
      } finally {
        this.loading = false
      }
    },
    
    clearFilters() {
      this.filters = {
        search: '',
        severity: '',
        status: ''
      }
      this.pagination.page = 1
      this.fetchAlerts()
    },
    
    handleSizeChange(val) {
      this.pagination.pageSize = val
      this.pagination.page = 1
      this.fetchAlerts()
    },
    
    handleCurrentChange(val) {
      this.pagination.page = val
      this.fetchAlerts()
    },
    
    acknowledgeAlert(alert) {
      ElMessageBox.confirm(
        `确认要将告警 "${alert.message}" 标记为已确认吗？`,
        '确认告警',
        {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        // 这里应该调用API确认告警
        ElMessage.success('告警已确认')
      }).catch(() => {
        ElMessage.info('取消确认')
      })
    },
    
    resolveAlert(alert) {
      ElMessageBox.confirm(
        `确认要将告警 "${alert.message}" 标记为已解决吗？`,
        '解决告警',
        {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        // 这里应该调用API解决告警
        ElMessage.success('告警已解决')
      }).catch(() => {
        ElMessage.info('取消解决')
      })
    },
    
    formatDate(dateString) {
      if (!dateString) return ''
      return dateString
    },
    
    getSeverityType(severity) {
      const severityMap = {
        'Critical': 'danger',
        'Major': 'warning',
        'Minor': 'info',
        'Warning': 'warning'
      }
      return severityMap[severity] || 'info'
    },
    
    getSeverityLabel(severity) {
      const severityMap = {
        'Critical': '严重',
        'Major': '主要',
        'Minor': '次要',
        'Warning': '警告'
      }
      return severityMap[severity] || severity
    },
    
    showDetail(alert) {
      this.selectedAlert = alert
      this.dialogVisible = true
    }
  }
}
</script>

<style scoped>
.alerts-container {
  padding: 20px;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>