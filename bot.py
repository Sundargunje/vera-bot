import os
import json
import uuid
import random
from http.server import HTTPServer, BaseHTTPRequestHandler

# =========================
# GLOBAL STORE
# =========================
store = {
    "categories": {},
    "merchants": {},
    "customers": {},
    "triggers": {}
}

sent_cache = set()  # 🔥 suppression memory

# =========================
# LOAD DATASET
# =========================
def load_dataset():
    for file in os.listdir("dataset/categories"):
        with open(f"dataset/categories/{file}") as f:
            data = json.load(f)
            store["categories"][data["slug"]] = data

    with open("dataset/merchants_seed.json") as f:
        for m in json.load(f)["merchants"]:
            store["merchants"][m["merchant_id"]] = m

    with open("dataset/customers_seed.json") as f:
        for c in json.load(f)["customers"]:
            store["customers"][c["customer_id"]] = c

    with open("dataset/triggers_seed.json") as f:
        for t in json.load(f)["triggers"]:
            store["triggers"][t["id"]] = t

    print("✅ Dataset loaded")

# =========================
# HELPER: Extract payload keyword
# =========================
def extract_item(trigger):
    top_item = trigger.get("payload", {}).get("top_item_id", "")

    item_map = {
        "fluoride": "fluoride care",
        "cleaning": "dental cleaning",
        "whitening": "teeth whitening",
        "braces": "orthodontic consultations"
    }

    for key in item_map:
        if key in top_item:
            return item_map[key]

    return "treatments"

# =========================
# HELPER: CTA variation
# =========================
def get_cta():
    return random.choice([
        "Want me to set this up for you?",
        "Should I activate this for you today?",
        "Want me to launch this for you?",
        "Shall I get this live for you today?"
    ])

# =========================
# MESSAGE ENGINE
# =========================
def build_message(category, merchant, trigger):
    kind = trigger.get("kind")
    name = merchant.get("identity", {}).get("owner_first_name", "there")

    ctr = merchant.get("performance", {}).get("ctr")
    peer_ctr = category.get("peer_stats", {}).get("avg_ctr")

    cta = get_cta()

    # -------- perf_dip --------
    if kind == "perf_dip" and ctr and peer_ctr:
        return (
            f"{name}, your CTR is {ctr}% vs {peer_ctr}% peer average this week — you're missing patient bookings right now. "
            f"Clinics in your locality are converting this gap with ₹299 first-visit checkup offers. "
            f"I can set this up for you today — {cta} Reply YES or STOP."
        )

    # -------- recall_due --------
    if kind == "recall_due":
        return (
            f"{name}, some of your past patients are due for follow-up this week — reaching them now can quickly bring back bookings. "
            f"I can send personalized reminders for you today — {cta} Reply YES or STOP."
        )

    # -------- research_digest --------
    if kind == "research_digest":
        item = extract_item(trigger)
        return (
            f"{name}, patient demand is rising in your area — people are actively searching for {item}, which can drive new bookings. "
            f"Clinics nearby are already using this to attract patients. "
            f"I can show what’s trending and help you act on it today — {cta}"
        )

    # -------- winback --------
    if kind == "winback":
        return (
            f"{name}, some of your previous patients haven’t visited recently — re-engaging them now can recover lost revenue. "
            f"I can create a targeted offer to bring them back — {cta} Reply YES or STOP."
        )

    # -------- seasonal --------
    if kind == "seasonal":
        return (
            f"{name}, patient demand is increasing due to seasonal trends — this is a great time to boost bookings. "
            f"I can create a quick offer to capture this demand — {cta} Reply YES or STOP."
        )

    # -------- default --------
    return (
        f"{name}, there’s an opportunity to improve your business performance this week. "
        f"I can help you act on this quickly — {cta} Reply YES or STOP."
    )

# =========================
# COMPOSE
# =========================
def compose(category, merchant, trigger):
    msg = build_message(category, merchant, trigger)

    return {
        "body": msg,
        "cta": "yes_stop",
        "send_as": "vera",
        "suppression_key": trigger.get("suppression_key", ""),
        "rationale": f"Triggered by {trigger.get('kind')}"
    }

# =========================
# REPLY HANDLER
# =========================

last_context = {}

def handle_reply(msg):
    m = msg.lower()

    # 🔹 Get last trigger context (if exists)
    trigger = last_context.get("trigger", {})
    item = trigger.get("item", "your services")
    kind = trigger.get("kind", "")

    # -----------------------
    # ✅ YES INTENT
    # -----------------------
    if any(x in m for x in ["yes", "ok", "sure", "go ahead"]):
        return {
            "action": "send",
            "body": f"Great — I’ll set up a targeted offer around {item} and activate it to attract more patients this week. I’ll share the details with you shortly."
        }

    # -----------------------
    # ❌ STOP INTENT
    # -----------------------
    elif any(x in m for x in ["stop", "no", "don't"]):
        return {"action": "end"}

    # -----------------------
    # 💰 BUSINESS IMPACT
    # -----------------------
    elif "booking" in m or "increase" in m:
        return {
            "action": "send",
            "body": f"This works by targeting patients already searching for {item} and converting them into bookings through focused offers and visibility improvements."
        }

    # -----------------------
    # ❓ HOW IT WORKS
    # -----------------------
    elif "how" in m:
        return {
            "action": "send",
            "body": f"It works by identifying demand trends like {item} and helping you act on them with targeted campaigns that bring in more patients."
        }

    # -----------------------
    # 💸 COST
    # -----------------------
    elif "cost" in m or "price" in m:
        return {
            "action": "send",
            "body": "It’s designed to be cost-effective and focused on generating more revenue than it spends — want me to show expected results?"
        }

    # -----------------------
    # 🤔 DOUBT / TRUST
    # -----------------------
    elif any(x in m for x in ["useful", "really", "worth"]):
        return {
            "action": "send",
            "body": f"Clinics using similar strategies for {item} are seeing improved visibility and more patient inquiries — it’s a proven way to grow bookings."
        }
    
    
    # -----------------------
    # 👋 GREETING
    # -----------------------
    elif any(x in m for x in ["hi", "hello", "hey"]):
        return {
        "action": "send",
        "body": "Hi! I’ve been helping you with ways to improve your bookings — would you like me to set something up based on current demand?"
     }
    # -----------------------
    # 🔁 DEFAULT SMART RESPONSE
    # -----------------------
    else:
        return {
            "action": "send",
            "body": f"I can help you grow bookings by leveraging demand for {item} and turning it into real patient visits — want me to set this up for you?"
        }

# =========================
# SERVER
# =========================
class Handler(BaseHTTPRequestHandler):

    def _send(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/v1/healthz":
            self._send(200, {"status": "ok"})
        elif self.path == "/v1/metadata":
            self._send(200, {"bot": "Vera", "version": "winner"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        # -------- context --------
        if self.path == "/v1/context":
            scope = body.get("scope")
            context_id = body.get("context_id")
            payload = body.get("payload")

            if scope and context_id:
                store[scope + "s"][context_id] = payload

            self._send(200, {"status": "stored"})

        # -------- tick --------
        elif self.path == "/v1/tick":
            actions = []

            for trig_id in body.get("available_triggers", []):

                trigger = store["triggers"].get(trig_id)
                if not trigger:
                    continue

                # 🔥 suppression check
                if trigger.get("suppression_key") in sent_cache:
                    continue

                merchant = store["merchants"].get(trigger.get("merchant_id"))
                if not merchant:
                    continue

                category = store["categories"].get(merchant.get("category_slug"))
                if not category:
                    continue

                res = compose(category, merchant, trigger)

                sent_cache.add(trigger.get("suppression_key"))

                actions.append({
                    "conversation_id": str(uuid.uuid4()),
                    "body": res["body"],
                    "cta": res["cta"],
                    "send_as": res["send_as"],
                    "suppression_key": res["suppression_key"],
                    "rationale": res["rationale"]
                })

            self._send(200, {"actions": actions})

        elif self.path == "/v1/reply":
            self._send(200, handle_reply(body.get("message", "")))

        else:
            self._send(404, {"error": "not found"})

# =========================
# RUN
# =========================
if __name__ == "__main__":
    load_dataset()
    print("🚀 Running on http://localhost:8080")
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()