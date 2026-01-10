<template>
  <div class="users-container">
    <el-card class="users-header">
      <div class="header-content">
        <h2>用户管理</h2>
        <div class="header-actions">
          <el-button v-if="isCurrentUserAdmin" type="primary" @click="showAddUserDialog">添加用户</el-button>
        </div>
      </div>
    </el-card>

    <el-card class="users-table">
      <el-table 
        :data="paginatedUsers" 
        style="width: 100%" 
        v-loading="loading"
        empty-text="暂无数据">
        <el-table-column prop="id" label="ID" width="80" sortable></el-table-column>
        <el-table-column prop="username" label="用户名" width="200"></el-table-column>
        <el-table-column prop="email" label="邮箱" width="250"></el-table-column>
        <el-table-column prop="role" label="角色" width="150">
          <template #default="scope">
            <el-tag :type="getRoleTagType(scope.row.role)">
              {{ getRoleText(scope.row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="200" sortable>
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              @change="toggleUserStatus(scope.row)"
              active-text="启用"
              inactive-text="禁用">
            </el-switch>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" :disabled="!isCurrentUserAdmin" @click="showEditUserDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" :disabled="!isCurrentUserAdmin || scope.row.username === 'admin'" @click="deleteUser(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="users && Array.isArray(users) ? users.length : 0">
        </el-pagination>
      </div>
    </el-card>

    <!-- 添加/编辑用户对话框 -->
    <el-dialog :title="dialogTitle" v-model="userDialogVisible" width="500px">
      <el-form :model="currentUser" :rules="userRules" ref="userForm" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="currentUser.username" :disabled="isEditMode"></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="currentUser.email"></el-input>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="currentUser.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin"></el-option>
            <el-option label="操作员" value="operator"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEditMode">
          <el-input v-model="currentUser.password" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword" v-if="!isEditMode">
          <el-input v-model="currentUser.confirmPassword" type="password" show-password></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="userDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveUser">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { 
  getUsers, 
  createUser, 
  updateUser, 
  deleteUser as deleteUserAPI,
  toggleUserStatus as toggleUserStatusAPI
} from '@/api/users'

export default {
  name: 'Users',
  data() {
    // 自定义确认密码验证规则
    const validateConfirmPassword = (rule, value, callback) => {
      if (!this.isEditMode) {
        if (!value) {
          callback(new Error('请确认密码'))
        } else if (value !== this.currentUser.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      } else {
        callback()
      }
    }

    return {
      loading: false,
      users: [],
      currentPage: 1,
      pageSize: 10,
      userDialogVisible: false,
      isEditMode: false,
      currentUser: {
        id: null,
        username: '',
        email: '',
        role: '',
        password: '',
        confirmPassword: ''
      },
      userRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ],
        role: [
          { required: true, message: '请选择角色', trigger: 'change' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 10, message: '密码长度至少10位', trigger: 'blur' }
        ],
        confirmPassword: [
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      }
    }
  },
  computed: {
    dialogTitle() {
      return this.isEditMode ? '编辑用户' : '添加用户'
    },
    isCurrentUserAdmin() {
      // 从localStorage获取当前用户角色
      const currentUserRole = localStorage.getItem('userRole');
      return currentUserRole && currentUserRole.toUpperCase() === 'ADMIN';
    },
    paginatedUsers() {
      if (!this.users || !Array.isArray(this.users)) {
        return [];
      }
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.users.slice(start, end)
    }
  },
  async mounted() {
    await this.loadUsers();
    // 确保在数据加载后正确计算分页
    this.$nextTick(() => {
      this.handleCurrentChange(1);
    });
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    },
    getRoleTagType(role) {
      switch (role) {
        case 'admin': return 'danger'
        case 'operator': return 'warning'
        case 'guest': return 'info'
        default: return 'info'
      }
    },
    getRoleText(role) {
      switch (role) {
        case 'admin': return '管理员'
        case 'operator': return '操作员'
        case 'guest': return '访客'
        default: return role || '未知角色'
      }
    },
    async loadUsers() {
      try {
        this.loading = true
        const response = await getUsers()
        console.log("API Response:", response)  // 调试信息
        // 修复数据处理逻辑 - 直接使用响应数据，而不是response.data
        this.users = Array.isArray(response) ? response : []
        console.log("Users loaded:", this.users)  // 调试信息
      } catch (error) {
        console.error('获取用户列表失败:', error)
        this.$message.error('获取用户列表失败')
        this.users = [] // 确保即使出错也有默认值
      } finally {
        this.loading = false
      }
    },
    showAddUserDialog() {
      this.isEditMode = false
      this.currentUser = {
        id: null,
        username: '',
        email: '',
        role: 'operator', // 默认角色
        password: '',
        confirmPassword: ''
      }
      this.userDialogVisible = true
    },
    showEditUserDialog(user) {
      this.isEditMode = true
      this.currentUser = { ...user }
      this.userDialogVisible = true
    },
    async toggleUserStatus(user) {
      try {
        // 确保传递的是布尔值
        const isActive = Boolean(user.is_active);
        const response = await toggleUserStatusAPI(user.id, isActive)
        this.$message.success(`用户 ${user.username} 状态已更新`)
      } catch (error) {
        console.error('更新用户状态失败:', error)
        this.$message.error('更新用户状态失败')
        // 恢复原来的值
        user.is_active = !user.is_active
      }
    },
    async deleteUser(user) {
      try {
        await this.$confirm(`确认删除用户 ${user.username} 吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await deleteUserAPI(user.id)
        this.$message.success('删除成功')
        await this.loadUsers() // 重新加载用户列表
      } catch (error) {
        console.error('删除用户失败:', error)
        this.$message.error('删除用户失败')
      }
    },
    async saveUser() {
      this.$refs.userForm.validate(async (valid) => {
        if (valid) {
          try {
            // 验证当前用户是否有权限进行操作
            if (!this.isCurrentUserAdmin && this.isEditMode) {
              // 操作员不能编辑用户信息
              this.$message.error('权限不足，只有管理员可以编辑用户信息');
              return;
            }
            
            if (this.isEditMode) {
              // 编辑用户 - 只有管理员可以编辑用户信息
              if (!this.isCurrentUserAdmin) {
                this.$message.error('权限不足，只有管理员可以编辑用户信息');
                return;
              }
              
              // 验证不能将操作员权限提升为管理员（除非当前用户是管理员）
              await updateUser(this.currentUser.id, {
                username: this.currentUser.username,
                email: this.currentUser.email,
                role: this.isCurrentUserAdmin ? this.currentUser.role : undefined, // 只有管理员可以更新角色
                password: this.currentUser.password || undefined  // 如果密码为空则不更新
              })
              this.$message.success('用户更新成功')
            } else {
              // 添加用户 - 只有管理员可以添加用户
              if (!this.isCurrentUserAdmin) {
                this.$message.error('权限不足，只有管理员可以添加用户');
                return;
              }
              
              // 添加用户时验证密码长度
              if (!this.currentUser.password || this.currentUser.password.length < 10) {
                this.$message.error('密码长度至少需要10位');
                return
              }
              
              await createUser({
                username: this.currentUser.username,
                email: this.currentUser.email,
                password: this.currentUser.password,
                role: this.currentUser.role  // 管理员可以指定角色
              })
              this.$message.success('用户添加成功')
            }
            this.userDialogVisible = false
            await this.loadUsers() // 重新加载用户列表
          } catch (error) {
            console.error('保存用户失败:', error)
            // 根据错误类型显示不同提示
            let errorMessage = '保存用户失败'
            if (error.response && error.response.data && error.response.data.detail) {
              errorMessage = error.response.data.detail
            } else if (error.message) {
              errorMessage = error.message
            }
            
            // 特殊处理422错误
            if (error.response && error.response.status === 422) {
              errorMessage = '提交的数据格式不正确，请检查输入信息'
            }
            
            this.$message.error(errorMessage)
          }
        }
      })
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
    },
    handleCurrentChange(val) {
      this.currentPage = val
    }
  }
}
</script>

<style scoped>
.users-container {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>