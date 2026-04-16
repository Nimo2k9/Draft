import requests
import os
import streamlit as st
import google.generativeai as genai

def get_secret(key):
    return os.getenv(key) or st.secrets.get(key)

genai.configure(api_key=get_secret("GEMINI_API_KEY"))

# -------------------------------
# MULTI FOOD DETECTION
# -------------------------------
def detect_foods(image_file):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        image_file.seek(0)
        image_bytes = image_file.read()

        response = model.generate_content([
            """Identify all food items in this image accurately.

Rules:
- Use common food names
- Be specific (e.g., chicken biryani, fried rice)
- Return comma-separated list
- No explanation
""",
            {
                "mime_type": image_file.type,
                "data": image_bytes
            }
        ])

        text = response.text.lower().strip()

        foods = [f.strip() for f in text.split(",") if f.strip()]

        return foods

    except Exception as e:
        return [f"error: {str(e)}"]


# -------------------------------
# BANGLADESHI FOOD MAPPING
# -------------------------------
def normalize_food(food):
    mapping = {
        "biryani": "chicken biryani",
        "kacchi": "chicken biryani",
        "khichuri": "rice and lentils",
        "polao": "rice pilaf",
        "pulao": "rice pilaf",
        "hilsa": "fish curry",
        "ilish": "fish curry",
        "beef bhuna": "beef curry",
        "dal": "lentil soup",
        "paratha": "flatbread"
    }

    for key in mapping:
        if key in food:
            return mapping[key]

    return food


# -------------------------------
# USDA NUTRITION
# -------------------------------
def get_nutrition(food):
    try:
        api_key = get_secret("USDA_API_KEY")

        url = "https://api.nal.usda.gov/fdc/v1/foods/search"

        params = {
            "query": food,
            "api_key": api_key
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        foods = data.get("foods")
        if not foods:
            return None

        nutrients = foods[0].get("foodNutrients", [])

        result = {
            "Calories": 0,
            "Protein": 0,
            "Fat": 0,
            "Carbs": 0
        }

        for n in nutrients:
            name = n.get("nutrientName", "").lower()

            if "energy" in name:
                result["Calories"] = n.get("value", 0)
            elif "protein" in name:
                result["Protein"] = n.get("value", 0)
            elif "fat" in name:
                result["Fat"] = n.get("value", 0)
            elif "carbohydrate" in name:
                result["Carbs"] = n.get("value", 0)

        return result

    except:
        return None
