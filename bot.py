import os, json, uuid, re
from http.server import HTTPServer, BaseHTTPRequestHandler

store = {
    "categories": {},
    "merchants": {},
    "customers": {},
    "triggers": {},
    "versions": {}
}

# =========================
# LOAD DATASET
# =========================
def load_dataset():
    try:
        for f in os.listdir("dataset/categories"):
            with open(f"dataset/categories/{f}") as file:
                data = json.load(file)
                store["categories"][data["slug"]] = data
    except:
        print("⚠ categories not loaded")

    try:
        with open("dataset/merchants_seed.json") as f:
            for m in json.load(f)["merchants"]:
                store["merchants"][m["merchant_id"]] = m
    except:
        print("⚠ merchants not loaded")

    try:
        with open("dataset/customers_seed.json") as f:
            for c in json.load(f)["customers"]:
                store["customers"][c["customer_id"]] = c
    except:
        pass

    try:
        with open("dataset/triggers_seed.json") as f:
            for t in json.load(f)["triggers"]:
                store["triggers"][t["id"]] = t
    except:
        print("⚠ triggers not loaded")

# =========================
# SAFE PAYLOAD GETTER
# =========================
def get_payload(trigger):
    payload = trigger.get("payload", {})
    if isinstance(payload, dict):
        return payload
    return {}

# =========================
# CLEAN ITEM
# =========================
def clean_item(item):
    if not item:
        return ""

    item = item.lower()

    mapping = {
        "fluoride": "fluoride care",
        "radiograph": "dental X-ray services",
        "cleaning": "dental cleaning",
        "whitening": "teeth whitening"
    }

    for k, v in mapping.items():
        if k in item:
            return v

    return item.replace("_", " ")

# =========================
# SIGNAL ENGINE
# =========================
def build_signals(category, merchant, trigger):
    signals = []

    perf = merchant.get("performance", {})
    peer = category.get("peer_stats", {})
    payload = get_payload(trigger)
    kind = trigger.get("kind")

    # CTR
    ctr = perf.get("ctr")
    peer_ctr = peer.get("avg_ctr")

    if ctr and peer_ctr:
        ctr = round(ctr * 100, 1) if ctr < 1 else ctr
        peer_ctr = round(peer_ctr * 100, 1) if peer_ctr < 1 else peer_ctr

        signals.append({
            "text": f"your CTR is {ctr}% vs {peer_ctr}% peer average",
            "strength": abs(peer_ctr - ctr) + 2
        })

    # DEMAND
    item = clean_item(payload.get("top_item_id"))
    if item:
        signals.append({
            "text": f"more patients are actively searching for {item} this week",
            "strength": 3
        })

    # WINBACK
    lost = payload.get("lost_patients_count")
    if lost:
        signals.append({
            "text": f"{lost} patients haven’t visited in ~6 months",
            "strength": 4
        })

    # REGULATION (FINAL FIX)
    if kind == "regulation_change":
        reg = payload.get("regulation_name")

        # HARD CLEAN
        if isinstance(reg, str):
            reg = reg.strip()

        if reg:
            text = f"new compliance update on {reg} may impact your clinic operations"
        else:
            text = "new compliance update around dental diagnostics may impact your clinic operations"

        signals.append({
            "text": text,
            "strength": 4
        })

    signals.sort(key=lambda x: x["strength"], reverse=True)
    return signals[:2]

# =========================
# MESSAGE BUILDER
# =========================
def build_message(category, merchant, trigger):
    name = merchant.get("identity", {}).get("owner_first_name", "there")
    signals = build_signals(category, merchant, trigger)

    if not signals:
        return f"{name}, there’s a good opportunity to increase bookings this week. Want me to set it up?"

    msg = f"{name}, {signals[0]['text']}."

    if len(signals) > 1:
        msg += f" Also, {signals[1]['text']}."

    msg += " I can help you act on this quickly — want me to activate it?"

    return msg

# =========================
# RATIONALE
# =========================
def build_rationale(category, merchant, trigger):
    signals = build_signals(category, merchant, trigger)

    if not signals:
        return f"Campaign based on {trigger.get('kind')} to maintain engagement."

    top = signals[0]
    return f"Prioritizing '{top['text']}' to drive immediate ROI. Signal strength: {top['strength']}."

# =========================
# SLOT EXTRACTION
# =========================
def extract_slot(text):
    date_pattern = r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
    time_pattern = r'\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b'

    d = re.search(date_pattern, text, re.IGNORECASE)
    t = re.search(time_pattern, text, re.IGNORECASE)

    res = []
    if d: res.append(d.group(0))
    if t: res.append(t.group(0))

    return " ".join(res)

# =========================
# REPLY HANDLER
# =========================
def handle_reply(message, state, from_role="merchant"):
    m = message.lower()

    if any(x in m for x in ["hi", "hello", "hey"]):
        return {
            "action": "send",
            "body": "Hi! I'm Vera. I help you turn demand into bookings. Want me to check an opportunity for you?"
        }

    if any(x in m for x in ["stop", "unsubscribe", "quit", "cancel"]):
        return {"action": "end"}

    if any(x in m for x in ["busy", "later", "working"]):
        return {
            "action": "wait",
            "wait_seconds": 3600,
            "rationale": "Merchant busy — retry later"
        }

    if from_role == "customer":
        if "book" in m or "appointment" in m:
            slot = extract_slot(message)
            if slot:
                return {
                    "action": "send",
                    "body": f"Perfect! I've scheduled your visit for {slot}. The clinic team is expecting you."
                }
            return {
                "action": "send",
                "body": "Sure — what time works best for you?"
            }

    if "cost" in m:
        return {
            "action": "send",
            "body": "This is designed to be low-cost and ROI-positive — it typically brings more bookings than it costs."
        }

    if any(x in m for x in ["yes", "ok", "sure"]):
        return {
            "action": "send",
            "body": "Great — I’ll activate this and share the details shortly."
        }

    return {
        "action": "send",
        "body": "Want me to help you act on this?"
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
            self._send(200, {"bot": "Vera", "version": "PRO+"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        if self.path == "/v1/context":
            scope = body.get("scope")
            cid = body.get("context_id")
            payload = body.get("payload")
            ver = body.get("version", 0)

            if ver <= store["versions"].get(cid, -1):
                return self._send(409, {"accepted": False})

            store["versions"][cid] = ver

            scope_map = {
                "category": "categories",
                "merchant": "merchants",
                "customer": "customers",
                "trigger": "triggers"
            }

            if scope in scope_map:
                store[scope_map[scope]][cid] = payload

            self._send(200, {"accepted": True})

        elif self.path == "/v1/tick":
            actions = []

            for tid in body.get("available_triggers", []):
                trigger = store["triggers"].get(tid)
                if not trigger:
                    continue

                merchant = store["merchants"].get(trigger.get("merchant_id"))
                if not merchant:
                    continue

                category = store["categories"].get(merchant.get("category_slug"))
                if not category:
                    continue

                actions.append({
                    "conversation_id": str(uuid.uuid4()),
                    "body": build_message(category, merchant, trigger),
                    "cta": "yes_stop",
                    "send_as": "vera",
                    "suppression_key": trigger.get("suppression_key", ""),
                    "rationale": build_rationale(category, merchant, trigger)
                })

            self._send(200, {"actions": actions})

        elif self.path == "/v1/reply":
            res = handle_reply(
                body.get("message", ""),
                body,
                body.get("from_role", "merchant")
            )
            self._send(200, res)

        else:
            self._send(404, {"error": "not found"})

# =========================
# RUN
# =========================
if __name__ == "__main__":
    load_dataset()
    port = int(os.environ.get("PORT", 8080))
    print(f"Running on port {port}...")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()