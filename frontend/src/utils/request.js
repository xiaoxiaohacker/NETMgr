import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建一个标志，用于标记是否正在跳转到登录页
let isRedirecting = false

// 创建 axios 实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL, // 使用环境变量
  timeout: 15000 // 请求超时时间
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 对于设备命令执行接口，增加超时时间到35秒，确保大于后端的30秒超时
    if (config.url && config.url.includes('/execute')) {
      config.timeout = 35000
    }
    
    return config
  },
  (error) => {
    // 对请求错误做些什么
    console.log(error) // for debug
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    return response.data
  },
  (error) => {
    // 对响应错误做点什么
    console.log('err' + error) // for debug
    
    // 如果正在跳转到登录页，则不显示错误消息
    if (isRedirecting) {
      return Promise.reject(error)
    }
    
    // 处理不同状态码的错误
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          // 未授权，清除本地存储并跳转到登录页
          localStorage.removeItem('access_token')
          localStorage.removeItem('username')
          localStorage.removeItem('systemName')
          
          // 设置跳转标志
          isRedirecting = true
          
          // 使用Vue Router跳转到登录页
          import('@/router').then(routerModule => {
            const router = routerModule.default
            router.push('/login').catch(err => {
              console.error('路由跳转失败:', err)
              // 如果router.push失败，则使用window.location
              window.location.href = '/#/login'
            })
          }).catch(err => {
            console.error('路由导入失败:', err)
            // 如果导入路由失败，则使用window.location
            window.location.href = '/#/login'
          })
          
          ElMessage.error('登录已过期，请重新登录')
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(data.detail || '请求失败')
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      // ElMessage.error('网络错误，请检查网络连接')
      //如果连续错误，只显示一次弹出提示
      if (!isRedirecting) {
        ElMessage.error('网络错误，请检查网络连接')
        isRedirecting = true
      }
      
      
    } else {
      // 其他错误
      ElMessage.error(error.message || '未知错误')
    }
    
    return Promise.reject(error)
  }
)

export default service