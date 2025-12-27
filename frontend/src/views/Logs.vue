<template>
  <div class="logs-container">
    <div class="logs-header">
      <h2>日志管理</h2>
      <div class="actions">
        <el-button type="primary" @click="searchLogs" :loading="loading">查询</el-button>
        <el-button @click="clearFilters">清空条件</el-button>
      </div>
    </div>
    
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input 
            v-model="filters.keyword" 
            placeholder="关键字搜索" 
            clearable
          />
        </el-col>
        <el-col :span="6">
          <el-select 
            v-model="filters.level" 
            placeholder="日志级别" 
            clearable 
            style="width: 100%"
          >
            <el-option label="全部" value="" />
            <el-option label="调试(DEBUG)" value="DEBUG" />
            <el-option label="信息(INFO)" value="INFO" />
            <el-option label="警告(WARNING)" value="WARNING" />
            <el-option label="错误(ERROR)" value="ERROR" />
            <el-option label="严重(FATAL)" value="FATAL" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DDTHH:mm:ss"
            format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="6">
          <el-button type="success" @click="exportLogs" :loading="exportLoading">导出日志</el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <el-card class="logs-card">
      <template #header>
        <div class="card-header">
          <span>日志列表</span>
        </div>
      </template>
      
      <el-table 
        :data="logs" 
        v-loading="loading"
        style="width: 100%"
        stripe
      >
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLogLevelType(row.level)">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user.username" label="用户" width="120">
          <template #default="{ row }">
            {{ row.user?.username || '系统' }}
          </template>
        </el-table-column>
        <el-table-column prop="device.name" label="设备" width="150">
          <template #default="{ row }">
            {{ row.device?.name || '系统' }}
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="message" label="日志内容" show-overflow-tooltip />
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import { getLogs, exportLogs } from '@/api/logs'
import { ElMessage } from 'element-plus'

export default {
  name: 'Logs',
  data() {
    return {
      filters: {
        keyword: '',
        level: '',
        module: ''
      },
      dateRange: [],
      loading: false,
      exportLoading: false,
      logs: [],
      pagination: {
        currentPage: 1,
        pageSize: 10,
        total: 0
      }
    }
  },
  mounted() {
    this.searchLogs()
  },
  methods: {
    async searchLogs() {
      this.loading = true
      try {
        const params = {
          page: this.pagination.currentPage,
          pageSize: this.pagination.pageSize,
          keyword: this.filters.keyword,
          level: this.filters.level || 'all'
        }
        
        if (this.dateRange && this.dateRange.length === 2) {
          params.start_date = this.dateRange[0]
          params.end_date = this.dateRange[1]
        }
        
        const response = await getLogs(params)
        
        // 安全地解析响应数据
        if (response && response.data) {
          this.logs = response.data
        } else {
          this.logs = []
        }
        
        // 安全地解析分页信息
        if (response && response.pagination) {
          this.pagination.total = response.pagination.total || 0
        } else if (response && response.total) {
          // 兼容另一种可能的响应格式
          this.pagination.total = response.total || 0
        } else {
          this.pagination.total = 0
        }
      } catch (error) {
        ElMessage.error('获取日志失败: ' + (error.message || '未知错误'))
        console.error('获取日志失败:', error)
        // 出错时重置数据
        this.logs = []
        this.pagination.total = 0
      } finally {
        this.loading = false
      }
    },
    
    clearFilters() {
      this.filters = {
        keyword: '',
        level: '',
        module: ''
      }
      this.dateRange = []
      this.pagination.currentPage = 1
      this.searchLogs()
    },
    
    handleSizeChange(val) {
      this.pagination.pageSize = val
      this.pagination.currentPage = 1
      this.searchLogs()
    },
    
    handleCurrentChange(val) {
      this.pagination.currentPage = val
      this.searchLogs()
    },
    
    async exportLogs() {
      this.exportLoading = true
      try {
        const params = {
          pageSize: 10000,
          keyword: this.filters.keyword,
          level: this.filters.level || 'all'
        }
        
        if (this.dateRange && this.dateRange.length === 2) {
          params.start_date = this.dateRange[0]
          params.end_date = this.dateRange[1]
        }
        
        const response = await exportLogs(params)
        
        // 处理Blob响应
        const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', 'system_logs.csv')
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        ElMessage.success('日志导出成功')
      } catch (error) {
        ElMessage.error('导出日志失败: ' + (error.message || '未知错误'))
        console.error('导出日志失败:', error)
      } finally {
        this.exportLoading = false
      }
    },
    
    getLogLevelType(level) {
      const levelMap = {
        'DEBUG': 'info',
        'INFO': 'primary',
        'WARNING': 'warning',
        'ERROR': 'danger',
        'FATAL': 'danger'
      }
      return levelMap[level] || 'info'
    },
    
    formatDate(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.logs-container {
  padding: 20px;
}

.logs-header {
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