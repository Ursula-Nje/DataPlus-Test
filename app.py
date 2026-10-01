from flask import Flask, request
import random

app = Flask(__name__)


@app.route("/ussd", methods=["GET", "POST"])
def ussd():

    text = request.form.get("text", "")

    if text == "":
        response = """CON Welcome to Mkononi Connect

1. Network Help
2. Buy Airtime
3. Check Balance
4. Report Fraud
5. Support"""

    elif text == "1":
        response = """CON Network Help

1. No Network
2. Slow Internet
3. Calls Dropping"""

    elif text == "1*1":
        ticket = "MC" + str(random.randint(1000, 9999))

        response = f"""END Your network problem has been reported.
Ticket: {ticket}"""

    else:
        response = "END Thank you for using Mkononi Connect."

    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)