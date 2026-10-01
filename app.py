from flask import Flask, request
import random
import os
import africastalking

app = Flask(__name__)

africastalking.initialize("sandbox", os.environ["AT_API_KEY"])
sms = africastalking.SMS


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

    if text == "":
        response = (
            "CON Welcome to Mkononi Connect\n\n"
            "1. Network Help\n"
            "2. Buy Airtime\n"
            "3. Check Balance\n"
            "4. Report Fraud\n"
            "5. Support"
        )

    # ---- Network Help ----
    elif text == "1":
        response = (
            "CON Network Help\n\n"
            "1. No Network\n"
            "2. Slow Internet\n"
            "3. Calls Dropping"
        )

    elif text in ("1*1", "1*2", "1*3"):
        issues = {
            "1*1": "No Network",
            "1*2": "Slow Internet",
            "1*3": "Calls Dropping",
        }
        ticket = make_ticket()
        send_sms(
            phone,
            f"Mkononi Connect: your report ({issues[text]}) has been received. "
            f"Ticket: {ticket}. We will follow up soon.",
        )
        response = (
            "END Your network problem has been reported.\n"
            f"Ticket: {ticket}\n"
            "A confirmation SMS has been sent."
        )

    # ---- Other menu options (placeholders for now) ----
    elif text == "2":
        response = "END Airtime purchase is coming soon."

    elif text == "3":
        response = "END Balance check is coming soon."

    elif text == "4":
        ticket = make_ticket()
        send_sms(phone, f"Mkononi Connect: fraud report received. Ticket: {ticket}.")
        response = f"END Fraud report received.\nTicket: {ticket}"

    elif text == "5":
        response = "END For support, please contact our team."

    else:
        response = "END Invalid choice. Please try again."

    return response, 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)