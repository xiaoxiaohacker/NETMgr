import request from '@/utils/request'

/**
 * 获取设备总体概览统计数据
 * @returns {Promise}
 */
export function getDeviceOverview() {
  return request({
    url: '/api/v1/device-stats/overview',
    method: 'get'
  })
}

/**
 * 获取网络流量监控数据
 * @returns {Promise}
 */
export function getTrafficMonitoring() {
  return request({
    url: '/api/v1/device-stats/traffic-monitoring',
    method: 'get'
  })
}

/**
 * 获取设备类型统计数据
 * @returns {Promise}
 */
export function getDeviceTypeStats() {
  return request({
    url: '/api/v1/device-stats/device-types',
    method: 'get'
  })
}

/**
 * 获取最近的设备告警信息
 * @returns {Promise}
 */
export function getRecentAlerts() {
  return request({
    url: '/api/v1/device-stats/recent-alerts',
    method: 'get'
  })
}

/**
 * 获取设备健康状态数据
 * @returns {Promise}
 */
export function getDeviceHealth() {
  return request({
    url: '/api/v1/device-stats/device-health',
    method: 'get'
  })
}

/**
 * 获取告警统计信息
 * @returns {Promise}
 */
export function getAlertStatistics() {
  return request({
    url: '/api/v1/alerts/statistics',
    method: 'get'
  })
}

/**
 * 获取设备状态分布
 * @returns {Promise}
 */
export function getDeviceStatusDistribution() {
  return request({
    url: '/api/v1/dashboard/device-status',
    method: 'get'
  })
}

/**
 * 获取警告设备信息
 * @returns {Promise}
 */
export function getWarningDevices() {
  return request({
    url: '/api/v1/dashboard/warnings',
    method: 'get'
  })
}

/**
 * 获取设备性能数据
 * @returns {Promise}
 */
export function getPerformanceData() {
  return request({
    url: '/api/v1/dashboard/performance',
    method: 'get'
  })
}

/**
 * 获取新的仪表盘统计信息
 * @returns {Promise}
 */
export function getNewDashboardStats() {
  return request({
    url: '/api/v1/dashboard/stats',
    method: 'get'
  })
}

/**
 * 获取仪表盘所需的所有数据（设备状态趋势、健康状况、网络流量）
 * @returns {Promise}
 */
export function getDashboardData() {
  return request({
    url: '/api/v1/dashboard/dashboard-data',
    method: 'get'
  })
}