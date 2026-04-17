import streamlit as st
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt

from utils import detect_foods, get_nutrition, normalize_food
from supabase_db import insert_meal, get_meals, delete_meal, update_meal
from auth import sign_up, sign_in, restore_session

# -------------------------------
# RESTORE SESSION
# -------------------------------
restore_session()

# -------------------------------
# CUSTOM CSS
# -------------------------------
st.markdown("""
<style>
.main { background-color: #f8fafc; }

.card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

.metric-card {
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    background: #ffffff;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
}

.title { font-size: 20px; font-weight: bold; }
.subtitle { color: gray; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

st.title("🍱 AI Food Analyzer (Premium Dashboard)")

# -------------------------------
# SESSION STATE
# -------------------------------
if "df" not in st.session_state:
    st.session_state.df = None
if "total" not in st.session_state:
    st.session_state.total = None
if "user" not in st.session_state:
    st.session_state.user = None
if "session" not in st.session_state:
    st.session_state.session = None

# -------------------------------
# AUTH
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
        st.sidebar.success("Account created!")
    except:
        st.sidebar.error("Signup failed")

if st.session_state.get("user"):
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.session = None
        st.rerun()

user = st.session_state.get("user")

if not user:
    st.warning("🔒 Please login to continue")
    st.stop()

st.sidebar.success(f"Logged in as: {user.email}")

# -------------------------------
# SIDEBAR ANALYTICS
# -------------------------------
st.sidebar.markdown("## 📊 Dashboard")

history = get_meals()

if history:
    df_hist = pd.DataFrame(history)

    total_cal = int(df_hist["calories"].sum())
    meal_count = len(df_hist)

    st.sidebar.metric("🔥 Total Calories", total_cal)
    st.sidebar.metric("🍽 Meals Logged", meal_count)

    if "category" in df_hist.columns:
        st.sidebar.markdown("### 🍽 By Category")
        cat_sum = df_hist.groupby("category")["calories"].sum()

        for cat, val in cat_sum.items():
            st.sidebar.write(f"{cat}: {int(val)} kcal")

    if "created_at" in df_hist.columns:
        df_hist["date"] = pd.to_datetime(df_hist["created_at"]).dt.date
        daily = df_hist.groupby("date")["calories"].sum()

        st.sidebar.markdown("### 📈 Trend")
        st.sidebar.line_chart(daily)

else:
    st.sidebar.info("No data yet")

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
            foods = st.text_input("Enter foods").split(",")

        foods = foods[:3]
        foods = [normalize_food(f.strip()) for f in foods]

        all_data = []

        for food in foods:
            nutrition = get_nutrition(food)
            if nutrition:
                nutrition["Food"] = food
                all_data.append(nutrition)

        if all_data:
            df = pd.DataFrame(all_data)
            total = df[["Calories","Protein","Fat","Carbs"]].sum()

            st.session_state.df = df
            st.session_state.total = total

# -------------------------------
# DISPLAY RESULTS
# -------------------------------
if st.session_state.df is not None:

    df = st.session_state.df
    total = st.session_state.total

    st.markdown('<div class="card">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f'<div class="metric-card">🔥<br>{int(total["Calories"])}<br>Calories</div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-card">💪<br>{int(total["Protein"])}<br>Protein</div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="metric-card">🧈<br>{int(total["Fat"])}<br>Fat</div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="metric-card">🍞<br>{int(total["Carbs"])}<br>Carbs</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    category = st.selectbox("Meal Type", ["Breakfast","Lunch","Dinner"])

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
        st.success("Saved!")

# -------------------------------
# HISTORY (CRUD)
# -------------------------------
st.divider()
st.subheader("📚 Your Meals")

if history:
    for _, row in df_hist.iterrows():

        st.markdown('<div class="card">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([4,1,1])

        with col1:
            st.markdown(f"""
            <div class="title">{row['food']}</div>
            <div class="subtitle">{row.get('category','')}</div>
            🔥 {int(row['calories'])} kcal
            """, unsafe_allow_html=True)

        with col2:
            if st.button("🗑️", key=f"d{row['id']}"):
                delete_meal(row["id"])
                st.rerun()

        with col3:
            if st.button("✏️", key=f"e{row['id']}"):
                st.session_state.edit_id = row["id"]
                st.session_state.edit_data = row

        st.markdown('</div>', unsafe_allow_html=True)

    if "edit_id" in st.session_state:
        st.subheader("Edit Meal")

        edit = st.session_state.edit_data

        calories = st.number_input("Calories", value=float(edit["calories"]))
        protein = st.number_input("Protein", value=float(edit["protein"]))
        fat = st.number_input("Fat", value=float(edit["fat"]))
        carbs = st.number_input("Carbs", value=float(edit["carbs"]))

        category = st.selectbox(
            "Category",
            ["Breakfast","Lunch","Dinner"],
            index=["Breakfast","Lunch","Dinner"].index(edit.get("category","Breakfast"))
        )

        if st.button("Update"):
            update_meal(
                st.session_state.edit_id,
                calories,
                protein,
                fat,
                carbs,
                category
            )
            del st.session_state.edit_id
            st.rerun()

else:
    st.info("No meals yet.")
