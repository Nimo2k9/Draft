from supabase import create_client
import streamlit as st

# -------------------------------
# CREATE CLIENT (WITH AUTH FIX)
# -------------------------------
def get_client():
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]  # ⚠️ Use ANON KEY
    )

    # 🔥 CRITICAL FIX: attach user session
    session = st.session_state.get("session")

    if session:
        try:
            supabase.postgrest.auth(session.access_token)
        except Exception as e:
            print("Auth attach error:", e)

    return supabase


# -------------------------------
# INSERT MEAL
# -------------------------------
def insert_meal(food, calories, protein, fat, carbs, category):
    supabase = get_client()

    data = {
        "food": str(food),
        "calories": float(calories),
        "protein": float(protein),
        "fat": float(fat),
        "carbs": float(carbs),
        "category": category
        # ❌ DO NOT send user_id (Supabase sets it)
    }

    try:
        return supabase.table("meals").insert(data).execute()
    except Exception as e:
        print("INSERT ERROR:", e)
        raise e


# -------------------------------
# GET MEALS (RLS FILTERED)
# -------------------------------
def get_meals():
    supabase = get_client()

    try:
        response = supabase.table("meals")\
            .select("*")\
            .order("created_at", desc=True)\
            .execute()

        return response.data

    except Exception as e:
        print("FETCH ERROR:", e)
        return []


# -------------------------------
# DELETE MEAL
# -------------------------------
def delete_meal(meal_id):
    supabase = get_client()

    try:
        return supabase.table("meals")\
            .delete()\
            .eq("id", meal_id)\
            .execute()

    except Exception as e:
        print("DELETE ERROR:", e)
        raise e


# -------------------------------
# UPDATE MEAL
# -------------------------------
def update_meal(meal_id, calories, protein, fat, carbs, category):
    supabase = get_client()

    data = {
        "calories": float(calories),
        "protein": float(protein),
        "fat": float(fat),
        "carbs": float(carbs),
        "category": category
    }

    try:
        return supabase.table("meals")\
            .update(data)\
            .eq("id", meal_id)\
            .execute()

    except Exception as e:
        print("UPDATE ERROR:", e)
        raise e
