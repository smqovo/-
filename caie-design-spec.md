# CAIE杯·全国大学生AI技能挑战赛 — 视觉设计规范 V1.0

> 交付对象：前端开发团队  
> 输出日期：2026-04-01  
> 设计顾问：UI Design Consultant

---

## 1. 色彩方案

### 1.1 核心色板

| 角色 | 色名 | HEX | 用途 |
|------|------|-----|------|
| **主色** | 深空蓝 | `#0A1628` | 页面主背景、Nav背景 |
| **主色-浅** | 星海蓝 | `#111D35` | 卡片背景、次级区域 |
| **辅助色** | 电光蓝 | `#2D7AFF` | 链接、按钮填充、选中态 |
| **辅助色-亮** | 天际蓝 | `#5B9AFF` | Hover态、次级按钮边框 |
| **强调色** | 赛博青 | `#00F0FF` | 倒计时数字、Badge、高亮标签、关键数据 |
| **强调色-辅** | 脉冲紫 | `#8B5CF6` | 渐变终点色、装饰性元素 |
| **成功色** | 激活绿 | `#10B981` | 成功状态、已完成步骤 |
| **警告色** | 信号橙 | `#F59E0B` | 截止提醒、警告状态 |
| **错误色** | 警报红 | `#EF4444` | 错误状态、必填提示 |
| **文字-主** | 纯白 | `#F8FAFC` | 标题、主文字 |
| **文字-次** | 银灰 | `#94A3B8` | 描述文字、辅助信息 |
| **文字-弱** | 暗灰 | `#475569` | 禁用态、placeholder |
| **分割线** | 边界灰 | `#1E293B` | 卡片边框、分割线 |

### 1.2 主题选择：深色主题（Dark Theme）

**理由：**
- 科技竞赛天然适合深色调，传达"前沿""专业""沉浸"的感觉
- 深色背景能让数据可视化、动效、渐变等视觉元素更加突出
- 面向18-25岁大学生群体，深色界面更符合目标用户对"酷"的预期
- 长时间浏览赛事规则等文本内容时，深色主题减少视觉疲劳

**注意：** 不提供浅色模式切换，保持统一品牌调性。

### 1.3 渐变方案

```
/* 主渐变 — 用于 Hero 背景叠加、CTA按钮 */
--gradient-primary: linear-gradient(135deg, #2D7AFF 0%, #8B5CF6 50%, #00F0FF 100%);

/* 按钮渐变 — 用于主CTA */
--gradient-button: linear-gradient(90deg, #2D7AFF 0%, #5B9AFF 100%);

/* 光晕渐变 — 用于背景装饰光球 */
--gradient-glow-blue: radial-gradient(circle, rgba(45,122,255,0.25) 0%, transparent 70%);
--gradient-glow-cyan: radial-gradient(circle, rgba(0,240,255,0.15) 0%, transparent 70%);
--gradient-glow-purple: radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%);

/* 卡片边框渐变 — 用于 Hover 态边框 */
--gradient-border: linear-gradient(135deg, #2D7AFF, #00F0FF);

/* 文字渐变 — 用于大标题强调 */
--gradient-text: linear-gradient(90deg, #2D7AFF, #00F0FF);
```

---

## 2. 字体方案

### 2.1 中文字体

| 层级 | 字体 | 备选 | 说明 |
|------|------|------|------|
| **标题** | `HarmonyOS Sans SC Bold` | `PingFang SC Semibold` → `Noto Sans SC Bold` | 笔画现代、几何感强，符合科技调性 |
| **正文** | `HarmonyOS Sans SC Regular` | `PingFang SC Regular` → `Noto Sans SC Regular` | 清晰易读，与标题统一家族 |

> **Web字体加载策略：** 首选通过CDN加载 HarmonyOS Sans SC（华为开源免费商用），fallback 到系统字体。

### 2.2 英文/数字字体

| 层级 | 字体 | 说明 |
|------|------|------|
| **品牌/数字** | `JetBrains Mono` | 等宽字体，用于倒计时、统计数据、代码展示 |
| **标题英文** | `Outfit` | 几何无衬线，科技感强，与中文标题字搭配和谐 |
| **正文英文** | `DM Sans` | 可读性优秀，中性现代，正文场景友好 |

> **加载方式：** Google Fonts CDN 加载 `Outfit:wght@600;700;800` + `DM Sans:wght@400;500` + `JetBrains Mono:wght@500;700`

### 2.3 字号层级（基于 rem，root = 16px）

| 层级 | 桌面端 | 移动端 | 字重 | 行高 | 用途 |
|------|--------|--------|------|------|------|
| **Display** | 72px / 4.5rem | 40px / 2.5rem | 800 | 1.1 | Hero 主标题 |
| **H1** | 48px / 3rem | 32px / 2rem | 700 | 1.2 | 板块标题 |
| **H2** | 36px / 2.25rem | 24px / 1.5rem | 700 | 1.3 | 子板块标题 |
| **H3** | 24px / 1.5rem | 20px / 1.25rem | 600 | 1.4 | 卡片标题 |
| **Body** | 16px / 1rem | 16px / 1rem | 400 | 1.75 | 正文 |
| **Body-sm** | 14px / 0.875rem | 14px / 0.875rem | 400 | 1.6 | 辅助说明 |
| **Caption** | 12px / 0.75rem | 12px / 0.75rem | 500 | 1.5 | 标注、徽标 |
| **Data** | 56px / 3.5rem | 36px / 2.25rem | 700 | 1.0 | 倒计时数字、统计数据（使用 JetBrains Mono） |

---

## 3. 布局风格

### 3.1 首屏 Hero 区域

**构成要素（从上到下）：**

```
┌─────────────────────────────────────────────────────────┐
│  [导航栏] 透明背景 → 下滑后毛玻璃 backdrop-blur         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ● 背景：深空蓝底 + 低透明度几何网格动画（粒子连线）      │
│  ● 左上/右下：模糊光球（蓝+紫渐变）缓慢飘动              │
│                                                         │
│  [竞赛LOGO]                                             │
│  "第一届 CAIE杯"           ← Display / 渐变文字          │
│  "全国大学生AI技能挑战赛"   ← H1 / 纯白                  │
│                                                         │
│  "以赛促学 · 以赛促用 · 以赛促新"  ← Body / 银灰          │
│                                                         │
│  [立即报名] [赛事详情]      ← 主CTA渐变按钮 + 幽灵按钮    │
│                                                         │
│  ─── 倒计时模块 ───                                      │
│  | 32天 | 08时 | 45分 | 12秒 |   ← JetBrains Mono      │
│  "距离报名截止"                                          │
│                                                         │
│  ─── 关键数据横条 ───                                    │
│  100+高校 | ¥50万奖金池 | 3大赛道 | 权威认证              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**动效要求：**
- 背景粒子使用 `canvas` 或 CSS animation，帧率锁定 30fps 控制性能
- 标题文字入场：逐行从底部 fade-in + slide-up，间隔 200ms
- CTA 按钮悬停：渐变流动 + 轻微放大（scale 1.03）
- 倒计时数字翻转动效（flip 或 scroll-counter 风格）

### 3.2 整体布局风格

**采用：全屏分块滚动（Section-based Scroll）+ 卡片系统**

```
Section 1: Hero（全屏100vh）
Section 2: 赛事亮点（三栏图标卡片）
Section 3: 赛道介绍（Tab切换 + 横向卡片滚动）
Section 4: 时间轴（竖向时间轴，左右交替）
Section 5: 奖项设置（数据卡片 + 渐变高亮）
Section 6: 评委/导师（头像网格 + Hover 浮层）
Section 7: 常见问题（手风琴展开）
Section 8: 合作伙伴（Logo 无限滚动）
Footer: 联系方式 + 备案信息
```

**全局布局规范：**
- 最大内容宽度：`1280px`，两侧 padding `24px`
- Section 间距：`120px`（移动端 `80px`）
- 卡片圆角：`16px`
- 卡片背景：`#111D35` + 1px 边框 `#1E293B`
- 卡片 Hover：边框变为渐变色 + 轻微上浮（translateY -4px）+ 蓝色光晕阴影

### 3.3 关键视觉元素

**背景：**
- 主背景色 `#0A1628`，叠加低透明度的几何网格线（类似电路板/神经网络）
- 每个 Section 交界处放置大型模糊渐变光球，打破单调感
- 可选：某些 Section 背景使用 `noise` 纹理增加质感（opacity 3-5%）

**图标：**
- 线性图标风格，`stroke-width: 1.5px`，颜色使用电光蓝 `#2D7AFF`
- 图标尺寸：`48px`（卡片内）/ `24px`（导航/辅助）
- 推荐图标库：Phosphor Icons 或 Lucide Icons

**装饰元素：**
- 渐变光球（Glow Orbs）：2-3 个大型模糊圆形，fixed 定位，随滚动缓慢位移
- 网格点阵：低透明度的等距点阵图案作为 Section 背景
- 渐变线条：`1px` 宽的渐变分割线（从蓝到透明）
- 数据可视化装饰：抽象的折线图/散点图作为背景装饰

---

## 4. 参考网站

| 网站 | URL | 参考要点 |
|------|-----|----------|
| **Vercel** | https://vercel.com | 深色主题执行标杆：渐变光效、卡片系统、字体层级、动效节奏 |
| **Linear** | https://linear.app | 极致科技感深色UI：光影质感、毛玻璃效果、克制的配色 |
| **Microsoft Imagine Cup** | https://imaginecup.microsoft.com | 学生竞赛官网结构参考：Hero倒计时、时间轴、赛事流程可视化 |
| **GitHub Universe** | https://githubuniverse.com | 科技大会官网：全屏视觉冲击、渐变文字、粒子背景、倒计时设计 |
| **Stripe Sessions** | https://stripe.com/sessions | 活动官网设计：信息密度控制、Section节奏、CTA层次 |

---

## 5. CSS 变量定义

```css
:root {
  /* ========== 色彩系统 ========== */
  
  /* 背景 */
  --bg-primary: #0A1628;
  --bg-secondary: #111D35;
  --bg-tertiary: #162040;
  --bg-elevated: #1A2744;
  
  /* 品牌色 */
  --color-blue: #2D7AFF;
  --color-blue-light: #5B9AFF;
  --color-blue-dark: #1A5FD9;
  --color-cyan: #00F0FF;
  --color-cyan-muted: rgba(0, 240, 255, 0.15);
  --color-purple: #8B5CF6;
  --color-purple-muted: rgba(139, 92, 246, 0.15);
  
  /* 功能色 */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  
  /* 文字 */
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-tertiary: #64748B;
  --text-disabled: #475569;
  
  /* 边框/分割 */
  --border-default: #1E293B;
  --border-hover: #2D7AFF;
  --border-subtle: rgba(255, 255, 255, 0.06);
  
  /* ========== 渐变 ========== */
  --gradient-primary: linear-gradient(135deg, #2D7AFF 0%, #8B5CF6 50%, #00F0FF 100%);
  --gradient-button: linear-gradient(90deg, #2D7AFF 0%, #5B9AFF 100%);
  --gradient-button-hover: linear-gradient(90deg, #5B9AFF 0%, #2D7AFF 100%);
  --gradient-text: linear-gradient(90deg, #2D7AFF, #00F0FF);
  --gradient-glow-blue: radial-gradient(circle, rgba(45,122,255,0.25) 0%, transparent 70%);
  --gradient-glow-cyan: radial-gradient(circle, rgba(0,240,255,0.15) 0%, transparent 70%);
  --gradient-glow-purple: radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%);
  --gradient-border: linear-gradient(135deg, #2D7AFF, #00F0FF);
  --gradient-card-hover: linear-gradient(135deg, rgba(45,122,255,0.1), rgba(0,240,255,0.05));
  
  /* ========== 字体 ========== */
  --font-display: 'Outfit', 'HarmonyOS Sans SC', 'PingFang SC', 'Noto Sans SC', sans-serif;
  --font-body: 'DM Sans', 'HarmonyOS Sans SC', 'PingFang SC', 'Noto Sans SC', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  
  /* ========== 字号 ========== */
  --text-display: 4.5rem;    /* 72px */
  --text-h1: 3rem;           /* 48px */
  --text-h2: 2.25rem;        /* 36px */
  --text-h3: 1.5rem;         /* 24px */
  --text-body: 1rem;         /* 16px */
  --text-body-sm: 0.875rem;  /* 14px */
  --text-caption: 0.75rem;   /* 12px */
  --text-data: 3.5rem;       /* 56px - 倒计时/统计数据 */
  
  /* ========== 间距 ========== */
  --space-xs: 0.25rem;   /* 4px */
  --space-sm: 0.5rem;    /* 8px */
  --space-md: 1rem;      /* 16px */
  --space-lg: 1.5rem;    /* 24px */
  --space-xl: 2rem;      /* 32px */
  --space-2xl: 3rem;     /* 48px */
  --space-3xl: 4rem;     /* 64px */
  --space-section: 7.5rem; /* 120px - Section间距 */
  
  /* ========== 圆角 ========== */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;
  
  /* ========== 阴影 ========== */
  --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.25);
  --shadow-card-hover: 0 8px 40px rgba(45, 122, 255, 0.15);
  --shadow-glow-blue: 0 0 40px rgba(45, 122, 255, 0.3);
  --shadow-glow-cyan: 0 0 40px rgba(0, 240, 255, 0.2);
  --shadow-button: 0 4px 16px rgba(45, 122, 255, 0.3);
  
  /* ========== 动效 ========== */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --duration-enter: 600ms;
  
  /* ========== 布局 ========== */
  --max-width: 1280px;
  --nav-height: 72px;
  --content-padding: 24px;
  
  /* ========== 毛玻璃 ========== */
  --glass-bg: rgba(10, 22, 40, 0.8);
  --glass-blur: blur(20px);
  --glass-border: 1px solid rgba(255, 255, 255, 0.06);
  
  /* ========== Z-Index 层级 ========== */
  --z-background: -1;
  --z-default: 0;
  --z-card: 10;
  --z-sticky: 100;
  --z-nav: 200;
  --z-modal: 300;
  --z-toast: 400;
}

/* ========== 移动端覆盖 ========== */
@media (max-width: 768px) {
  :root {
    --text-display: 2.5rem;
    --text-h1: 2rem;
    --text-h2: 1.5rem;
    --text-h3: 1.25rem;
    --text-data: 2.25rem;
    --space-section: 5rem;
    --nav-height: 60px;
    --content-padding: 16px;
  }
}

/* ========== 常用工具类 ========== */

/* 渐变文字 */
.text-gradient {
  background: var(--gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 毛玻璃卡片 */
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--glass-border);
  border-radius: var(--radius-lg);
}

/* 渐变边框卡片 */
.gradient-border-card {
  position: relative;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 1px;
}
.gradient-border-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: var(--radius-lg);
  padding: 1px;
  background: var(--gradient-border);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity var(--duration-normal) var(--ease-in-out);
}
.gradient-border-card:hover::before {
  opacity: 1;
}

/* 光晕按钮 */
.btn-primary {
  background: var(--gradient-button);
  color: var(--text-primary);
  border: none;
  border-radius: var(--radius-full);
  padding: 14px 32px;
  font-family: var(--font-body);
  font-size: var(--text-body);
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-button);
  transition: all var(--duration-normal) var(--ease-out-expo);
}
.btn-primary:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 6px 24px rgba(45, 122, 255, 0.4);
}

/* 幽灵按钮 */
.btn-ghost {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  padding: 14px 32px;
  font-family: var(--font-body);
  font-size: var(--text-body);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-in-out);
}
.btn-ghost:hover {
  border-color: var(--color-blue);
  background: rgba(45, 122, 255, 0.08);
}
```

---

## 6. 补充说明

### 组件规范速查

| 组件 | 圆角 | 背景 | 边框 | 悬停效果 |
|------|------|------|------|----------|
| 导航栏 | 0 | 毛玻璃 | 底部1px | — |
| 卡片 | 16px | `--bg-secondary` | 1px `--border-default` | 渐变边框 + 上浮4px + 蓝色阴影 |
| 按钮-主 | 9999px | 渐变 | 无 | 上浮2px + 放大1.03 |
| 按钮-次 | 9999px | 透明 | 1px白 | 边框变蓝 + 蓝色底色8% |
| 输入框 | 12px | `--bg-tertiary` | 1px `--border-default` | 边框变蓝 |
| Badge | 9999px | `--color-cyan-muted` | 无 | — |
| 时间轴节点 | 50% | 渐变 | 无 | 放大 + 光晕 |

### Google Fonts 引入代码

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@500;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
```

### 中文字体 CDN 引入

```html
<!-- HarmonyOS Sans SC（华为开源，免费商用） -->
<link href="https://s1.hdslb.com/bfs/static/jinkela/long/font/regular.css" rel="stylesheet">
```

> **备注：** 如 HarmonyOS Sans 的 CDN 不稳定，可降级使用系统字体 PingFang SC / Noto Sans SC，视觉差异在可接受范围内。

---

*此规范文件可直接交付前端开发团队使用。CSS 变量部分可直接复制到项目全局样式文件中。*
