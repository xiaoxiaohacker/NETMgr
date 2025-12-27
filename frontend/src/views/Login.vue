<template>
  <div class="login-container">
    <div class="login-form">
      <h2>网络设备管理系统</h2>
      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        :rules="loginRules" 
        class="login-form-body"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            native-type="submit" 
            :loading="loading"
            style="width: 100%"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'

// 表单引用
const loginFormRef = ref()

// 路由实例
const router = useRouter()

// 登录表单数据
const loginForm = reactive({
  username: 'admin',
  password: '520131xiao'
})

// 登录规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

// 记住我
const rememberMe = ref(false)

// 加载状态
const loading = ref(false)

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      
      try {
        // 调用登录API - 修正参数传递方式
        const response = await login(loginForm.username, loginForm.password)
        
        // 保存token到localStorage
        localStorage.setItem('access_token', response.access_token)
        localStorage.setItem('access_token_username', loginForm.username)
        
        // 如果选择了"记住我"，保存用户名
        if (rememberMe.value) {
          localStorage.setItem('access_token_remembered_username', loginForm.username)
        } else {
          localStorage.removeItem('access_token_remembered_username')
        }
        
        loading.value = false
        
        // 登录成功跳转到首页
        ElMessage.success('登录成功')
        router.push('/')
      } catch (error) {
        loading.value = false
        console.error('登录失败:', error)
        ElMessage.error('登录失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
      }
    }
  })
}

// 页面加载时检查是否记住用户名
onMounted(() => {
  const rememberedUsername = localStorage.getItem('access_token_remembered_username')
  if (rememberedUsername) {
    loginForm.username = rememberedUsername
    rememberMe.value = true
  }
})
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.login-form {
  width: 100%;
  max-width: 400px;
  padding: 30px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-form h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.login-form-body {
  margin-top: 20px;
}
</style>