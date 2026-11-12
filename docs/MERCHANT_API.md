# Payverve Merchant API

Accept payments on your website or app with Payverve. Your buyer pays by bank
transfer from any Nigerian bank app, and the money lands in your Payverve
wallet. Payverve tells your server when an order is paid.

- **Base URL:** `https://api.payverve.ng`
- **Format:** JSON in, JSON out (`Content-Type: application/json`)
- **Currency:** NGN only

---

## Contents

1. [How it works](#1-how-it-works)
2. [Get your keys](#2-get-your-keys)
3. [Create a charge](#3-create-a-charge)
4. [Send the buyer to checkout](#4-send-the-buyer-to-checkout)
5. [Confirm the payment](#5-confirm-the-payment)
6. [Webhooks](#6-webhooks)
7. [Managing your keys and webhook](#7-managing-your-keys-and-webhook)
8. [Errors](#8-errors)
9. [Things to know before going live](#9-things-to-know-before-going-live)
10. [Integration checklist](#10-integration-checklist)

---

## 1. How it works

```
Your server              Payverve                         Buyer
    |                        |                               |
    |-- POST /charges ------>|                               |
    |<-- checkout_url -------|                               |
    |------------------ redirect to checkout_url ----------->|
    |                        |<---- bank transfer -----------|
    |                        |  (charge marked paid)         |
    |<-- webhook charge.paid-|                               |
    |                        |------ back to callback_url -->|
    |-- GET /charges/{ref} ->|                               |
    |<-- paid: true ---------|                               |
    |  ship the order                                        |
```

1. Your **server** creates a **charge** for an order, using your secret key.
2. You send the buyer to the `checkout_url` in the response. It shows the
   amount, the account to transfer to, and a 30-minute countdown.
3. The buyer transfers the money. The checkout page notices within seconds,
   shows "Payment received", and sends the buyer back to your `callback_url`.
4. Payverve posts a signed `charge.paid` **webhook** to your server.
5. Your server **verifies** the charge with `GET /charges/{reference}` before
   it delivers anything.

> **The one rule:** only ever treat an order as paid after your *server* gets
> `"paid": true` from `GET /charges/{reference}`, or a webhook whose signature
> you have checked. A buyer landing on your `callback_url` proves nothing:
> anyone can type that URL.

---

## 2. Get your keys

You need a Payverve account with KYC completed (BVN, NIN and address in the
Payverve app). KYC gives you the bank account your buyers pay into. Without
it, your checkout cannot accept bank transfers.

### 2.1 Sign in

```bash
curl -X POST https://api.payverve.ng/user-login \
  -H "Content-Type: application/json" \
  -d '{"email_address": "you@example.com", "password": "your-password"}'
```

Copy `data.access_token` from the response. It is short-lived, so use it
straight away and sign in again when a call answers `401`.

### 2.2 Register your shop

```bash
curl -X POST https://api.payverve.ng/merchants \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "business_name": "Kebi Stores",
        "webhook_url": "https://kebistores.com/payverve/webhook"
      }'
```

`webhook_url` is optional. Leave it out if you will only confirm payments by
calling `GET /charges/{reference}`.

**Response `201`:**

```json
{
  "code": 201,
  "status_message": "created",
  "message": "merchant profile created",
  "data": {
    "merchant_id": "6f1c…",
    "business_name": "Kebi Stores",
    "public_key": "pk_live_…",
    "secret_key": "sk_live_…",
    "webhook_url": "https://kebistores.com/payverve/webhook",
    "webhook_secret": "whsec_…",
    "notice": "store the secret key and webhook secret now; neither can be shown again"
  }
}
```

| Key | What it is for | Where it may live |
|---|---|---|
| `public_key` (`pk_…`) | Identifies your shop. Not needed for any call today. | Anywhere |
| `secret_key` (`sk_…`) | Authenticates your server when it creates and checks charges. | **Your server only**, in an environment variable |
| `webhook_secret` (`whsec_…`) | Lets you check that a webhook really came from Payverve. | **Your server only** |

> **Store `secret_key` and `webhook_secret` now.** Payverve keeps only a hash
> of the secret key and cannot show either again. If you lose one, replace it
> (see [section 7](#7-managing-your-keys-and-webhook)).
>
> Never put the secret key in a browser, a mobile app, a public repository,
> or a chat message. Anyone holding it can create charges as your shop.

### 2.3 Check your profile

```bash
curl https://api.payverve.ng/merchants/me \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "code": 200,
  "status_message": "success",
  "data": {
    "merchant_id": "6f1c…",
    "business_name": "Kebi Stores",
    "public_key": "pk_live_…",
    "secret_key_preview": "...9f2a",
    "webhook_url": "https://kebistores.com/payverve/webhook",
    "webhook_configured": true,
    "is_active": true,
    "settlement_account_number": "1000137010",
    "settlement_bank": "bellbank microfinance bank"
  }
}
```

If `settlement_account_number` is `null`, finish KYC in the Payverve app
first. Until you do, buyers cannot pay you by transfer.

---

## 3. Create a charge

Create one charge per order, from your server, just before you send the buyer
to pay.

`POST /charges`

**Headers:**
```
Authorization: Bearer sk_live_…
Content-Type: application/json
```

**Body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `reference` | string | yes | Your own ID for this payment, e.g. your order number. Unique per shop. |
| `amount` | string or number | yes | In naira, e.g. `"15250.00"`. Must be greater than 0. |
| `callback_url` | string | no | Where to send the buyer after paying. Must be an `http://` or `https://` URL. |
| `currency` | string | no | `"ngn"`, the default and only supported value. |

```bash
curl -X POST https://api.payverve.ng/charges \
  -H "Authorization: Bearer $PAYVERVE_SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "reference": "ORDER-1042",
        "amount": "15250.00",
        "callback_url": "https://kebistores.com/orders/1042/thanks"
      }'
```

**Response `201`:**

```json
{
  "code": 201,
  "status_message": "created",
  "data": {
    "charge_code": "_74duiqegQWs8d2RcGJADJpu",
    "reference": "ORDER-1042",
    "amount": "15250.00",
    "currency": "NGN",
    "status": "pending",
    "method": null,
    "business_name": "Kebi Stores",
    "expires_at": "2026-11-12T14:35:10.123456",
    "seconds_remaining": 1800,
    "checkout_url": "https://api.payverve.ng/pay/_74duiqegQWs8d2RcGJADJpu"
  }
}
```

- A charge stays payable for **30 minutes**. After that its `status` becomes
  `expired` and it can no longer be paid.
- `expires_at` is in UTC, without a timezone suffix.

### Sending the same reference twice

Creating a charge is **idempotent on `reference`**. If your request times out
and you send it again, you get the *same* charge back rather than a second
one, so the buyer can never pay twice for one order.

This also means:

- Sending an existing `reference` with a **different amount** returns the
  original charge with the **original amount**. If the basket changes, use a
  new reference.
- An **expired** charge comes back with `seconds_remaining: 0` and cannot be
  paid. To let the buyer try again, create a new charge with a new
  reference, e.g. `ORDER-1042-2`.

---

## 4. Send the buyer to checkout

Redirect the buyer's browser to `checkout_url`, or open it in a new tab or a
WebView.

The page shows:

- your business name, the amount and your order reference;
- the account number and bank to transfer to, with copy buttons;
- a countdown until the charge expires;
- "Payment received" once the transfer lands, then a redirect back to you
  after about 4 seconds.

The buyer returns to your `callback_url` with two query parameters added:

```
https://kebistores.com/orders/1042/thanks?reference=ORDER-1042&charge_code=_74duiqegQWs8d2RcGJADJpu
```

Use `reference` to look up the order, then **verify it from your server**
(next section) before you show "Order confirmed". If the buyer arrives but
the charge is not yet paid, show "We're confirming your payment" and check
again.

If you want to build your own payment screen instead, the same information is
available as JSON at `GET /checkout/{charge_code}`. It needs no authentication
and returns this one charge only, including a `bank_transfer` object with
`account_number`, `bank_name` and `available`.

---

## 5. Confirm the payment

`GET /charges/{reference}`

```bash
curl https://api.payverve.ng/charges/ORDER-1042 \
  -H "Authorization: Bearer $PAYVERVE_SECRET_KEY"
```

**Response `200`:**

```json
{
  "code": 200,
  "status_message": "success",
  "data": {
    "charge_code": "_74duiqegQWs8d2RcGJADJpu",
    "reference": "ORDER-1042",
    "amount": "15250.00",
    "currency": "NGN",
    "status": "paid",
    "method": "transfer",
    "business_name": "Kebi Stores",
    "expires_at": "2026-11-12T14:35:10.123456",
    "seconds_remaining": 1210,
    "paid": true,
    "paid_at": "2026-11-12T14:15:52.004211",
    "settlement_reference": "000013241112141550000123456789"
  }
}
```

| `status` | Meaning | What to do |
|---|---|---|
| `pending` | Not paid yet, still inside the 30 minutes. | Wait. Check again shortly. |
| `paid` | Money received. `paid` is `true`. | Deliver the order. |
| `expired` | Not paid within 30 minutes. | Cancel the order, or create a new charge with a new reference. |

Before delivering, also check that `amount` is what you expect for that order.

`method` is `transfer` for a bank transfer and `wallet` for a payment from a
Payverve balance. `settlement_reference` identifies the money movement. Keep
it in case you need to raise a query with Payverve.

**Example: Node.js (18+)**

```js
async function isPaid(reference, expectedAmount) {
  const res = await fetch(
    `https://api.payverve.ng/charges/${encodeURIComponent(reference)}`,
    { headers: { Authorization: `Bearer ${process.env.PAYVERVE_SECRET_KEY}` } }
  );
  if (!res.ok) return false;
  const { data } = await res.json();
  return data.paid === true && data.amount === expectedAmount;
}
```

**Example: PHP**

```php
function payverve_is_paid(string $reference, string $expectedAmount): bool {
    $ch = curl_init('https://api.payverve.ng/charges/' . rawurlencode($reference));
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . getenv('PAYVERVE_SECRET_KEY')],
        CURLOPT_TIMEOUT => 15,
    ]);
    $body = curl_exec($ch);
    $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($status !== 200) return false;
    $data = json_decode($body, true)['data'] ?? [];
    return ($data['paid'] ?? false) === true && ($data['amount'] ?? '') === $expectedAmount;
}
```

**Example: Python**

```python
import os, requests

def is_paid(reference: str, expected_amount: str) -> bool:
    r = requests.get(
        f"https://api.payverve.ng/charges/{reference}",
        headers={"Authorization": f"Bearer {os.environ['PAYVERVE_SECRET_KEY']}"},
        timeout=15,
    )
    if r.status_code != 200:
        return False
    data = r.json()["data"]
    return data["paid"] is True and data["amount"] == expected_amount
```

---

## 6. Webhooks

If you set a `webhook_url`, Payverve sends a `POST` to it when a charge is
paid, so you don't have to keep checking.

### 6.1 The request

**Headers:**
```
Content-Type: application/json
X-Payverve-Event: charge.paid
X-Payverve-Signature: 5d41402abc4b2a76b9719d911017c592…
```

**Body:**
```json
{"data":{"amount":"15250.00","charge_code":"_74duiqegQWs8d2RcGJADJpu","currency":"NGN","method":"transfer","paid_at":"2026-11-12T14:15:52.004211","reference":"ORDER-1042","settlement_reference":"000013241112141550000123456789","status":"paid"},"event":"charge.paid"}
```

### 6.2 Check the signature

`X-Payverve-Signature` is the HMAC-SHA256 of the **raw request body**, using
your `webhook_secret` as the key, as lowercase hex.

- Compute it over the **exact bytes you received**, before any JSON parsing.
  Re-encoding the JSON changes the bytes and the signature will not match.
- Compare with a **constant-time** function.
- If it does not match, answer `401` and ignore the request.

**Node.js (Express)**

```js
const crypto = require('crypto');
const express = require('express');
const app = express();

app.post('/payverve/webhook',
  express.raw({ type: 'application/json' }),   // raw body, not express.json()
  async (req, res) => {
    const expected = crypto
      .createHmac('sha256', process.env.PAYVERVE_WEBHOOK_SECRET)
      .update(req.body)                         // a Buffer of the exact bytes
      .digest('hex');
    const given = req.get('X-Payverve-Signature') || '';

    const ok = given.length === expected.length &&
      crypto.timingSafeEqual(Buffer.from(given), Buffer.from(expected));
    if (!ok) return res.status(401).end();

    const event = JSON.parse(req.body.toString('utf8'));
    if (event.event === 'charge.paid') {
      await markOrderPaid(event.data.reference, event.data.amount); // idempotent!
    }
    res.status(200).end();
  });
```

**PHP**

```php
$raw = file_get_contents('php://input');
$expected = hash_hmac('sha256', $raw, getenv('PAYVERVE_WEBHOOK_SECRET'));
$given = $_SERVER['HTTP_X_PAYVERVE_SIGNATURE'] ?? '';

if (!hash_equals($expected, $given)) {
    http_response_code(401);
    exit;
}

$event = json_decode($raw, true);
if ($event['event'] === 'charge.paid') {
    mark_order_paid($event['data']['reference'], $event['data']['amount']); // idempotent!
}
http_response_code(200);
```

**Python (Flask)**

```python
import hashlib, hmac, os
from flask import Flask, request, abort

app = Flask(__name__)

@app.post("/payverve/webhook")
def payverve_webhook():
    raw = request.get_data()  # exact bytes
    expected = hmac.new(os.environ["PAYVERVE_WEBHOOK_SECRET"].encode(),
                        raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, request.headers.get("X-Payverve-Signature", "")):
        abort(401)

    event = request.get_json()
    if event["event"] == "charge.paid":
        mark_order_paid(event["data"]["reference"], event["data"]["amount"])  # idempotent!
    return "", 200
```

### 6.3 Answer quickly, and handle repeats

- Return any **2xx** status within 15 seconds. Do slow work, like sending
  emails, after you respond.
- Anything else (a non-2xx answer, a timeout, a redirect) counts as a failed
  attempt. Payverve tries up to six times in all, backing off from a few
  minutes to an hour apart (roughly 1h45m in total). Payverve does not follow
  redirects, so give the final URL.
- You may get the **same event more than once**. Make "mark order paid" safe
  to run twice: check whether the order is already paid first.
- If every attempt fails, Payverve stops trying. The charge is still `paid`,
  and `GET /charges/{reference}` will say so. Webhooks are a convenience, and
  that endpoint is the source of truth.

### 6.4 Webhook URL rules

- It must be `https://`.
- It must be a public address. `localhost`, private network addresses
  (`10.x`, `192.168.x`, `172.16–31.x`), `127.0.0.1` and similar are refused.
- To test webhooks on your own computer, use a tunnel such as ngrok or
  Cloudflare Tunnel, which gives you a public `https` URL.

---

## 7. Managing your keys and webhook

These calls use your Payverve login (`Authorization: Bearer <access_token>`
from `/user-login`), and **each needs your transaction PIN** in the body. A
wrong PIN changes nothing.

### Replace the secret key

Use this if the key is lost or may have leaked.

```bash
curl -X POST https://api.payverve.ng/merchants/me/secret-key \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"transaction_pin": "123456"}'
```

The response contains the new `secret_key`, shown once. **The old key stops
working immediately**, so update your server straight away. `public_key` does
not change.

### Replace the webhook secret

```bash
curl -X POST https://api.payverve.ng/merchants/me/webhook-secret \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"transaction_pin": "123456"}'
```

The response contains the new `webhook_secret`, shown once. From now on,
every webhook is signed with it, including retries that were already waiting.

### Change or remove the webhook URL

```bash
curl -X PUT https://api.payverve.ng/merchants/me/webhook \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"transaction_pin": "123456", "webhook_url": "https://kebistores.com/payverve/webhook"}'
```

Send `"webhook_url": null` to stop webhooks and rely on
`GET /charges/{reference}` only. Events already queued still go to the
address that was set when they happened.

---

## 8. Errors

Every error has the same shape:

```json
{
  "code": 400,
  "status_message": "bad request",
  "message": "amount must be greater than zero"
}
```

| HTTP | When |
|---|---|
| `400` | Missing or invalid input, e.g. no `reference`, a bad `amount`, an invalid `callback_url` or `webhook_url`, or a wrong transaction PIN. Read `message`. |
| `401` | Missing, wrong or replaced secret key. The message is the same in every case on purpose. |
| `404` | No charge with that reference for your shop, or no merchant profile on your account. |
| `409` | A merchant profile already exists for this account. |
| `410` | Paying an expired charge from a Payverve balance. (`GET /charges/{reference}` never returns 410; it returns `200` with `status: "expired"`.) |
| `500` | Something went wrong on Payverve's side. Retry later. Retrying `POST /charges` with the same `reference` is safe. |

---

## 9. Things to know before going live

**There is no test mode yet.** Every key is a live key and every payment
moves real money. Test with a small amount, e.g. ₦100, and a real bank
transfer.

**The buyer must send the exact amount, in one transfer.** Every charge for
your shop is paid into the same account number, and a bank transfer carries
no order reference. Payverve matches a transfer to a charge by its amount.
As a result:

- A transfer for a different amount, or split across two transfers, does
  not mark any charge paid. The money still reaches your Payverve wallet.
- If two buyers have open charges for the **same amount** and only one pays,
  Payverve marks the **older** charge paid. That can be the wrong buyer.
  Busy shops should make amounts differ slightly, for example by adding a few
  kobo or naira per order, until per-order account numbers are available.
- A transfer that arrives after a charge has expired does not mark it paid.
  The money still reaches your wallet, and you will need to settle with the
  buyer yourself.

**Fees.** The bank's incoming-transfer fee is deducted before the money
reaches your wallet, so your wallet receives slightly less than the charge
amount. The charge itself is matched on the amount the buyer sent.

**The name the buyer sees.** When the buyer enters the account number, their
bank may show the name on your Payverve account rather than your business
name. Tell buyers to expect this. The checkout page already warns them.

---

## 10. Integration checklist

- [ ] KYC is done and `GET /merchants/me` shows a `settlement_account_number`.
- [ ] `secret_key` and `webhook_secret` are in server environment variables,
      not in code, a browser, or a mobile app.
- [ ] Each order attempt gets its own `reference`.
- [ ] The order is marked paid only after `GET /charges/{reference}` returns
      `"paid": true` with the right `amount`, or after a webhook with a valid
      signature.
- [ ] The `callback_url` page verifies from your server. It never trusts the
      redirect on its own.
- [ ] The webhook handler checks the signature on the raw body, returns 2xx
      quickly, and is safe to run twice for the same event.
- [ ] You have done one real end-to-end payment with a small amount.
