<template>
  <div class="device-detail">
    <el-page-header @back="goBack" :content="device.name || '设备详情'" />
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 设备基本信息 -->
      <el-col :span="16">
        <el-card class="device-info-card">
          <template #header>
            <div class="card-header">
              <span>设备信息</span>
              <el-button type="primary" @click="handleEditDevice">编辑</el-button>
            </div>
          </template>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="设备名称">{{ device.name }}</el-descriptions-item>
            <el-descriptions-item label="设备ID">{{ device.id }}</el-descriptions-item>
            <el-descriptions-item label="管理IP">{{ device.management_ip }}</el-descriptions-item>
            <el-descriptions-item label="厂商">{{ device.vendor }}</el-descriptions-item>
            <el-descriptions-item label="型号">{{ device.model }}</el-descriptions-item>
            <el-descriptions-item label="操作系统">{{ device.os_version }}</el-descriptions-item>
            <el-descriptions-item label="序列号">{{ device.serial_number }}</el-descriptions-item>
            <el-descriptions-item label="设备类型">{{ device.device_type }}</el-descriptions-item>
            <el-descriptions-item label="用户名">{{ device.username }}</el-descriptions-item>
            <el-descriptions-item label="端口">{{ device.port }}</el-descriptions-item>
            <el-descriptions-item label="位置">{{ device.location }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="device.status === 'online' ? 'success' : 'danger'">
                {{ device.status }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
        
        <!-- 设备接口信息和配置备份并列 -->
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="12">
            <el-card class="device-interfaces-card">
              <template #header>
                <div class="card-header">
                  <span>接口信息</span>
                  <el-button @click="loadInterfaces">刷新</el-button>
                </div>
              </template>
              
              <el-table 
                :data="interfaces" 
                v-loading="interfacesLoading" 
                style="width: 100%"
                height="400"
                max-height="400"
              >
                <el-table-column prop="name" label="接口名称" />
                <el-table-column prop="status" label="状态">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'up' ? 'success' : 'danger'">
                      {{ row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="adminStatus" label="管理状态">
                  <template #default="{ row }">
                    <el-tag :type="row.adminStatus === 'up' ? 'success' : 'info'">
                      {{ row.adminStatus }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card class="backups-card">
              <template #header>
                <div class="card-header">
                  <span>配置备份</span>
                  <el-button @click="loadBackups">刷新</el-button>
                </div>
              </template>
              
              <el-table 
                :data="backups" 
                v-loading="backupsLoading" 
                style="width: 100%"
                height="400"
                max-height="400"
              >
                <el-table-column prop="created_at" label="备份时间" />
                <el-table-column prop="description" label="描述" />
                <el-table-column prop="filename" label="文件名" />
                <el-table-column label="操作" width="120">
                  <template #default="{ row }">
                    <el-button size="small" @click="handleDownloadBackup(row)">下载</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-col>
      
      <!-- 操作面板 -->
      <el-col :span="8">
        <el-card class="operations-card">
          <template #header>
            <div class="card-header">
              <span>操作</span>
            </div>
          </template>
          
          <div class="operations">
            <el-button type="primary" @click="handleCheckConnectivity" style="width: 100%; margin-bottom: 10px;">
              检查连通性
            </el-button>
            <el-button @click="handleGetConfig" style="width: 100%; margin-bottom: 10px;">
              获取配置
            </el-button>
            <el-button @click="handleSaveConfig" style="width: 100%; margin-bottom: 10px;">
              保存配置
            </el-button>
            <el-button @click="handleExecuteCommand" style="width: 100%; margin-bottom: 10px;">
              执行命令
            </el-button>
            <el-button @click="handleBackupConfig" style="width: 100%; margin-bottom: 10px;">
              备份配置
            </el-button>
            <el-button type="danger" @click="handleDeleteDevice" style="width: 100%;">
              删除设备
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card class="snmp-config-card">
          <template #header>
            <div class="card-header">
              <span>SNMP配置</span>
              <el-button type="primary" @click="showSNMPEditDialog">编辑SNMP配置</el-button>
            </div>
          </template>
          
          <el-descriptions :column="1" border>
            <el-descriptions-item label="团体名">{{ device.snmp_community }}</el-descriptions-item>
            <el-descriptions-item label="协议版本">{{ device.snmp_version }}</el-descriptions-item>
            <el-descriptions-item label="监听端口号">{{ device.snmp_port }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 编辑设备对话框 -->
    <el-dialog title="编辑设备" v-model="editDialogVisible" width="500px">
      <el-form :model="editDeviceForm" label-width="100px">
        <el-form-item label="设备名称">
          <el-input v-model="editDeviceForm.name" />
        </el-form-item>
        <el-form-item label="管理IP">
          <el-input v-model="editDeviceForm.management_ip" />
        </el-form-item>
        <el-form-item label="厂商">
          <el-select v-model="editDeviceForm.vendor" placeholder="请选择厂商">
            <el-option label="Cisco" value="Cisco" />
            <el-option label="Huawei" value="Huawei" />
            <el-option label="H3C" value="H3C" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="editDeviceForm.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="editDeviceForm.password" type="password" />
        </el-form-item>
        <el-form-item label="使能密码">
          <el-input v-model="editDeviceForm.enable_password" type="password" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="editDeviceForm.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="editDeviceForm.location" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveDevice">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 编辑SNMP配置对话框 -->
    <el-dialog title="编辑SNMP配置" v-model="snmpEditDialogVisible" width="500px">
      <el-form :model="snmpEditForm" label-width="100px">
        <el-form-item label="团体名">
          <el-input v-model="snmpEditForm.snmp_community" placeholder="请输入SNMP团体名" />
        </el-form-item>
        <el-form-item label="协议版本">
          <el-select v-model="snmpEditForm.snmp_version" placeholder="请选择SNMP版本">
            <el-option label="v1" value="1" />
            <el-option label="v2c" value="2" />
            <el-option label="v3" value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="监听端口号">
          <el-input-number 
            v-model="snmpEditForm.snmp_port" 
            :min="1" 
            :max="65535" 
            placeholder="默认161"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="snmpEditDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveSNMPConfig">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 实时终端对话框 -->
    <el-dialog 
      title="设备终端" 
      v-model="terminalVisible" 
      width="800px"
      :before-close="handleTerminalClose"
    >
      <div class="terminal-container">
        <div ref="terminalOutput" class="terminal-output"></div>
        <div class="terminal-input-area">
          <el-input
            ref="terminalInput"
            v-model="terminalCommand"
            placeholder="输入命令..."
            @keyup.enter="sendTerminalCommand"
            :disabled="sendingCommand"
          />
          <el-button 
            type="primary" 
            @click="sendTerminalCommand" 
            :loading="sendingCommand"
            style="margin-left: 10px;"
          >
            发送
          </el-button>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="clearTerminal">清屏</el-button>
          <el-button @click="terminalVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 配置显示对话框 -->
    <el-dialog title="设备配置" v-model="configDialogVisible" width="600px">
      <pre class="config-content">{{ configContent }}</pre>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="configDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="downloadConfig">下载</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getDevice,
  getDeviceInfo,
  getDeviceInterfaces,
  getDeviceConfig,
  saveDeviceConfig,
  executeDeviceCommand,
  backupDeviceConfig,
  getDeviceBackups,
  downloadConfigBackup,
  updateDevice,
  deleteDevice,
  checkConnectivity
} from '@/api/device'

const route = useRoute()
const router = useRouter()

// 设备信息
const device = ref({})
const interfaces = ref([])
const backups = ref([])

// 加载状态
const interfacesLoading = ref(false)
const backupsLoading = ref(false)

// 对话框状态
const editDialogVisible = ref(false)
const terminalVisible = ref(false)
const configDialogVisible = ref(false)
const snmpEditDialogVisible = ref(false)

// 表单数据
const editDeviceForm = reactive({})
const snmpEditForm = reactive({
  snmp_community: '',
  snmp_version: 'v2c',
  snmp_port: 161
})

// 配置内容
const configContent = ref('')

// 返回上一页
const goBack = () => {
  router.go(-1)
}

// 加载设备信息
const loadDevice = async () => {
  try {
    const deviceId = route.params.id
    const response = await getDevice(deviceId)
    device.value = response
    Object.assign(editDeviceForm, response)
    
    // Initialize SNMP form with device data
    snmpEditForm.snmp_community = response.snmp_community || ''
    snmpEditForm.snmp_version = response.snmp_version || 'v2c'
    snmpEditForm.snmp_port = response.snmp_port || 161
    
    // 获取设备详细信息并更新到数据库
    try {
      const infoResponse = await getDeviceInfo(deviceId)
      if (infoResponse && infoResponse.info_source === "device") {
        // 提取详细信息
        const deviceInfo = {
          model: infoResponse.model || infoResponse.module || '',
          os_version: infoResponse.os_version || infoResponse.software_version || infoResponse.version || '',
          serial_number: infoResponse.serial_number || infoResponse.sn || '',
          // 移除了端口数的处理，因为这个信息不应该从设备信息接口获取
        }
        
        // 更新设备信息到数据库
        await updateDevice(deviceId, {
          ...response,
          ...deviceInfo
        })
        
        // 更新本地数据
        Object.assign(device.value, deviceInfo)
        Object.assign(editDeviceForm, deviceInfo)
      }
    } catch (infoError) {
      console.warn('获取设备详细信息失败:', infoError)
    }
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
    
    ElMessage.error('加载设备信息失败: ' + error.message)
  }
}

// 加载接口信息
const loadInterfaces = async () => {
  interfacesLoading.value = true
  try {
    const deviceId = route.params.id
    const response = await getDeviceInterfaces(deviceId)
    let interfacesData = []
    
    // 转换接口数据格式以适配表格
    if (Array.isArray(response)) {
      // 如果响应直接是数组
      interfacesData = response
    } else if (response && typeof response === 'object') {
      // 如果响应是对象，可能包含接口数组
      interfacesData = response.interfaces || response.data || Object.values(response)[0] || []
    }
    
    // 处理接口数据
    if (Array.isArray(interfacesData)) {
      interfaces.value = interfacesData.map(item => ({
        name: item.interface_name,
        status: item.operational_status,
        adminStatus: item.admin_status
      }))
      
      // 统计端口数量（排除逻辑接口如LoopBack、NULL、Vlanif等）
      const portCount = interfacesData.filter(item => 
        item.interface_name && 
        !item.interface_name.startsWith('LoopBack') && 
        !item.interface_name.startsWith('NULL') && 
        !item.interface_name.startsWith('Vlanif')
      ).length
      
      // 不再自动更新设备端口为接口数量
      // 注释掉下面这段代码，因为设备端口应该是指SSH/Telnet端口，而不是物理接口数量
      /*
      if (device.value.port !== portCount) {
        try {
          await updateDevice(deviceId, {
            ...device.value,
            port: portCount
          })
          device.value.port = portCount
          editDeviceForm.port = portCount
        } catch (updateError) {
          console.warn('更新端口数量失败:', updateError)
        }
      }
      */
    } else {
      interfaces.value = []
    }
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
      interfaces.value = []
      interfacesLoading.value = false
      return
    }
    
    console.error('加载接口信息失败:', error)
    ElMessage.error('加载接口信息失败: ' + error.message)
    interfaces.value = []
  } finally {
    interfacesLoading.value = false
  }
}

// 加载备份信息
const loadBackups = async () => {
  backupsLoading.value = true
  try {
    const deviceId = route.params.id
    const response = await getDeviceBackups(deviceId)
    backups.value = response
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
      backups.value = []
      backupsLoading.value = false
      return
    }
    
    ElMessage.error('加载备份信息失败: ' + error.message)
    backups.value = []
  } finally {
    backupsLoading.value = false
  }
}

// 处理编辑设备
const handleEditDevice = () => {
  editDialogVisible.value = true
}

// 保存设备信息
const saveDevice = async () => {
  try {
    const deviceId = route.params.id
    await updateDevice(deviceId, editDeviceForm)
    ElMessage.success('设备信息更新成功')
    editDialogVisible.value = false
    loadDevice()
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
    
    ElMessage.error('更新设备信息失败: ' + error.message)
  }
}

// 检查连通性
const handleCheckConnectivity = async () => {
  try {
    const deviceId = route.params.id
    const response = await checkConnectivity(device.value.management_ip)
    
    // 根据检查结果显示不同的消息
    if (response.is_reachable) {
      ElMessage.success(`连通性检查成功，响应时间: ${response.response_time}ms`)
    } else {
      ElMessage.error('连通性检查失败，设备不可达')
    }
    
    console.log('连通性检查结果:', response)
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
    
    ElMessage.error('连通性检查失败: ' + error.message)
  }
}

// 获取配置
const handleGetConfig = async () => {
  try {
    const deviceId = route.params.id
    // 显示加载提示
    ElMessage.info('正在获取设备配置，请稍候...')
    
    const response = await getDeviceConfig(deviceId)
    
    // 检查响应数据
    if (response && response.config) {
      // 将配置数组转换为带换行的字符串
      configContent.value = response.config.join('\n')
    } else {
      configContent.value = '未获取到设备配置'
    }
    
    configDialogVisible.value = true
    ElMessage.success('获取配置成功')
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
    
    ElMessage.error('获取配置失败: ' + error.message)
  }
}

// 保存配置
const handleSaveConfig = async () => {
  try {
    const deviceId = route.params.id
    const configData = {
      config: configContent.value.split('\n')
    }
    
    await saveDeviceConfig(deviceId, configData)
    ElMessage.success('配置保存成功')
    configDialogVisible.value = false
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
    
    ElMessage.error('配置保存失败: ' + error.message)
  }
}

// 处理执行命令
const handleExecuteCommand = async () => {
  terminalVisible.value = true
  terminalCommand.value = ''
  commandHistory.value = []
  
  // 初始化终端输出
  nextTick(() => {
    if (terminalOutput.value) {
      terminalOutput.value.innerHTML = '<div class="terminal-welcome">正在连接设备...</div>'
      terminalOutput.value.scrollTop = terminalOutput.value.scrollHeight
    }
  })
  
  // 尝试建立连接
  await connectTerminal()
}

// 建立终端连接
const connectTerminal = async () => {
  try {
    const deviceId = route.params.id
    // 使用executeDeviceCommand建立会话
    const response = await executeDeviceCommand(deviceId, { 
      command: 'session-start'
    })
    
    // 检查响应中是否包含会话令牌
    if (response.session_token) {
      sessionToken.value = response.session_token
      isConnected.value = true
      appendToTerminal(`已连接到设备 ${device.value.name} (${device.value.management_ip})`, true)
    } else {
      // 如果后端不支持会话功能，仍然可以使用保持连接的模式
      isConnected.value = true
      appendToTerminal(`已连接到设备 ${device.value.name} (${device.value.management_ip})`, true)
    }
    
    // 聚焦到输入框
    await nextTick()
    if (terminalInput.value) {
      terminalInput.value.focus()
    }
  } catch (error) {
    console.error('建立终端连接失败:', error)
    appendToTerminal(`连接失败: ${error.message || '无法连接到设备'}`, true)
    isConnected.value = false
  }
}

// 发送终端命令
const sendTerminalCommand = async () => {
  if (!terminalCommand.value.trim() || sendingCommand.value) return
  
  const command = terminalCommand.value.trim()
  commandHistory.value.push(command)
  
  // 显示用户输入的命令
  appendToTerminal(`$ ${command}`, true)
  
  sendingCommand.value = true
  try {
    const deviceId = route.params.id
    const commandData = { 
      command,
      session_token: sessionToken.value  // 发送命令时带上会话令牌
    }
    
    const response = await executeDeviceCommand(deviceId, commandData)
    
    // 检查响应中是否有新的会话令牌
    if (response.session_token) {
      sessionToken.value = response.session_token
    }
    
    // 显示命令输出
    if (response.output) {
      appendToTerminal(response.output)
    } else {
      appendToTerminal('(无输出)')
    }
    
    // 清空输入框
    terminalCommand.value = ''
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
      terminalVisible.value = false
      sendingCommand.value = false
      return
    }
    
    console.error('执行命令失败:', error)
    appendToTerminal(`错误: ${error.message || '命令执行失败'}`)
  } finally {
    sendingCommand.value = false
    // 聚焦到输入框
    await nextTick()
    if (terminalInput.value) {
      terminalInput.value.focus()
    }
  }
}

// 断开终端连接
const disconnectTerminal = async () => {
  if (isConnected.value && sessionToken.value) {
    try {
      const deviceId = route.params.id
      await executeDeviceCommand(deviceId, { 
        command: 'session-end',
        session_token: sessionToken.value
      })
      appendToTerminal('已断开与设备的连接', true)
    } catch (error) {
      console.error('断开连接时出错:', error)
      appendToTerminal('断开连接时出错', true)
    } finally {
      sessionToken.value = null
      isConnected.value = false
    }
  } else {
    isConnected.value = false
  }
}

// 添加内容到终端输出
const appendToTerminal = (content, isHtml = false) => {
  if (terminalOutput.value) {
    if (!isHtml) {
      // 如果不是HTML，则按行分割并逐行添加
      const lines = content.split('\n')
      lines.forEach(line => {
        const lineDiv = document.createElement('div')
        lineDiv.className = 'terminal-line'
        lineDiv.textContent = line
        terminalOutput.value.appendChild(lineDiv)
      })
    } else {
      // 如果是HTML，则直接添加
      const lineDiv = document.createElement('div')
      lineDiv.className = 'terminal-line'
      lineDiv.innerHTML = content
      terminalOutput.value.appendChild(lineDiv)
    }
    
    // 滚动到底部
    terminalOutput.value.scrollTop = terminalOutput.value.scrollHeight
  }
}

// 清屏
const clearTerminal = () => {
  if (terminalOutput.value) {
    terminalOutput.value.innerHTML = '<div class="terminal-welcome">终端已清屏</div>'
  }
}

// 处理终端关闭
const handleTerminalClose = (done) => {
  const disconnectAndClose = async () => {
    await disconnectTerminal()
    done()
  }
  
  ElMessageBox.confirm('确定要关闭终端吗？这将断开与设备的连接。')
    .then(() => {
      disconnectAndClose()
    })
    .catch(() => {
      // 取消关闭
    })
}

// 备份配置
const handleBackupConfig = async () => {
  try {
    const deviceId = route.params.id
    const configData = {
      device_id: deviceId,
      description: '手动备份',
      taken_by: '管理员'
    }
    await backupDeviceConfig(deviceId, configData)
    ElMessage.success('配置备份成功')
    loadBackups()
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
    
    ElMessage.error('配置备份失败: ' + error.message)
  }
}

// 删除设备
const handleDeleteDevice = () => {
  ElMessageBox.confirm(
    '确认要删除该设备吗？此操作不可恢复！',
    '警告',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const deviceId = route.params.id
      await deleteDevice(deviceId)
      ElMessage.success('删除成功')
      router.push('/devices')
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
      
      ElMessage.error('删除失败: ' + error.message)
    }
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

// 下载备份
const handleDownloadBackup = async (backup) => {
  try {
    const response = await downloadConfigBackup(backup.id)
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', backup.filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
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
    
    ElMessage.error('下载备份失败: ' + error.message)
  }
}

// 下载配置
const downloadConfig = () => {
  // 创建Blob对象
  const blob = new Blob([configContent.value], { type: 'text/plain' })
  const url = window.URL.createObjectURL(blob)
  
  // 创建下载链接
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `${device.value.name}_config.txt`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  // 释放URL对象
  window.URL.revokeObjectURL(url)
}

// 保存SNMP配置
const saveSNMPConfig = async () => {
  try {
    const deviceId = route.params.id
    const snmpData = {
      snmp_community: snmpEditForm.snmp_community,
      snmp_version: snmpEditForm.snmp_version,
      snmp_port: snmpEditForm.snmp_port
    }
    
    await updateDevice(deviceId, { ...device.value, ...snmpData })
    ElMessage.success('SNMP配置更新成功')
    snmpEditDialogVisible.value = false
    loadDevice()
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
    
    ElMessage.error('更新SNMP配置失败: ' + error.message)
  }
}

// 显示SNMP编辑对话框
const showSNMPEditDialog = () => {
  snmpEditDialogVisible.value = true
}

// 页面加载时获取数据
onMounted(() => {
  loadDevice()
  loadInterfaces()
  loadBackups()
})
</script>

<style scoped>
.device-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.operations {
  display: flex;
  flex-direction: column;
}

.config-content {
  max-height: 400px;
  overflow-y: auto;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
}

.terminal-container {
  height: 500px;
  display: flex;
  flex-direction: column;
}

.terminal-output {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
  background-color: #000;
  color: #0f0;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  overflow-y: auto;
  min-height: 300px;
}

.terminal-line {
  margin-bottom: 5px;
  line-height: 1.5;
}

.terminal-welcome {
  color: #909399;
  margin-bottom: 10px;
}

.terminal-command {
  color: #67c23a;
}

.terminal-error {
  color: #f56c6c;
}

.terminal-input-area {
  display: flex;
  align-items: center;
}
</style>