import request from '@/utils/request'

/**
 * 获取拓扑图设备列表
 * @returns {Promise}
 */
export function getTopologyDevices() {
  return request({
    url: '/api/v1/topology/devices',
    method: 'get'
  })
}

/**
 * 获取拓扑图连接关系
 * @returns {Promise}
 */
export function getTopologyLinks() {
  return request({
    url: '/api/v1/topology/links',
    method: 'get'
  })
}

/**
 * 获取拓扑图布局信息
 * @returns {Promise}
 */
export function getTopologyLayout() {
  return request({
    url: '/api/v1/topology/layout',
    method: 'get'
  })
}

/**
 * 保存拓扑图布局信息
 * @param {Object} data 布局数据
 * @returns {Promise}
 */
export function saveTopologyLayout(data) {
  return request({
    url: '/api/v1/topology/layout/save',
    method: 'post',
    data
  })
}

/**
 * 刷新拓扑图数据
 * @returns {Promise}
 */
export function refreshTopology() {
  return request({
    url: '/api/v1/topology/refresh',
    method: 'post'
  })
}