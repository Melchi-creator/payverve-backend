# Testing deposits and transfers with BellBank's sandbox

Runs the backend on your machine against BellBank's **sandbox**, with its own
local database, so no live money moves and no real customer is touched.

The sandbox does not check IP addresses, so no proxy (Fixie) is needed.

## One-time setup

1. **Sandbox keys.** In the BellBank business portal, go to
   *Settings → API Configuration → Test mode* and generate a Consumer Key and
   Consumer Secret. These are different from the live keys in `.env`.

2. **Sandbox profile.** Copy the template and put the test keys in it:

   ```powershell
   Copy-Item sample.env.sandbox .env.sandbox
   notepad .env.sandbox
   ```

   `.env.sandbox` is gitignored. Anything it does not set comes from `.env`.
   It sets `BELLBANK_SANDBOX=true`, and the app **refuses to start** if
   `BELLBANK_BASEURL` is then not a sandbox URL.

3. **Sandbox database.**

   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -h localhost -p 5433 -U postgres payverve_sandbox
   $env:ENV_FILE = ".env.sandbox"
   flask --app wsgi:payverve db upgrade
   ```

## Each session

```powershell
$env:ENV_FILE = ".env.sandbox"
python server.py
```

The first line printed must be:

```
[config] BELLBANK SANDBOX: BellBank calls go to https://sandbox-baas-api.bellmonie.com; database localhost:5433/payverve_sandbox
```

If it is not there, stop: you are not in the sandbox.

The API is then at `http://localhost:10000`. Point the Postman collection
(`Payverve.postman_collection.json`) or a debug build of the app at it.

## Getting an account number

Register, verify and log in as usual, then complete KYC (BVN, NIN, address).
The BellBank sandbox account is created after the address step.

## Testing a deposit

**Simulated** (always works, no BellBank involved):

```powershell
python scripts\simulate_bellbank_deposit.py <account number> 500 --fee 20
python scripts\simulate_bellbank_deposit.py <account number> 500 --repeat 2
```

The first should credit ₦480 (₦500 less the ₦20 fee) with a "Money Received"
and a "Bank Charge" row. The second sends the same notification twice and must
credit only once.

**Real sandbox notification** (BellBank calls your machine):

1. Expose the local server, e.g. `cloudflared tunnel --url http://localhost:10000`.
2. In the portal's *Test mode* settings, set the Webhook URL to
   `<tunnel url>/bellbank/webhook`.
3. Make a sandbox payment into the account. The first notification is
   rejected and the log prints `this request came from <ip>`: add that IP to
   `BELLBANK_WEBHOOK_IPS` in `.env.sandbox`, restart, and pay again.

## Testing a transfer out

BellBank's sandbox test recipient is bank code `010`, account `1001011000`.

```
POST /local-transfers
{ "bank_code": "010", "account_number": "1001011000", "amount": "100",
  "narration": "sandbox test", "recipient_name": "Test Account",
  "recipient_bank": "Test Bank", "user_id": "<id>", "wallet_id": "<id>" }
```

The wallet is debited before BellBank is called. A refusal refunds it and
answers 400. A transfer the bank accepts is usually `pending` first; if the
outcome cannot be known (network error), the money stays reserved and the log
says to requery the reference rather than refunding.
