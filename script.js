let userPhone = "";

function startSession() {

    userPhone = document.getElementById("phoneNumber").value;

    if (userPhone.length < 10) {
        alert("Please enter a valid phone number.");
        return;
    }

    showMenu();
}

function showMenu() {

    document.getElementById("screen").innerHTML = `
        <h3>Mkononi Connect</h3>

        <p>Welcome ${userPhone}</p>

        <div class="ussd-option" onclick="balance()">
            1. Check Balance
        </div>

        <div class="ussd-option" onclick="airtime()">
            2. Buy Airtime
        </div>

        <div class="ussd-option" onclick="services()">
            3. Network Help
        </div>

        <div class="ussd-option" onclick="support()">
            4. Customer Support
        </div>

        <div class="ussd-option" onclick="fraud()">
            5. Report Fraud
        </div>
    `;
}

function balance() {

    document.getElementById("screen").innerHTML = `
        <h3>Account Balance</h3>
        <p>Airtime Balance</p>
        <h2>KES 245.00</h2>

        <p>Data Balance</p>
        <h2>2.4 GB</h2>

        <button class="back" onclick="showMenu()">Back</button>
    `;
}

function airtime() {

    document.getElementById("screen").innerHTML = `
        <h3>Buy Airtime</h3>
        <p>Select amount:</p>

        <div class="ussd-option" onclick="purchase(50)">
            KES 50
        </div>

        <div class="ussd-option" onclick="purchase(100)">
            KES 100
        </div>

        <div class="ussd-option" onclick="purchase(200)">
            KES 200
        </div>

        <button class="back" onclick="showMenu()">Back</button>
    `;
}

function purchase(amount) {

    document.getElementById("screen").innerHTML = `
        <h3>Transaction Successful</h3>

        <p>KES ${amount} airtime has been purchased successfully.</p>

        <p>SMS confirmation sent to ${userPhone}.</p>

        <button onclick="showMenu()">Main Menu</button>
    `;

    increaseTransactions();
}

function services() {

    document.getElementById("screen").innerHTML = `
        <h3>Network Help</h3>

        <p>What problem are you experiencing?</p>

        <div class="ussd-option" onclick="reportIssue('No Network')">
            1. No Network
        </div>

        <div class="ussd-option" onclick="reportIssue('Slow Internet')">
            2. Slow Internet
        </div>

        <div class="ussd-option" onclick="reportIssue('Dropped Calls')">
            3. Calls Dropping
        </div>

        <button class="back" onclick="showMenu()">Back</button>
    `;
}

function reportIssue(problem) {

    let ticket = "MC" + Math.floor(1000 + Math.random() * 9000);

    document.getElementById("screen").innerHTML = `
        <h3>Report Received ✓</h3>

        <p>Your <strong>${problem}</strong> report has been recorded.</p>

        <p>Ticket: <strong>#${ticket}</strong></p>

        <p>You will receive an SMS when there is an update.</p>

        <button onclick="showMenu()">Main Menu</button>
    `;

    increaseSessions();
    increaseSMS();
}

function support() {

    document.getElementById("screen").innerHTML = `
        <h3>Customer Support</h3>

        <p>Our support team is available.</p>

        <p>Call: 100</p>
        <p>SMS: HELP to 123</p>

        <button class="back" onclick="showMenu()">Back</button>
    `;
}

function fraud() {

    document.getElementById("screen").innerHTML = `
        <h3>Report Fraud</h3>

        <p>Have you received a suspicious message or call?</p>

        <div class="ussd-option" onclick="fraudReported()">
            Yes — Report Incident
        </div>

        <button class="back" onclick="showMenu()">Back</button>
    `;
}

function fraudReported() {

    document.getElementById("screen").innerHTML = `
        <h3>Report Submitted ✓</h3>

        <p>Your fraud report has been securely recorded.</p>

        <p>An SMS confirmation has been sent.</p>

        <button onclick="showMenu()">Main Menu</button>
    `;

    increaseSMS();
}

function increaseTransactions() {

    let element = document.getElementById("transactions");

    element.innerText =
        parseInt(element.innerText) + 1;
}

function increaseSessions() {

    let element = document.getElementById("sessions");

    element.innerText =
        parseInt(element.innerText) + 1;
}

function increaseSMS() {

    let element = document.getElementById("sms");

    element.innerText =
        parseInt(element.innerText) + 1;
}