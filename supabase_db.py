from supabase import create_client
import streamlit as st

def get_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# -------------------------------
# INSERT MEAL
# -------------------------------
def insert_meal(food, calories, protein, fat, carbs):
    supabase = get_client()

    data = {
        "food": food,
        "calories": float(calories),
        "protein": float(protein),
        "fat": float(fat),
        "carbs": float(carbs)
    }

    supabase.table("meals").insert(data).execute()

# -------------------------------
# FETCH MEALS
# -------------------------------
def get_meals():
    supabase = get_client()

    response = supabase.table("meals").select("*").order("created_at", desc=True).execute()

    return response.data
