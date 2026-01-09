# NetMgr 前端项目

NetMgr 是一个网络设备管理系统，前端使用 Vue 3、Element Plus 和 Vite 构建。

## 项目结构

```
src/
├── api/           # API接口定义
├── assets/        # 静态资源
├── components/    # 公共组件
├── router/        # 路由配置
├── utils/         # 工具函数
├── views/         # 页面组件
├── App.vue        # 根组件
└── main.ts        # 入口文件
```

## 安装依赖

```bash
npm install
```

## 开发环境启动

```bash
npm run dev
```

## 构建生产版本

```bash
npm run build
```

## 预览生产版本

```bash
npm run preview
```

## 主要功能

- 设备管理
- 网络拓扑
- 实时监控
- 告警管理
- 任务管理
- 日志管理
- 配置备份
- 用户管理
- 系统设置

## 技术栈

- Vue 3
- TypeScript
- Element Plus
- Vite
- Pinia (状态管理)
- Vue Router

## 开发规范

- 使用 Composition API
- 遵循 ESLint 代码规范
- 组件命名采用 PascalCase
- Props 验证使用 TypeScript 接口
