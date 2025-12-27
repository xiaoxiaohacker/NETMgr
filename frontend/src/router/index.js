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

export default router