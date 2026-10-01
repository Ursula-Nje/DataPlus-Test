from flask import Flask, request
import random
import os
import africastalking

app = Flask(__name__)

africastalking.initialize("sandbox", os.environ["AT_API_KEY"])
sms = africastalking.SMS

AIRTIME_AMOUNTS = {"1": 10, "2": 20, "3": 50, "4": 100}
NETWORK_ISSUES = {"1": "No Network", "2": "Slow Internet", "3": "Calls Dropping"}


def send_sms(phone, message):
    try:
        return sms.send(message, [phone])
    except Exception as e:
        print("SMS failed:", e)


def make_ticket():
    return "MC" + str(random.randint(1000, 9999))


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
            ticket = make_ticket()
            send_sms(
                phone,
                f"Mkononi Connect: your report ({NETWORK_ISSUES[parts[1]]}) "
                f"has been received. Ticket: {ticket}. We will follow up soon.",
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
                ref = "AT" + str(random.randint(100000, 999999))
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
        ticket = make_ticket()
        send_sms(phone, f"Mkononi Connect: fraud report received. Ticket: {ticket}.")
        response = f"END Fraud report received.\nTicket: {ticket}"

    elif parts[0] == "5":
        response = "END For support, please contact our team."

    else:
        response = "END Invalid choice. Please try again."

    return response, 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)