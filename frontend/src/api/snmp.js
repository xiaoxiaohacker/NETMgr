import request from '@/utils/request'

/**
 * 获取SNMP配置信息
 * @returns {Promise}
 */
export function getSNMPConfig() {
  return request({
    url: '/api/v1/snmp/config',
    method: 'get'
  })
}

/**
 * 更新SNMP配置信息
 * @param {Object} data SNMP配置信息
 * @returns {Promise}
 */
export function updateSNMPConfig(data) {
  return request({
    url: '/api/v1/snmp/config',
    method: 'put',
    data
  })
}

/**
 * 配置设备SNMP Trap
 * @param {Number} deviceId 设备ID
 * @param {Object} data SNMP配置信息
 * @returns {Promise}
 */
export function configureSNMPTrap(deviceId, data) {
  return request({
    url: `/api/v1/devices/${deviceId}/configure-snmp-trap`,
    method: 'post',
    data
  })
}

/**
 * 获取设备SNMP配置
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function getDeviceSNMPConfig(deviceId) {
  return request({
    url: `/api/v1/devices/${deviceId}/snmp-config`,
    method: 'get'
  })
}

/**
 * 更新设备SNMP配置
 * @param {Number} deviceId 设备ID
 * @param {Object} data SNMP配置信息
 * @returns {Promise}
 */
export function updateDeviceSNMPConfig(deviceId, data) {
  return request({
    url: `/api/v1/devices/${deviceId}/snmp-config`,
    method: 'put',
    data
  })
}

/**
 * 测试设备SNMP连接
 * @param {Number} deviceId 设备ID
 * @returns {Promise}
 */
export function testSNMPConnection(deviceId) {
  return request({
    url: `/api/v1/devices/${deviceId}/test-snmp`,
    method: 'post'
  })
}