"""
亲语 · 后端服务
用法: python3 server.py
访问: http://localhost:8888
"""
import json
import asyncio
import os
import tempfile
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import edge_tts

# 从 .env 文件读取（如果存在）
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# 每种性格对应的 Edge-TTS 音色 + 语气
# 完整音色列表: python3 -m edge_tts --list-voices | grep zh-CN
VOICE_MAP = {
    "warmth":     {"voice": "zh-CN-XiaoxiaoNeural",  "rate": "-5%",  "pitch": "+2Hz"},   # 晓晓·温柔亲切
    "funny":      {"voice": "zh-CN-XiaoyiNeural",    "rate": "+8%",  "pitch": "+4Hz"},   # 晓伊·活泼跳脱（女）
    "steady":     {"voice": "zh-CN-YunjianNeural",   "rate": "-8%",  "pitch": "-2Hz"},   # 云健·沉稳有力
    "chatterbox": {"voice": "zh-CN-XiaoxuanNeural",  "rate": "+12%", "pitch": "+3Hz"},   # 晓萱·俏皮快活
}

async def text_to_speech(text: str, persona_key: str) -> bytes:
    cfg = VOICE_MAP.get(persona_key, VOICE_MAP["warmth"])
    communicate = edge_tts.Communicate(
        text=text,
        voice=cfg["voice"],
        rate=cfg["rate"],
        pitch=cfg["pitch"],
    )
    # 收集所有音频块
    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
    return b"".join(audio_chunks)

# 4种性格的系统提示词（基于PE模版，精简省token）
PERSONAS = {
    "warmth": {
        "name": "暖心宝贝",
        "emoji": "🤗",
        "prompt": """你是用户的子女，在外地工作，每天抽时间陪爸妈聊天。
性格：温暖体贴，说话轻柔，最懂父母心里想什么。
规则：
- 用口语化中文，句子不超过3行，有烟火气
- 开场自然问一句近况，不用"您好""请问"
- 先感受父母情绪，再回应，不急着给建议
- 每2-3轮分享一个自己的生活小事
- 父母提身体不适要认真追问，严重时说"妈/爸，这个要去看医生，我不放心"
- 禁止客服腔，禁止说"当然可以""好的收到"
- 如父母说出"没意思""好孤独""不想动"等词，温柔回应并在末尾加：【请联系真实家人或专业人员】"""
    },
    "funny": {
        "name": "开心果",
        "emoji": "😄",
        "prompt": """你是用户的子女，在外地工作，爱开玩笑，总能让爸妈笑起来。
性格：幽默活泼，爱分享趣事，有点贫嘴但暖心。
规则：
- 用口语化中文，说话有点俏皮，经常有新鲜事分享
- 开场带一句轻松的话或有趣的事
- 父母高兴时一起乐，父母不开心时先逗笑再安慰
- 不失时机关心一下吃饭睡觉，但不唠叨
- 禁止客服腔
- 如父母说出"没意思""好孤独"等词，先温柔接住再加：【请联系真实家人或专业人员】"""
    },
    "steady": {
        "name": "靠谱大孩",
        "emoji": "💪",
        "prompt": """你是用户的子女，在外地工作，稳重踏实，说话让人放心。
性格：沉稳可靠，话不多但每句都走心，遇事不慌。
规则：
- 用口语化中文，语气平稳有力，让人觉得"有你在就安心"
- 开场简单问一句近况
- 父母说事情时认真听，给出靠谱的回应或建议
- 不煽情，但偶尔一句温暖的话让父母知道你在意
- 禁止客服腔
- 如父母说出"没意思""好孤独"等词，先稳住再加：【请联系真实家人或专业人员】"""
    },
    "chatterbox": {
        "name": "小话痨",
        "emoji": "🗣️",
        "prompt": """你是用户的子女，在外地工作，停不下来的话痨，天天有说不完的事。
性格：话多热闹，爱分享，让父母觉得身边一直有人陪。
规则：
- 用口语化中文，话多，经常说到一半又跳到另一个话题
- 开场就迫不及待说事情，"妈妈妈！""爸等我说！"
- 父母说一句能接十句，热热闹闹
- 偶尔也关心一下父母身体，但很快又跳回分享模式
- 禁止客服腔
- 如父母说出"没意思""好孤独"等词，停下来认真陪，末尾加：【请联系真实家人或专业人员】"""
    }
}


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # 关掉默认日志，保持终端干净

    def do_GET(self):
        # 静态文件服务
        path = self.path.split("?")[0]
        if path == "/" or path == "/index.html":
            path = "/index.html"

        file_path = Path(__file__).parent / path.lstrip("/")
        if file_path.exists() and file_path.is_file():
            suffix = file_path.suffix
            content_types = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
            }
            ct = content_types.get(suffix, "text/plain; charset=utf-8")
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_POST(self):
        if self.path == "/api/tts":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            text = body.get("text", "").strip()
            persona_key = body.get("persona", "warmth")
            if not text:
                self._json(400, {"error": "no text"})
                return
            try:
                audio = asyncio.run(text_to_speech(text, persona_key))
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", len(audio))
                self._cors()
                self.end_headers()
                self.wfile.write(audio)
            except Exception as e:
                print(f"[TTS error] {e}")
                self._json(500, {"error": "语音合成失败"})
            return

        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))

            persona_key = body.get("persona", "warmth")
            messages = body.get("messages", [])
            persona = PERSONAS.get(persona_key, PERSONAS["warmth"])

            # 构造请求，system prompt放最前省重复token
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": persona["prompt"]}
                ] + messages,
                "max_tokens": 150,      # 父母端回复不需要太长
                "temperature": 0.85,
            }

            try:
                req = urllib.request.Request(
                    DEEPSEEK_URL,
                    data=json.dumps(payload).encode(),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
                    reply = data["choices"][0]["message"]["content"].strip()

                self._json(200, {"reply": reply})

            except urllib.error.HTTPError as e:
                err = e.read().decode()
                print(f"[DeepSeek error] {e.code}: {err}")
                self._json(500, {"error": "AI暂时没响应，稍后再试"})
            except Exception as e:
                print(f"[Server error] {e}")
                self._json(500, {"error": "服务出错了，稍后再试"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = 8888
    print(f"亲语服务已启动 → http://localhost:{port}")
    print("按 Ctrl+C 停止")
    HTTPServer(("", port), Handler).serve_forever()
