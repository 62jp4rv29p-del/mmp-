# 亲语 · 关爱父母情感交流

> 不在身边，但让父母每天都感受到你的爱。

让空巢父母与 AI「子女」对话的情感陪伴网页应用。父母选择一个性格角色，用文字或语音聊天，AI 以子女的口吻回应，TTS 实时朗读，Live2D 数字人同步说话。

## 角色

| 角色 | 性格 | 模型 | 声音 |
|---|---|---|---|
| 暖心宝贝 | 温柔体贴 | Haru | 晓晓·女 |
| 开心果 | 活泼爱笑 | Mao | 晓伊·女 |
| 靠谱大孩 | 稳重踏实 | Mark | 云健·男 |
| 小话痨 | 热闹话多 | Hiyori | 晓萱·女 |

## 安装

```bash
# 安装依赖
pip3 install edge-tts
```

## 启动

```bash
python3 server.py
```

浏览器打开 http://localhost:8888

## 配置

复制 `.env.example` 为 `.env`，填入你的 DeepSeek API Key：

```
DEEPSEEK_API_KEY=sk-your-key-here
```

## 目录结构

```
index.html        # 主页面（角色选择 + 聊天）
server.py         # 后端（DeepSeek 对话 + Edge-TTS 语音）
lib/              # 本地 JS 库（PIXI + Live2D SDK）
models/           # Live2D 模型文件
  Haru/
  Mao/
  Mark/
  Hiyori/
.env              # API Key（不进 git）
```
