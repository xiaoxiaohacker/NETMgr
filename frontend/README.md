# NetMgr 前端项目

## 项目介绍
NetMgr前端项目是基于Vue 3和Vite构建的网络设备管理系统用户界面。该项目提供直观的Web界面，用于管理网络设备、监控设备状态、执行配置备份等操作。

## 主要功能
- 设备管理界面（添加、编辑、删除设备）
- 设备状态监控（在线/离线状态）
- 接口状态查看
- 配置备份与恢复
- 网络拓扑可视化
- 系统仪表板（统计信息展示）
- 用户认证与管理
- 系统日志查看

## 技术栈
- **前端框架**: Vue 3
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **路由管理**: Vue Router
- **样式**: SCSS

## 项目结构
```
src/
├── api/              # API接口定义
│   ├── auth.js       # 认证相关API
│   ├── device.js     # 设备管理API
│   ├── dashboard.js  # 仪表板API
│   └── ...           # 其他API模块
├── assets/           # 静态资源
├── components/       # 公共组件
│   ├── DeviceCard.vue    # 设备卡片组件
│   ├── StatusIndicator.vue # 状态指示器组件
│   └── ...               # 其他组件
├── views/            # 页面视图
│   ├── DeviceList.vue    # 设备列表页
│   ├── DeviceDetail.vue  # 设备详情页
│   ├── Dashboard.vue     # 仪表板页
│   └── ...               # 其他页面
├── router/           # 路由配置
├── utils/            # 工具函数
│   ├── auth.js       # 认证相关工具
│   └── request.js    # 请求工具
└── main.ts           # 应用入口
```

## 环境要求
- Node.js 16+
- npm 或 yarn
- 后端服务 (运行在 http://localhost:8000)

## 项目设置

```bash
npm install
```

## 开发环境

### 编译和热重载
```bash
npm run dev
```

开发服务器将运行在 `http://localhost:5173`，并自动打开浏览器。

### 开发服务器代理配置
开发服务器已配置代理，将 `/api` 请求转发到后端服务 (http://127.0.0.1:8000)，解决开发环境下的跨域问题。

## 生产构建

### 编译和压缩
```bash
npm run build
```

构建产物将生成在 `dist/` 目录，可用于生产环境部署。

### 预览生产构建
```bash
npm run preview
```

在本地预览生产构建的项目。

## 代码规范

### Vue组件规范
- 使用单文件组件（SFC）格式
- 遵循Vue 3 Composition API
- 使用TypeScript进行类型检查（如适用）
- 组件名称使用PascalCase格式

### 样式规范
- 使用SCSS进行样式编写
- 遵循BEM命名规范
- 组件样式使用scoped属性或CSS Modules

### JavaScript规范
- 使用ES6+语法
- 遵循Airbnb JavaScript风格指南
- 使用ESLint进行代码检查
- 使用Prettier进行代码格式化

## API集成

### 认证
- 所有API请求会自动添加JWT令牌到Authorization头
- 认证过期时自动重定向到登录页面

### 错误处理
- 统一的错误处理机制
- 用户友好的错误提示
- 网络错误重试机制

## 环境配置

### 开发环境配置
创建 `.env.development` 文件：
```
VITE_API_BASE_URL=http://localhost:8000
```

### 生产环境配置
创建 `.env.production` 文件：
```
VITE_API_BASE_URL=https://your-backend-domain.com
```

## 前端代理配置
在 `vite.config.ts` 中配置了开发服务器代理，将API请求转发到后端服务：
```typescript
export default defineConfig({
  // ...
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
```

## 项目部署

### 静态文件部署
1. 运行 `npm run build` 生成生产构建
2. 将 `dist/` 目录内容部署到Web服务器
3. 配置Web服务器将未匹配的路由重定向到 `index.html`

### Nginx配置示例
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 将API请求代理到后端服务
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 调试和开发工具

### 推荐IDE
- VS Code + Volar插件

### 浏览器扩展
- Vue DevTools: 用于调试Vue组件状态和事件

### 开发工具
- Vue DevTools: Chrome/Firefox扩展，用于调试Vue应用
- Element Plus: UI组件库，提供丰富的组件

## 贡献指南

### 开发流程
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

### 代码提交规范
- 使用有意义的提交信息
- 遵循"动词+描述"的格式
- 如有重要变更，更新相关文档

## 常见问题

### 1. 开发环境API请求失败
- 检查后端服务是否运行在 `http://127.0.0.1:8000`
- 确认代理配置正确

### 2. 样式不生效
- 检查是否使用了CSS作用域
- 确认SCSS语法正确

### 3. 组件通信问题
- 使用props进行父子组件通信
- 使用emit进行子父组件通信
- 使用Pinia进行跨组件状态管理

## 许可证

[在此处添加项目许可证信息]