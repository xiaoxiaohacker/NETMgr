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
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCurrentUser } from '@/api/auth'
import { updateUser } from '@/api/users'

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
  if (passwordForm.oldPassword || passwordForm.newPassword || passwordForm.confirmPassword) {
    // 检查是否填写了所有密码字段
    if (!(passwordForm.oldPassword && passwordForm.newPassword && passwordForm.confirmPassword)) {
      ElMessage.error('修改密码需要填写所有密码字段')
      return
    }
    
    // 验证新密码和确认密码是否一致
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      ElMessage.error('两次输入的新密码不一致')
      return
    }
    
    // 验证密码长度
    if (passwordForm.newPassword.length < 6) {
      ElMessage.error('新密码长度至少6位')
      return
    }
    
    // 确认是否真的要修改密码
    try {
      await ElMessageBox.confirm(
        '确认要修改您的密码吗？',
        '修改密码',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      // 用户取消了操作
      return
    }
    
    // 调用API更新用户信息，包括密码
    try {
      const userData = {
        username: userInfo.username,
        email: userInfo.email,
        is_active: userInfo.is_active,
        password: passwordForm.newPassword // 将新密码作为password字段发送
      }
      
      const response = await updateUser(userInfo.id, userData)
      ElMessage.success('密码修改成功！')
      
      // 重置密码表单
      resetPasswordForm()
    } catch (error) {
      console.error('修改密码失败:', error)
      ElMessage.error('密码修改失败: ' + (error.response?.data?.detail || error.message))
    }
  } else {
    // 仅更新个人信息（邮箱等）
    try {
      const userData = {
        username: userInfo.username,
        email: userInfo.email,
        is_active: userInfo.is_active,
        password: "" // 不修改密码时，不需要发送密码
      }
      
      // 如果没有修改密码，我们只发送邮箱更新请求
      const response = await updateUser(userInfo.id, {
        username: userInfo.username,
        email: userInfo.email,
        is_active: userInfo.is_active,
        password: undefined // 不包含password字段，这样就不会更新密码
      })
      
      ElMessage.success('个人信息保存成功')
    } catch (error) {
      console.error('保存个人信息失败:', error)
      ElMessage.error('保存个人信息失败: ' + (error.response?.data?.detail || error.message))
    }
  }
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