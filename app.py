from flask import Flask, request
import sqlite3
import os
import africastalking
import html
app = Flask(__name__)

africastalking.initialize("sandbox", os.environ["AT_API_KEY"])
sms = africastalking.SMS

DB_FILE = "mkononi.db"

AIRTIME_AMOUNTS = {"1": 10, "2": 20, "3": 50, "4": 100}
NETWORK_ISSUES = {"1": "No Network", "2": "Slow Internet", "3": "Calls Dropping"}


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


def send_sms(phone, message):
    try:
        return sms.send(message, [phone])
    except Exception as e:
        print("SMS failed:", e)


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
                "1. KES 10\n"
                "2. KES 20\n"
                "3. KES 50\n"
                "4. KES 100"
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
                send_sms(
                    phone,
                    f"Mkononi Connect: airtime request of KES {amount} received. "
                    f"Ref: {ref}.",
                )
                response = (
                    f"END Request for KES {amount} airtime received.\n"
                    f"Ref: {ref}\n"
                    "A receipt SMS has been sent."
                )
            elif parts[2] == "2":
                response = "END Purchase cancelled."
            else:
                response = "END Invalid choice. Please try again."
        else:
            response = "END Invalid choice. Please try again."

    # ---- Placeholders ----
    elif parts[0] == "3":
        response = "END Balance check is coming soon."

    elif parts[0] == "4":
        ticket = save_request("MC", "fraud_report", "", phone)
        send_sms(phone, f"Mkononi Connect: fraud report received. Ticket: {ticket}.")
        response = f"END Fraud report received.\nTicket: {ticket}"

    elif parts[0] == "5":
        response = "END For support, please contact our team."

    else:
        response = "END Invalid choice. Please try again."

    return response, 200, {"Content-Type": "text/plain"}

@app.route("/admin")
def admin():
    key = os.environ.get("ADMIN_KEY")
    if not key or request.args.get("key") != key:
        return "Not authorised", 403

    with sqlite3.connect(DB_FILE) as conn:
        total = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        summary = conn.execute(
            "SELECT kind, COALESCE(NULLIF(detail, ''), '-'), COUNT(*) "
            "FROM requests GROUP BY kind, detail ORDER BY COUNT(*) DESC"
        ).fetchall()
        recent = conn.execute(
            "SELECT ref, kind, detail, phone, created_at "
            "FROM requests ORDER BY id DESC LIMIT 20"
        ).fetchall()

    def mask(p):
        return p[:4] + "****" + p[-3:] if p and len(p) > 7 else "****"

    summary_rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{html.escape(d)}</td><td>{n}</td></tr>"
        for k, d, n in summary
    )
    recent_rows = "".join(
        f"<tr><td>{html.escape(str(r))}</td><td>{html.escape(k)}</td>"
        f"<td>{html.escape(d or '-')}</td><td>{html.escape(mask(p))}</td>"
        f"<td>{html.escape(str(t))}</td></tr>"
        for r, k, d, p, t in recent
    )

    return f"""
    <html><head><title>Mkononi Connect Admin</title>
    <style>
      body {{ font-family: sans-serif; margin: 2rem; }}
      table {{ border-collapse: collapse; margin-bottom: 2rem; }}
      th, td {{ border: 1px solid #ccc; padding: 6px 12px; text-align: left; }}
      th {{ background: #f0f0f0; }}
    </style></head><body>
      <h1>Mkononi Connect</h1>
      <h2>Total requests: {total}</h2>
      <h3>By type</h3>
      <table><tr><th>Kind</th><th>Detail</th><th>Count</th></tr>{summary_rows}</table>
      <h3>Latest 20</h3>
      <table><tr><th>Ref</th><th>Kind</th><th>Detail</th><th>Phone</th><th>Time</th></tr>{recent_rows}</table>
    </body></html>
    """

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)