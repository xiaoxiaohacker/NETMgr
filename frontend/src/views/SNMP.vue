<template>
  <div class="snmp-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>SNMP配置</span>
          <el-button type="primary" size="small" @click="saveSNMPConfig">保存配置</el-button>
        </div>
      </template>
      
      <el-form :model="snmpSettings" label-width="150px">
        <el-form-item label="Trap监听地址">
          <el-input 
            v-model="snmpSettings.trap_listen_address" 
            placeholder="请输入监听地址"
          />
        </el-form-item>
        
        <el-form-item label="Trap监听端口">
          <el-input-number 
            v-model="snmpSettings.trap_listen_port" 
            :min="1" 
            :max="65535"
            controls-position="right"
          />
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
          <pre><code>snmp-agent target-host trap address udp-domain {{ snmpSettings.trap_listen_address || '[监听地址]' }} udp-port {{ snmpSettings.trap_listen_port || '162' }} params securityname {{ snmpSettings.community_strings[0] || 'public' }}
snmp-agent trap enable</code></pre>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import { getSNMPConfig, updateSNMPConfig } from '@/api/snmp'

export default {
  name: 'SNMP',
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
        { value: 'private', label: 'private' }
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
        console.log('开始加载SNMP配置...');
        const response = await getSNMPConfig()
        console.log('SNMP配置响应完整数据:', response);
        
        // 检查响应是否存在且具有success属性
        if (!response || typeof response !== 'object') {
          throw new Error('API响应格式不正确');
        }
        
        // 检查success状态
        if (response.success === false) {
          throw new Error(response.message || '获取SNMP配置失败');
        }
        
        // 检查data字段是否存在
        if (!response.data || typeof response.data !== 'object') {
          throw new Error('响应数据格式不正确');
        }
        
        // 更新配置数据
        this.snmpSettings.trap_listen_address = response.data.trap_listen_address || this.snmpSettings.trap_listen_address;
        this.snmpSettings.trap_listen_port = response.data.trap_listen_port || this.snmpSettings.trap_listen_port;
        
        // 处理社区字符串
        if (Array.isArray(response.data.community_strings)) {
          this.snmpSettings.community_strings = [...response.data.community_strings];
        } else if (typeof response.data.community_strings === 'string') {
          this.snmpSettings.community_strings = [response.data.community_strings];
        }
        
        // 处理允许的主机
        if (Array.isArray(response.data.allowed_hosts)) {
          this.snmpSettings.allowed_hosts = [...response.data.allowed_hosts];
        } else if (typeof response.data.allowed_hosts === 'string') {
          this.snmpSettings.allowed_hosts = [response.data.allowed_hosts];
        }
        
        console.log('SNMP配置加载成功:', this.snmpSettings);
      } catch (error) {
        console.error('加载SNMP配置失败:', error);
        ElMessage.error(`加载SNMP配置失败: ${error.message}`);
      }
    },
    
    async saveSNMPConfig() {
      try {
        const configData = {
          trap_listen_address: this.snmpSettings.trap_listen_address,
          trap_listen_port: this.snmpSettings.trap_listen_port,
          community_strings: this.snmpSettings.community_strings,
          allowed_hosts: this.snmpSettings.allowed_hosts
        };
        
        const response = await updateSNMPConfig(configData);
        
        if (response && response.success === true) {
          ElMessage.success('SNMP配置保存成功');
        } else {
          ElMessage.error(response?.message || '保存SNMP配置失败');
        }
      } catch (error) {
        console.error('保存SNMP配置失败:', error);
        ElMessage.error('保存SNMP配置失败: ' + error.message);
      }
    }
  }
}

</script>

<style scoped>
.snmp-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.guide-content {
  line-height: 1.6;
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
}
</style>