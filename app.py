import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
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

FILE_URL = "https://dengromko.pythonanywhere.com/static/uploads/users.txt"

# Підключення до Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_path = "hale-mantra-452117-n7-d894ab047cfb.json"
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)

# Відкриття таблиці (заміни "SHEET_ID" на свій)
SHEET_ID = "1MdcrCtHgwuNW8QCAkffdtXvDj6Y18laXLfCyOjsyH_I"
sheet = client.open_by_key(SHEET_ID).worksheet("fixcallback")


# Головна сторінка з формою
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Генерація платежу
@app.route("/pay" , methods = ["POST"])
def pay():
    name = request.form.get("name")
    surname = request.form.get("surname")
    phone = request.form.get("phone")

    # Генеруємо унікальний order_id
    order_id = str(uuid.uuid4())

    liqpay = LiqPay(LIQPAY_PUBLIC_KEY , LIQPAY_PRIVATE_KEY)
    params = {
        "action": "pay" ,
        "amount": "100" ,
        "currency": "USD" ,
        "description": f"Payment for clothes by {name} {surname}" ,
        "order_id": order_id ,
        "version": "3" ,
        "sandbox": 0 ,  # Тестовий режим (0 - для реального платежу)
        "server_url": "https://sockswebapp.onrender.com/pay-callback" ,
    }

    signature = liqpay.cnb_signature(params)
    data = liqpay.cnb_data(params)

    return render_template("pay.html" , data = data , signature = signature , name = name , surname = surname ,
                           phone = phone , order_id = order_id)


# Callback для перевірки платежу
@app.route("/pay-callback" , methods = ["POST"])
def pay_callback():
    data = request.form.get("data")
    signature = request.form.get("signature")

    # Генеруємо підпис для перевірки коректності даних
    calculated_signature = base64.b64encode(
        hashlib.sha1((LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY).encode()).digest()
    ).decode()

    if calculated_signature == signature:
        response = json.loads(base64.b64decode(data).decode("utf-8"))
        print("✅ Callback успішний:" , response)

        # Перевіряємо статус платежу
        if response.get("status") == "success":
            # Отримуємо всі значення з першого стовпця
            first_column_values = sheet.col_values(1)

            # Знаходимо перший порожній рядок
            empty_row_index = None
            for i , value in enumerate(first_column_values):
                if not value:
                    empty_row_index = i + 1  # Індексація в Google Sheets починається з 1
                    break

            # Якщо немає порожніх рядків, додаємо новий рядок в кінець
            if empty_row_index is None:
                empty_row_index = len(first_column_values) + 1

            # Записуємо дані в порожній рядок
            sheet.insert_row([response['status'], response['sender_first_name'], response['sender_last_name']] ,
                             index = empty_row_index)

            logging.info("Платіж успішно записано в таблицю")

        return jsonify({"status": "success" , "data": response})

    return jsonify({"status": "error" , "message": "Invalid signature"}) , 400


if __name__ == "__main__":
    app.run(debug = True)