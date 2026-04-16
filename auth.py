from supabase import create_client
import streamlit as st

def get_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

# -------------------------------
# SIGN UP
# -------------------------------
def sign_up(email, password):
    supabase = get_client()
    return supabase.auth.sign_up({"email": email, "password": password})

# -------------------------------
# LOGIN
# -------------------------------
def sign_in(email, password):
    supabase = get_client()
    return supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

# -------------------------------
# GET USER
# -------------------------------
def get_user():
    supabase = get_client()
    return supabase.auth.get_user()
