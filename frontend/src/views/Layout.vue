<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo">NetMgr 网络管理系统</div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        :router="false"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><Monitor /></el-icon>
          <span>设备管理</span>
        </el-menu-item>
        <el-menu-item index="/topology">
          <el-icon><Share /></el-icon>
          <span>网络拓扑</span>
        </el-menu-item>
        <el-menu-item index="/monitor">
          <el-icon><DataLine /></el-icon>
          <span>实时监控</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <span>告警管理</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><Collection /></el-icon>
          <span>任务管理</span>
        </el-menu-item>
        <el-menu-item index="/logs">
          <el-icon><Document /></el-icon>
          <span>日志管理</span>
        </el-menu-item>
        <el-menu-item index="/backup">
          <el-icon><Coin /></el-icon>
          <span>配置备份</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon>
            <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24"><path fill="currentColor" d="m18.42 14.5l-.37-.16a5.99 5.99 0 0 0 .74-2.34c0-.84-.16-1.64-.46-2.38l.37-.16a2.3 2.3 0 0 0 1.35-2.01V6c0-.62-.37-1.17-.92-1.39l-.55-.2a5.2 5.2 0 0 0-1.03-1.03l-.2-.55c-.22-.55-.77-.92-1.39-.92h-1.5c-.77 0-1.48.38-1.92 1.01l-.3.46c-.42.63-1.01 1.13-1.7 1.46l-.56.27c-.5.24-1.07.38-1.65.38s-1.15-.14-1.65-.38l-.56-.27c-.69-.33-1.28-.83-1.7-1.46l-.3-.46C6.01 3.38 5.3 3 4.53 3H3c-.62 0-1.17.37-1.39.92l-.2.55c-.34.59-.58 1.24-.7 1.93l-.07.5c-.28.09-.56.22-.8.39c-.55.37-.88.99-.88 1.66v1.5c0 .77.38 1.48 1.01 1.92l.46.3c.63.42 1.13 1.01 1.46 1.7l.27.56c.24.5.38 1.07.38 1.65s-.14 1.15-.38 1.65l-.27.56c-.33.69-.83 1.28-1.46 1.7l.46-.3C3.38 17.99 3 18.7 3 19.47v1.5c0 .62.37 1.17.92 1.39l.55.2c.34.19.7.33 1.07.42l.43.1c.48.5.2 1.3-.42 1.3H3c-.55 0-1-.45-1-1s.45-1 1-1h.53c.28 0 .55-.11.76-.31c.2-.2.31-.47.31-.76V19.5c0-.77-.38-1.48-1.01-1.92l-.46-.3c-.63-.42-1.13-1.01-1.46-1.7l-.27-.56c-.24-.5-.38-1.07-.38-1.65s.14-1.15.38-1.65l.27-.56c.33-.69.83-1.28 1.46-1.7l.46-.3C5.02 9.01 5.4 8.3 5.4 7.53v-1.5c0-.29-.11-.56-.31-.76c-.2-.2-.47-.31-.76-.31H3c-.55 0-1-.45-1-1s.45-1 1-1h.53c.28 0 .55.11.76.31c.2.2.31.47.31.76v1.5c0 .77.38 1.48 1.01 1.92l.46.3c.63.42 1.13 1.01 1.46 1.7l.27.56c.24.5.38 1.07.38 1.65s-.14 1.15-.38 1.65l-.27.56c-.33.69-.83 1.28-1.46 1.7l-.46.3c-.63.44-1.01 1.15-1.01 1.92v1.5c0 .29.11.56.31.76c.2.2.47.31.76.31H6c.62 0 .9-.8.42-1.3l-.43-.1c-.37-.09-.73-.23-1.07-.42l-.55-.2c-.55-.22-.92-.77-.92-1.39v-1.5c0-.67.33-1.29.88-1.66c.24-.17.52-.3.8-.39l.07-.5c.12-.69.36-1.34.7-1.93l.2-.55c.22-.55.77-.92 1.39-.92h1.5c.58 0 1.15.14 1.65.38l.56.27c.69.33 1.28.83 1.7 1.46l.3.46c.44.63 1.15 1.01 1.92 1.01h1.5c.62 0 1.17-.37 1.39-.92l.2-.55c.34-.59.58-1.24.7-1.93l.07-.5c.28-.09.56-.22.8-.39c.55-.37.88-.99.88-1.66v-1.5c0-.67-.33-1.29-.88-1.66c-.24-.17-.52-.3-.8-.39z"/><path fill="currentColor" d="M12 15c1.66 0 3-1.34 3-3s-1.34-3-3-3s-3 1.34-3 3s1.34 3 3 3zm0-4c.55 0 1 .45 1 1s-.45 1-1 1s-1-.45-1-1s.45-1 1-1z"/></svg>
          </el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主体区域 -->
    <el-container>
      <!-- 头部 -->
      <el-header class="header">
        <div class="header-left">
          <h2>{{ pageTitle }}</h2>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-avatar :size="30" icon="UserFilled" />
              <span class="username">{{ username }} <el-tag size="small" type="info">{{ userRoleDisplay }}</el-tag></span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { isTokenValid } from '@/utils/auth'
import {
  Odometer,
  Monitor,
  Share,
  DataLine,
  Bell,
  Collection,
  Document,
  Coin,
  User
} from '@element-plus/icons-vue'

// 模拟登出API调用
const logout = () => {
  return new Promise((resolve) => {
    setTimeout(() => resolve(), 500)
  })
}

// 路由相关
const route = useRoute()
const router = useRouter()

// 令牌检查定时器
let tokenCheckInterval = null

// 当前激活菜单
const activeMenu = computed(() => {
  const { meta, path } = route
  // 如果设置了meta.activeMenu，则使用它
  if (meta.activeMenu) {
    return meta.activeMenu
  }
  return path
})

// 页面标题
const pageTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表盘',
    '/devices': '设备管理',
    '/topology': '网络拓扑',
    '/monitor': '实时监控',
    '/alerts': '告警管理',
    '/tasks': '任务管理',
    '/logs': '日志管理',
    '/backup': '配置备份',
    '/users': '用户管理',
    '/settings': '系统设置',
    '/profile': '个人信息'
  }
  return titles[route.path] || '网络设备管理系统'
})

// 用户名和角色
const username = ref(localStorage.getItem('username') || '管理员')
const userRole = ref('')
const userRoleDisplay = computed(() => {
  if (userRole.value === 'admin') {
    return '管理员'
  } else if (userRole.value === 'operator') {
    return '操作员'
  }
  // 如果没有角色信息，默认显示为管理员
  return '管理员'
})

// 在组件挂载时获取用户角色
onMounted(() => {
  // 立即检查一次令牌有效性
  checkTokenValidity()
  
  // 从localStorage获取用户角色信息
  const storedRole = localStorage.getItem('userRole')
  if (storedRole) {
    userRole.value = storedRole
  }
  
  // 每分钟检查一次令牌有效性
  tokenCheckInterval = setInterval(checkTokenValidity, 60000)
})

// 处理用户命令
const handleUserCommand = (command) => {
  if (command === 'logout') {
    // 显示确认对话框
    ElMessageBox.confirm(
      '确定要退出登录吗？',
      '退出登录',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(async () => {
      try {
        // 调用后端登出接口
        await logout()
        ElMessage.success('登出成功')
      } catch (error) {
        // 即使后端调用失败，也要清除本地token
        console.error('登出接口调用失败:', error)
      } finally {
        // 清除本地存储的token、用户名和角色
        localStorage.removeItem('access_token')
        localStorage.removeItem('username')
        localStorage.removeItem('userRole')
        localStorage.removeItem('systemName')
        
        // 跳转到登录页 - 使用router.push确保正确跳转
        router.push('/login').catch(err => {
          console.error('路由跳转失败:', err)
          // 如果router.push失败，则使用window.location
          window.location.href = '/#/login'
        })
      }
    }).catch(() => {
      // 用户取消登出
    })
  } else if (command === 'profile') {
    // 跳转到个人信息页面
    router.push('/profile')
  }
}

// 处理菜单选择
const handleMenuSelect = (index) => {
  // 检查令牌有效性，如果无效则不允许导航
  const token = localStorage.getItem('access_token')
  if (!token || !isTokenValid(token)) {
    ElMessage.error('登录已过期，请重新登录')
    router.push('/login').catch(err => {
      console.error('路由跳转失败:', err)
      window.location.href = '/#/login'
    })
    return
  }

  console.log('Menu selected:', index)
  console.log('Current route:', route.path)
  
  // 如果点击的是当前页面，不执行跳转
  if (route.path === index) {
    console.log('Already on the selected page, skipping navigation')
    return
  }
  
  console.log('Navigating to:', index)
  router.push(index).catch(err => {
    console.error('Navigation error:', err)
  })
}

// 监听路由变化，用于调试
watch(route, (to, from) => {
  console.log('Route changed from', from.path, 'to', to.path)
  
  // 每次路由变化时也检查令牌有效性
  const token = localStorage.getItem('access_token')
  if (token && !isTokenValid(token)) {
    // 令牌已过期，清除本地存储并跳转到登录页
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
    localStorage.removeItem('userRole')
    localStorage.removeItem('systemName')
    ElMessage.error('登录已过期，请重新登录')
    
    // 使用router跳转到登录页
    router.push('/login').catch(err => {
      console.error('路由跳转失败:', err)
      // 如果router.push失败，则使用window.location
      window.location.href = '/#/login'
    })
  }
})

// 检查令牌有效性
const checkTokenValidity = () => {
  const token = localStorage.getItem('access_token')
  if (token && !isTokenValid(token)) {
    // 令牌已过期，清除本地存储并跳转到登录页
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
    localStorage.removeItem('userRole')
    localStorage.removeItem('systemName')
    ElMessage.error('登录已过期，请重新登录')
    
    // 使用router跳转到登录页
    router.push('/login').catch(err => {
      console.error('路由跳转失败:', err)
      // 如果router.push失败，则使用window.location
      window.location.href = '/#/login'
    })
  }
}

// 组件卸载前清理定时器
onBeforeUnmount(() => {
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval)
  }
})

</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  transition: width 0.28s;
  overflow: hidden;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  background-color: #2c3e50;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
}

.sidebar-menu {
  border: none;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0 20px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 10px;
  font-size: 14px;
  color: #333;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>