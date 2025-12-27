<template>
  <div class="settings-container">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="基本设置" name="basic">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统基本信息</span>
            </div>
          </template>
          
          <el-form :model="basicSettings" label-width="120px">
            <el-form-item label="系统名称">
              <el-input v-model="basicSettings.systemName" />
            </el-form-item>
            
            <el-form-item label="系统描述">
              <el-input 
                v-model="basicSettings.description" 
                type="textarea" 
                :rows="3"
              />
            </el-form-item>
            
            <el-form-item label="默认语言">
              <el-select v-model="basicSettings.language">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="时区">
              <el-select v-model="basicSettings.timezone">
                <el-option label="北京时间 (UTC+8)" value="Asia/Shanghai" />
                <el-option label="东京时间 (UTC+9)" value="Asia/Tokyo" />
                <el-option label="纽约时间 (UTC-5)" value="America/New_York" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveBasicSettings" :loading="loading.basic">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="自动扫描" name="auto-scan">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>自动扫描配置</span>
            </div>
          </template>
          
          <el-form :model="scanSettings" label-width="150px">
            <el-form-item label="启用自动扫描">
              <el-switch v-model="scanSettings.enabled" />
            </el-form-item>
            
            <el-form-item label="扫描间隔">
              <el-input-number 
                v-model="scanSettings.interval" 
                :min="1" 
                :max="1440"
              /> 分钟
            </el-form-item>
            
            <el-form-item label="扫描IP范围">
              <el-input 
                v-model="scanSettings.ipRange" 
                placeholder="例如: 192.168.1.0/24"
              />
            </el-form-item>
            
            <el-form-item label="扫描端口">
              <el-input 
                v-model="scanSettings.ports" 
                placeholder="例如: 22,23,80,443"
              />
            </el-form-item>
            
            <el-form-item label="设备厂商识别">
              <el-checkbox-group v-model="scanSettings.vendors">
                <el-checkbox label="Cisco" />
                <el-checkbox label="Huawei" />
                <el-checkbox label="H3C" />
                <el-checkbox label="Juniper" />
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveScanSettings" :loading="loading.scan">保存设置</el-button>
              <el-button @click="startManualScan" :loading="loading.manualScan">手动扫描</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="网络扫描" name="network-scan">
        <div class="scan-section">
          <h3>网络主机扫描</h3>
          <p>扫描指定网络范围内的主机，并与现有设备IP进行比对</p>
          
          <el-form :model="scanConfig" label-width="120px" style="max-width: 600px; margin-top: 20px;">
            <el-form-item label="扫描范围">
              <el-input 
                v-model="scanConfig.ipRange" 
                placeholder="请输入IP范围，例如：192.168.1.0/24"
                :disabled="loading.scan"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="primary" 
                @click="startNetworkScan" 
                :loading="loading.scan"
                :disabled="!scanConfig.ipRange"
              >
                {{ loading.scan ? '扫描中...' : '开始扫描' }}
              </el-button>
            </el-form-item>
          </el-form>
          
          <div v-if="scanResults.total_discovered > 0" class="scan-results">
            <h4>扫描结果</h4>
            <el-card class="result-card">
              <div class="result-summary">
                <div class="result-item">
                  <h5>总发现主机</h5>
                  <p class="result-number">{{ scanResults.total_discovered }}</p>
                </div>
                <div class="result-item">
                  <h5>新主机</h5>
                  <p class="result-number new-hosts">{{ scanResults.new_count }}</p>
                </div>
                <div class="result-item">
                  <h5>已知设备</h5>
                  <p class="result-number known-devices">{{ scanResults.existing_count }}</p>
                </div>
              </div>
              
              <div v-if="scanResults.new_hosts.length > 0" class="new-hosts-section">
                <h4>新发现的主机 (可添加为设备)</h4>
                <el-table :data="scanResults.new_hosts.map(ip => ({ ip }))" style="width: 100%">
                  <el-table-column prop="ip" label="IP地址" width="200" />
                  <el-table-column label="操作" width="150">
                    <template #default="{ row }">
                      <el-button size="small" @click="addNewHostToDevice(row.ip)">添加为设备</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              
              <div v-if="scanResults.existing_hosts.length > 0" class="existing-hosts-section">
                <h4>已知设备</h4>
                <el-table :data="scanResults.existing_hosts.map(ip => ({ ip }))" style="width: 100%">
                  <el-table-column prop="ip" label="IP地址" />
                </el-table>
              </div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="通知设置" name="notification">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>通知配置</span>
            </div>
          </template>
          
          <el-form :model="notificationSettings" label-width="120px">
            <el-form-item label="邮件通知">
              <el-switch v-model="notificationSettings.emailEnabled" />
            </el-form-item>
            
            <div v-if="notificationSettings.emailEnabled">
              <el-form-item label="SMTP服务器">
                <el-input v-model="notificationSettings.smtpServer" />
              </el-form-item>
              
              <el-form-item label="SMTP端口">
                <el-input-number 
                  v-model="notificationSettings.smtpPort" 
                  :min="1" 
                  :max="65535"
                />
              </el-form-item>
              
              <el-form-item label="用户名">
                <el-input v-model="notificationSettings.smtpUsername" />
              </el-form-item>
              
              <el-form-item label="密码">
                <el-input 
                  v-model="notificationSettings.smtpPassword" 
                  type="password" 
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="发件人邮箱">
                <el-input v-model="notificationSettings.senderEmail" />
              </el-form-item>
              
              <el-form-item label="收件人列表">
                <el-input 
                  v-model="notificationSettings.recipients" 
                  type="textarea" 
                  :rows="3"
                  placeholder="多个邮箱地址请用逗号分隔"
                />
              </el-form-item>
            </div>
            
            <el-form-item label="短信通知">
              <el-switch v-model="notificationSettings.smsEnabled" />
            </el-form-item>
            
            <div v-if="notificationSettings.smsEnabled">
              <el-form-item label="短信网关">
                <el-input v-model="notificationSettings.smsGateway" />
              </el-form-item>
              
              <el-form-item label="API密钥">
                <el-input 
                  v-model="notificationSettings.smsApiKey" 
                  type="password" 
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="短信签名">
                <el-input v-model="notificationSettings.smsSignature" />
              </el-form-item>
            </div>
            
            <el-form-item>
              <el-button type="primary" @click="saveNotificationSettings" :loading="loading.notification">保存设置</el-button>
              <el-button @click="testNotifications" :loading="loading.testNotification">测试通知</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="SNMP设置" name="snmp">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>SNMP Trap配置</span>
            </div>
          </template>
          
          <div class="snmp-settings-link">
            <p>SNMP Trap配置已移动到专用页面，请点击下方按钮前往配置：</p>
            <el-button type="primary" @click="$router.push('/snmp-settings')">前往SNMP配置页面</el-button>
          </div>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="系统维护" name="maintenance">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统维护</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card class="maintenance-card">
                <div class="maintenance-item">
                  <h4>备份与恢复</h4>
                  <p>定期备份系统配置和数据</p>
                  <div class="actions">
                    <el-button type="primary" @click="backupSystem" :loading="loading.backup">立即备份</el-button>
                    <el-button @click="restoreSystem">恢复系统</el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
            
            <el-col :span="12">
              <el-card class="maintenance-card">
                <div class="maintenance-item">
                  <h4>日志清理</h4>
                  <p>清理历史日志以释放磁盘空间</p>
                  <div class="actions">
                    <el-button @click="cleanLogs" :loading="loading.cleanLogs">清理日志</el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
          
          <el-row :gutter="20" style="margin-top: 20px;">
            <el-col :span="12">
              <el-card class="maintenance-card">
                <div class="maintenance-item">
                  <h4>系统重启</h4>
                  <p>重启系统服务</p>
                  <div class="actions">
                    <el-button type="danger" @click="restartSystem" :loading="loading.restart">重启系统</el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
            
            <el-col :span="12">
              <el-card class="maintenance-card">
                <div class="maintenance-item">
                  <h4>系统信息</h4>
                  <p>查看系统版本和运行状态</p>
                  <div class="actions">
                    <el-button @click="viewSystemInfo" :loading="loading.systemInfo">查看详情</el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  getBasicSettings, 
  updateBasicSettings, 
  getScanSettings, 
  updateScanSettings, 
  getNotificationSettings, 
  updateNotificationSettings, 
  testNotifications as testNotificationsApi, 
  cleanupLogs,
  backupSystem as backupSystemApi, 
  restartSystem as restartSystemApi,
  getSystemInfo,
  scanNetworkHosts as scanNetworkHostsApi
} from '@/api/settings'

// 加载状态
const loading = reactive({
  basic: false,
  scan: false,
  notification: false,
  testNotification: false,
  cleanLogs: false,
  backup: false,
  restart: false,
  systemInfo: false,
  manualScan: false
})

// 网络扫描配置
const scanConfig = reactive({
  ipRange: '192.168.1.0/24'
})

// 扫描结果
const scanResults = reactive({
  total_discovered: 0,
  new_hosts: [],
  existing_hosts: [],
  new_count: 0,
  existing_count: 0
})

// 激活的标签页
const activeTab = ref('basic')

// 基本设置
const basicSettings = reactive({
  systemName: '网络设备管理系统',
  description: '一套完整的企业级网络设备管理解决方案',
  language: 'zh-CN',
  timezone: 'Asia/Shanghai'
})

// 扫描设置
const scanSettings = reactive({
  enabled: true,
  interval: 30,
  ipRange: '192.168.1.0/24',
  ports: '22,23,80,443',
  vendors: ['Cisco', 'Huawei', 'H3C']
})

// 通知设置
const notificationSettings = reactive({
  emailEnabled: true,
  smtpServer: 'smtp.example.com',
  smtpPort: 587,
  smtpUsername: 'admin@example.com',
  smtpPassword: '',
  senderEmail: 'admin@example.com',
  recipients: 'user1@example.com,user2@example.com',
  smsEnabled: false,
  smsGateway: '',
  smsApiKey: '',
  smsSignature: ''
})

// 初始化设置
onMounted(() => {
  loadSettings()
})

// 加载所有设置
const loadSettings = async () => {
  try {
    // 加载基本设置
    const basicRes = await getBasicSettings()
    Object.assign(basicSettings, basicRes)
    
    // 加载扫描设置
    const scanRes = await getScanSettings()
    Object.assign(scanSettings, scanRes)
    
    // 加载通知设置
    const notificationRes = await getNotificationSettings()
    Object.assign(notificationSettings, notificationRes)
  } catch (error) {
    console.error('加载设置失败:', error)
    ElMessage.error('加载设置失败: ' + error.message)
  }
}

// 保存基本设置
const saveBasicSettings = async () => {
  loading.basic = true
  try {
    await updateBasicSettings(basicSettings)
    ElMessage.success('基本设置已保存')
  } catch (error) {
    console.error('保存基本设置失败:', error)
    ElMessage.error('保存基本设置失败: ' + error.message)
  } finally {
    loading.basic = false
  }
}

// 保存扫描设置
const saveScanSettings = async () => {
  loading.scan = true
  try {
    await updateScanSettings(scanSettings)
    ElMessage.success('扫描设置已保存')
  } catch (error) {
    console.error('保存扫描设置失败:', error)
    ElMessage.error('保存扫描设置失败: ' + error.message)
  } finally {
    loading.scan = false
  }
}

// 开始手动扫描
const startManualScan = async () => {
  loading.manualScan = true
  try {
    // 从扫描设置中获取IP范围
    const ipRange = scanSettings.ipRange || '192.168.1.0/24'
    const response = await scanNetworkHostsApi(ipRange)
    
    // 检查API响应结构，根据实际返回的数据结构处理
    console.log('手动扫描API响应:', response)
    
    // 如果response直接是数据对象（而不是axios的响应对象）
    const result = response.data || response
    
    // 显示扫描结果
    ElMessage.success(`手动扫描完成，发现 ${result.total_discovered} 个主机`)
    console.log('手动扫描结果:', result)
  } catch (error) {
    console.error('手动扫描失败:', error)
    ElMessage.error('手动扫描失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.manualScan = false
  }
}

// 开始网络扫描
const startNetworkScan = async () => {
  if (!scanConfig.ipRange) {
    ElMessage.warning('请输入扫描的IP范围')
    return
  }
  
  loading.scan = true
  try {
    const response = await scanNetworkHostsApi(scanConfig.ipRange)
    console.log('网络扫描API响应:', response)
    
    // 检查API响应结构，根据实际返回的数据结构处理
    const result = response.data || response
    
    Object.assign(scanResults, result)
    ElMessage.success(`扫描完成，发现 ${result.total_discovered} 个主机`)
  } catch (error) {
    console.error('网络扫描失败:', error)
    ElMessage.error('网络扫描失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.scan = false
  }
}

// 添加新主机到设备
const addNewHostToDevice = (ip) => {
  ElMessageBox.confirm(
    `确定要将主机 ${ip} 添加为新设备吗？`,
    '确认添加',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    // 跳转到设备添加页面，并预填IP地址
    window.open(`/devices/add?ip=${ip}`, '_blank')
  }).catch(() => {
    // 用户取消操作
  })
}

// 保存通知设置
const saveNotificationSettings = async () => {
  loading.notification = true
  try {
    await updateNotificationSettings(notificationSettings)
    ElMessage.success('通知设置已保存')
  } catch (error) {
    console.error('保存通知设置失败:', error)
    ElMessage.error('保存通知设置失败: ' + error.message)
  } finally {
    loading.notification = false
  }
}

// 测试通知
const testNotifications = async () => {
  loading.testNotification = true
  try {
    await testNotificationsApi()
    ElMessage.success('测试通知已发送')
  } catch (error) {
    console.error('发送测试通知失败:', error)
    ElMessage.error('发送测试通知失败: ' + error.message)
  } finally {
    loading.testNotification = false
  }
}

// 备份系统
const backupSystemHandler = async () => {
  try {
    await backupSystemApi()
    ElMessage.success('系统备份任务已启动')
    console.log('备份系统')
  } catch (error) {
    console.error('系统备份失败:', error)
    ElMessage.error('系统备份失败: ' + error.message)
  }
}

const backupSystem = () => {
  ElMessageBox.confirm(
    '确定要立即备份系统吗？',
    '系统备份',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    backupSystemHandler()
  })
}

// 恢复系统
const restoreSystem = () => {
  ElMessageBox.confirm(
    '确定要从备份恢复系统吗？此操作将覆盖当前配置。',
    '系统恢复',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.info('请选择备份文件')
    console.log('恢复系统')
  })
}

// 清理日志
const cleanLogs = async () => {
  try {
    await cleanupLogs()
    ElMessage.success('日志清理完成')
    console.log('清理日志')
  } catch (error) {
    console.error('日志清理失败:', error)
    ElMessage.error('日志清理失败: ' + error.message)
  }
}

// 重启系统
const restartSystemHandler = async () => {
  try {
    await restartSystemApi()
    ElMessage.success('系统重启中...')
    console.log('重启系统')
  } catch (error) {
    console.error('系统重启失败:', error)
    ElMessage.error('系统重启失败: ' + error.message)
  }
}

const restartSystem = () => {
  ElMessageBox.confirm(
    '确定要重启系统吗？重启期间服务将暂时中断。',
    '系统重启',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    restartSystemHandler()
  })
}

// 查看系统信息
const viewSystemInfo = async () => {
  try {
    const info = await getSystemInfo()
    console.log('系统信息:', info)
    ElMessage.info(`系统版本: ${info.version}, 设备数量: ${info.device_count}`)
  } catch (error) {
    console.error('获取系统信息失败:', error)
    ElMessage.error('获取系统信息失败: ' + error.message)
  }
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
  height: 100%;
}

.card-header {
  font-weight: bold;
}

.maintenance-card {
  height: 100%;
}

.maintenance-item h4 {
  margin-top: 0;
}

.maintenance-item p {
  color: #909399;
  margin-bottom: 20px;
}

.actions {
  display: flex;
  gap: 10px;
}

.snmp-settings-link {
  text-align: center;
  padding: 40px 0;
}

/* 网络扫描相关样式 */
.scan-section {
  padding: 20px 0;
  
  h3 {
    margin-bottom: 10px;
    color: #303133;
    font-size: 18px;
    font-weight: bold;
  }
  
  p {
    color: #606266;
    margin-bottom: 20px;
  }
  
  .scan-results {
    margin-top: 30px;
    
    h4 {
      margin-bottom: 15px;
      color: #303133;
      font-size: 16px;
    }
    
    .result-card {
      margin-top: 15px;
      border: 1px solid #e4e7ed;
      
      .result-summary {
        display: flex;
        justify-content: space-around;
        margin-bottom: 20px;
        padding: 15px 0;
        
        .result-item {
          text-align: center;
          flex: 1;
          padding: 0 10px;
          
          h5 {
            margin: 0 0 10px 0;
            color: #606266;
            font-size: 14px;
          }
          
          .result-number {
            font-size: 24px;
            font-weight: bold;
            margin: 0;
            
            &.new-hosts {
              color: #67c23a;
            }
            
            &.known-devices {
              color: #409eff;
            }
          }
        }
      }
      
      .new-hosts-section,
      .existing-hosts-section {
        margin-top: 20px;
        
        h4 {
          margin-bottom: 15px;
          color: #303133;
          font-size: 16px;
        }
      }
    }
  }
}

.snmp-settings-link p {
  font-size: 16px;
  margin-bottom: 20px;
  color: #606266;
}
</style>