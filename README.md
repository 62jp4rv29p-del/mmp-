# 亲语 · 关爱父母情感交流

> 不在身边，但让父母每天都感受到你的爱。

「亲语」是一款面向异地家庭的 AI 情感陪伴 Demo。子女用 60 秒发送今日关怀，父母随时可与 AI 数字孩子聊天，感受陪伴。

---

## 产品截图

| 登录页 | 父母主页 | 聊天页 |
|---|---|---|
| 紫色星空插画背景 | 3D 卡通角色 + 气泡问候 | Live2D 数字人 + 语音对话 |

---

## 功能一览

### 子女端

| 功能 | 说明 |
|---|---|
| 注册 / 登录 | 手机号 + 昵称，自动识别已有账号 |
| 邀请码生成 | 自动生成 6 位数字邀请码，发给父母完成家庭绑定 |
| 今日关怀发送 | 6 种情景模板（上班忙碌 / 天气叮嘱 / 想你了 / 好好吃饭 / 注意健康 / 开心事分享）+ AI 润色，60 秒完成 |
| 父母状态查看 | 实时查看父母今日心情、最近活跃时间、健康报告 |
| 危机预警 | 父母聊天触发负面情绪词时，主页展示黄色预警卡片 |

### 父母端

| 功能 | 说明 |
|---|---|
| 注册 / 登录 | 手机号 + 昵称 + 性别选择（妈妈 / 爸爸） |
| 邀请码绑定 | 6 格输入框，输入子女邀请码完成家庭绑定 |
| 关怀卡片 | 登录后自动弹出子女最新关怀，支持 TTS 语音朗读，看过一次不重复弹 |
| 快捷记录 | 一键记录睡眠 / 饮食 / 心情 / 身体状态，自动组装成对话发给 AI |
| AI 情感陪伴 | 4 种性格角色 + Live2D 数字人动画 + TTS 语音输出 |
| 情绪聊天 | 选择今日心情（开心 / 平静 / 累 / 孤独）直接进入聊天 |
| 关怀提醒 | AI 生成每日心灵短句 |
| 健康报告 | 填写血压 / 心率 / 步数等，自动同步给子女 |
| 回忆相册 | 上传家庭照片，子女也可查看 |
| 更多设置 | 语音音量 / 字体大小（小14px · 中19px · 大26px）/ 自动朗读 / 消息提醒 |

### AI 角色

| 角色 | 性格 | 头像 | 声音 |
|---|---|---|---|
| 暖心宝贝 | 温柔体贴，最懂您心里想什么 | 即梦 3D · 黄色卫衣男生 | 晓晓·女声 |
| 开心果 | 活泼幽默，每天让您笑 | 即梦 3D · 绿色卫衣女生 | 晓伊·女声 |
| 靠谱大孩 | 稳重踏实，说话让人放心 | 即梦 3D · 紫色帽子女生 | 云健·男声 |
| 小话痨 | 话多热闹，天天有说不完的事 | 即梦 3D · 粉色毛衣女生 | 晓萱·女声 |

### 安全机制

| 机制 | 说明 |
|---|---|
| 危机干预 | 检测「好孤独」「没意思」等负面情绪词，触发独立预警链路，记录到数据库并在子女端展示 |
| AI 免责声明 | 聊天界面底部常驻「这是 AI 陪伴，不是真实的子女」 |
| 关怀卡声明 | 关怀卡片底部注明「以上内容由 AI 陪伴助手代为传达，不是真实的孩子发言」 |

---

## 快速开始

### 1. 安装依赖

```bash
pip3 install edge-tts
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的 Key：

```
DEEPSEEK_API_KEY=sk-your-deepseek-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 3. 创建 Supabase 数据表

在 Supabase SQL 编辑器里执行以下建表语句：

```sql
-- 用户表
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  phone text unique not null,
  name text not null,
  role text not null,  -- 'child' | 'parent'
  last_active_at timestamptz default now(),
  created_at timestamptz default now()
);

-- 家庭绑定表
create table if not exists families (
  id uuid primary key default gen_random_uuid(),
  child_id uuid not null,
  parent_id uuid,
  invite_code text unique not null,
  bound_at timestamptz,
  created_at timestamptz default now()
);

-- 关怀卡片表
create table if not exists care_cards (
  id uuid primary key default gen_random_uuid(),
  family_id uuid not null,
  child_id uuid not null,
  template text,
  content text not null,
  is_read boolean default false,
  created_at timestamptz default now()
);

-- 危机预警表
create table if not exists crisis_alerts (
  id uuid primary key default gen_random_uuid(),
  family_id uuid not null,
  trigger_text text not null,
  is_notified boolean default false,
  created_at timestamptz default now()
);

-- 心情记录表
create table if not exists mood_logs (
  id uuid primary key default gen_random_uuid(),
  family_id uuid not null,
  user_id uuid not null,
  mood text not null,
  note text default '',
  log_date date not null default current_date,
  created_at timestamptz default now()
);

-- 家庭相册表
create table if not exists album_photos (
  id uuid primary key default gen_random_uuid(),
  family_id uuid not null,
  user_id uuid not null,
  image_data text not null,
  created_at timestamptz default now()
);
```

### 4. 启动服务

```bash
python3 server.py
```

浏览器打开 **http://localhost:8888**

---

## 使用流程

### 子女端

1. 选「我是子女」→ 填手机号和昵称 → 进入主页
2. 复制 6 位邀请码发给父母
3. 点「给爸妈发今日关怀」→ 选情景模板 → 可选 AI 润色 → 发送

### 父母端

1. 选「我是父母」→ 选妈妈 / 爸爸 → 填手机号和昵称
2. 输入子女邀请码 → 绑定成功
3. 自动弹出子女发来的关怀卡片，点「听孩子说」语音朗读
4. 点「去和孩子聊聊」或选择角色 → 开始 AI 对话
5. 可用睡眠 / 饮食 / 心情 / 身体状态快捷按钮记录今日状况

---

## 技术架构

```
index.html     # 全部前端（SPA，纯原生 JS，无框架）
server.py      # Python 后端（标准库 HTTPServer，无第三方框架）
avatars/       # 即梦 AI 生成的 3D 角色头像（4 个角色 + 登录页少女）
lib/           # 前端 JS 库（PIXI.js + Live2D Cubism SDK）
models/        # Live2D 模型（Haru / Mao / Mark / Hiyori / Ren）
.env           # API Key（不进 git，参考 .env.example）
```

### 后端 API 一览

| 接口 | 功能 |
|---|---|
| `POST /api/register` | 注册或登录，子女自动生成邀请码和家庭 |
| `POST /api/bind` | 父母用邀请码绑定家庭 |
| `POST /api/send_care` | 子女发送关怀，写入 care_cards |
| `POST /api/latest_care` | 父母拉取最新关怀卡片（自动标记已读） |
| `POST /api/care` | AI 润色关怀文案（DeepSeek） |
| `POST /api/chat` | AI 情感对话（DeepSeek）|
| `POST /api/tts` | 文字转语音（Edge-TTS） |
| `POST /api/save_mood` | 父母记录今日心情 |
| `POST /api/family_status` | 子女拉取父母状态（心情 + 活跃时间 + 健康报告） |
| `POST /api/crisis` | 记录危机预警 |
| `POST /api/crisis_alerts` | 子女查询危机预警记录 |
| `POST /api/save_album` | 上传家庭相册照片 |
| `POST /api/get_album` | 拉取家庭相册 |
| `POST /api/delete_photo` | 删除相册照片 |
| `POST /api/parent_reports` | 子女拉取父母健康报告 |

---

## 依赖

- **Python 3.9+**（标准库，无需安装框架）
- [edge-tts](https://github.com/rany2/edge-tts) — 微软 Edge TTS 免费语音合成
- [DeepSeek API](https://platform.deepseek.com) — AI 对话与文案润色
- [Supabase](https://supabase.com) — PostgreSQL 数据库云服务（免费额度够用）
- Live2D Cubism SDK（已内置于 `lib/`，无需单独安装）
