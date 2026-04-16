import streamlit as st
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt

from utils import detect_foods, get_nutrition, normalize_food
from supabase_db import insert_meal, get_meals

st.title("🍱 AI Food Analyzer V2 (Multi-Food + Charts + Database)")

# -------------------------------
# INIT DATABASE
# -------------------------------
init_db()

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

        # ⚡ limit for performance
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

            st.subheader("📊 Nutrition Table")
            st.dataframe(df)

            # -----------------------
            # DOWNLOAD REPORT
            # -----------------------
            csv = df.to_csv(index=False)
            st.download_button("📥 Download Nutrition Report", csv, "nutrition.csv")

            # -----------------------
            # TOTALS
            # -----------------------
            total = df[["Calories","Protein","Fat","Carbs"]].sum()

            st.subheader("🔥 Total Nutrition")
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Calories", int(total["Calories"]))
            col2.metric("Protein", int(total["Protein"]))
            col3.metric("Fat", int(total["Fat"]))
            col4.metric("Carbs", int(total["Carbs"]))

            # -----------------------
            # CALORIE GOAL
            # -----------------------
            goal = st.number_input("🎯 Daily Calorie Goal", value=2000)

            progress = total["Calories"] / goal if goal else 0
            st.progress(min(progress, 1.0))
            st.write(f"🔥 {int(total['Calories'])} / {goal} kcal ({int(progress*100)}%)")

            # -----------------------
            # SMART WARNINGS
            # -----------------------
            if total["Calories"] > 800:
                st.warning("⚠️ High calorie meal!")

            if total["Protein"] < 10:
                st.info("💡 Low protein meal")

            # -----------------------
            # PER FOOD DISPLAY
            # -----------------------
            st.subheader("🍽 Per Food Calories")
            for food, cal in zip(df["Food"], df["Calories"]):
                st.write(f"{food} → {int(cal)} kcal")

            # -----------------------
            # SAVE TO DATABASE
            # -----------------------
            if st.button("💾 Save Meal to Database"):
                for _, row in df.iterrows():
                    insert_meal(
                        row["Food"],
                        row["Calories"],
                        row["Protein"],
                        row["Fat"],
                        row["Carbs"]
                    )
                st.success("✅ Saved to database!")

            # -----------------------
            # BAR CHART
            # -----------------------
            st.subheader("📊 Macronutrients Bar Chart")

            fig, ax = plt.subplots()
            ax.bar(total.index, total.values)
            st.pyplot(fig)

            # -----------------------
            # PIE CHART
            # -----------------------
            st.subheader("🥧 Macronutrients Distribution")

            fig2, ax2 = plt.subplots()
            ax2.pie(total.values, labels=total.index, autopct='%1.1f%%')
            st.pyplot(fig2)


# -------------------------------
# DATABASE HISTORY SECTION
# -------------------------------
st.divider()
st.subheader("📚 Saved Meal History")

history = get_meals()

if history:
    import pandas as pd
    df_hist = pd.DataFrame(history)

    st.dataframe(df_hist)

    st.subheader("📈 Calories Over Time")
    st.line_chart(df_hist["calories"])
else:
    st.info("No saved data yet.")
