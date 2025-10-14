import streamlit as st
import requests

# ---------------- CONFIG ----------------
API_BASE_URL = "http://127.0.0.1:8000"  # Your FastAPI backend
st.set_page_config(page_title="Auth System", page_icon="🔐", layout="centered")

# ---------------- SESSION STATE SETUP ----------------
if "token" not in st.session_state:
    st.session_state.token = None
if "page" not in st.session_state:
    st.session_state.page = "Login"

# ---------------- HELPER FUNCTIONS ----------------
def api_post(endpoint, data):
    """Reusable POST request handler."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data)
        return response
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def api_get(endpoint, headers=None):
    """Reusable GET request handler."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
        return response
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

# ---------------- PAGE NAVIGATION ----------------
menu = ["Register", "Login"]
if st.session_state.token:
    menu = ["Profile", "Products", "Logout"]
elif st.session_state.page == "Forgot Password":
    menu = ["Forgot Password"]
elif st.session_state.page == "Reset Password":
    menu = ["Reset Password"]

selection = st.sidebar.radio("Navigation", menu)

# ---------------- REGISTER PAGE ----------------
if selection == "Register":
    st.title("📝 Register")

    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Register")

    if submit:
        data = {"name": name, "email": email, "password": password}
        response = api_post("/auth/register", data)
        if response and response.status_code == 200:
            st.success("✅ Registration successful! Check your email for verification link.")
        else:
            st.error(response.json().get("detail", "Registration failed"))

# ---------------- LOGIN PAGE ----------------
elif selection == "Login":
    st.title("🔐 Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        data = {"username": email, "password": password}
        response = api_post("/auth/login", data)
        if response and response.status_code == 200:
            token = response.json()["access_token"]
            st.session_state.token = token
            st.success("✅ Login successful!")
            st.session_state.page = "Profile"
            st.rerun()
        else:
            st.error(response.json().get("detail", "Invalid credentials."))

    # Forgot Password Button
    if st.button("Forgot Password?"):
        st.session_state.page = "Forgot Password"
        st.rerun()

# ---------------- FORGOT PASSWORD PAGE ----------------
elif selection == "Forgot Password":
    st.title("🔑 Forgot Password")

    with st.form("forgot_form"):
        email = st.text_input("Enter your registered email")
        submit = st.form_submit_button("Send Reset Link")

    if submit:
        response = api_post("/auth/forgot-password", {"email": email})
        if response and response.status_code == 200:
            st.success("✅ Reset link sent! Check your email.")
        else:
            st.error(response.json().get("detail", "Failed to send reset link."))

    if st.button("⬅️ Back to Login"):
        st.session_state.page = "Login"
        st.rerun()

# ---------------- RESET PASSWORD PAGE ----------------
elif selection == "Reset Password":
    st.title("🔁 Reset Password")

    with st.form("reset_form"):
        token = st.text_input("Reset Token (from email)")
        new_password = st.text_input("New Password", type="password")
        submit = st.form_submit_button("Reset Password")

    if submit:
        response = api_post("/auth/reset-password", {"token": token, "new_password": new_password})
        if response and response.status_code == 200:
            st.success("✅ Password reset successful!")
            st.session_state.page = "Login"
            st.rerun()
        else:
            st.error(response.json().get("detail", "Reset failed."))

# ---------------- PROFILE PAGE ----------------
elif selection == "Profile":
    st.title("👤 User Profile")

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = api_get("/users/profile", headers=headers)
    if response and response.status_code == 200:
        profile = response.json()
        st.write(f"**Name:** {profile['name']}")
        st.write(f"**Email:** {profile['email']}")
        st.write(f"**Role:** {profile.get('role', 'user')}")
    else:
        st.error("Failed to fetch profile. Please log in again.")
        st.session_state.token = None
        st.session_state.page = "Login"
        st.rerun()

# ---------------- PRODUCTS PAGE ----------------
elif selection == "Products":
    st.title("🛍️ Product List")

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = api_get("/products", headers=headers)
    if response and response.status_code == 200:
        products = response.json()
        for p in products:
            st.subheader(p["name"])
            st.write(f"💲 Price: {p['price']}")
            st.write(f"📦 Stock: {p['stock']}")
            st.divider()
    else:
        st.warning("No products found or access denied.")

# ---------------- LOGOUT PAGE ----------------
elif selection == "Logout":
    st.title("🚪 Logout")

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = api_post("/auth/logout", data={})
    if response and response.status_code == 200:
        st.success("✅ Logged out successfully!")
    else:
        st.warning("Logout request failed or token already invalidated.")

    st.session_state.token = None
    st.session_state.page = "Login"
    st.rerun()
