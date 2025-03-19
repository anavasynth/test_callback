from flask import Flask , render_template , request , jsonify
from liqpay import LiqPay
import hashlib
import base64
import json
import os
import uuid


app = Flask(__name__)

# Ваші ключі LiqPay
LIQPAY_PUBLIC_KEY = "sandbox_i82004666388"
LIQPAY_PRIVATE_KEY = "sandbox_2bZ5yQJd7LtJrz7JTz6D3LiuziFpCiN9rT7PLQDZ"

@app.route("/pay" , methods = ["GET"])
def pay():
    order_id = str(uuid.uuid4())
    liqpay = LiqPay(LIQPAY_PUBLIC_KEY , LIQPAY_PRIVATE_KEY)
    params = {
        "action": "pay" ,
        "amount": "100" ,
        "currency": "USD" ,
        "description": "Payment for clothes" ,
        "order_id": order_id ,
        "version": "3" ,
        "sandbox": 0 ,  # Використовуємо тестовий режим
        "server_url": "https://sockswebapp.onrender.com/pay-callbac"
    }
    signature = liqpay.cnb_signature(params)
    data = liqpay.cnb_data(params)

    return render_template("pay.html" , data = data , signature = signature)


@app.route("/pay-callback" , methods = ["POST"])
def pay_callback():
    liqpay = LiqPay(LIQPAY_PUBLIC_KEY , LIQPAY_PRIVATE_KEY)

    data = request.form.get("data")
    signature = request.form.get("signature")

    # Генеруємо підпис для перевірки коректності даних
    calculated_signature = base64.b64encode(
        hashlib.sha1((LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY).encode()).digest()
    ).decode()

    if calculated_signature == signature:
        response = json.loads(base64.b64decode(data).decode("utf-8"))
        print("✅ Callback успішний:" , response)
        return jsonify({"status": "success" , "data": response})

    return jsonify({"status": "error" , "message": "Invalid signature"}) , 400


if __name__ == "__main__":
    app.run(debug = True)