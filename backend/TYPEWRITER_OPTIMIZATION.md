# 打字机效果优化方案

## 核心思路

用打字机效果展示"生图提示词",填充用户等待时间,让15秒的生图过程变得有趣。

## 时间分配

```
用户上传图片
  ↓
【5秒】 VLLM生成prompt (后端)
  ↓
【20秒】打字机展示prompt (前端) ← 吸引注意力
  ‖  同时并行
  ↓
【15秒】Seedream生图 (后端,并行开始)
  ↓
生成完成,展示结果
```

**关键**: 打字机20秒 > 生图15秒,所以用户看完打字机时,图已经生成好了!

## 前端改动

### 1. 数据结构 (v2.zh.html line 693+)

在`homeGlowV2()`中添加:

```javascript
return {
    // ... 现有字段

    // 新增:打字机效果
    generationPrompt: '',  // VLLM生成的完整prompt
    displayedPrompt: '',   // 打字机当前显示的内容
    isTyping: false,       // 是否正在打字
    typingSpeed: 50,       // 打字速度(ms/字符)
```

### 2. UI组件 (v2.zh.html line 412-471 processing section)

在"AI分析步骤"和"流式物品"之间,插入打字机区域:

```html
<!-- 在line 453 </template> 和 line 457 之间插入 -->

<!-- 打字机:展示生图提示词 -->
<div x-show="displayedPrompt.length > 0"
     class="w-full max-w-md pt-6">
    <div class="bg-white/80 backdrop-blur-sm rounded-xl border border-sage/10 p-5 space-y-3">
        <div class="flex items-center gap-2 text-sage">
            <svg class="w-4 h-4 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 20h9"/>
                <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>
            </svg>
            <span class="text-xs font-medium">AI 创作思路</span>
        </div>
        <p class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap"
           x-text="displayedPrompt"></p>
        <div x-show="isTyping" class="inline-block w-2 h-4 bg-sage animate-pulse"></div>
    </div>
</div>
```

### 3. 打字机逻辑 (v2.zh.html line 682+)

添加打字机方法:

```javascript
// 在homeGlowV2()对象中添加这些方法

// 启动打字机效果
startTypewriter(fullText, speed = 50) {
    this.generationPrompt = fullText;
    this.displayedPrompt = '';
    this.isTyping = true;

    let index = 0;
    const typeNextChar = () => {
        if (index < fullText.length) {
            this.displayedPrompt += fullText[index];
            index++;
            setTimeout(typeNextChar, speed);
        } else {
            this.isTyping = false;
        }
    };

    typeNextChar();
},

// 停止打字机(如果需要快速跳过)
stopTypewriter() {
    this.displayedPrompt = this.generationPrompt;
    this.isTyping = false;
},
```

### 4. 轮询时启动打字机 (v2.zh.html line 1185+)

修改`pollTaskStatus()`方法,在收到prompt时启动打字机:

```javascript
async pollTaskStatus() {
    // ... 现有代码

    const data = await res.json();

    // 新增:收到生图prompt时,启动打字机
    if (data.generation_prompt && !this.displayedPrompt) {
        this.startTypewriter(data.generation_prompt, 50);  // 50ms/字符
    }

    // ... 其余现有代码
}
```

## 后端改动

### 修改task状态返回 (backend/services/task_service.py)

在轮询接口返回时,加入`generation_prompt`字段:

```python
# 在get_task_status()方法中
if task.status in ['generating', 'identifying', 'matching']:
    return {
        "status": task.status,
        "message": ...,
        "generation_prompt": task.generation_prompt,  # 新增这行
        "result": ...
    }
```

确保task对象有`generation_prompt`字段(应该已经在v2的transform中保存了)。

## 计算最优打字速度

目标:让打字机时间 ≥ 生图时间,避免打完字还在等。

```
设打字速度为 x ms/字符
冷色调v3提示词长度: 255字

打字总时间 = 255 * x

希望: 255 * x ≥ 15000ms (生图时间)
解得: x ≥ 58ms

建议: x = 80ms (稍慢一点,更有仪式感)
总打字时间 = 255 * 80 = 20400ms ≈ 20秒
```

**完美!** 用户看20秒打字机,生图只需15秒,无缝衔接!

## CSS优化

添加平滑滚动和淡入动画:

```css
/* 在<style>标签中添加 */
.typewriter-cursor {
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

.prompt-text {
    font-family: 'Noto Sans SC', monospace;
    line-height: 1.8;
    color: #374151;
}
```

## 用户体验提升

1. **打字速度可调**:太快看不清,太慢无聊
   - 建议:80ms/字符 (阅读友好)

2. **跳过按钮**:有些用户不想看
   ```html
   <button @click="stopTypewriter()"
           class="text-xs text-gray-400 hover:text-sage">
       跳过 →
   </button>
   ```

3. **渐变显示**:每段文字淡入
   ```javascript
   // 可以按句子分段,每句淡入
   ```

## 额外好处

1. **教育用户**: 让用户理解AI如何工作
2. **专业感**: 像真的设计师在思考
3. **降低焦虑**: 有东西看,不会觉得卡住了
4. **品牌差异化**: 其他产品只有loading圈

## 实现顺序

1. ✅ 后端:确保task返回`generation_prompt`
2. ✅ 前端:添加数据字段和UI组件
3. ✅ 前端:实现打字机逻辑
4. ✅ 前端:接入轮询,触发打字机
5. ✅ 调优:调整速度,测试体验
