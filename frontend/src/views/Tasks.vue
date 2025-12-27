<template>
  <div class="tasks-container">
    <el-card class="tasks-header">
      <div class="header-content">
        <h2>任务管理</h2>
        <div class="header-actions">
          <el-button type="primary" @click="fetchTasks">刷新</el-button>
          <el-button @click="showCreateTaskDialog">创建任务</el-button>
        </div>
      </div>
    </el-card>

    <el-card class="tasks-filter">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="任务状态">
          <el-select v-model="filterForm.status" placeholder="请选择任务状态" clearable>
            <el-option label="全部" value=""></el-option>
            <el-option label="等待中" value="pending"></el-option>
            <el-option label="进行中" value="running"></el-option>
            <el-option label="已完成" value="completed"></el-option>
            <el-option label="失败" value="failed"></el-option>
            <el-option label="已取消" value="cancelled"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="任务类型">
          <el-select v-model="filterForm.type" placeholder="请选择任务类型" clearable>
            <el-option label="配置备份" value="config_backup"></el-option>
            <el-option label="设备巡检" value="device_inspection"></el-option>
            <el-option label="固件升级" value="firmware_upgrade"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchTasks">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="tasks-table">
      <el-table :data="paginatedTasks" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="任务ID" width="80"></el-table-column>
        <el-table-column prop="name" label="任务名称" show-overflow-tooltip></el-table-column>
        <el-table-column prop="task_type" label="任务类型" width="120">
          <template #default="scope">
            <el-tag :type="getTypeTagType(scope.row.task_type)">
              {{ getTypeText(scope.row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusTagType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="150">
          <template #default="scope">
            <el-progress 
              :percentage="scope.row.progress" 
              :status="getProgressStatus(scope.row.status)">
            </el-progress>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.completed_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="viewTaskDetails(scope.row)">详情</el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="cancelTask(scope.row)" 
              :disabled="scope.row.status !== 'pending' && scope.row.status !== 'running'">
              取消
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteTask(scope.row)"
              :disabled="scope.row.status === 'running'">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total">
        </el-pagination>
      </div>
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog title="创建任务" v-model="taskDialogVisible" width="600px">
      <el-form :model="newTask" :rules="taskRules" ref="taskForm" label-width="120px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="newTask.name"></el-input>
        </el-form-item>
        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="newTask.task_type" placeholder="请选择任务类型" style="width: 100%" @change="onTaskTypeChange">
            <el-option label="配置备份" value="config_backup"></el-option>
            <el-option label="设备巡检" value="device_inspection"></el-option>
            <el-option label="固件升级" value="firmware_upgrade"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="目标设备" prop="target_device_ids">
          <el-select 
            v-model="newTask.target_device_ids" 
            multiple 
            filterable
            collapse-tags
            collapse-tags-tooltip
            placeholder="请选择目标设备"
            style="width: 100%">
            <template #header>
              <div style="padding: 4px 0; border-bottom: 1px solid #eee;">
                <el-checkbox 
                  :indeterminate="isIndeterminate" 
                  v-model="selectAllDevices" 
                  @change="handleSelectAllDevices">
                  全选
                </el-checkbox>
              </div>
            </template>
            <el-option
              v-for="device in availableDevices"
              :key="device.id"
              :label="`${device.name} (${device.management_ip})`"
              :value="device.id">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="计划执行时间" prop="scheduled_time">
          <el-date-picker
            v-model="newTask.scheduled_time"
            type="datetime"
            placeholder="选择日期时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%">
          </el-date-picker>
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input 
            v-model="newTask.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入任务描述">
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="taskDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createTask">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog title="任务详情" v-model="detailDialogVisible" width="700px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
        <el-descriptions-item label="任务名称">{{ currentTask.name }}</el-descriptions-item>
        <el-descriptions-item label="任务类型">
          <el-tag :type="getTypeTagType(currentTask.task_type)">
            {{ getTypeText(currentTask.task_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusTagType(currentTask.status)">
            {{ getStatusText(currentTask.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进度">
          <el-progress 
            :percentage="currentTask.progress" 
            :status="getProgressStatus(currentTask.status)">
          </el-progress>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentTask.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatDate(currentTask.started_at) }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ formatDate(currentTask.completed_at) }}</el-descriptions-item>
        <el-descriptions-item label="目标设备">
          <el-tag 
            v-for="device in currentTask.target_devices" 
            :key="device.id" 
            style="margin-right: 5px;">
            {{ device.name }} ({{ device.management_ip }})
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="任务描述">{{ currentTask.description }}</el-descriptions-item>
        <el-descriptions-item label="执行日志">
          <el-input 
            type="textarea" 
            :rows="5" 
            v-model="currentTask.logs" 
            readonly>
          </el-input>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button 
            v-if="currentTask.status === 'pending'" 
            type="primary" 
            @click="executeTask(currentTask)">
            立即执行
          </el-button>
          <el-button v-if="currentTask.task_type === 'config_backup' && currentTask.status === 'completed'" 
                     type="primary" 
                     @click="viewBackupResults">
            查看备份结果
          </el-button>
          <el-button 
            v-if="currentTask.task_type === 'device_inspection' && currentTask.status === 'completed'" 
            type="success" 
            @click="downloadInspectionReport(currentTask)">
            下载巡检报告
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getTasks, createTask, getTaskDetail, cancelTask, deleteTask, executeTask } from '@/api/task'
import { getDevices } from '@/api/device'
import { getDeviceBackups } from '@/api/device'

export default {
  name: 'Tasks',
  data() {
    return {
      loading: false,
      tasks: [],
      availableDevices: [],
      currentPage: 1,
      pageSize: 10,
      total: 0,
      filterForm: {
        status: '',
        type: ''
      },
      taskDialogVisible: false,
      detailDialogVisible: false,
      selectAllDevices: false,
      isIndeterminate: false,
      newTask: {
        name: '',
        task_type: '',
        target_device_ids: [],
        scheduled_time: '',
        description: ''
      },
      currentTask: {},
      taskRules: {
        name: [
          { required: true, message: '请输入任务名称', trigger: 'blur' }
        ],
        task_type: [
          { required: true, message: '请选择任务类型', trigger: 'change' }
        ],
        target_device_ids: [
          { required: true, message: '请选择目标设备', trigger: 'change' }
        ]
      }
    }
  },
  computed: {
    filteredTasks() {
      return this.tasks
    },
    paginatedTasks() {
      // 计算分页后的任务列表
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.tasks.slice(start, end)
    }
  },
  watch: {
    'newTask.target_device_ids': {
      handler(val) {
        const checkedCount = val.length
        this.selectAllDevices = checkedCount === this.availableDevices.length && checkedCount > 0
        this.isIndeterminate = checkedCount > 0 && checkedCount < this.availableDevices.length
      },
      deep: true
    }
  },
  mounted() {
    this.fetchTasks()
    this.loadDevices()
  },
  methods: {
    async fetchTasks() {
      this.loading = true
      try {
        const params = {
          page: this.currentPage,
          page_size: this.pageSize,
          status: this.filterForm.status || undefined,
          task_type: this.filterForm.type || undefined
        }
        
        const response = await getTasks(params)
        this.tasks = response.data
        this.total = response.total
        this.$message.success('任务列表加载成功')
      } catch (error) {
        this.$message.error('获取任务列表失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.loading = false
      }
    },
    async loadDevices() {
      try {
        const response = await getDevices()
        this.availableDevices = response
      } catch (error) {
        this.$message.error('获取设备列表失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    getTypeTagType(type) {
      switch (type) {
        case 'config_backup': return 'primary'
        case 'device_inspection': return 'success'
        case 'firmware_upgrade': return 'warning'
        case 'config_restore': return 'info'
        case 'security_audit': return 'danger'
        case 'performance_monitoring': return 'warning'
        case 'network_optimization': return 'primary'
        default: return ''
      }
    },
    getTypeText(type) {
      switch (type) {
        case 'config_backup': return '配置备份'
        case 'device_inspection': return '设备巡检'
        case 'firmware_upgrade': return '固件升级'
        default: return type
      }
    },
    getStatusTagType(status) {
      switch (status) {
        case 'pending': return 'info'
        case 'running': return 'warning'
        case 'completed': return 'success'
        case 'failed': return 'danger'
        case 'cancelled': return 'info'
        default: return ''
      }
    },
    getStatusText(status) {
      switch (status) {
        case 'pending': return '等待中'
        case 'running': return '进行中'
        case 'completed': return '已完成'
        case 'failed': return '失败'
        case 'cancelled': return '已取消'
        default: return status
      }
    },
    getProgressStatus(status) {
      switch (status) {
        case 'completed': return 'success'
        case 'failed': return 'exception'
        case 'cancelled': return 'exception'
        default: return null
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    },
    showCreateTaskDialog() {
      this.newTask = {
        name: '',
        task_type: '',
        target_device_ids: [],
        scheduled_time: '',
        description: ''
      }
      this.selectAllDevices = false
      this.isIndeterminate = false
      this.taskDialogVisible = true
    },
    onTaskTypeChange(value) {
      // 当任务类型改变时的处理逻辑
      console.log('任务类型已更改:', value)
    },
    handleSelectAllDevices(val) {
      if (val) {
        this.newTask.target_device_ids = this.availableDevices.map(device => device.id)
      } else {
        this.newTask.target_device_ids = []
      }
      this.isIndeterminate = false
    },
    createTask() {
      this.$refs.taskForm.validate(async (valid) => {
        if (valid) {
          try {
            // 处理发送到后端的数据格式
            const taskData = {
              name: this.newTask.name,
              task_type: this.newTask.task_type,
              target_device_ids: this.newTask.target_device_ids,
              description: this.newTask.description || undefined
            }
            
            // 只有当计划执行时间不为空时才发送该字段
            if (this.newTask.scheduled_time) {
              taskData.scheduled_time = this.newTask.scheduled_time
            }
            
            const response = await createTask(taskData)
            this.tasks.unshift(response)
            this.taskDialogVisible = false
            this.$message.success('任务创建成功')
            this.fetchTasks()
          } catch (error) {
            // 特别处理认证错误
            if (error.response && error.response.status === 401) {
              this.$message.error('登录已过期，请重新登录')
              // 清除本地存储并跳转到登录页
              localStorage.removeItem('token')
              localStorage.removeItem('username')
              if (window.location.hash !== '#/login') {
                window.location.hash = '#/login'
              }
              return
            }
            
            this.$message.error('任务创建失败: ' + (error.response?.data?.detail || error.message))
          }
        }
      })
    },
    async viewTaskDetails(task) {
      try {
        const response = await getTaskDetail(task.id)
        this.currentTask = response
        this.detailDialogVisible = true
      } catch (error) {
        // 特别处理认证错误
        if (error.response && error.response.status === 401) {
          this.$message.error('登录已过期，请重新登录')
          // 清除本地存储并跳转到登录页
          localStorage.removeItem('token')
          localStorage.removeItem('username')
          if (window.location.hash !== '#/login') {
            window.location.hash = '#/login'
          }
          return
        }
        
        this.$message.error('获取任务详情失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    async executeTask(task) {
      try {
        await this.$confirm(`确认立即执行任务 "${task.name}" 吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await executeTask(task.id)
        this.$message.success('任务已开始执行')
        this.detailDialogVisible = false
        this.fetchTasks()
      } catch (error) {
        if (error !== 'cancel') {
          // 特别处理认证错误
          if (error.response && error.response.status === 401) {
            this.$message.error('登录已过期，请重新登录')
            // 清除本地存储并跳转到登录页
            localStorage.removeItem('token')
            localStorage.removeItem('username')
            if (window.location.hash !== '#/login') {
              window.location.hash = '#/login'
            }
            return
          }
          
          this.$message.error('执行任务失败: ' + (error.response?.data?.detail || error.message))
        }
      }
    },
    async cancelTask(task) {
      try {
        await this.$confirm(`确认取消任务 "${task.name}" 吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await cancelTask(task.id)
        this.$message.success('任务已取消')
        this.fetchTasks()
      } catch (error) {
        if (error !== 'cancel') {
          // 特别处理认证错误
          if (error.response && error.response.status === 401) {
            this.$message.error('登录已过期，请重新登录')
            // 清除本地存储并跳转到登录页
            localStorage.removeItem('token')
            localStorage.removeItem('username')
            if (window.location.hash !== '#/login') {
              window.location.hash = '#/login'
            }
            return
          }
          
          this.$message.error('取消任务失败: ' + (error.response?.data?.detail || error.message))
        }
      }
    },
    async deleteTask(task) {
      try {
        await this.$confirm(`确认删除任务 "${task.name}" 吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await deleteTask(task.id)
        this.$message.success('任务已删除')
        this.fetchTasks()
      } catch (error) {
        if (error !== 'cancel') {
          // 特别处理认证错误
          if (error.response && error.response.status === 401) {
            this.$message.error('登录已过期，请重新登录')
            // 清除本地存储并跳转到登录页
            localStorage.removeItem('token')
            localStorage.removeItem('username')
            if (window.location.hash !== '#/login') {
              window.location.hash = '#/login'
            }
            return
          }
          
          this.$message.error('删除任务失败: ' + (error.response?.data?.detail || error.message))
        }
      }
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
      this.fetchTasks()
    },
    handleCurrentChange(val) {
      this.currentPage = val
      this.fetchTasks()
    },
    resetFilters() {
      this.filterForm = {
        status: '',
        type: ''
      }
      this.fetchTasks()
    },
    async viewBackupResults() {
      // 查看配置备份任务的结果
      try {
        // 跳转到备份管理页面，并传递设备ID参数
        this.$router.push({ name: 'Backup' })
        this.detailDialogVisible = false
      } catch (error) {
        this.$message.error('跳转到备份页面失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    // 下载设备巡检报告
    async downloadInspectionReport(task) {
      try {
        // 构建下载URL - 使用项目中已配置的axios实例
        const token = localStorage.getItem('access_token')
        if (!token) {
          this.$message.error('未找到访问令牌')
          return
        }
        
        // 直接使用fetch API来处理文件下载
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/tasks/${task.id}/download-report`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
        
        if (!response.ok) {
          // 尝试获取错误响应文本
          const errorText = await response.text().catch(() => '未知错误')
          let errorMessage = errorText
          try {
            // 尝试解析JSON错误响应
            const errorJson = JSON.parse(errorText)
            errorMessage = errorJson.detail || errorText
          } catch (e) {
            // 如果不是JSON格式，使用原始文本
          }
          throw new Error(errorMessage)
        }
        
        // 获取响应数据
        const blob = await response.blob()
        
        // 创建下载链接
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `inspection_report_${task.id}.txt`)
        document.body.appendChild(link)
        link.click()
        
        // 清理
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        this.$message.success('巡检报告开始下载')
      } catch (error) {
        console.error('下载巡检报告失败:', error)
        this.$message.error('下载巡检报告失败: ' + (error.message || '未知错误'))
      }
    }
  }
}
</script>

<style scoped>
.tasks-container {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
