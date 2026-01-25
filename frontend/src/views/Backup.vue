<template>
  <div class="backup-management">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <span>备份管理</span>
          <el-button type="primary" @click="refreshBackups">刷新</el-button>
        </div>
      </template>
      
      <el-table :data="backups" v-loading="loading" stripe style="width: 100%" sortable>
        <el-table-column prop="id" label="备份ID" width="80" sortable></el-table-column>
        <el-table-column prop="device_id" label="设备ID" width="80" sortable></el-table-column>
        <el-table-column prop="device_name" label="设备名称" sortable></el-table-column>
        <el-table-column prop="device_ip" label="设备IP" sortable></el-table-column>
        <el-table-column prop="filename" label="文件名" sortable></el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleDownload(row)">下载</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" ></el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAllConfigBackups, downloadConfigBackup, deleteConfigBackup } from '@/api/backup'
import { getDevices } from '@/api/device'

const backups = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const devices = ref([]) // 存储设备信息

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 获取所有设备信息
const fetchDevices = async () => {
  try {
    const response = await getDevices()
    devices.value = response
  } catch (error) {
    console.error('获取设备列表失败:', error)
    ElMessage.error('获取设备列表失败: ' + (error.message || '未知错误'))
  }
}

// 获取所有备份列表
const fetchBackups = async () => {
  try {
    loading.value = true
    const response = await getAllConfigBackups({
      page: currentPage.value,
      size: pageSize.value
    })
    
    // 根据响应结构调整数据提取方式
    if (response.data) {
      backups.value = response.data.items || response.data || []
      total.value = response.data.total || 0
    } else {
      backups.value = response.items || []
      total.value = response.total || 0
    }
    
    // 为每个备份添加设备名称和IP信息
    backups.value.forEach(backup => {
      const device = devices.value.find(d => d.id === backup.device_id)
      if (device) {
        backup.device_name = device.name
        backup.device_ip = device.management_ip
      } else {
        backup.device_name = '未知设备'
        backup.device_ip = '未知IP'
      }
    })
  } catch (error) {
    console.error('获取备份列表失败:', error)
    ElMessage.error('获取备份列表失败: ' + (error.message || '未知错误'))
    backups.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 刷新备份列表
const refreshBackups = () => {
  fetchBackups()
}

// 处理分页大小变化
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchBackups()
}

// 处理当前页变化
const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchBackups()
}

// 下载备份文件
const handleDownload = async (backup, sanitize = false) => {
  try {
    const response = await downloadConfigBackup(backup.id)
    
    // 确保内容是字符串
    let content = response
    if (content instanceof Blob) {
      // 如果是Blob类型，需要转换为文本
      content = await content.text()
    } else if (typeof content !== 'string') {
      content = String(content)
    }
    
    let filename = backup.filename
    
    // 如果需要脱敏，处理配置内容
    if (sanitize) {
      content = sanitizeConfig(content)
      // 修改文件名为脱敏版本
      const parts = backup.filename.split('.')
      if (parts.length > 1) {
        const ext = parts.pop()
        filename = `${parts.join('.')}_sanitized.${ext}`
      } else {
        filename = `${backup.filename}_sanitized`
      }
    }
    
    // 创建下载链接
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    
    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success(sanitize ? '脱敏配置下载成功' : '配置下载成功')
  } catch (error) {
    ElMessage.error('下载失败: ' + (error.message || '未知错误'))
  }
}

// 删除备份
const handleDelete = (backup) => {
  ElMessageBox.confirm(
    `确认要删除备份文件 "${backup.filename}" 吗？此操作不可恢复！`,
    '警告',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteConfigBackup(backup.id)
      ElMessage.success('删除成功')
      fetchBackups() // 刷新列表
    } catch (error) {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

onMounted(() => {
  fetchDevices() // 先获取设备信息
  fetchBackups() // 再获取备份列表
})
</script>

<style scoped>
.page-header {
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
  justify-content: center;
}
</style>