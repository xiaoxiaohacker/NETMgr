import request from '@/utils/request'

/**
 * 获取用户列表
 * @returns {Promise}
 */
export function getUsers() {
  return request({
    url: '/api/v1/users/',
    method: 'get'
  })
}

/**
 * 创建用户
 * @param {Object} data - 用户数据
 * @returns {Promise}
 */
export function createUser(data) {
  return request({
    url: '/api/v1/users/',
    method: 'post',
    data
  })
}

/**
 * 更新用户
 * @param {Number} userId - 用户ID
 * @param {Object} data - 用户数据
 * @returns {Promise}
 */
export function updateUser(userId, data) {
  return request({
    url: `/api/v1/users/${userId}`,
    method: 'put',
    data
  })
}

/**
 * 删除用户
 * @param {Number} userId - 用户ID
 * @returns {Promise}
 */
export function deleteUser(userId) {
  return request({
    url: `/api/v1/users/${userId}`,
    method: 'delete'
  })
}

/**
 * 切换用户状态
 * @param {Number} userId - 用户ID
 * @param {Boolean} isActive - 激活状态
 * @returns {Promise}
 */
export function toggleUserStatus(userId, isActive) {
  return request({
    url: `/api/v1/users/${userId}/status`,
    method: 'patch',
    data: { is_active: isActive }
  })
}