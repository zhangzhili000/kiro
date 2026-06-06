# 企业知识库前端

## 环境要求

- Node.js 18+
- npm 9+

## 安装

```bash
cd frontend
npm install
```

## 运行

```bash
npm run dev
```

访问 http://localhost:5120 查看应用。

## 项目结构

```
frontend/
├── src/
│   ├── api/          # API封装
│   ├── assets/       # 静态资源
│   ├── components/   # 公共组件
│   ├── layouts/      # 布局组件
│   ├── router/       # 路由配置
│   ├── stores/       # 状态管理
│   ├── utils/        # 工具函数
│   └── views/        # 页面组件
├── public/          # 公共资源
└── vite.config.js    # Vite配置
```

## 主要功能

- 用户认证（登录/注册）
- 文档管理（创建/编辑/删除/搜索）
- 分类和标签管理
- 评论和收藏
- 通知中心
- 管理员面板（用户管理、审计日志）
