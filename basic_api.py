from flask import Flask, request, jsonify
import requests
import datetime
app = Flask(__name__)

# Veriyi geçici olarak burada saklıyoruz
latest_result = {"message": "Henüz veri gelmedi."}


import json


@app.route('/receive', methods=['POST'])
def receive_from_n8n():
    global latest_result
    data = request.get_json()

    print("Gelen data:", data)

    return jsonify({"data":data}), 200




@app.route('/latest', methods=['GET'])
def get_latest_data():
    return jsonify({"latest_result":latest_result}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
