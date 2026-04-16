from supabase import create_client
import streamlit as st

def get_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]   # ⚠️ KEEP anon key
    )

# -------------------------------
# SIGN UP
# -------------------------------
def sign_up(email, password):
    supabase = get_client()
    return supabase.auth.sign_up({
        "email": email,
        "password": password
    })

# -------------------------------
# LOGIN + STORE SESSION
# -------------------------------
def sign_in(email, password):
    supabase = get_client()

    res = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    # ✅ store session
    st.session_state.session = res.session
    st.session_state.user = res.user

    return res


# -------------------------------
# RESTORE SESSION (IMPORTANT)
# -------------------------------
def restore_session():
    session = st.session_state.get("session")

    if session:
        supabase = get_client()

        try:
            supabase.auth.set_session(
                access_token=session.access_token,
                refresh_token=session.refresh_token
            )

            user = supabase.auth.get_user().user
            st.session_state.user = user

        except:
            st.session_state.user = None
