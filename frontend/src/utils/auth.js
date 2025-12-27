/**
 * 检查JWT令牌是否有效
 * @param {string} token JWT令牌
 * @returns {boolean} 令牌是否有效
 */
export function isTokenValid(token) {
  if (!token) return false
  
  try {
    // 解析JWT令牌以检查过期时间
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp
    const currentTime = Math.floor(Date.now() / 1000)
    
    // 检查令牌是否已过期
    return exp > currentTime
  } catch (e) {
    // 如果令牌格式不正确，视为无效
    return false
  }
}

/**
 * 获取令牌剩余有效时间（秒）
 * @param {string} token JWT令牌
 * @returns {number|null} 剩余有效时间（秒），如果令牌无效则返回null
 */
export function getTokenExpirationTime(token) {
  if (!token) return null
  
  try {
    // 解析JWT令牌以获取过期时间
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp
    const currentTime = Math.floor(Date.now() / 1000)
    
    // 计算剩余时间
    const remainingTime = exp - currentTime
    return remainingTime > 0 ? remainingTime : 0
  } catch (e) {
    // 如果令牌格式不正确，返回null
    return null
  }
}