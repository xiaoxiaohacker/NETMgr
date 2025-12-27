import request from '@/utils/request'

/**
 * 获取基本设置
 * @returns {Promise}
 */
export function getBasicSettings() {
  return request({
    url: '/api/v1/settings/basic',
    method: 'get'
  })
}

/**
 * 更新基本设置
 * @param {Object} settings 基本设置数据
 * @returns {Promise}
 */
export function updateBasicSettings(settings) {
  return request({
    url: '/api/v1/settings/basic',
    method: 'put',
    data: settings
  })
}

/**
 * 获取扫描设置
 * @returns {Promise}
 */
export function getScanSettings() {
  return request({
    url: '/api/v1/settings/scan',
    method: 'get'
  })
}

/**
 * 更新扫描设置
 * @param {Object} settings 扫描设置数据
 * @returns {Promise}
 */
export function updateScanSettings(settings) {
  return request({
    url: '/api/v1/settings/scan',
    method: 'put',
    data: settings
  })
}

/**
 * 获取通知设置
 * @returns {Promise}
 */
export function getNotificationSettings() {
  return request({
    url: '/api/v1/settings/notification',
    method: 'get'
  })
}

/**
 * 更新通知设置
 * @param {Object} settings 通知设置数据
 * @returns {Promise}
 */
export function updateNotificationSettings(settings) {
  return request({
    url: '/api/v1/settings/notification',
    method: 'put',
    data: settings
  })
}

/**
 * 测试通知
 * @returns {Promise}
 */
export function testNotifications() {
  return request({
    url: '/api/v1/settings/notification/test',
    method: 'post'
  })
}

/**
 * 扫描网络发现主机
 * @param {String} ipRange IP地址范围
 * @returns {Promise}
 */
export function scanNetworkHosts(ipRange) {
  return request({
    url: `/api/v1/settings/scan/discover?ip_range=${encodeURIComponent(ipRange)}`,
    method: 'post'
  })
}

/**
 * 清理日志
 * @param {Number} days 保留天数
 * @returns {Promise}
 */
export function cleanupLogs(days = 30) {
  return request({
    url: `/api/v1/settings/maintenance/cleanup-logs?days=${days}`,
    method: 'post'
  })
}

/**
 * 备份系统
 * @returns {Promise}
 */
export function backupSystem() {
  return request({
    url: '/api/v1/settings/maintenance/backup-system',
    method: 'post'
  })
}

/**
 * 重启系统
 * @returns {Promise}
 */
export function restartSystem() {
  return request({
    url: '/api/v1/settings/maintenance/restart',
    method: 'post'
  })
}

/**
 * 获取系统信息
 * @returns {Promise}
 */
export function getSystemInfo() {
  return request({
    url: '/api/v1/settings/system-info',
    method: 'get'
  })
}