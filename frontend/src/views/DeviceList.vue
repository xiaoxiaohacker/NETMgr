<template>
  <div class="device-management">
    <h1>设备管理</h1>
    
    <!-- 搜索和操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="handleAddDevice">添加设备</el-button>
      <el-button @click="loadDevices" :loading="loading">刷新</el-button>
      <el-button @click="handleBatchImport">批量导入</el-button>
      <el-button @click="exportDeviceList">导出设备列表</el-button>
      
      <!-- 批量操作按钮 -->
      <el-dropdown v-if="selectedDevices.length > 0 || selectAllMode" @command="handleBatchAction" style="margin-left: 10px;">
        <el-button type="warning">
          批量操作 <el-icon><arrow-down /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="backup">批量备份</el-dropdown-item>
            <el-dropdown-item command="delete">批量删除</el-dropdown-item>
            <el-dropdown-item command="export">导出选中项</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      
      <!-- 全选开关 -->
      <el-switch
        v-model="selectAllMode"
        @change="toggleSelectAll"
        active-text="选择所有匹配项"
        style="margin-left: 15px;"
      />
      
      <!-- 高级搜索按钮 -->
      <el-button @click="showAdvancedSearch = !showAdvancedSearch" style="margin-left: 10px;">
        {{ showAdvancedSearch ? '隐藏高级搜索' : '高级搜索' }}
      </el-button>
      
      <div class="search-box">
        <el-input
          :model-value="searchText"
          @input="debouncedSearch"
          placeholder="搜索设备 (支持多关键词)"
          clearable
          style="width: 300px; margin-left: 20px;"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>
    
    <!-- 高级搜索面板 -->
    <div v-show="showAdvancedSearch" class="advanced-search-panel">
      <el-form :inline="true" :model="advancedSearchForm" class="demo-form-inline">
        <el-form-item label="设备名称">
          <el-input v-model="advancedSearchForm.name" placeholder="设备名称" />
        </el-form-item>
        <el-form-item label="管理IP">
          <el-input v-model="advancedSearchForm.ip" placeholder="管理IP" />
        </el-form-item>
        <el-form-item label="厂商">
          <el-select v-model="advancedSearchForm.vendor" placeholder="厂商" clearable>
            <el-option label="Cisco" value="Cisco" />
            <el-option label="Huawei" value="Huawei" />
            <el-option label="H3C" value="H3C" />
            <el-option label="Ruijie" value="Ruijie" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="advancedSearchForm.deviceType" placeholder="设备类型" clearable>
            <el-option label="交换机" value="switch" />
            <el-option label="路由器" value="router" />
            <el-option label="防火墙" value="firewall" />
            <el-option label="服务器" value="server" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="advancedSearchForm.status" placeholder="状态" clearable>
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleAdvancedSearch">搜索</el-button>
          <el-button @click="resetAdvancedSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 设备表格 -->
    <el-table
      :data="filteredDevices"
      v-loading="loading"
      element-loading-text="加载中..."
      border
      style="width: 100%; margin-top: 20px;"
      @selection-change="handleSelectionChange"
      :default-sort="{prop: 'id', order: 'ascending'}"
      :row-class-name="tableRowClassName"
      @sort-change="handleSortChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" sortable="custom" />
      <el-table-column prop="name" label="设备名称" sortable="custom">
        <template #default="{ row }">
          <el-link type="primary" @click="goToDeviceDetail(row.id)">{{ row.name }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="management_ip" label="管理IP" sortable="custom" />
      <el-table-column prop="vendor" label="厂商" sortable="custom" />
      <el-table-column prop="model" label="型号" sortable="custom" />
      <el-table-column prop="device_type" label="设备类型" sortable="custom" />
      <el-table-column prop="location" label="位置" sortable="custom" />
      <el-table-column prop="status" label="状态" sortable="custom" :filters="[
        { text: '在线', value: 'online' },
        { text: '离线', value: 'offline' }
      ]" :filter-method="filterStatus">
        <template #default="{ row }">
          <el-tag 
            :type="row.status === 'online' ? 'success' : row.status === 'offline' ? 'danger' : 'warning'"
            :effect="row.status === 'online' ? 'dark' : 'light'"
          >
            {{ row.status === 'online' ? '在线' : row.status === 'offline' ? '离线' : row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handleView(row)">查看</el-button>
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" @click="handleCheckConnectivity(row)">连通性</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <el-pagination
      v-if="totalFilteredDevices > pageSize"
      :current-page="currentPage"
      :page-sizes="[10, 20, 50, 100]"
      :page-size="pageSize"
      :total="totalFilteredDevices"
      layout="total, sizes, prev, pager, next, jumper"
      style="margin-top: 20px; text-align: right;"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />
    
    <!-- 设备编辑对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        :model="currentDevice"
        :rules="deviceRules"
        ref="deviceForm"
        label-width="100px"
      >
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="currentDevice.name" />
        </el-form-item>
        <el-form-item label="管理IP" prop="management_ip">
          <el-input v-model="currentDevice.management_ip" />
        </el-form-item>
        <el-form-item label="厂商" prop="vendor">
          <el-select v-model="currentDevice.vendor" placeholder="请选择厂商">
            <el-option label="Cisco" value="Cisco" />
            <el-option label="Huawei" value="Huawei" />
            <el-option label="H3C" value="H3C" />
            <el-option label="ruijie" value="ruijie" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="currentDevice.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="currentDevice.password" type="password" />
        </el-form-item>
        <el-form-item label="使能密码" prop="enable_password">
          <el-input v-model="currentDevice.enable_password" type="password" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="currentDevice.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="currentDevice.location" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveDevice">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 批量导入对话框 -->
    <el-dialog
      title="批量导入设备"
      v-model="importDialogVisible"
      width="500px"
    >
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".csv"
      >
        <el-button slot="trigger" type="primary">选择文件</el-button>
        <div class="el-upload__tip">
          只能上传CSV文件，且不超过10MB
        </div>
      </el-upload>
      
      <div style="margin-top: 15px;">
        <el-button type="success" @click="downloadTemplate" size="small">
          下载模板文件
        </el-button>
        <span style="margin-left: 10px; font-size: 12px; color: #999;">
          请先下载模板文件，按格式填写后上传
        </span>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitImport">导入</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import {
  getDevices,
  addDevice,
  updateDevice,
  deleteDevice,
  checkConnectivity,
  batchImportDevices,
  backupDeviceConfig
} from '@/api/device'

// 批量操作相关数据
const selectedDevices = ref([])

const router = useRouter()

// 设备列表相关数据
const devices = ref([])
const loading = ref(false)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const showAdvancedSearch = ref(false)

// 高级搜索表单
const advancedSearchForm = reactive({
  name: '',
  ip: '',
  vendor: '',
  deviceType: '',
  status: ''
})

// 定时器引用
const statusCheckTimer = ref(null)

// 对话框相关数据
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)

// 文件上传引用
const uploadRef = ref(null)
const importFile = ref(null)

// 当前编辑的设备
const currentDevice = reactive({
  id: undefined,
  name: '',
  management_ip: '',
  vendor: '',
  model: '',
  os_version: '',
  serial_number: '',
  username: '',
  password: '',
  enable_password: '',
  port: 22,
  device_type: 'switch',
  location: ''
})

// 表单验证规则
const deviceRules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  management_ip: [
    { required: true, message: '请输入管理IP', trigger: 'blur' }
  ],
  vendor: [{ required: true, message: '请选择厂商', trigger: 'change' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 表单引用
const deviceForm = ref(null)

// 添加一个新的ref来跟踪是否选择了所有设备
const selectAllMode = ref(false)
const totalFilteredDevices = ref(0)

// 添加排序相关响应式变量
const sortProperty = ref('id')
const sortOrder = ref('ascending') // 'ascending' 或 'descending'

// 计算过滤后的设备列表（包含分页和排序）
const filteredDevices = computed(() => {
  let result = [...devices.value] // 创建副本避免修改原始数据
  
  // 处理普通文本搜索
  if (searchText.value) {
    const searchTerms = searchText.value.toLowerCase().trim().split(/\s+/)
    result = result.filter(device => {
      // 搜索设备的所有文本字段
      const searchableFields = [
        device.name,
        device.management_ip,
        device.vendor,
        device.model,
        device.os_version,
        device.serial_number,
        device.location,
        device.device_type,
        device.status
      ].filter(Boolean) // 过滤掉undefined或null值
      
      const searchText = searchableFields.join(' ').toLowerCase()
      
      // 支持多关键词搜索（AND关系）
      return searchTerms.every(term => searchText.includes(term))
    })
  }
  
  // 处理高级搜索
  if (advancedSearchForm.name) {
    const nameTerm = advancedSearchForm.name.toLowerCase()
    result = result.filter(device => 
      device.name && device.name.toLowerCase().includes(nameTerm)
    )
  }
  
  if (advancedSearchForm.ip) {
    const ipTerm = advancedSearchForm.ip.toLowerCase()
    result = result.filter(device => 
      device.management_ip && device.management_ip.toLowerCase().includes(ipTerm)
    )
  }
  
  if (advancedSearchForm.vendor) {
    result = result.filter(device => device.vendor === advancedSearchForm.vendor)
  }
  
  if (advancedSearchForm.deviceType) {
    result = result.filter(device => device.device_type === advancedSearchForm.deviceType)
  }
  
  if (advancedSearchForm.status) {
    result = result.filter(device => device.status === advancedSearchForm.status)
  }
  
  // 应用排序
  result.sort((a, b) => {
    let valA = a[sortProperty.value]
    let valB = b[sortProperty.value]
    
    // 如果是字符串，转换为小写进行比较
    if (typeof valA === 'string' && typeof valB === 'string') {
      valA = valA.toLowerCase()
      valB = valB.toLowerCase()
    }
    
    // 如果是数字，直接比较
    if (typeof valA === 'number' && typeof valB === 'number') {
      return sortOrder.value === 'ascending' ? valA - valB : valB - valA
    }
    
    // 字符串比较
    if (valA < valB) {
      return sortOrder.value === 'ascending' ? -1 : 1
    }
    if (valA > valB) {
      return sortOrder.value === 'ascending' ? 1 : -1
    }
    return 0
  })
  
  // 更新过滤后的设备总数
  totalFilteredDevices.value = result.length
  
  // 分页处理
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

// 添加搜索防抖功能
const debouncedSearch = debounce((value) => {
  searchText.value = value
  currentPage.value = 1 // 重置到第一页
}, 300)

// 防抖函数
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// 修改处理选择变化的函数
const handleSelectionChange = (selection) => {
  // 只有当不是全选模式时才更新selectedDevices
  if (!selectAllMode.value) {
    selectedDevices.value = selection
  }
}

// 新增：切换全选模式
const toggleSelectAll = (value) => {
  // value参数是el-switch组件传递的当前值
  selectAllMode.value = value
  if (value) {
    // 全选模式下，将所有过滤后的设备存储起来
    selectedDevices.value = [...devices.value]
    ElMessage.info(`已选择所有 ${totalFilteredDevices.value} 个匹配的设备`)
  } else {
    // 退出全选模式，清空选择
    selectedDevices.value = []
  }
}

// 为表格行添加CSS类名
const tableRowClassName = ({ row }) => {
  if (row.status === 'offline') {
    return 'offline-row'
  }
  return ''
}

// 状态过滤方法
const filterStatus = (value, row) => {
  return row.status === value
}

// 排序处理方法
const handleSortChange = ({ column, prop, order }) => {
  if (prop && order) {
    sortProperty.value = prop
    sortOrder.value = order
  } else {
    // 如果没有排序要求，恢复默认排序（按ID升序）
    sortProperty.value = 'id'
    sortOrder.value = 'ascending'
  }
}

// 跳转到设备详情页
const goToDeviceDetail = (deviceId) => {
  router.push(`/devices/${deviceId}`)
}

// 加载设备列表
const loadDevices = async () => {
  console.log('开始加载设备列表...')
  loading.value = true
  try {
    const response = await getDevices()
    console.log('获取到设备数据:', response)
    devices.value = response
    
    // 如果处于全选模式，需要更新选中的设备列表
    if (selectAllMode.value) {
      selectedDevices.value = [...devices.value]
      ElMessage.info(`已选择所有 ${devices.value.length} 个设备`)
    }
    
    ElMessage.success('设备列表刷新成功')
  } catch (error) {
    console.error('加载设备列表失败:', error)
    ElMessage.error('加载设备列表失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
    console.log('设备列表加载完成')
  }
}

// 处理添加设备
const handleAddDevice = () => {
  dialogTitle.value = '添加设备'
  isEdit.value = false
  resetCurrentDevice()
  dialogVisible.value = true
}

// 处理编辑设备
const handleEdit = (device) => {
  dialogTitle.value = '编辑设备'
  isEdit.value = true
  Object.assign(currentDevice, device)
  dialogVisible.value = true
}

// 处理查看设备
const handleView = (device) => {
  dialogTitle.value = '查看设备'
  isEdit.value = true
  Object.assign(currentDevice, device)
  // 查看模式下禁用编辑
  dialogVisible.value = true
}

// 处理删除设备
const handleDelete = (device) => {
  ElMessageBox.confirm(
    `确认要删除设备 "${device.name}" 吗？此操作不可恢复！`,
    '警告',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteDevice(device.id)
      ElMessage.success('删除成功')
      loadDevices()
    } catch (error) {
      ElMessage.error('删除失败: ' + error.message)
    }
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

// 处理检查连通性
const handleCheckConnectivity = async (device) => {
  try {
    const response = await checkConnectivity(device.management_ip)
    
    // 根据检查结果显示不同的消息
    if (response.is_reachable) {
      ElMessage.success(`设备 ${device.name} 连通性检查成功，响应时间: ${response.response_time}ms`)
    } else {
      ElMessage.error(`设备 ${device.name} 连通性检查失败，设备不可达`)
    }
    
    console.log('连通性检查结果:', response)
    
    // 更新设备状态
    const updatedDevice = devices.value.find(d => d.id === device.id)
    if (updatedDevice) {
      updatedDevice.status = response.is_reachable ? 'online' : 'offline'
      // 如果有响应时间，也可以更新
      if (response.response_time !== null) {
        console.log(`响应时间: ${response.response_time}ms`)
      }
    }
  } catch (error) {
    ElMessage.error(`连通性检查失败: ${error.message}`)
  }
}

// WebSocket连接相关变量
const wsConnection = ref(null)
const wsReconnectAttempts = ref(0)
const maxReconnectAttempts = 5
const reconnectInterval = 5000 // 5秒重连间隔

// 初始化WebSocket连接
const initWebSocket = () => {
  // 检查是否存在有效的token - 使用正确的键名 access_token
  const token = localStorage.getItem('access_token')
  if (!token) {
    console.warn('没有找到有效token，无法初始化WebSocket连接')
    return
  }
  
  // 获取后端API的基础URL并替换协议以构建WebSocket URL
  const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  let wsUrl = apiUrl.replace('http', 'ws') + '/ws/device-status'
  
  // 如果URL中包含token，将其添加到WebSocket连接URL中
  wsUrl += `?token=${token}`
  
  try {
    wsConnection.value = new WebSocket(wsUrl)
    
    wsConnection.value.onopen = () => {
      console.log('WebSocket连接已建立')
      wsReconnectAttempts.value = 0 // 连接成功，重置重连计数
    }
    
    wsConnection.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('收到WebSocket消息:', data)
        
        // 处理设备状态更新消息
        if (data.type === 'device_status_update') {
          updateDeviceStatusInList(data.device_id, data.status, data.message)
        } else if (data.type === 'batch_device_status_update') {
          // 批量更新设备状态
          data.updates.forEach(update => {
            updateDeviceStatusInList(update.device_id, update.status, update.message)
          })
        }
      } catch (error) {
        console.error('处理WebSocket消息时出错:', error)
      }
    }
    
    wsConnection.value.onclose = () => {
      console.log('WebSocket连接已关闭')
      attemptReconnect()
    }
    
    wsConnection.value.onerror = (error) => {
      console.error('WebSocket连接出错:', error)
    }
  } catch (error) {
    console.error('初始化WebSocket连接失败:', error)
    attemptReconnect()
  }
}

// 更新列表中设备的状态
const updateDeviceStatusInList = (deviceId, newStatus, message = null) => {
  const device = devices.value.find(d => d.id === deviceId)
  if (device) {
    console.log(`更新设备 ${device.name} (${device.management_ip}) 状态为: ${newStatus}`)
    device.status = newStatus
    
    // 可选：显示状态变更通知
    if (message) {
      console.log(message)
    }
  }
}

// 尝试重连WebSocket
const attemptReconnect = () => {
  if (wsReconnectAttempts.value < maxReconnectAttempts) {
    wsReconnectAttempts.value++
    console.log(`尝试重连WebSocket (${wsReconnectAttempts.value}/${maxReconnectAttempts})`)
    setTimeout(() => {
      initWebSocket()
    }, reconnectInterval)
  } else {
    console.error('WebSocket重连次数已达上限，停止重连')
  }
}

// 关闭WebSocket连接
const closeWebSocket = () => {
  if (wsConnection.value) {
    wsConnection.value.close()
    wsConnection.value = null
  }
}

// 定时检查所有设备状态
const checkAllDeviceStatus = async () => {
  if (devices.value.length === 0) {
    console.log('设备列表为空，跳过状态检查')
    return
  }
  
  console.log(`开始定时检查 ${devices.value.length} 个设备的状态`)
  
  // 检查是否存在有效的token - 使用正确的键名 access_token
  const token = localStorage.getItem('access_token')
  if (!token) {
    console.warn('没有找到有效token，跳过本次设备状态检查（定时器将继续运行）')
    // 不停止定时检查，因为token可能会在后续操作中恢复
    return
  }
  
  // 并行执行连通性检查，但限制并发数量以避免性能问题
  const CONCURRENCY_LIMIT = 10; // 限制并发数
  const deviceChunks = [];
  
  // 将设备列表分成块，每块最多CONCURRENCY_LIMIT个设备
  for (let i = 0; i < devices.value.length; i += CONCURRENCY_LIMIT) {
    deviceChunks.push(devices.value.slice(i, i + CONCURRENCY_LIMIT));
  }
  
  // 顺序处理每个块
  for (const chunk of deviceChunks) {
    const checkPromises = chunk.map(async (device) => {
      try {
        console.log(`正在检查设备 ${device.name} (${device.management_ip}) 的连通性...`)
        // 对于定时检查，我们直接处理错误而不是抛出它们
        const response = await checkConnectivity(device.management_ip).catch(error => {
          // 特别处理认证错误
          if (error.response && error.response.status === 401) {
            console.warn('认证过期，跳过本次设备状态检查（定时器将继续运行）')
            // 不停止定时检查，因为token可能会在后续操作中恢复
            return { is_reachable: false }
          }
          
          // 静默处理连通性检查错误，只在控制台记录
          console.error(`检查设备 ${device.name || device.management_ip} 连通性失败:`, error.message)
          // 返回一个默认的失败响应
          return { is_reachable: false }
        })
        
        // 直接更新设备状态
        const newStatus = response.is_reachable ? 'online' : 'offline'
        console.log(`设备 ${device.name} (${device.management_ip}) 状态: ${newStatus}`)
        device.status = newStatus
        
        // 更新到数据库
        try {
          await updateDevice(device.id, { status: device.status })
          console.log(`设备 ${device.name} 状态更新成功`)
        } catch (updateError) {
          // 特别处理认证错误
          if (updateError.response && updateError.response.status === 401) {
            console.warn('认证过期，跳过本次设备状态更新（定时器将继续运行）')
            // 不停止定时检查，因为token可能会在后续操作中恢复
            return
          }
          
          // 如果是超时错误，尝试重试一次
          if (updateError.code === 'ECONNABORTED' || updateError.message.includes('timeout')) {
            console.log(`更新设备 ${device.name || device.management_ip} 状态超时，正在重试...`)
            try {
              await new Promise(resolve => setTimeout(resolve, 1000)) // 等待1秒后重试
              await updateDevice(device.id, { status: device.status })
              console.log(`重试更新设备 ${device.name} 状态成功`)
            } catch (retryError) {
              console.error(`重试更新设备 ${device.name || device.management_ip} 状态失败:`, retryError.message)
            }
          } else {
            // 静默处理其他数据库更新错误，只在控制台记录
            console.error(`更新设备 ${device.name || device.management_ip} 状态到数据库失败:`, updateError.message)
          }
        }
      } catch (error) {
        console.error(`处理设备 ${device.name} 状态检查时发生错误:`, error)
        // 设置为离线状态
        device.status = 'offline'
      }
    });
    
    // 并行处理当前块中的所有设备
    await Promise.all(checkPromises);
    
    // 在处理完一个块后稍作延迟，以避免对服务器造成过大压力
    if (deviceChunks.indexOf(chunk) < deviceChunks.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 500)); // 等待500毫秒再处理下一个块
    }
  }
  
  console.log('所有设备状态检查完成')
}

// 开始定时检查设备状态
const startStatusChecking = () => {
  console.log('开始定时检查设备状态...')
  // 检查token是否存在
  const token = localStorage.getItem('access_token')
  console.log('当前token状态:', token ? '存在' : '不存在')
  console.log('当前用户名:', localStorage.getItem('access_token_username'))
  
  // 立即执行一次
  checkAllDeviceStatus()
  
  // 每30分钟执行一次（作为后备机制，主要依赖WebSocket推送）
  statusCheckTimer.value = setInterval(() => {
    console.log('定时器触发设备状态检查...')
    const currentToken = localStorage.getItem('access_token')
    console.log('当前token状态:', currentToken ? '存在' : '不存在')
    checkAllDeviceStatus()
  }, 1800000)  // 30分钟 = 30 * 60 * 1000毫秒
  
  console.log('定时检查已启动，ID:', statusCheckTimer.value)
  
  // 初始化WebSocket连接以接收实时状态更新
  initWebSocket()
}

// 停止定时检查
const stopStatusChecking = () => {
  if (statusCheckTimer.value) {
    clearInterval(statusCheckTimer.value)
    statusCheckTimer.value = null
  }
}

// 保存设备（添加或更新）
const saveDevice = () => {
  deviceForm.value.validate(async (valid) => {
    if (valid) {
      try {
        if (isEdit.value) {
          // 更新设备
          await updateDevice(currentDevice.id, currentDevice)
          ElMessage.success('更新成功')
        } else {
          // 添加设备
          await addDevice(currentDevice)
          ElMessage.success('添加成功')
        }
        dialogVisible.value = false
        loadDevices()
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
          return
        }
        
        ElMessage.error((isEdit.value ? '更新' : '添加') + '失败: ' + error.message)
      }
    }
  })
}

// 重置当前设备数据
const resetCurrentDevice = () => {
  Object.assign(currentDevice, {
    id: undefined,
    name: '',
    management_ip: '',
    vendor: '',
    model: '',
    os_version: '',
    serial_number: '',
    username: '',
    password: '',
    enable_password: '',
    port: 22,
    device_type: 'switch',
    location: ''
  })
}

// 处理对话框关闭
const handleDialogClose = () => {
  deviceForm.value.resetFields()
}

// 处理分页变化
const handlePageChange = (page) => {
  currentPage.value = page
}

// 处理页面大小变更
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1 // 重置到第一页
}

// 处理批量导入
const handleBatchImport = () => {
  importDialogVisible.value = true
}

// 处理文件选择
const handleFileChange = (file) => {
  importFile.value = file.raw
}

// 提交导入
const submitImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择要导入的文件')
    return
  }

  const formData = new FormData()
  formData.append('file', importFile.value)

  try {
    const response = await batchImportDevices(formData)
    // 正确地访问响应数据中的导入计数
    const importedCount = response.success || 0
    ElMessage.success(`设备导入完成！成功导入 ${importedCount} 条记录，失败 ${response.failed || 0} 条`)
    importDialogVisible.value = false
    loadDevices()
    
    // 显示详细的失败信息（如果有）
    if (response.failed > 0 && response.failed_devices && response.failed_devices.length > 0) {
      let failMessages = '部分设备导入失败:\n'
      response.failed_devices.slice(0, 5).forEach((fail, index) => {
        failMessages += `${index + 1}. 第${fail.row}行: ${fail.error}\n`
      })
      if (response.failed_devices.length > 5) {
        failMessages += `...还有${response.failed_devices.length - 5}个失败项`
      }
      ElMessage.warning(failMessages)
    }
  } catch (error) {
    ElMessage.error('导入失败: ' + error.message)
  }
}

// 处理批量操作
const handleBatchAction = (command) => {
  switch (command) {
    case 'backup':
      handleBatchBackup()
      break
    case 'delete':
      handleBatchDelete()
      break
    case 'export':
      exportSelectedDevices()
      break
  }
}

// 处理批量备份
const handleBatchBackup = () => {
  let message
  let count
  let devicesToBackup
  
  if (selectAllMode.value) {
    count = totalFilteredDevices.value
    message = `确认要为所有 ${count} 个匹配的设备执行配置备份吗？`
    // 获取所有过滤后的设备
    devicesToBackup = [...devices.value]
    
    // 如果有搜索条件，进行过滤
    if (searchText.value) {
      devicesToBackup = devicesToBackup.filter(device =>
        Object.values(device).some(val =>
          String(val).toLowerCase().includes(searchText.value.toLowerCase())
        )
      )
    }
  } else {
    if (selectedDevices.value.length === 0) {
      ElMessage.warning('请先选择要备份的设备')
      return
    }
    count = selectedDevices.value.length
    message = `确认要为选中的 ${count} 个设备执行配置备份吗？`
    devicesToBackup = [...selectedDevices.value]
  }

  ElMessageBox.confirm(
    message,
    '确认',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    // 显示进度消息
    const loading = ElLoading.service({
      lock: true,
      text: '正在执行批量备份...',
      background: 'rgba(0, 0, 0, 0.7)'
    })

    try {
      console.log('开始批量备份，设备数量：', devicesToBackup?.length || 0)
      
      // 检查是否有设备需要备份
      if (!devicesToBackup || devicesToBackup.length === 0) {
        console.warn('没有设备需要备份')
        loading.close()
        ElMessage.warning('没有设备需要备份')
        return
      }
      
      // 批量执行备份任务 - 使用for循环而不是Promise.all，以便处理单个失败的情况
      let successCount = 0
      let failCount = 0
      const failedDevices = []
      
      for (const device of devicesToBackup) {
        console.log('正在备份设备：', device)
        try {
          // 确保设备有必要的属性
          if (!device || !device.id) {
            console.error('设备信息不完整:', device)
            failCount++
            if (device && device.name) {
              failedDevices.push(`${device.name}(ID未知)`)
            } else {
              failedDevices.push('未知设备')
            }
            continue
          }
          
          const configData = {
            device_id: device.id,
            description: '批量备份',
            taken_by: localStorage.getItem('username') || '系统管理员'
          }
          
          console.log('发送备份请求，设备ID：', device.id, '配置数据：', configData)
          await backupDeviceConfig(device.id, configData)
          console.log('设备备份成功：', device.name || device.id)
          successCount++
        } catch (error) {
          console.error(`设备 ${device.name || device.id} 备份失败:`, error)
          failCount++
          failedDevices.push(`${device.name || '未知设备'}(${device.management_ip || '未知IP'})`)
        }
      }
      
      // 关闭进度消息
      loading.close()
      
      // 显示结果摘要
      if (failCount === 0) {
        ElMessage.success(`批量备份完成！成功: ${successCount}，失败: ${failCount}`)
      } else {
        ElMessage({
          message: `批量备份完成！成功: ${successCount}，失败: ${failCount}${failedDevices.length > 0 ? '，失败设备: ' + failedDevices.join(', ') : ''}`,
          type: 'warning',
          duration: 0, // 持久显示
          showClose: true
        })
      }
      
      // 刷新设备列表
      loadDevices()
    } catch (error) {
      console.error('批量备份过程发生错误:', error)
      // 关闭进度消息
      loading.close()
      
      // 特别处理认证错误
      if (error.response && error.response.status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        // 清除本地存储并跳转到登录页
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        if (window.location.hash !== '#/login') {
          window.location.hash = '#/login'
        }
        return
      }
      
      ElMessage.error('批量备份过程中发生错误: ' + error.message)
    }
  }).catch(action => {
    console.error('MessageBox确认框发生错误:', action)
    // Element Plus的MessageBox在用户点击取消或关闭对话框时会传入action参数
    if (action === 'cancel') {
      ElMessage.info('已取消批量备份')
    } else {
      // 其他错误情况
      ElMessage.error('批量备份过程中发生错误')
    }
  })
}

// 修改处理批量删除函数
const handleBatchDelete = () => {
  let message
  let count
  
  if (selectAllMode.value) {
    count = totalFilteredDevices.value
    message = `确认要删除所有 ${count} 个匹配的设备吗？此操作不可恢复！`
  } else {
    if (selectedDevices.value.length === 0) {
      ElMessage.warning('请先选择要删除的设备')
      return
    }
    count = selectedDevices.value.length
    message = `确认要删除选中的 ${count} 个设备吗？此操作不可恢复！`
  }

  ElMessageBox.confirm(
    message,
    '警告',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      let deletePromises
      
      if (selectAllMode.value) {
        // 全选模式下，删除所有过滤后的设备
        // 首先获取所有需要删除的设备
        let devicesToDelete = [...devices.value]
        
        // 如果有搜索条件，进行过滤
        if (searchText.value) {
          devicesToDelete = devicesToDelete.filter(device =>
            Object.values(device).some(val =>
              String(val).toLowerCase().includes(searchText.value.toLowerCase())
            )
          )
        }
        
        deletePromises = devicesToDelete.map(device => 
          deleteDevice(device.id)
        )
      } else {
        // 普通模式下，只删除选中的设备
        deletePromises = selectedDevices.value.map(device => 
          deleteDevice(device.id)
        )
      }
      
      await Promise.all(deletePromises)
      ElMessage.success('批量删除成功')
      
      // 重置全选模式
      selectAllMode.value = false
      selectedDevices.value = []
      
      loadDevices()
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
        return
      }
      
      ElMessage.error('批量删除失败: ' + error.message)
    }
  }).catch(() => {
    ElMessage.info('已取消批量删除')
  })
}

// 导出设备列表为CSV格式
const exportDeviceList = () => {
  if (devices.value.length === 0) {
    ElMessage.warning('没有设备数据可以导出')
    return
  }

  // 定义CSV文件的列标题和对应字段
  const headers = ['ID', '设备名称', '管理IP', '厂商', '型号', '设备类型', '位置', '状态']
  const fields = ['id', 'name', 'management_ip', 'vendor', 'model', 'device_type', 'location', 'status']

  // 构建CSV内容
  let csvContent = headers.join(',') + '\n'

  // 添加数据行
  devices.value.forEach(device => {
    const row = fields.map(field => {
      let value = device[field]
      // 确保值是字符串
      if (value === null || value === undefined) {
        value = ''
      } else {
        value = String(value)
      }
      // 处理包含逗号、换行符或引号的值
      if (value.includes(',') || value.includes('"') || value.includes('\n')) {
        return `"${value.replace(/"/g, '""')}"`
      }
      return value
    }).join(',')
    csvContent += row + '\n'
  })

  // 创建Blob对象
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })

  // 创建下载链接
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `设备列表_${new Date().toISOString().slice(0, 10)}.csv`)
  link.style.visibility = 'hidden'

  // 触发下载
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  ElMessage.success(`成功导出 ${devices.value.length} 个设备`)
}

// 导出选中的设备
const exportSelectedDevices = () => {
  let devicesToExport

  if (selectAllMode.value) {
    // 全选模式下，获取所有过滤后的设备
    devicesToExport = [...devices.value]
    
    // 如果有搜索条件，进行过滤
    if (searchText.value) {
      devicesToExport = devicesToExport.filter(device =>
        Object.values(device).some(val =>
          String(val).toLowerCase().includes(searchText.value.toLowerCase())
        )
      )
    }
  } else {
    if (selectedDevices.value.length === 0) {
      ElMessage.warning('请先选择要导出的设备')
      return
    }
    devicesToExport = [...selectedDevices.value]
  }

  // 定义CSV文件的列标题和对应字段
  const headers = ['ID', '设备名称', '管理IP', '厂商', '型号', '操作系统版本', '序列号', '用户名', '端口', '设备类型', '位置', '状态']
  const fields = ['id', 'name', 'management_ip', 'vendor', 'model', 'os_version', 'serial_number', 'username', 'port', 'device_type', 'location', 'status']

  // 构建CSV内容
  let csvContent = headers.join(',') + '\n'

  // 添加数据行
  devicesToExport.forEach(device => {
    const row = fields.map(field => {
      const value = device[field]
      // 处理包含逗号或引号的值
      if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`
      }
      return value
    }).join(',')
    csvContent += row + '\n'
  })

  // 创建Blob对象
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })

  // 创建下载链接
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', selectAllMode.value ?
    `所有匹配设备列表_${new Date().toISOString().slice(0, 10)}.csv` :
    `选中设备列表_${new Date().toISOString().slice(0, 10)}.csv`)
  link.style.visibility = 'hidden'

  // 触发下载
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  ElMessage.success(`成功导出 ${devicesToExport.length} 个设备`)
}

// 处理高级搜索
const handleAdvancedSearch = () => {
  // 重置到第一页
  currentPage.value = 1
}

// 重置高级搜索
const resetAdvancedSearch = () => {
  advancedSearchForm.name = ''
  advancedSearchForm.ip = ''
  advancedSearchForm.vendor = ''
  advancedSearchForm.deviceType = ''
  advancedSearchForm.status = ''
  // 重置到第一页
  currentPage.value = 1
}

// 下载模板文件
const downloadTemplate = () => {
  // 创建CSV模板内容（只包含示例行，不包含表头）
  const csvContent = `设备1,192.168.1.100,Cisco,admin,password,enable123,22,WS-C2960,15.0(2)SE,FOC12345678,机房A,switch\n设备2,192.168.1.101,Huawei,admin,password,,22,S5720,V200R019C00,ABC12345678,机房B,switch`;
  
  // 创建Blob对象
  const blob = new Blob(['\ufeff' + csvContent], { 
    type: 'text/csv;charset=utf-8;' 
  });
  
  // 创建下载链接
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', '设备导入模板.csv');
  link.style.visibility = 'hidden';
  
  // 触发下载
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// 在组件挂载时启动定时检查
onMounted(async () => {
  await loadDevices()  // 等待设备列表加载完成
  startStatusChecking()  // 然后开始定时检查
})

// 页面卸载时清理定时器和WebSocket连接
onUnmounted(() => {
  stopStatusChecking()
  closeWebSocket()
})
</script>

<style scoped>
.device-management {
  padding: 20px;
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.search-box {
  flex: 1;
  min-width: 200px;
}

.advanced-search-panel {
  background-color: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  margin: 15px 0;
}

.demo-form-inline .el-form-item {
  margin-right: 15px;
  margin-bottom: 15px;
}

.demo-form-inline .el-form-item:last-child {
  margin-right: 0;
}

.offline-row {
  background-color: #fef0f0;
}

:deep(.el-table__row.offline-row:hover) td {
  background-color: #fde2e2 !important;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    margin-top: 10px;
    width: 100%;
  }
  
  .el-table th,
  .el-table td {
    padding: 5px 0;
  }
}
</style>