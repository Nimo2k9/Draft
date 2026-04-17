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

st.title("🍱 AI Food Analyzer (Cloud + User Tracker)")

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
# 🔐 AUTH SIDEBAR
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

# -------------------------------
# LOGOUT
# -------------------------------
if st.session_state.get("user"):
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.session = None
        st.rerun()

# -------------------------------
# BLOCK IF NOT LOGGED IN
# -------------------------------
user = st.session_state.get("user")

if not user:
    st.warning("🔒 Please login to use the app")
    st.stop()

st.sidebar.success(f"Logged in as: {user.email}")


# -------------------------------
# FILE UPLOAD
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

        st.success(f"Detected foods: {', '.join(foods)}")

        all_data = []

        for food in foods:
            nutrition = get_nutrition(food)

            if nutrition:
                nutrition["Food"] = food
                all_data.append(nutrition)

        if all_data:
            df = pd.DataFrame(all_data)
            total = df[["Calories","Protein","Fat","Carbs"]].sum()

            # SAVE TO SESSION
            st.session_state.df = df
            st.session_state.total = total


# -------------------------------
# DISPLAY RESULTS
# -------------------------------
if st.session_state.df is not None:

    df = st.session_state.df
    total = st.session_state.total

    st.subheader("📊 Nutrition Table")
    st.dataframe(df)

    # DOWNLOAD
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Nutrition Report", csv, "nutrition.csv")

    # TOTALS
    st.subheader("🔥 Total Nutrition")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Calories", int(total["Calories"]))
    col2.metric("Protein", int(total["Protein"]))
    col3.metric("Fat", int(total["Fat"]))
    col4.metric("Carbs", int(total["Carbs"]))

    # CALORIE GOAL
    goal = st.number_input("🎯 Daily Calorie Goal", value=2000)

    progress = total["Calories"] / goal if goal else 0
    st.progress(min(progress, 1.0))
    st.write(f"{int(total['Calories'])} / {goal} kcal ({int(progress*100)}%)")

    # WARNINGS
    if total["Calories"] > 800:
        st.warning("⚠️ High calorie meal!")

    if total["Protein"] < 10:
        st.info("💡 Low protein meal")

    # PER FOOD DISPLAY
    st.subheader("🍽 Per Food Calories")
    for food, cal in zip(df["Food"], df["Calories"]):
        st.write(f"{food} → {int(cal)} kcal")

    # -------------------------------
    # SAVE TO DATABASE (NO user_id!)
    # -------------------------------
    if st.button("💾 Save Meal to Database"):
        for _, row in df.iterrows():
            insert_meal(
                row["Food"],
                row["Calories"],
                row["Protein"],
                row["Fat"],
                row["Carbs"]
            )
        st.success("✅ Saved to your account!")

    # BAR CHART
    st.subheader("📊 Macronutrients Bar Chart")
    fig, ax = plt.subplots()
    ax.bar(total.index, total.values)
    st.pyplot(fig)

    # PIE CHART
    st.subheader("🥧 Macronutrients Distribution")
    fig2, ax2 = plt.subplots()
    ax2.pie(total.values, labels=total.index, autopct='%1.1f%%')
    st.pyplot(fig2)


# -------------------------------
# USER HISTORY (RLS HANDLES FILTER)
# -------------------------------
st.divider()
st.subheader("📚 Your Meal History")

history = get_meals()

if history:
    df_hist = pd.DataFrame(history)

    for _, row in df_hist.iterrows():

        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            # -----------------------
            # DISPLAY
            # -----------------------
            with col1:
                st.write(f"🍽 {row['food']}")
                st.write(f"🔥 {int(row['calories'])} kcal | "
                         f"P: {row['protein']} | "
                         f"F: {row['fat']} | "
                         f"C: {row['carbs']}")

            # -----------------------
            # DELETE BUTTON
            # -----------------------
            with col2:
                if st.button("🗑️ Delete", key=f"del_{row['id']}"):
                    delete_meal(row["id"])
                    st.success("Deleted!")
                    st.rerun()

            # -----------------------
            # EDIT BUTTON
            # -----------------------
            with col3:
                if st.button("✏️ Edit", key=f"edit_{row['id']}"):
                    st.session_state.edit_id = row["id"]
                    st.session_state.edit_data = row

    # -------------------------------
    # EDIT FORM
    # -------------------------------
    if "edit_id" in st.session_state:

        st.subheader("✏️ Edit Meal")

        edit = st.session_state.edit_data

        calories = st.number_input("Calories", value=float(edit["calories"]))
        protein = st.number_input("Protein", value=float(edit["protein"]))
        fat = st.number_input("Fat", value=float(edit["fat"]))
        carbs = st.number_input("Carbs", value=float(edit["carbs"]))

        if st.button("💾 Update Meal"):
            update_meal(
                st.session_state.edit_id,
                calories,
                protein,
                fat,
                carbs
            )

            st.success("Updated!")
            del st.session_state.edit_id
            del st.session_state.edit_data
            st.rerun()

else:
    st.info("No meals saved yet.")
