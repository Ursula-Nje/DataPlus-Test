from flask import Flask, request
import sqlite3
import os
import html
import africastalking
import datetime

app = Flask(__name__)

africastalking.initialize("sandbox", os.environ["AT_API_KEY"])
sms = africastalking.SMS

DB_FILE = "mkononi.db"

AIRTIME_AMOUNTS = {"1": 10, "2": 20, "3": 50, "4": 100}
NETWORK_ISSUES = {"1": "No Network", "2": "Slow Internet", "3": "Calls Dropping"}
SUPPORT_TOPICS = {"1": "Billing", "2": "Network", "3": "Account", "4": "Other"}


# ---------------- Database ----------------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ref TEXT,
                kind TEXT NOT NULL,
                detail TEXT,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS balances (
                phone TEXT PRIMARY KEY,
                amount INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def save_request(prefix, kind, detail, phone):
    """Save a request and return its unique reference, e.g. MC1001."""
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute(
            "INSERT INTO requests (kind, detail, phone) VALUES (?, ?, ?)",
            (kind, detail, phone),
        )
        ref = f"{prefix}{1000 + cur.lastrowid}"
        conn.execute("UPDATE requests SET ref = ? WHERE id = ?", (ref, cur.lastrowid))
    return ref


def add_balance(phone, amount):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO balances (phone, amount) VALUES (?, ?) "
            "ON CONFLICT(phone) DO UPDATE SET amount = amount + excluded.amount",
            (phone, amount),
        )


def get_balance(phone):
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute(
            "SELECT amount FROM balances WHERE phone = ?", (phone,)
        ).fetchone()
    return row[0] if row else 0


# ---------------- SMS ----------------
def send_sms(phone, message):
    try:
        return sms.send(message, [phone])
    except Exception as e:
        print("SMS failed:", e)


# ---------------- USSD ----------------
@app.route("/ussd", methods=["GET", "POST"])
def ussd():
    text = request.form.get("text", "")
    phone = request.form.get("phoneNumber", "")
    parts = text.split("*") if text else []

    # ---- Main menu ----
    if not parts:
        response = (
            "CON Welcome to Mkononi Connect\n\n"
            "1. Network Help\n"
            "2. Buy Airtime\n"
            "3. Check Balance\n"
            "4. Report Fraud\n"
            "5. Support"
        )

    # ---- 1. Network Help ----
    elif parts[0] == "1":
        if len(parts) == 1:
            response = (
                "CON Network Help\n\n"
                "1. No Network\n"
                "2. Slow Internet\n"
                "3. Calls Dropping"
            )
        elif len(parts) == 2 and parts[1] in NETWORK_ISSUES:
            issue = NETWORK_ISSUES[parts[1]]
            ticket = save_request("MC", "network_issue", issue, phone)
            send_sms(
                phone,
                f"Mkononi Connect: your report ({issue}) has been received. "
                f"Ticket: {ticket}. We will follow up soon.",
            )
            response = (
                "END Your network problem has been reported.\n"
                f"Ticket: {ticket}\n"
                "A confirmation SMS has been sent."
            )
        else:
            response = "END Invalid choice. Please try again."

    # ---- 2. Buy Airtime ----
    elif parts[0] == "2":
        if len(parts) == 1:
            response = (
                "CON Select amount\n\n"
                "1.sh10=50mins,1hrs\n"
                "2.sh20=45mins,3hrs\n"
                "3.sh50=120mins,24hrs\n"
                "4.sh100=unlimited,24hrs"
            )
        elif len(parts) == 2 and parts[1] in AIRTIME_AMOUNTS:
            amount = AIRTIME_AMOUNTS[parts[1]]
            response = (
                f"CON Buy KES {amount} airtime?\n\n"
                "1. Confirm\n"
                "2. Cancel"
            )
        elif len(parts) == 3 and parts[1] in AIRTIME_AMOUNTS:
            amount = AIRTIME_AMOUNTS[parts[1]]
            if parts[2] == "1":
                ref = save_request("AT", "airtime", f"KES {amount}", phone)
                add_balance(phone, amount)
                balance = get_balance(phone)
                send_sms(
                    phone,
                    f"Mkononi Connect: KES {amount} airtime received. "
                    f"Ref: {ref}. New balance: KES {balance}.",
                )
                response = (
                    f"END KES {amount} airtime added.\n"
                    f"Ref: {ref}\n"
                    f"New balance: KES {balance}\n"
                    "A receipt SMS has been sent."
                )
            elif parts[2] == "2":
                response = "END Purchase cancelled."
            else:
                response = "END Invalid choice. Please try again."
        else:
            response = "END Invalid choice. Please try again."

    # ---- 3. Check Balance ----
    elif parts[0] == "3":
        if len(parts) == 1:
            response = f"END Your balance is KES {get_balance(phone)}."
        else:
            response = "END Invalid choice. Please try again."

    # ---- 4. Report Fraud ----
    elif parts[0] == "4":
        ticket = save_request("MC", "fraud_report", "", phone)
        send_sms(phone, f"Mkononi Connect: fraud report received. Ticket: {ticket}.")
        response = f"END Fraud report received.\nTicket: {ticket}"

    # ---- 5. Support ----
    elif parts[0] == "5":
        if len(parts) == 1:
            response = (
                "CON Support\n\n"
                "1. Billing\n"
                "2. Network\n"
                "3. Account\n"
                "4. Other"
            )
        elif len(parts) == 2 and parts[1] in SUPPORT_TOPICS:
            response = "CON Describe your issue briefly:"
        elif len(parts) >= 3 and parts[1] in SUPPORT_TOPICS:
            topic = SUPPORT_TOPICS[parts[1]]
            message = "*".join(parts[2:]).strip()[:160]
            if not message:
                response = "END No message received. Please try again."
            else:
                ticket = save_request("SP", "support", f"{topic}: {message}", phone)
                send_sms(
                    phone,
                    f"Mkononi Connect: support request ({topic}) received. "
                    f"Ticket: {ticket}. Our team will contact you.",
                )
                response = (
                    "END Your message has been received.\n"
                    f"Ticket: {ticket}\n"
                    "A confirmation SMS has been sent."
                )
        else:
            response = "END Invalid choice. Please try again."

    else:
        response = "END Invalid choice. Please try again."

    return response, 200, {"Content-Type": "text/plain"}


# ---------------- Admin dashboard ----------------
ADMIN_CSS = """
:root {
  --black:#0d0d0d; --charcoal:#1a1a1a; --grey:#2b2b2b; --line:#3a3a3a;
  --muted:#9a9a9a; --beige:#d9c8a9; --beige-soft:#efe4cf;
}
* { box-sizing: border-box; }
body { margin:0; font-family:"Segoe UI", system-ui, sans-serif;
       background:var(--black); color:var(--beige-soft); }
header { padding:28px 40px; border-bottom:2px solid var(--beige);
         background:linear-gradient(135deg, var(--charcoal), var(--grey)); }
header h1 { margin:0; font-size:1.6rem; letter-spacing:.5px; color:var(--beige); }
header p { margin:4px 0 0; color:var(--muted); font-size:.9rem; }
main { padding:32px 40px; max-width:1100px; margin:0 auto; }
.cards { display:grid; gap:16px; margin-bottom:32px;
         grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); }
.card { background:var(--charcoal); border:1px solid var(--line);
        border-left:4px solid var(--beige); border-radius:10px;
        padding:18px 20px; transition:transform .15s, border-color .15s; }
.card:hover { transform:translateY(-3px); border-color:var(--beige); }
.card .num { font-size:2.2rem; font-weight:700; color:var(--beige); }
.card .label { color:var(--muted); font-size:.8rem;
               text-transform:uppercase; letter-spacing:1px; }
h2 { font-size:1rem; text-transform:uppercase; letter-spacing:1.5px;
     color:var(--beige); margin:32px 0 12px; }
.panel { background:var(--charcoal); border:1px solid var(--line);
         border-radius:10px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; }
th { text-align:left; padding:12px 16px; background:var(--grey); color:var(--beige);
     font-size:.75rem; text-transform:uppercase; letter-spacing:1px; }
td { padding:12px 16px; border-top:1px solid var(--line); font-size:.9rem; }
tbody tr:hover { background:var(--grey); }
.badge { display:inline-block; padding:2px 10px; border-radius:999px;
         font-size:.75rem; background:var(--grey);
         border:1px solid var(--beige); color:var(--beige); }
.empty { padding:24px; color:var(--muted); text-align:center; }

.charts { display:grid; gap:24px; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); }
.vchart { display:flex; align-items:stretch; gap:12px; height:220px; padding:28px 20px 12px; }
.col { flex:1; display:flex; flex-direction:column; }
.barwrap { flex:1; display:flex; align-items:flex-end; }
.barv { width:100%; background:var(--beige); border-radius:6px 6px 0 0;
        min-height:3px; position:relative; transition:background .15s; }
.barv:hover { background:var(--beige-soft); }
.barv span { position:absolute; top:-20px; width:100%; text-align:center;
             font-size:.75rem; color:var(--beige-soft); }
.xl { text-align:center; color:var(--muted); font-size:.75rem; margin-top:8px; }
.hchart { padding:20px; }
.hrow { display:flex; align-items:center; gap:12px; margin-bottom:14px; }
.hrow:last-child { margin-bottom:0; }
.hl { width:120px; font-size:.85rem; color:var(--muted); }
.htrack { flex:1; background:var(--grey); border-radius:999px; height:12px; overflow:hidden; }
.hfill { height:100%; background:var(--beige); border-radius:999px; }
.hn { width:32px; text-align:right; font-weight:600; color:var(--beige); }

"""


@app.route("/admin")
def admin():
    key = os.environ.get("ADMIN_KEY")
    if not key or request.args.get("key") != key:
        return "Not authorised", 403

    with sqlite3.connect(DB_FILE) as conn:
        total = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        kinds = dict(
            conn.execute("SELECT kind, COUNT(*) FROM requests GROUP BY kind").fetchall()
        )
        summary = conn.execute(
            "SELECT kind, "
            "CASE WHEN kind = 'support' THEN substr(detail, 1, instr(detail, ':') - 1) "
            "ELSE COALESCE(NULLIF(detail, ''), '-') END AS d, COUNT(*) "
            "FROM requests GROUP BY kind, d ORDER BY COUNT(*) DESC"
        ).fetchall()
        recent = conn.execute(
            "SELECT ref, kind, detail, phone, created_at "
            "FROM requests ORDER BY id DESC LIMIT 20"
        ).fetchall()
        balance_total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM balances"
        ).fetchone()[0]
        daily = dict(
            conn.execute(
                "SELECT date(created_at), COUNT(*) FROM requests "
                "WHERE date(created_at) >= date('now', '-6 days') "
                "GROUP BY date(created_at)"
            ).fetchall()
        )
    today = datetime.datetime.now(datetime.timezone.utc).date()
    days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    day_counts = [daily.get(d.isoformat(), 0) for d in days]
    max_day = max(day_counts) or 1
    day_bars = "".join(
        f'<div class="col"><div class="barwrap">'
        f'<div class="barv" style="height:{int(c / max_day * 100)}%"><span>{c}</span></div>'
        f'</div><div class="xl">{d.strftime("%a")}</div></div>'
        for d, c in zip(days, day_counts)
    )

    labels = {
        "network_issue": "Network issues",
        "airtime": "Airtime",
        "support": "Support",
        "fraud_report": "Fraud reports",
    }
    max_kind = max(kinds.values(), default=1) or 1
    type_bars = "".join(
        f'<div class="hrow"><div class="hl">{html.escape(labels.get(k, k))}</div>'
        f'<div class="htrack"><div class="hfill" style="width:{int(n / max_kind * 100)}%"></div></div>'
        f'<div class="hn">{n}</div></div>'
        for k, n in sorted(kinds.items(), key=lambda x: -x[1])
    ) or '<div class="empty">No data yet</div>'

    def mask(p):
        return p[:4] + "****" + p[-3:] if p and len(p) > 7 else "****"

    def card(num, label):
        return (f'<div class="card"><div class="num">{num}</div>'
                f'<div class="label">{label}</div></div>')

    cards = (
        card(total, "Total requests")
        + card(kinds.get("network_issue", 0), "Network issues")
        + card(kinds.get("airtime", 0), "Airtime requests")
        + card(kinds.get("support", 0), "Support tickets")
        + card(kinds.get("fraud_report", 0), "Fraud reports")
        + card(f"KES {balance_total}", "Total balances")
    )

    summary_rows = "".join(
        f'<tr><td><span class="badge">{html.escape(k)}</span></td>'
        f"<td>{html.escape(str(d))}</td><td>{n}</td></tr>"
        for k, d, n in summary
    ) or '<tr><td colspan="3" class="empty">No data yet</td></tr>'

    recent_rows = "".join(
        f"<tr><td>{html.escape(str(r))}</td>"
        f'<td><span class="badge">{html.escape(k)}</span></td>'
        f"<td>{html.escape(d or '-')}</td><td>{html.escape(mask(p))}</td>"
        f"<td>{html.escape(str(t))}</td></tr>"
        for r, k, d, p, t in recent
    ) or '<tr><td colspan="5" class="empty">No requests yet</td></tr>'

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mkononi Connect Admin</title>
<style>{ADMIN_CSS}</style>
</head><body>
<header>
  <h1>Mkononi Connect</h1>
  <p>Admin dashboard</p>
</header>
<main>
  <div class="cards">{cards}</div>
  <div class="charts">
    <div>
      <h2>Last 7 days</h2>
      <div class="panel vchart">{day_bars}</div>
    </div>
    <div>
      <h2>Requests by type</h2>
      <div class="panel hchart">{type_bars}</div>
    </div>
  </div>

  <h2>By type</h2>
  <div class="panel"><table>
    <thead><tr><th>Kind</th><th>Detail</th><th>Count</th></tr></thead>
    <tbody>{summary_rows}</tbody>
  </table></div>

  <h2>Latest 20 requests</h2>
  <div class="panel"><table>
    <thead><tr><th>Ref</th><th>Kind</th><th>Detail</th><th>Phone</th><th>Time</th></tr></thead>
    <tbody>{recent_rows}</tbody>
  </table></div>
</main>
</body></html>"""


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)