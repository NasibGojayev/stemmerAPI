from flask import Flask, request
import requests
import base64, hashlib, json

app = Flask(__name__)

# Simulated private key (replace this with your real one when Epoint gives it)
PRIVATE_KEY = "fake_private_key_123"

@app.route('/')
def index():
    return "✅ Payprocessor backend is running."

@app.route('/payment-result', methods=['POST'])
def payment_result():
    data = request.form.get("data")
    signature = request.form.get("signature")

    if not data or not signature:
        return "❌ Missing data or signature", 400

    # Step 1: Recreate the expected signature
    check_string = PRIVATE_KEY + data + PRIVATE_KEY
    expected_signature = base64.b64encode(
        hashlib.sha1(check_string.encode(), usedforsecurity=False).digest()
    ).decode()

    if signature != expected_signature:
        print("⛔ Signature mismatch!")
        return "❌ Invalid signature", 403

    # Step 2: Decode and parse the base64 data
    try:
        decoded_data = json.loads(base64.b64decode(data).decode())
    except Exception as e:
        print("⛔ Data decoding failed:", str(e))
        return "❌ Invalid data format", 400

    print("✅ Payment verified")
    print("🧾 Data:", decoded_data)

    return f"OK - {decoded_data}", 200

@app.route('/start-payment', methods=['POST'])
def start_payment():
    data = request.get_json()
    amount = data.get('amount')
    order_id = data.get('order_id')
    description = data.get('description', 'No description')

    if not amount or not order_id:
        return {"error": "Missing amount or order_id"}, 400

    public_key = "i000200791"
    private_key = "your_real_private_key"

    payload = {
        "public_key": public_key,
        "amount": amount,
        "currency": "AZN",
        "order_id": order_id,
        "description": description,
        "language": "az",
        "success_redirect_url": "https://whatshop.az/#/success",
        "error_redirect_url": "https://whatshop.az/#/error",
        "result_url": "https://epoint.pythonanywhere.com/payment-result"
    }
    # Here don't forget to change the url to your own (which you assigned as the response reciever)

    try:
        json_string = json.dumps(payload, separators=(',', ':'))
        data_encoded = base64.b64encode(json_string.encode()).decode()
        sign_string = private_key + data_encoded + private_key
        signature = base64.b64encode(
            hashlib.sha1(sign_string.encode()).digest()
        ).decode()

        response = requests.post("https://epoint.az/api/1/request", data={
            "data": data_encoded,
            "signature": signature
        })

        if response.status_code != 200:
            return {
                "error": "Epoint API error",
                "details": response.text,
                "xeta": payload.get("error_redirect_url", "Not found")
            }, 500

        try:
            result = response.json()
        except Exception as parse_error:
            return {
                "error": "Epoint returned invalid JSON",
                "raw": response.text,
                "exception": str(parse_error)
            }, 500

        return {"redirect_url": result.get("redirect_url")}, 200

    except Exception as e:
        return {
            "error": "Exception while creating payment",
            "details": str(e)
        }, 500
