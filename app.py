from flask import Flask, request, jsonify, render_template
import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Environment variables yükle
load_dotenv()

# MongoDB bağlantısı 
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

# Veritabanı ve koleksiyon seç
db = client["proje13"]
collection = db["proje13"]

app = Flask(__name__)

# Azure bilgilerini environment variables'dan al
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AZURE_API_KEY}"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        payload = {
            "input_data": {
                "columns": [
                    "Pregnancies",
                    "Glucose",
                    "BloodPressure",
                    "SkinThickness",
                    "Insulin",
                    "BMI",
                    "DiabetesPedigreeFunction",
                    "Age"
                ],
                "index": [0],
                "data": [[
                    data["pregnancies"],
                    data["glucose"],
                    data["bloodPressure"],
                    data["skinThickness"],
                    data["insulin"],
                    data["bmi"],
                    data["diabetesPedigreeFunction"],
                    data["age"]
                ]]
            }
        }

        response = requests.post(AZURE_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list):
            prediction = result[0]
            probability = None
        elif isinstance(result, dict) and "result" in result:
            prediction = result["result"][0].get("predicted_label")
            probability = result["result"][0].get("probability")
        else:
            return jsonify({"error": "Beklenmeyen yanıt formatı", "received_response": result}), 500

        # MongoDB'ye veriyi kaydet
        save_data = {
            "input": payload["input_data"]["data"][0],
            "prediction": prediction,
            "probability": probability
        }
        collection.insert_one(save_data)

        return jsonify({
            "prediction": prediction,
            "probability": probability
        })

    except requests.exceptions.RequestException as e:
        print("API İsteği Hatası:", str(e))
        return jsonify({"error": f"API isteği başarısız: {str(e)}"}), 500
    except Exception as e:
        print("Hata oluştu:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)