import streamlit as st
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from utils import detect_foods, get_nutrition, normalize_food
from supabase_db import insert_meal, get_meals, delete_meal, update_meal
from auth import sign_up, sign_in, restore_session

# -------------------------------
# RESTORE SESSION
# -------------------------------
restore_session()

st.title("🍱 AI Food Analyzer (SaaS Version)")

# -------------------------------
# SESSION STATE
# -------------------------------
if "df" not in st.session_state:
    st.session_state.df = None

if "total" not in st.session_state:
    st.session_state.total = None

if "foods" not in st.session_state:
    st.session_state.foods = None

# -------------------------------
# AUTH SIDEBAR
# -------------------------------
st.sidebar.title("🔐 Account")

email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    try:
        sign_in(email, password)
        st.sidebar.success("Logged in!")
    except:
        st.sidebar.error("Login failed")

if st.sidebar.button("Sign Up"):
    try:
        sign_up(email, password)
        st.sidebar.success("Account created! Now login.")
    except:
        st.sidebar.error("Signup failed")

# LOGOUT
if st.session_state.get("user"):
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.session = None
        st.rerun()

# BLOCK IF NOT LOGGED IN
user = st.session_state.get("user")

if not user:
    st.warning("🔒 Please login to use the app")
    st.stop()

st.sidebar.success(f"Logged in as: {user.email}")

# -------------------------------
# IMAGE UPLOAD
# -------------------------------
uploaded_file = st.file_uploader("Upload Food Image", type=["jpg","png","jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    image = image.resize((512, 512))
    st.image(image)

    if st.button("Analyze Food"):

        uploaded_file.seek(0)
        foods = detect_foods(uploaded_file)

        if "error" in foods[0]:
            st.warning("⚠️ Detection failed. Enter manually.")
            foods = st.text_input("Enter foods (comma separated)").split(",")

        foods = foods[:3]
        foods = [normalize_food(f.strip()) for f in foods]

        st.session_state.foods = foods
        st.success(f"Detected foods: {', '.join(foods)}")

# -------------------------------
# PORTION-BASED NUTRITION
# -------------------------------
if st.session_state.foods:

    foods = st.session_state.foods
    per100_data = []

    for food in foods:
        nutrition = get_nutrition(food)
        if nutrition:
            nutrition["Food"] = food
            per100_data.append(nutrition)

    if per100_data:
        df_100 = pd.DataFrame(per100_data)

        st.subheader("📊 Nutrition (per 100g)")
        st.dataframe(df_100)

        # Portion input
        st.subheader("⚖️ Enter Portion Size (grams)")
        portions = {}

        for food in foods:
            portions[food] = st.number_input(
                f"{food} (grams)",
                min_value=0,
                value=100,
                step=10,
                key=f"portion_{food}"
            )

        if st.button("Calculate Nutrition"):

            final_data = []
            total_values = {"Calories":0, "Protein":0, "Fat":0, "Carbs":0}

            for _, row in df_100.iterrows():
                food = row["Food"]
                factor = portions[food] / 100

                calories = row["Calories"] * factor
                protein = row["Protein"] * factor
                fat = row["Fat"] * factor
                carbs = row["Carbs"] * factor

                total_values["Calories"] += calories
                total_values["Protein"] += protein
                total_values["Fat"] += fat
                total_values["Carbs"] += carbs

                final_data.append({
                    "Food": food,
                    "Portion (g)": portions[food],
                    "Calories": round(calories,2),
                    "Protein": round(protein,2),
                    "Fat": round(fat,2),
                    "Carbs": round(carbs,2)
                })

            st.session_state.df = pd.DataFrame(final_data)
            st.session_state.total = pd.Series(total_values)

# -------------------------------
# DISPLAY RESULTS
# -------------------------------
if st.session_state.df is not None:

    df = st.session_state.df
    total = st.session_state.total

    st.subheader("📊 Final Nutrition Table")
    st.dataframe(df)

    csv = df.to_csv(index=False)
    st.download_button("📥 Download Nutrition Report", csv, "nutrition.csv")

    st.subheader("🔥 Total Nutrition")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Calories", int(total["Calories"]))
    col2.metric("Protein", int(total["Protein"]))
    col3.metric("Fat", int(total["Fat"]))
    col4.metric("Carbs", int(total["Carbs"]))

    category = st.selectbox(
        "🍽 Select Meal Type",
        ["Breakfast", "Lunch", "Dinner"]
    )

    if st.button("💾 Save Meal"):
        for _, row in df.iterrows():
            insert_meal(
                row["Food"],
                row["Calories"],
                row["Protein"],
                row["Fat"],
                row["Carbs"],
                category
            )
        st.success("✅ Saved to your account!")

    # Charts
    st.subheader("📊 Macronutrients")
    fig, ax = plt.subplots()
    ax.bar(total.index, total.values)
    st.pyplot(fig)

    st.subheader("🥧 Distribution")
    fig2, ax2 = plt.subplots()
    ax2.pie(total.values, labels=total.index, autopct='%1.1f%%')
    st.pyplot(fig2)

# -------------------------------
# HISTORY (FINAL UPDATED)
# -------------------------------
st.divider()
st.subheader("📚 Your Meal History")

history = get_meals()

if history:
    df_hist = pd.DataFrame(history)

    # Sort latest first
    if "created_at" in df_hist.columns:
        df_hist = df_hist.sort_values(by="created_at", ascending=False)

    # Download full history
    st.subheader("📥 Download Full History")
    csv_full = df_hist.to_csv(index=False)
    st.download_button(
        "Download All Meals (CSV)",
        csv_full,
        "meal_history_full.csv"
    )

    # Show last 5
    st.subheader("📚 Recent Meals (Last 5)")
    df_recent = df_hist.head(5)

    for _, row in df_recent.iterrows():

        # FORMAT DATE (FIXED)
        created_at = row.get("created_at")
        try:
            formatted_date = datetime.fromisoformat(str(created_at)).strftime("%d %b %Y, %I:%M %p")
        except:
            formatted_date = "N/A"

        col1, col2, col3 = st.columns([3,1,1])

        with col1:
            st.write(f"🍽 {row['food']} ({row.get('category','-')})")
            st.write(f"🕒 {formatted_date}")
            st.write(f"🔥 {int(row['calories'])} kcal | "
                     f"P:{row['protein']} F:{row['fat']} C:{row['carbs']}")

        with col2:
            if st.button("🗑️", key=f"del_{row['id']}"):
                delete_meal(row["id"])
                st.rerun()

        with col3:
            if st.button("✏️", key=f"edit_{row['id']}"):
                st.session_state.edit_id = row["id"]
                st.session_state.edit_data = row

    # EDIT FORM
    if "edit_id" in st.session_state:

        st.subheader("✏️ Edit Meal")

        edit = st.session_state.edit_data

        calories = st.number_input("Calories", value=float(edit["calories"]))
        protein = st.number_input("Protein", value=float(edit["protein"]))
        fat = st.number_input("Fat", value=float(edit["fat"]))
        carbs = st.number_input("Carbs", value=float(edit["carbs"]))

        category = st.selectbox(
            "Meal Type",
            ["Breakfast","Lunch","Dinner"],
            index=["Breakfast","Lunch","Dinner"].index(edit.get("category","Breakfast"))
        )

        if st.button("💾 Update"):
            update_meal(
                st.session_state.edit_id,
                calories,
                protein,
                fat,
                carbs,
                category
            )

            del st.session_state.edit_id
            del st.session_state.edit_data
            st.success("Updated!")
            st.rerun()

else:
    st.info("No meals saved yet.")
