import request from '@/utils/request'

/**
 * 获取设备列表
 * @returns {Promise}
 */
export function getDevices(session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: '/api/v1/devices/',
    method: 'get',
    params
  })
}

/**
 * 添加设备
 * @param {Object} data 设备信息
 * @returns {Promise}
 */
export function addDevice(data, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: '/api/v1/devices/',
    method: 'post',
    data,
    params
  })
}

/**
 * 获取设备详情
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function getDevice(deviceId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}`,
    method: 'get',
    params
  })
}

/**
 * 更新设备信息
 * @param {Number} deviceId 设备ID
 * @param {Object} data 设备信息
 * @returns {Promise}
 */
export function updateDevice(deviceId, data, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}`,
    method: 'put',
    data,
    params
  })
}

/**
 * 删除设备
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function deleteDevice(deviceId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}`,
    method: 'delete',
    params
  })
}

/**
 * 获取设备概览统计信息
 * @returns {Promise}
 */
export function getDeviceOverview(session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: '/api/v1/device-stats/overview',
    method: 'get',
    params
  })
}

/**
 * 获取设备详细信息（通过适配器）
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function getDeviceInfo(deviceId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}/info`,
    method: 'get',
    params
  })
}

/**
 * 获取设备所有接口信息
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function getDeviceInterfaces(deviceId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}/interfaces`,
    method: 'get',
    params
  })
}

/**
 * 获取指定接口状态
 * @param {Number} deviceId 设备ID
 * @param {String} interfaceName 接口名称
 * @returns {Promise}
 */
export function getDeviceInterfaceStatus(deviceId, interfaceName, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}/interface/${interfaceName}`,
    method: 'get',
    params
  })
}

/**
 * 检查设备连通性
 * @param {string} ip 设备IP地址
 * @returns {Promise}
 */
export function checkConnectivity(ip, session_token = null) {
  const params = session_token ? { ...session_token, ip: encodeURIComponent(ip) } : { ip: encodeURIComponent(ip) }
  return request({
    url: `/api/v1/devices/check-connectivity`,
    method: 'get',
    params
  })
}

/**
 * 批量导入设备
 * @param {FormData} formData 包含CSV文件的表单数据
 * @returns {Promise}
 */
export function batchImportDevices(formData, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: '/api/v1/devices/batch-import',
    method: 'post',
    data: formData,
    params,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取设备配置
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function getDeviceConfig(deviceId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}/config`,
    method: 'get',
    params
  })
}

/**
 * 保存设备配置
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function saveDeviceConfig(deviceId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}/save-config`,
    method: 'post',
    params
  })
}

/**
 * 执行设备命令
 * @param {Number} deviceId 设备ID
 * @param {Object} commandData 命令数据
 * @returns {Promise}
 */
export function executeDeviceCommand(deviceId, commandData, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}/execute`,
    method: 'post',
    data: commandData,
    params
  })
}

/**
 * 备份设备配置
 * @param {Number} deviceId 设备ID
 * @param {Object} configData 配置数据
 * @returns {Promise}
 */
export function backupDeviceConfig(deviceId, configData, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}/config-backup`,
    method: 'post',
    data: configData,
    params
  })
}

/**
 * 获取设备的所有配置备份
 * @param {Number} deviceId 设备ID
 * @param {Number} limit 返回的最大记录数
 * @returns {Promise}
 */
export function getDeviceBackups(deviceId, limit = 100, session_token = null) {
  const params = session_token ? { limit, session_token } : { limit }
  return request({
    url: `/api/v1/devices/${deviceId}/config-backups`,
    method: 'get',
    params
  })
}

/**
 * 获取指定的配置备份
 * @param {Number} backupId 配置备份ID
 * @returns {Promise}
 */
export function getBackup(backupId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/config-backups/${backupId}`,
    method: 'get',
    params
  })
}

/**
 * 删除指定的配置备份
 * @param {Number} backupId 配置备份ID
 * @returns {Promise}
 */
export function deleteBackup(backupId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/config-backups/${backupId}`,
    method: 'delete',
    params
  })
}

/**
 * 获取设备的最新配置备份
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function getLatestBackup(deviceId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}/config-backup/latest`,
    method: 'get',
    params
  })
}

/**
 * 下载设备当前配置
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function downloadDeviceConfig(deviceId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/${deviceId}/config/download`,
    method: 'get',
    params,
    responseType: 'blob'
  })
}

/**
 * 下载配置备份文件
 * @param {Number} backupId 配置备份ID
 * @returns {Promise}
 */
export function downloadConfigBackup(backupId, session_token = null) {
  const params = session_token ? { session_token } : {}
  return request({
    url: `/api/v1/devices/config-backups/${backupId}/download`,
    method: 'get',
    params,
    responseType: 'blob'
  })
}