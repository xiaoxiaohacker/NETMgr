<template>
  <div class="snmp-settings-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>SNMP Trap配置</span>
          <el-button type="primary" size="small" @click="saveSNMPConfig">保存配置</el-button>
        </div>
      </template>
      
      <el-form :model="snmpSettings" label-width="150px">
        <el-form-item label="Trap监听地址">
          <el-input 
            v-model="snmpSettings.trap_listen_address" 
            placeholder="请输入监听地址"
          />
          <div class="form-tip">监听所有网络接口请填写 0.0.0.0</div>
        </el-form-item>
        
        <el-form-item label="Trap监听端口">
          <el-input-number 
            v-model="snmpSettings.trap_listen_port" 
            :min="1" 
            :max="65535"
            controls-position="right"
          />
          <div class="form-tip">SNMP Trap标准端口为162</div>
        </el-form-item>
        
        <el-form-item label="社区字符串">
          <el-select 
            v-model="snmpSettings.community_strings" 
            multiple 
            filterable 
            allow-create 
            default-first-option
            placeholder="请输入社区字符串，可输入多个">
            <el-option
              v-for="item in communityOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
          <div class="form-tip">设备发送Trap时使用的社区字符串</div>
        </el-form-item>
        
        <el-form-item label="允许的主机">
          <el-select
            v-model="snmpSettings.allowed_hosts"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入允许发送Trap的主机IP地址">
            <el-option
              v-for="item in hostOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
          <div class="form-tip">留空表示允许所有主机发送Trap</div>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>SNMP Trap配置指南</span>
        </div>
      </template>
      
      <div class="guide-content">
        <h4>手动配置设备Trap：</h4>
        <p>如果设备不支持通过系统自动配置SNMP Trap，请按照以下步骤手动配置：</p>
        
        <div class="command-guide">
          <h5>Cisco设备配置示例：</h5>
          <pre><code>snmp-server host {{ snmpSettings.trap_listen_address || '[监听地址]' }} version 2c {{ snmpSettings.community_strings[0] || 'public' }}
snmp-server enable traps</code></pre>
        </div>
        
        <div class="command-guide">
          <h5>华为设备配置示例：</h5>
          <pre><code>snmp-agent target-host trap address udp-domain {{ snmpSettings.trap_listen_address || '[监听地址]' }} udp-port {{ snmpSettings.trap_listen_port || '162' }} params securityname {{ snmpSettings.community_strings[0] || 'public' }}
snmp-agent trap enable</code></pre>
        </div>
        
        <div class="command-guide">
          <h5>H3C设备配置示例：</h5>
          <pre><code>snmp-agent target-host trap host-name {{ snmpSettings.trap_listen_address || '[监听地址]' }} udp-port {{ snmpSettings.trap_listen_port || '162' }} securityname {{ snmpSettings.community_strings[0] || 'public' }}
snmp-agent trap enable</code></pre>
        </div>
        
        <div class="note">
          <p><strong>注意：</strong>配置完成后需要重启SNMP Trap监听服务才能使新配置生效。</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import { getSNMPConfig, updateSNMPConfig } from '@/api/snmp'

export default {
  name: 'SNMPSettings',
  data() {
    return {
      snmpSettings: {
        trap_listen_address: '0.0.0.0',
        trap_listen_port: 162,
        community_strings: ['public'],
        allowed_hosts: []
      },
      communityOptions: [
        { value: 'public', label: 'public' },
        { value: 'private', label: 'private' },
        { value: 'monitor', label: 'monitor' }
      ],
      hostOptions: []
    }
  },
  
  mounted() {
    this.loadSNMPConfig()
  },
  
  methods: {
    async loadSNMPConfig() {
      try {
        const response = await getSNMPConfig()
        if (response && response.success) {
          this.snmpSettings = { ...this.snmpSettings, ...response.data }
        } else {
          ElMessage.warning('加载SNMP配置失败: ' + (response?.message || '未知错误'))
        }
      } catch (error) {
        console.error('加载SNMP配置失败:', error)
        ElMessage.error('加载SNMP配置失败: ' + (error.message || '未知错误'))
      }
    },
    
    async saveSNMPConfig() {
      try {
        const response = await updateSNMPConfig(this.snmpSettings)
        if (response && response.success) {
          ElMessage.success('SNMP配置保存成功')
        } else {
          ElMessage.error('SNMP配置保存失败: ' + (response?.message || '未知错误'))
        }
      } catch (error) {
        console.error('保存SNMP配置失败:', error)
        ElMessage.error('保存SNMP配置失败: ' + (error.message || '未知错误'))
      }
    }
  }
}
</script>

<style scoped>
.snmp-settings-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.guide-content {
  line-height: 1.6;
}

.guide-content h4 {
  margin-top: 0;
}

.command-guide {
  margin: 15px 0;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.command-guide h5 {
  margin: 0 0 10px 0;
  color: #303133;
}

.command-guide pre {
  margin: 0;
  padding: 10px;
  background-color: #fff;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}

.note {
  margin-top: 15px;
  padding: 10px;
  background-color: #fff6e5;
  border-left: 4px solid #ffa726;
  border-radius: 4px;
}

.note strong {
  color: #333;
}
</style>