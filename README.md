# 亲语 · 关爱父母情感交流

> 不在身边，但让父母每天都感受到你的爱。

「亲语」是一款让异地子女与父母保持情感连接的 AI Demo。子女用 60 秒发送今日关怀，父母随时可与 AI 聊天感受陪伴。

---

## 功能一览

### 子女端

| 功能 | 说明 |
|---|---|
| 注册/登录 | 手机号 + 姓名，自动识别已有账号 |
| 生成邀请码 | 6 位数字，发给父母完成家庭绑定 |
| 每日关怀发送 | 6 种情景模板，一键选择 + AI 润色，发送后存入数据库 |
| 危机预警 | 父母聊天触发负面情绪词时，主页显示黄色预警卡片 |

### 父母端

| 功能 | 说明 |
|---|---|
| 注册/登录 | 手机号 + 姓名 |
| 邀请码绑定 | 输入子女的 6 位邀请码，完成家庭绑定 |
| 关怀卡片展示 | 登录后自动显示子女最新关怀，支持 TTS 语音朗读 |
| AI 情感陪伴对话 | 4 种性格角色 + Live2D 数字人 + 语音输入/输出 |

### AI 角色

| 角色 | 性格 | Live2D 模型 | 声音 |
|---|---|---|---|
| 暖心宝贝 | 温柔体贴，最懂您心里想什么 | Haru | 晓晓·女声 |
| 开心果 | 活泼幽默，每天让您笑 | Mao | 晓伊·女声 |
| 靠谱大孩 | 稳重踏实，说话让人放心 | Mark | 云健·男声 |
| 小话痨 | 话多热闹，天天有说不完的事 | Hiyori | 晓萱·女声 |

### 安全与数据

| 机制 | 说明 |
|---|---|
| 危机干预 | 检测「好孤独」「没意思」等负面情绪词，触发预警并存入数据库通知子女 |
| AI 标注 | 聊天界面常驻提示「这是 AI 陪伴，不是真实的子女」 |
| 数据自动清理 | 15 天未登录的账号及其所有数据自动删除（Supabase 定时任务） |

---

## 快速开始

### 1. 安装依赖

```bash
pip3 install edge-tts
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入 API Key：

```
DEEPSEEK_API_KEY=sk-your-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 3. 启动服务

```bash
python3 server.py
```

浏览器打开 `http://localhost:8888`

---

## 完整使用流程

**子女端（两个浏览器窗口模拟）：**
1. 选「我是子女」→ 填手机号和姓名 → 进入主页
2. 看到 6 位邀请码，复制给父母
3. 点「给爸妈发今日关怀」→ 选情景 → 发送

**父母端：**
1. 选「我是父母」→ 填手机号和姓名 → 进入绑定页
2. 输入子女的邀请码 → 绑定成功
3. 自动显示子女发来的关怀卡片，点「听孩子说」语音朗读
4. 点「去和孩子聊聊」→ 选性格角色 → 开始 AI 对话

---

## 技术架构

```
index.html        # 前端（登录/注册、子女主页、父母卡片、AI聊天）
server.py         # 后端（注册/绑定/关怀/对话/TTS/危机 API）
lib/              # 本地 JS 库（PIXI + Live2D SDK）
models/           # Live2D 模型（Haru / Mao / Mark / Hiyori）
.env              # API Key（不进 git）
```

### 后端 API

| 接口 | 说明 |
|---|---|
| `POST /api/register` | 注册或登录，子女自动生成邀请码 |
| `POST /api/bind` | 父母用邀请码绑定家庭 |
| `POST /api/send_care` | 子女发送关怀，存入数据库 |
| `POST /api/latest_care` | 父母拉取最新关怀卡片 |
| `POST /api/care` | AI 润色关怀文案（DeepSeek） |
| `POST /api/chat` | AI 情感对话（DeepSeek） |
| `POST /api/tts` | 文字转语音（Edge-TTS） |
| `POST /api/crisis` | 记录危机预警 |
| `POST /api/crisis_alerts` | 子女查询危机预警记录 |

### 数据库（Supabase）

| 表 | 用途 |
|---|---|
| `users` | 用户（子女/父母），含 `last_active_at` |
| `families` | 家庭绑定关系，含邀请码 |
| `care_cards` | 子女发送的关怀内容 |
| `crisis_alerts` | 父母触发危机词的记录 |

---

## 依赖

- Python 3.9+
- [edge-tts](https://github.com/rany2/edge-tts) — 微软 Edge TTS 语音合成
- [DeepSeek API](https://platform.deepseek.com) — AI 对话与文案润色
- [Supabase](https://supabase.com) — 数据库与用户数据存储
- Live2D Cubism SDK（已内置于 `lib/`）
