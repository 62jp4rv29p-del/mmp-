"""
亲语 · 后端服务
用法: python3 server.py
访问: http://localhost:8888
"""
import json
import asyncio
import os
import random
import string
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

DEEPSEEK_API_KEY  = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL      = "https://api.deepseek.com/chat/completions"

SUPABASE_URL      = os.environ.get("SUPABASE_URL", "https://qhhyiumlpcccuxrzekxz.supabase.co")
SUPABASE_KEY      = os.environ.get("SUPABASE_SERVICE_KEY", "")  # service_role key

# ── Supabase REST 工具 ──────────────────────────────────────────
def sb_req(method: str, table: str, body=None, params: str = ""):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if params:
        url += "?" + params
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("apikey", SUPABASE_KEY)
    req.add_header("Authorization", f"Bearer {SUPABASE_KEY}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Prefer", "return=representation")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def sb_get(table: str, params: str = ""):
    return sb_req("GET", table, params=params)

def sb_post(table: str, body: dict):
    return sb_req("POST", table, body=body)

def sb_patch(table: str, body: dict, params: str = ""):
    return sb_req("PATCH", table, body=body, params=params)

def touch_active(user_id: str):
    from datetime import datetime, timezone
    try:
        sb_patch("users", {"last_active_at": datetime.now(timezone.utc).isoformat()}, f"id=eq.{user_id}")
    except Exception:
        pass

def gen_invite_code() -> str:
    return "".join(random.choices(string.digits, k=6))

# ── TTS 音色 ───────────────────────────────────────────────────
VOICE_MAP = {
    "warmth":     {"voice": "zh-CN-XiaoxiaoNeural",  "rate": "-5%",  "pitch": "+2Hz"},
    "funny":      {"voice": "zh-CN-XiaoyiNeural",    "rate": "+8%",  "pitch": "+4Hz"},
    "steady":     {"voice": "zh-CN-YunjianNeural",   "rate": "-8%",  "pitch": "-2Hz"},
    "chatterbox": {"voice": "zh-CN-XiaoxuanNeural",  "rate": "+12%", "pitch": "+3Hz"},
}

async def text_to_speech(text: str, persona_key: str) -> bytes:
    cfg = VOICE_MAP.get(persona_key, VOICE_MAP["warmth"])
    communicate = edge_tts.Communicate(
        text=text, voice=cfg["voice"], rate=cfg["rate"], pitch=cfg["pitch"],
    )
    chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)

# ── AI 性格提示词 ───────────────────────────────────────────────
PERSONAS = {
    "warmth": {
        "name": "暖心宝贝",
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
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/" or path == "/index.html":
            path = "/index.html"
        file_path = Path(__file__).parent / path.lstrip("/")
        if file_path.exists() and file_path.is_file():
            suffix = file_path.suffix
            content_types = {
                ".html": "text/html; charset=utf-8",
                ".css":  "text/css; charset=utf-8",
                ".js":   "application/javascript; charset=utf-8",
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
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length))

        # ── 注册 ──────────────────────────────────────────────
        if self.path == "/api/register":
            phone = body.get("phone", "").strip()
            name  = body.get("name", "").strip()
            role  = body.get("role", "")   # "child" | "parent"

            if not phone or not name or role not in ("child", "parent"):
                self._json(400, {"error": "参数不完整"}); return

            # 查手机号是否已注册
            existing = sb_get("users", f"phone=eq.{phone}&select=id,name,role")
            if existing:
                u = existing[0]
                if u["role"] != role:
                    self._json(400, {"error": "该手机号已用其他身份注册"}); return
                # 已注册直接返回（自动登录）
                user_id = u["id"]
            else:
                created = sb_post("users", {"phone": phone, "name": name, "role": role})
                user_id = created[0]["id"]

            result = {"user_id": user_id, "name": name, "role": role}

            # 子女：自动创建家庭 + 邀请码（如果还没有）
            if role == "child":
                fam = sb_get("families", f"child_id=eq.{user_id}&select=invite_code,parent_id,id")
                if fam:
                    result["invite_code"] = fam[0]["invite_code"]
                    result["family_id"]   = fam[0]["id"]
                    result["bound"]       = fam[0]["parent_id"] is not None
                else:
                    code = gen_invite_code()
                    # 确保 code 不重复
                    while sb_get("families", f"invite_code=eq.{code}"):
                        code = gen_invite_code()
                    new_fam = sb_post("families", {"child_id": user_id, "invite_code": code})
                    result["invite_code"] = code
                    result["family_id"]   = new_fam[0]["id"]
                    result["bound"]       = False

            # 父母：查是否已绑定
            if role == "parent":
                fam = sb_get("families", f"parent_id=eq.{user_id}&select=id,invite_code")
                result["bound"] = len(fam) > 0
                if fam:
                    result["family_id"] = fam[0]["id"]

            touch_active(user_id)
            self._json(200, result)

        # ── 父母绑定（输入邀请码） ─────────────────────────────
        elif self.path == "/api/bind":
            parent_id   = body.get("parent_id", "")
            invite_code = body.get("invite_code", "").strip()

            if not parent_id or not invite_code:
                self._json(400, {"error": "参数不完整"}); return

            fam = sb_get("families", f"invite_code=eq.{invite_code}&select=id,child_id,parent_id")
            if not fam:
                self._json(404, {"error": "邀请码不存在，请确认后重试"}); return
            f = fam[0]
            if f["parent_id"] and f["parent_id"] != parent_id:
                self._json(400, {"error": "该邀请码已被使用"}); return

            # 绑定
            from datetime import datetime, timezone
            sb_patch("families", {
                "parent_id": parent_id,
                "bound_at": datetime.now(timezone.utc).isoformat()
            }, f"invite_code=eq.{invite_code}")

            # 取子女名字
            child = sb_get("users", f"id=eq.{f['child_id']}&select=name")
            child_name = child[0]["name"] if child else "孩子"

            self._json(200, {
                "family_id":  f["id"],
                "child_name": child_name
            })

        # ── 子女发关怀 ─────────────────────────────────────────
        elif self.path == "/api/send_care":
            family_id = body.get("family_id", "")
            child_id  = body.get("child_id", "")
            template  = body.get("template", "")
            content   = body.get("content", "").strip()

            if not family_id or not child_id or not content:
                self._json(400, {"error": "参数不完整"}); return

            card = sb_post("care_cards", {
                "family_id": family_id,
                "child_id":  child_id,
                "template":  template,
                "content":   content,
            })
            touch_active(child_id)
            self._json(200, {"card_id": card[0]["id"]})

        # ── 父母拉取最新关怀 ────────────────────────────────────
        elif self.path == "/api/latest_care":
            family_id = body.get("family_id", "")
            if not family_id:
                self._json(400, {"error": "缺少 family_id"}); return

            cards = sb_get("care_cards",
                f"family_id=eq.{family_id}&order=created_at.desc&limit=1&select=id,template,content,created_at,is_read")
            if not cards:
                self._json(200, {"card": None}); return

            card = cards[0]
            # 标记已读
            sb_patch("care_cards", {"is_read": True}, f"id=eq.{card['id']}")
            self._json(200, {"card": card})

        # ── 危机记录 ───────────────────────────────────────────
        if self.path == "/api/crisis":
            family_id   = body.get("family_id", "")
            trigger_text = body.get("trigger_text", "").strip()
            if not family_id or not trigger_text:
                self._json(400, {"error": "参数不完整"}); return
            try:
                sb_post("crisis_alerts", {
                    "family_id":    family_id,
                    "trigger_text": trigger_text,
                })
                self._json(200, {"ok": True})
            except Exception as e:
                print(f"[crisis error] {e}")
                self._json(500, {"error": "记录失败"})
            return

        # ── 查询危机记录（子女端） ──────────────────────────────
        if self.path == "/api/crisis_alerts":
            family_id = body.get("family_id", "")
            if not family_id:
                self._json(400, {"error": "缺少 family_id"}); return
            try:
                alerts = sb_get("crisis_alerts",
                    f"family_id=eq.{family_id}&order=created_at.desc&limit=3&select=id,trigger_text,created_at,is_notified")
                self._json(200, {"alerts": alerts})
            except Exception as e:
                print(f"[crisis_alerts error] {e}")
                self._json(500, {"error": "查询失败"})
            return

        # ── AI 润色关怀文案 ────────────────────────────────────
        elif self.path == "/api/care":
            template = body.get("template", "")
            text     = body.get("text", "").strip()
            if not text:
                self._json(400, {"error": "no text"}); return

            tpl_names = {
                "busy": "上班忙碌", "weather": "天气叮嘱", "miss": "想你了",
                "meal": "好好吃饭", "health": "注意健康", "happy": "开心事分享",
            }
            care_prompt = f"""你是帮子女写给父母的关怀短信润色助手。
用温暖自然的口语中文，保留原意，让文字更像孩子亲口说的话。
主题：{tpl_names.get(template, '日常关怀')}
要求：2-4句话，不超过80字，不加称谓，不用表情符号。
只输出润色后的文字，不加任何解释。"""

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": care_prompt},
                    {"role": "user",   "content": text}
                ],
                "max_tokens": 120, "temperature": 0.8,
            }
            try:
                req = urllib.request.Request(
                    DEEPSEEK_URL, data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json",
                             "Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read())
                self._json(200, {"text": data["choices"][0]["message"]["content"].strip()})
            except Exception as e:
                print(f"[care error] {e}")
                self._json(200, {"text": text})

        # ── AI 对话 ────────────────────────────────────────────
        elif self.path == "/api/chat":
            persona_key = body.get("persona", "warmth")
            messages    = body.get("messages", [])
            persona     = PERSONAS.get(persona_key, PERSONAS["warmth"])

            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": persona["prompt"]}] + messages,
                "max_tokens": 150, "temperature": 0.85,
            }
            try:
                req = urllib.request.Request(
                    DEEPSEEK_URL, data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json",
                             "Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
                reply = data["choices"][0]["message"]["content"].strip()
                # 聊天说明父母在活跃，更新时间（从 family_id 反查 parent_id）
                parent_info = sb_get("families", f"id=eq.{body.get('family_id','')}&select=parent_id")
                if parent_info and parent_info[0].get("parent_id"):
                    touch_active(parent_info[0]["parent_id"])
                self._json(200, {"reply": reply})
            except urllib.error.HTTPError as e:
                print(f"[DeepSeek error] {e.code}: {e.read().decode()}")
                self._json(500, {"error": "AI暂时没响应，稍后再试"})
            except Exception as e:
                print(f"[Server error] {e}")
                self._json(500, {"error": "服务出错了，稍后再试"})

        # ── TTS ───────────────────────────────────────────────
        elif self.path == "/api/tts":
            text        = body.get("text", "").strip()
            persona_key = body.get("persona", "warmth")
            if not text:
                self._json(400, {"error": "no text"}); return
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
