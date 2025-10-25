import os
import json
import time
import threading
from datetime import datetime, timedelta

import requests
from flask import Flask, request, jsonify

# ================== CONFIG ==================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID_DEFAULT = os.environ.get("TELEGRAM_CHAT_ID")  # اختياري للتذكيرات المجدولة

if not TOKEN:
    raise ValueError("Missing env: TELEGRAM_BOT_TOKEN")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
PLAN_FILE = "content_plan.json"

app = Flask(__name__)


# ================== HELPERS ==================
def load_plan():
    if not os.path.exists(PLAN_FILE):
        return {}
    with open(PLAN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plan(plan):
    with open(PLAN_FILE, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)


def tg_send(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=15)
        r.raise_for_status()
        print(f"[send] -> {chat_id}: OK")
    except requests.RequestException as e:
        print(f"[send] ERROR -> {chat_id}: {e}")


# ================== CORE (SCHEDULER) ==================
def check_for_reminders():
    print("[scheduler] checking...")
    plan = load_plan()
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    if not CHAT_ID_DEFAULT:
        print("[scheduler] TELEGRAM_CHAT_ID not set. Skip push reminders.")
        return

    for client, schedule in plan.items():
        # publish today
        if today in schedule and schedule[today].get("status") == "pending":
            task_id = f"task_{client}_{today}"
            idea = schedule[today].get("idea", "No idea specified")
            msg = (
                f"🚀 *Publish Reminder*\n\n"
                f"Today for: *{client}*\n"
                f"Idea: _{idea}_"
            )
            kb = {"inline_keyboard": [[{"text": "✅ Acknowledge", "callback_data": f"ack_{task_id}"}]]}
            tg_send(CHAT_ID_DEFAULT, msg, kb)

        # design for tomorrow
        if tomorrow in schedule and schedule[tomorrow].get("status") == "pending":
            task_id = f"task_{client}_{tomorrow}"
            idea = schedule[tomorrow].get("idea", "No idea specified")
            msg = (
                f"🔔 *Design Reminder*\n\n"
                f"For: *{client}*\n"
                f"Publishing tomorrow ({tomorrow})\n"
                f"Idea: _{idea}_"
            )
            kb = {"inline_keyboard": [[{"text": "✅ Acknowledge", "callback_data": f"ack_{task_id}"}]]}
            tg_send(CHAT_ID_DEFAULT, msg, kb)

    print("[scheduler] done.")


def run_scheduler():
    while True:
        try:
            check_for_reminders()
        except Exception as e:
            print(f"[scheduler] ERROR: {e}")
        time.sleep(60 * 60 * 24)  # كل 24 ساعة


# ================== WEBHOOK ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    # --- callbacks ---
    if "callback_query" in data:
        cb = data["callback_query"]
        cb_data = cb.get("data", "")
        chat_id = cb.get("message", {}).get("chat", {}).get("id")

        if cb_data.startswith("ack_task_") or cb_data.startswith("ack_task") or cb_data.startswith("ack_"):
            # ندعم كل الصيغ المحتملة: ack_task_client_YYYY-MM-DD / ack_task_... / ack_task...
            parts = cb_data.split("_")
            try:
                # ابحث عن التاريخ في النهاية
                yyyy, mm, dd = parts[-3], parts[-2], parts[-1]
                client_name = "_".join(parts[2:-3]).replace("__", "_").strip() or "unknown"
                task_date = f"{yyyy}-{mm}-{dd}"
            except Exception:
                tg_send(chat_id, "⚠️ Unable to parse task id.")
                return "OK", 200

            plan = load_plan()
            if client_name in plan and task_date in plan[client_name]:
                plan[client_name][task_date]["status"] = "acknowledged"
                save_plan(plan)
                tg_send(chat_id, f"✅ Task for *{client_name}* on *{task_date}* acknowledged.")
            else:
                tg_send(chat_id, "⚠️ Task not found.")
        return "OK", 200

    # --- messages ---
    if "message" in data:
        msg = data["message"]
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "") or ""

        if text.startswith("/start"):
            tg_send(chat_id, "مرحبًا! أرسل:\n`/addplan Client; YYYY-MM-DD; Idea`", None)
            return "OK", 200

        if text.startswith("/addplan"):
            # expected: /addplan Client Name; YYYY-MM-DD; Post Idea
            try:
                # افصل الأمر عن بقية السطر ثم قسّم على ;
                body = text[len("/addplan"):].strip()
                client_part, date_part, idea_part = [p.strip() for p in body.split(";", 2)]
                datetime.strptime(date_part, "%Y-%m-%d")

                plan = load_plan()
                plan.setdefault(client_part, {})
                plan[client_part][date_part] = {"idea": idea_part, "status": "pending"}
                save_plan(plan)
                tg_send(chat_id, f"✅ Plan added for *{client_part}* on *{date_part}*.")
            except Exception as e:
                tg_send(
                    chat_id,
                    "Format:\n`/addplan Client; YYYY-MM-DD; Idea`\n"
                    f"Error: `{e}`",
                )
            return "OK", 200

        # افتراضي: إرجاع صدى
        tg_send(chat_id, "تم الاستلام ✅")
        return "OK", 200

    return "OK", 200


# ============ DIAGNOSTICS ============
@app.get("/")
def index():
    return "Reminder Bot is running!"

@app.get("/health")
def health():
    return jsonify(status="ok", time=datetime.utcnow().isoformat())


# ================== MAIN ==================
if __name__ == "__main__":
    # مجدول في الخلفية
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()

    # Flask
    app.run(host="0.0.0.0", port=8080)
