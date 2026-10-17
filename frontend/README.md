# Frontend - 换装相机 前端

## 概述

换装相机 前端是一个移动端优先的单页应用（SPA），使用原生技术栈构建，提供流畅的零决策 AI 家装改造体验。

**核心特色**:
- 📱 移动端优先设计
- 🚀 零依赖构建（无需 npm/webpack）
- ⚡ 轻量级（< 100KB）
- 🎨 现代极简美学
- 🌐 多语言支持（中文/英文）

## 技术栈

- **HTML5** - 页面结构（单文件应用）
- **Tailwind CSS v3** - 样式框架（CDN）
- **Alpine.js v3** - 轻量级交互框架（15KB，CDN）
- **原生 JavaScript** - 业务逻辑（无需编译）

## 项目结构

```
frontend/
├── v2.zh.html           # 🔥 主应用（中文版，生产环境）
├── v2.html              # 英文版
├── index.html           # v1版本（已废弃）
├── src/                 # v1 Vue代码（已废弃）
└── public/              # 静态资源目录
```

**重要**: 当前生产环境使用 `v2.zh.html`，这是一个完全自包含的单文件应用。

## 核心功能（v2）

### 1. 图片上传
- ✅ 支持点击上传和拖拽上传
- ✅ 实时图片预览
- ✅ 文件类型验证（JPG/PNG/WebP）
- ✅ 文件大小限制（10MB）
- ✅ 优雅的上传区域设计

### 2. AI 分析动画（零决策）
**关键特性**: 用户无需选择任何参数，AI 自动判断风格和预算

- ✅ 模拟 AI 分析步骤动画
  - 上传成功 (0s)
  - 识别房间布局 (2.25s)
  - 分析光线条件 (4.5s)
  - 理解现有风格 (6.75s)
  - 构思设计方案 (9.75s)
  - 绘制效果图 (13.5s)
- ✅ 实际生成时间：15-20秒
- ✅ 动画与真实进度无关（固定延迟）
- ✅ 出图后立即停止动画

### 3. 图片对比展示
- ✅ 左右滑块对比（原图 vs 效果图）
- ✅ 拖动滑块查看改造差异
- ✅ Progressive JPEG 加载（模糊到清晰）

### 4. 购物清单
- ✅ AI 识别图中物品
- ✅ 匹配拼多多商品
- ✅ 显示商品图片、价格、名称
- ✅ 一键跳转购买链接
- ✅ 显示预估总价

## 页面流程（v2 零决策）

```
Step 1: 上传照片
  - 点击或拖拽上传
  - 实时预览
  ↓
Step 2: AI 分析（自动）
  - 显示 AI 分析步骤动画
  - 后台调用 /api/v1/generate-v2
  - 无需用户选择任何参数
  ↓
Step 3: 效果图生成
  - 15-20秒生成完成
  - Progressive JPEG 加载
  - 自动停止步骤动画
  ↓
Step 4: 对比展示
  - 滑块对比原图和效果图
  - 点击"查看购物清单"
  ↓
Step 5: 购物清单
  - AI 识别图中物品
  - 匹配拼多多商品
  - 显示价格和购买链接
```

## API 集成

### 配置

```javascript
const API_BASE = 'http://localhost:8000/api/v1';
const BACKEND_URL = 'http://localhost:8000';
```

### 主要 API 调用（v2）

1. **上传图片**
   ```javascript
   POST /api/v1/upload
   Content-Type: multipart/form-data

   // 请求
   FormData: { file: File }

   // 响应
   {
     "image_id": "abc123",
     "message": "图片上传成功"
   }
   ```

2. **生成效果图（v2 - 零决策）**
   ```javascript
   POST /api/v1/generate-v2
   Content-Type: application/json

   // 请求
   {
     "image_id": "abc123",
     "lang": "zh"  // 或 "en"
   }

   // 响应
   {
     "result": {
       "generated_image_url": "/uploads/generated_xxx.jpg",
       "room_type": "living_room",
       "applied_style": "nordic",
       "space_analysis": {
         "lighting": "充足的自然光",
         "existing_style": "简约现代"
       }
     }
   }
   ```

3. **识别物品**
   ```javascript
   POST /api/v1/identify-items
   Content-Type: application/json

   // 请求
   {
     "image_url": "/uploads/generated_xxx.jpg"
   }

   // 响应
   {
     "items": ["地毯", "抱枕", "落地灯", "绿植"],
     "message": "物品识别成功"
   }
   ```

4. **搜索商品**
   ```javascript
   POST /api/v1/products/search
   Content-Type: application/json

   // 请求
   {
     "keywords": "北欧风地毯"
   }

   // 响应
   {
     "products": [{
       "title": "北欧简约地毯",
       "price": 299.00,
       "image_url": "...",
       "product_url": "拼多多链接"
     }]
   }
   ```

## 状态管理（Alpine.js）

v2 版本使用 Alpine.js 的 `x-data` 进行轻量级状态管理：

```javascript
{
  // 页面状态
  step: 'upload',           // 'upload' | 'processing' | 'results' | 'error'
  dragover: false,          // 拖拽状态

  // 图片相关
  previewUrl: null,         // 预览图片 URL
  uploadedImageUrl: null,   // 上传后的完整 URL
  generatedImageUrl: null,  // 生成图片 URL
  imageId: null,            // 图片 ID

  // AI 分析步骤动画
  analysisSteps: [
    { text: '上传成功', delay: 0, visible: false, completed: false },
    { text: '识别房间布局', delay: 2250, visible: false, completed: false },
    // ... 更多步骤
  ],
  analysisTimer: null,      // 步骤定时器

  // 结果数据
  shoppingList: [],         // 购物清单
  totalPrice: 0,            // 总价
  sliderPos: 50,            // 滑块位置（%）
  loadingProducts: false,   // 商品加载状态

  // 风格选择（高级功能）
  showStylePicker: false,
  selectedStyle: null,
  regenerating: false,

  // 错误处理
  errorMessage: '',

  // 用户认证
  user: null,
  accessToken: null,

  // 历史记录
  historyCount: 0,
  showHistoryPanel: false
}
```

### 关键方法

```javascript
// 文件上传
handleFileSelect(event)
handleDrop(event)

// 图片处理
async uploadImage()

// 生成流程
async startGeneration()
startAnalysisSteps()      // 启动步骤动画
stopAnalysisSteps()       // 停止步骤动画

// 商品相关
async loadProducts()
async identifyAndMatchProducts()

// 工具方法
async loadHistory()
async saveToHistory()
```

## 样式设计

### 颜色主题

- `deep-night`: #1a1a2e - 深色背景
- `midnight`: #16213e - 午夜蓝
- `twilight`: #0f3460 - 暮色蓝
- `sunset`: #e94560 - 日落红（主色）
- `golden`: #f4a261 - 金色（强调色）
- `cream`: #faf3e0 - 奶油色（文字色）
- `sage`: #a7c4a0 - 鼠尾草绿

### 字体

- **主字体**: Noto Sans SC（中文）
- **标题字体**: Playfair Display（英文）

### 动画效果

- 渐入动画（fade-in）
- 进度条闪烁动画（shimmer）
- 加载点动画（bounce）
- 卡片悬停效果

## 响应式设计

- 移动端优先设计
- 最大宽度限制（max-w-lg）
- 触摸友好的按钮尺寸
- 适配不同屏幕尺寸

## 用户体验优化

1. **加载状态**: 显示加载动画和提示信息
2. **错误处理**: 友好的错误提示
3. **图片预览**: 即时预览上传的图片
4. **进度反馈**: 实时显示任务进度
5. **操作反馈**: 按钮点击动画

## 开发指南

### 本地开发

```bash
cd frontend

# 使用 Python 内置服务器
python -m http.server 3000

# 或使用 Node.js serve
npx serve -p 3000
```

访问: `http://localhost:3000`

### 修改 API 地址

编辑 `index.html` 中的配置：

```javascript
const API_BASE = 'http://your-backend-url/api/v1';
const BACKEND_URL = 'http://your-backend-url';
```

### 添加新功能

1. 在 `index.html` 中添加新的 HTML 结构
2. 在 Alpine.js 数据中添加新的状态
3. 添加对应的方法处理逻辑

## 扩展开发

### 组件化改造

可以将单文件应用拆分为组件：

```
src/
├── components/
│   ├── UploadZone.vue
│   ├── StyleSelector.vue
│   ├── ProgressBar.vue
│   └── ProductCard.vue
├── pages/
│   ├── UploadPage.vue
│   ├── GeneratePage.vue
│   └── ResultPage.vue
└── utils/
    └── api.js
```

### 使用构建工具

可以迁移到现代前端框架：

- **Next.js** - 支持 SSR
- **Vite + Vue/React** - 快速开发
- **小程序** - 微信/支付宝小程序版本

## 注意事项

1. **CORS**: 确保后端配置了正确的 CORS 设置
2. **图片路径**: 注意处理相对路径和绝对路径
3. **错误处理**: 所有 API 调用都应该有错误处理
4. **性能优化**: 图片压缩、懒加载等
5. **兼容性**: 测试不同浏览器和设备的兼容性

## 技术亮点

### 1. 零决策体验
用户只需上传照片，AI 自动判断：
- 房间类型（客厅/卧室/厨房等）
- 装修风格（北欧/日式/工业风等）
- 预算档位（根据空间分析智能推荐）

### 2. 步骤动画设计
```javascript
// 固定延迟，与真实进度无关
const delays = [0, 2250, 4500, 6750, 9750, 13500]; // 毫秒

// 出图后立即停止动画
if (generatedImageUrl) {
  stopAnalysisSteps();
  step = 'results';
}
```

**设计理念**:
- 让等待过程有趣（展示 AI 思考过程）
- 不撒谎（不显示虚假的百分比进度）
- 实际生成时间：15-20秒

### 3. Progressive JPEG 加载
后端自动转换为渐进式 JPEG：
- 用户先看到模糊图
- 逐渐变清晰
- 提升感知加载速度

### 4. 图片对比滑块
```javascript
// 滑块拖动逻辑
<div x-on:mousedown="isDragging = true">
  <div :style="`clip-path: inset(0 ${100 - sliderPos}% 0 0)`">
    <!-- 生成图 -->
  </div>
</div>
```

### 5. 单文件应用
- 无需构建工具
- CDN 加载依赖
- 部署简单（直接上传 HTML）
- 体积小（< 100KB）

## 开发技巧

### 调试 API 请求
```javascript
// 在浏览器控制台
console.log('Image ID:', this.imageId);
console.log('Generated URL:', this.generatedImageUrl);
```

### 修改步骤延迟
在 `analysisSteps` 数组中修改 `delay` 值：
```javascript
{ text: '识别房间布局', delay: 2250 },  // 改为 3000 会延长 0.75秒
```

### 测试错误处理
```javascript
// 模拟 API 错误
throw new Error('测试错误');
```

## 常见问题

### Q: 为什么步骤动画是固定延迟？
A: 真实的 AI 生成进度难以预测（15-30秒不等），使用固定延迟避免进度条倒退或卡顿。

### Q: 如何添加新的分析步骤？
A: 在 `analysisSteps` 数组中添加新对象，注意 `delay` 值要递增。

### Q: 图片对比滑块不流畅怎么办？
A: 检查图片大小，确保使用 Progressive JPEG（后端自动转换）。

## 部署

### 生产环境部署

1. **上传文件到服务器**
```bash
scp v2.zh.html root@SERVER:/var/www/homeglow/frontend/
```

2. **Nginx 配置**
```nginx
location / {
    root /var/www/homeglow/frontend;
    try_files $uri $uri/ /v2.zh.html;
    expires 1h;
}
```

3. **清除缓存**
```bash
# 修改文件名或添加版本号
# v2.zh.html?v=20260208
```

### 小程序迁移

推荐使用 **uni-app** 迁移：
- 80% 代码可复用
- 支持多端发布
- 详见 [小程序开发计划](../../docs/miniprogram-plan.md)

## 性能优化

### 已实现
- ✅ CDN 加载依赖（Tailwind, Alpine.js）
- ✅ Progressive JPEG 图片
- ✅ 图片懒加载（购物清单）
- ✅ 防抖处理（滑块拖动）

### 待优化
- [ ] 图片预加载（提前加载生成图）
- [ ] Service Worker（离线支持）
- [ ] 虚拟滚动（长列表优化）
- [ ] 骨架屏（加载占位）

## 相关文档

- 📖 [后端 README](../backend/README.md) - 后端 API 文档
- 🏗️ [架构文档](../docs/ARCHITECTURE.md) - 系统架构
- 🤖 [AI 上下文](../docs/AI_CONTEXT.md) - 设计决策和上下文
- 📱 [小程序计划](../docs/miniprogram-plan.md) - 小程序开发

## 更新日志

### v2.0 (2026-02-08)
- ✨ 零决策体验（无需选择参数）
- ✨ AI 分析步骤动画
- ✨ Progressive JPEG 加载优化
- ✨ 图片对比滑块
- 🐛 修复图片加载卡顿
- 🐛 修复步骤动画时间问题

### v1.0 (2025-12)
- 🎉 初始版本
- ✨ 参数选择流程
- ✨ 任务进度轮询



