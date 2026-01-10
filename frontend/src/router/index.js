import { createRouter, createWebHashHistory } from 'vue-router'
import Layout from '@/views/Layout.vue'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import DeviceList from '@/views/DeviceList.vue'
import DeviceDetail from '@/views/DeviceDetail.vue'
import Topology from '@/views/Topology.vue'
import Alerts from '@/views/Alerts.vue'
import Logs from '@/views/Logs.vue'
import Settings from '@/views/Settings.vue'
import SNMPSettings from '@/views/SNMPSettings.vue'
import Profile from '@/views/Profile.vue'
import Monitor from '@/views/Monitor.vue'
import Tasks from '@/views/Tasks.vue'
import Backup from '@/views/Backup.vue'
import Users from '@/views/Users.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'devices',
        name: 'DeviceList',
        component: DeviceList
      },
      {
        path: 'devices/:id',
        name: 'DeviceDetail',
        component: DeviceDetail,
        props: true
      },
      {
        path: 'topology',
        name: 'Topology',
        component: Topology
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: Alerts
      },
      {
        path: 'logs',
        name: 'Logs',
        component: Logs
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings
      },
      {
        path: 'snmp-settings',
        name: 'SNMPSettings',
        component: SNMPSettings
      },
      {
        path: 'profile',
        name: 'Profile',
        component: Profile
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: Monitor
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: Tasks
      },
      {
        path: 'backup',
        name: 'Backup',
        component: Backup
      },
      {
        path: 'users',
        name: 'Users',
        component: Users
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 添加全局前置守卫
router.beforeEach((to, from, next) => {
  // 检查是否访问登录页面
  if (to.path === '/login') {
    // 如果访问登录页面，直接放行
    next()
  } else {
    // 检查是否有有效的token
    const token = localStorage.getItem('access_token')
    
    if (!token) {
      // 没有token，重定向到登录页面
      next('/login')
    } else {
      // 有token，检查是否有效
      try {
        // 解析JWT令牌以检查过期时间
        const payload = JSON.parse(atob(token.split('.')[1]))
        const exp = payload.exp
        const currentTime = Math.floor(Date.now() / 1000)
        
        if (exp > currentTime) {
          // 令牌有效，允许访问
          next()
        } else {
          // 令牌已过期，清除本地存储并重定向到登录页
          localStorage.removeItem('access_token')
          localStorage.removeItem('username')
          localStorage.removeItem('userRole')
          localStorage.removeItem('systemName')
          next('/login')
        }
      } catch (e) {
        // 令牌格式不正确，重定向到登录页面
        localStorage.removeItem('access_token')
        localStorage.removeItem('username')
        localStorage.removeItem('userRole')
        localStorage.removeItem('systemName')
        next('/login')
      }
    }
  }
})

export default router