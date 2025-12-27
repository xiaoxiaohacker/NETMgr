<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
        </div>
      </template>
      
      <el-form 
        :model="userInfo" 
        :rules="rules" 
        ref="profileForm" 
        label-width="120px"
        class="profile-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="userInfo.username" disabled></el-input>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="userInfo.email"></el-input>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="创建时间" prop="created_at">
              <el-input v-model="formattedCreatedAt" disabled></el-input>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="激活状态" prop="is_active">
              <el-switch
                v-model="userInfo.is_active"
                disabled
                active-text="已激活"
                inactive-text="未激活">
              </el-switch>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider></el-divider>
        
        <el-row :gutter="20">
          <el-col :span="24">
            <h3>修改密码</h3>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="旧密码" prop="oldPassword">
              <el-input 
                v-model="passwordForm.oldPassword" 
                type="password" 
                show-password
                placeholder="请输入当前密码"
              ></el-input>
            </el-form-item>
          </el-col>
          
          <el-col :span="12"></el-col>
          
          <el-col :span="12">
            <el-form-item label="新密码" prop="newPassword">
              <el-input 
                v-model="passwordForm.newPassword" 
                type="password" 
                show-password
                placeholder="请输入新密码"
              ></el-input>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input 
                v-model="passwordForm.confirmPassword" 
                type="password" 
                show-password
                placeholder="请再次输入新密码"
              ></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button type="primary" @click="saveProfile">保存信息</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getCurrentUser } from '@/api/auth'

// 表单引用
const profileForm = ref(null)

// 用户信息
const userInfo = reactive({
  id: '',
  username: '',
  email: '',
  is_active: true,
  created_at: ''
})

// 密码表单
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 格式化创建时间
const formattedCreatedAt = computed(() => {
  if (userInfo.created_at) {
    // 尝试多种日期格式解析
    const date = new Date(userInfo.created_at)
    if (!isNaN(date.getTime())) {
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    return userInfo.created_at
  }
  return ''
})

// 表单验证规则
const rules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  oldPassword: [
    { required: false, message: '请输入当前密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  newPassword: [
    { required: false, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: false, message: '请确认新密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value && value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ]
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await getCurrentUser()
    Object.assign(userInfo, response)
  } catch (error) {
    ElMessage.error('获取用户信息失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 保存个人信息
const saveProfile = async () => {
  // 验证表单
  const valid = await profileForm.value.validate().catch(() => false)
  if (!valid) {
    ElMessage.error('请正确填写表单信息')
    return
  }
  
  // 检查密码修改
  if ((passwordForm.newPassword || passwordForm.confirmPassword || passwordForm.oldPassword)) {
    if (!(passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.oldPassword)) {
      ElMessage.error('修改密码需要填写所有密码字段')
      return
    }
    
    // 如果填写了新密码但两次输入不一致
    if (passwordForm.newPassword && passwordForm.newPassword !== passwordForm.confirmPassword) {
      ElMessage.error('两次输入的新密码不一致')
      return
    }
    
    // 模拟密码修改操作（实际项目中需要调用后端API）
    ElMessage({
      message: '密码修改功能需要后端支持，当前为演示版本',
      type: 'warning'
    })
  }
  
  // 模拟保存操作
  ElMessage.success('个人信息保存成功')
  resetPasswordForm()
}

// 重置表单
const resetForm = () => {
  profileForm.value.resetFields()
  resetPasswordForm()
}

// 重置密码表单
const resetPasswordForm = () => {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
}

// 页面加载时获取用户信息
onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.profile-form {
  margin-top: 20px;
}

.el-row {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>