# Frontend Source - 前端源代码目录

## 概述

此目录用于存放前端源代码文件，当前项目使用单文件应用（`index.html`），此目录为预留结构，用于未来组件化改造。

## 目录结构

```
src/
├── assets/          # 静态资源文件
│   ├── images/      # 图片资源
│   ├── icons/       # 图标资源
│   └── fonts/       # 字体文件
│
├── components/      # 可复用组件
│   ├── UploadZone/  # 上传组件
│   ├── StyleSelector/ # 风格选择器
│   ├── ProgressBar/  # 进度条
│   └── ProductCard/  # 商品卡片
│
├── hooks/           # 自定义 Hooks
│   ├── useApi.js    # API 调用 Hook
│   ├── useUpload.js # 上传 Hook
│   └── usePolling.js # 轮询 Hook
│
├── pages/           # 页面组件
│   ├── UploadPage/  # 上传页面
│   ├── GeneratePage/ # 生成页面
│   └── ResultPage/  # 结果页面
│
├── styles/          # 样式文件
│   ├── global.css   # 全局样式
│   ├── variables.css # CSS 变量
│   └── animations.css # 动画样式
│
└── utils/           # 工具函数
    ├── api.js       # API 封装
    ├── validation.js # 验证函数
    └── helpers.js   # 辅助函数
```

## 使用说明

### 当前状态

当前项目使用单文件应用（`index.html`），所有代码都在一个文件中。此目录结构是为未来组件化改造预留的。

### 组件化改造建议

如果要将项目改造为组件化应用，可以：

1. **使用 Vue.js**
   - 将 `index.html` 中的 Alpine.js 代码迁移到 Vue 组件
   - 使用 Vue Router 管理路由
   - 使用 Pinia/Vuex 管理状态

2. **使用 React**
   - 将 HTML 结构转换为 React 组件
   - 使用 React Router 管理路由
   - 使用 Redux/Zustand 管理状态

3. **使用 Next.js**
   - 支持 SSR 和静态生成
   - 更好的 SEO 支持
   - 内置路由和 API 路由

### 文件组织建议

#### components/ 目录

每个组件一个文件夹，包含：
- `Component.vue/jsx` - 组件文件
- `Component.css` - 组件样式（可选）
- `Component.test.js` - 测试文件（可选）

#### utils/ 目录

工具函数按功能分类：
- `api.js` - API 调用封装
- `validation.js` - 表单验证
- `helpers.js` - 通用辅助函数
- `constants.js` - 常量定义

#### hooks/ 目录

自定义 Hooks（React）或 Composables（Vue）：
- `useApi.js` - API 调用 Hook
- `useUpload.js` - 文件上传 Hook
- `usePolling.js` - 轮询任务状态 Hook

## 开发规范

### 命名规范

- **组件**: PascalCase（如 `UploadZone.vue`）
- **工具函数**: camelCase（如 `formatPrice.js`）
- **常量**: UPPER_SNAKE_CASE（如 `API_BASE_URL`）

### 代码组织

- 每个文件只做一件事
- 保持函数简洁（不超过 50 行）
- 使用注释说明复杂逻辑
- 提取可复用的逻辑到工具函数

## 注意事项

1. **当前未使用**: 此目录结构当前未使用，所有代码在 `index.html` 中
2. **未来扩展**: 如需组件化改造，可以参考此结构
3. **保持简洁**: 不要过度设计，根据实际需求添加文件



