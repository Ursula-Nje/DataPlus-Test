# DataPlus-Test

A USSD and SMS service built with Python (Flask) and the Africa's Talking API. Users dial a USSD code to get network help, buy airtime, check their balance, report fraud and contact support. Every request is saved to a database and viewable on a password-protected admin dashboard.

## Features
- **USSD menu** with five options: Network Help, Buy Airtime, Check Balance, Report Fraud, Support
- **SMS confirmations** with ticket or reference numbers after each request
- **SQLite storage** for requests and per-phone balances
- **Admin dashboard** (`/admin`) with summary cards, a 7-day chart, a requests-by-type chart and a latest-requests table. Phone numbers are masked.

## Tech stack
Python, Flask, SQLite, Africa's Talking (USSD and SMS, sandbox)

## Setup
1. Install the dependencies:
```
   pip install -r requirements.txt
```
2. Set two environment variables (never commit these):
   - `AT_API_KEY`: your Africa's Talking sandbox API key
   - `ADMIN_KEY`: a password for the admin dashboard
3. Run the app:
```
   python app.py
```
4. Make port 5000 publicly reachable and set your Africa's Talking USSD callback URL to `https://<your-host>/ussd`.
5. Open the dashboard at `/admin?key=<ADMIN_KEY>`.
docs
dashboard.png
dashboard1.png
dashboard2.png
dashboard3.png
dashboard4.png
dashboard5.png

## Notes
- The balance feature is simulated in the app's own database. It is not connected to a real airtime account.
- This project uses the Africa's Talking sandbox. Going live needs a real shortcode and a production server.