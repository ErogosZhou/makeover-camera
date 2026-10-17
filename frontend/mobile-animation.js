/**
 * 移动端炫酷动画效果
 * 在v2.zh.mobile.html中使用
 */

// 全屏动画控制器
const MobileAnimationController = {
    // 元素引用
    elements: {
        takeover: null,
        bg: null,
        glass: null,
        lyrics: null,
        lyricsContent: null
    },

    // 状态
    state: {
        isActive: false,
        isLyricsShowing: false,
        currentImageDataUrl: null
    },

    // 初始化
    init() {
        console.log('🎬 MobileAnimationController.init() 开始初始化');
        this.elements = {
            takeover: document.getElementById('fullscreenTakeover'),
            bg: document.getElementById('fullscreenBg'),
            glass: document.getElementById('glassLayer'),
            lyrics: document.getElementById('lyricsContainer'),
            lyricsContent: document.getElementById('lyricsContent')
        };
        console.log('🎬 元素查找结果:', {
            takeover: !!this.elements.takeover,
            bg: !!this.elements.bg,
            glass: !!this.elements.glass,
            lyrics: !!this.elements.lyrics,
            lyricsContent: !!this.elements.lyricsContent
        });
    },

    // 开始动画序列
    async start(imageDataUrl) {
        console.log('🎬 MobileAnimationController.start() 被调用');
        console.log('   📸 图片URL长度:', imageDataUrl?.length);

        if (!this.elements.takeover) {
            console.error('❌ 全屏动画元素未找到');
            return;
        }

        console.log('✅ 全屏动画元素已找到，开始动画序列');
        this.state.currentImageDataUrl = imageDataUrl;
        this.state.isActive = true;

        // 1. 设置背景图并显示容器
        this.elements.bg.style.backgroundImage = `url(${imageDataUrl})`;
        this.elements.takeover.classList.add('active');

        // 2. 等待100ms后开始扩展动画
        await this.sleep(100);
        this.elements.takeover.classList.add('expanded');

        // 3. 1.4秒后开始毛玻璃效果
        await this.sleep(1400);
        this.elements.takeover.classList.add('glass-active');
    },

    // 显示提示词歌词
    async showLyrics(promptText) {
        console.log('🎵 MobileAnimationController.showLyrics() 被调用');
        console.log('   📝 提示词长度:', promptText?.length);
        console.log('   ⚠️ isLyricsShowing状态:', this.state.isLyricsShowing);

        if (this.state.isLyricsShowing) {
            console.log('   ⚠️ 歌词已经在显示中，跳过');
            return;
        }
        this.state.isLyricsShowing = true;

        // 等待毛玻璃效果完成
        console.log('   ⏳ 等待1.8秒后显示歌词容器');
        await this.sleep(1800);

        console.log('   ✅ 添加visible类到歌词容器');
        // 显示歌词容器
        this.elements.lyrics.classList.add('visible');

        // 等待500ms后开始打字机
        await this.sleep(500);

        // 按标点符号分割文本
        this.typeLyrics(promptText);
    },

    // 打字机效果 - 遇到标点符号换行
    typeLyrics(text) {
        console.log('⌨️ typeLyrics() 开始打字机效果');
        // 清空现有内容
        this.elements.lyricsContent.innerHTML = '';

        // 分割文本：按标点符号和换行符分割
        const segments = text.split(/([，。、；！？\n]+)/).filter(Boolean);
        console.log('   📄 分割为', segments.length, '个片段');

        let currentLine = '';
        let segmentIndex = 0;
        let charIndex = 0;

        const typeNext = () => {
            if (segmentIndex >= segments.length) return;

            const segment = segments[segmentIndex];

            // 如果是标点符号，加入当前行并换行
            if (/[，。、；！？\n]+/.test(segment)) {
                currentLine += segment;
                this.addLyricLine(currentLine);
                currentLine = '';
                segmentIndex++;
                charIndex = 0;
                setTimeout(typeNext, 400); // 标点后停顿
            } else {
                // 逐字添加
                if (charIndex < segment.length) {
                    currentLine += segment[charIndex];
                    charIndex++;
                    setTimeout(typeNext, 50); // 打字速度
                } else {
                    // 当前段落完成
                    segmentIndex++;
                    charIndex = 0;
                    setTimeout(typeNext, 100);
                }
            }
        };

        typeNext();
    },

    // 添加歌词行
    addLyricLine(text) {
        const line = document.createElement('div');
        line.className = 'lyric-line';

        // 重点行高亮（包含风格/MUJI/【】等）
        if (text.includes('【') || text.includes('风') || text.includes('MUJI') || text.includes('重要')) {
            line.classList.add('emphasis');
        }

        line.textContent = text.trim();
        this.elements.lyricsContent.appendChild(line);

        // 自动滚动到最新行
        setTimeout(() => {
            line.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    },

    // 完成动画 - 清晰化并显示结果
    async finish(resultImageUrl) {
        // 1. 歌词消散
        this.elements.lyrics.classList.add('fade-out');

        await this.sleep(1500);

        // 2. 毛玻璃清晰化
        this.elements.glass.classList.add('clearing');

        await this.sleep(2500);

        // 3. 隐藏全屏动画
        this.elements.takeover.classList.remove('active');

        // 4. 重置状态
        await this.sleep(500);
        this.reset();
    },

    // 重置状态
    reset() {
        this.state.isActive = false;
        this.state.isLyricsShowing = false;
        this.state.currentImageDataUrl = null;

        // 移除所有class
        this.elements.takeover.classList.remove('active', 'expanded', 'glass-active');
        this.elements.glass.classList.remove('clearing');
        this.elements.lyrics.classList.remove('visible', 'fade-out');

        // 清空内容
        this.elements.lyricsContent.innerHTML = '';
        this.elements.bg.style.backgroundImage = '';
    },

    // 工具函数 - sleep
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};

// 在页面加载后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('📦 DOMContentLoaded - 准备初始化 MobileAnimationController');
    MobileAnimationController.init();
    console.log('✅ MobileAnimationController 初始化完成');
});

// 导出给全局使用
console.log('📦 mobile-animation.js 加载完成，导出 MobileAnimationController 到 window');
window.MobileAnimationController = MobileAnimationController;
