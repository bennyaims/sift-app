import streamlit as st
import base64
import json
from supabase import create_client
from datetime import date, timedelta

st.set_page_config(page_title="SIFT", layout="wide")

st.markdown("""
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#00ff88">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="SIFT">
<link rel="apple-touch-icon" href="icon-192.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js');
  });
}
</script>
""", unsafe_allow_html=True)

# =========================
# LOAD ANZSCO + LOGO
# =========================
@st.cache_data
def load_anzsco():
    with open('anzscoData.json') as f:
        return json.load(f)

@st.cache_data
def load_logo_base64():
    try:
        with open("sift_logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

ANZSCO = load_anzsco()
LOGO_B64 = load_logo_base64()

def render_bg_logo():
    if LOGO_B64:
        st.markdown(f"""
        <style>
        .stApp {{
            background-color: #white;
            position: relative;
        }}
        .stApp::before {{
            content: ""; 
            position: fixed; 
            top: 50%; 
            left: 50%;
            transform: translate(-50%, -50%);
            width: 70vw; 
            height: 70vh; 
            opacity: 0.5;
            background: url(data:image/png;base64,{LOGO_B64}) no-repeat center;
            background-size: contain; 
            z-index: 0; 
            pointer-events: none;
        }}
        [data-testid="stAppViewContainer"] {{
            background-color: transparent;
            position: relative;
            z-index: 1;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0);
        }}
        </style>
        """, unsafe_allow_html=True)

# =========================
# INIT SUPABASE
# =========================
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

db = init_supabase()

# =========================
# SESSION STATE INIT
# =========================
if "page" not in st.session_state: st.session_state.page = "entry"
if "step" not in st.session_state: st.session_state.step = 1
if "worker_data" not in st.session_state: st.session_state.worker_data = {"licences": []}
if "user" not in st.session_state: st.session_state.user = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "feed"

# =========================
# HELPERS
# =========================
def go_to(page): st.session_state.page = page; st.rerun()
def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1
def require_user():
    if not st.session_state.user:
        st.error("You must be logged in."); st.stop()
    return st.session_state.user

render_bg_logo()

# =========================
# ENTRY SCREEN
# =========================
if st.session_state.page == "entry":
    st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    html, body,.stApp { margin: 0; padding: 0; background: black; overflow: hidden; }
 .video-wrap { position: fixed; inset: 0; width: 100vw; height: 100vh; }
    video { width: 100%; height: 100%; object-fit: cover; }
 .enter-box { position: fixed; bottom: 10%; width: 100%; text-align: center; font-size: 22px; color: white; opacity: 0; transition: opacity 1s ease; }
 .enter-box.show { opacity: 1; }
 .triangle { font-size: 40px; display: block; margin-top: 10px; animation: pulse 1.5s infinite; cursor: pointer; }
    @keyframes pulse { 0% {transform: scale(1); opacity: 0.6;} 50% {transform: scale(1.2); opacity: 1;} 100% {transform: scale(1); opacity: 0.6;} }
    </style>
    """, unsafe_allow_html=True)

    video_file = open("sift_animation.mp4", "rb").read()
    video_base64 = base64.b64encode(video_file).decode()

    st.markdown(f"""
    <div class="video-wrap">
        <video id="vid" muted playsinline autoplay>
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
        </video>
    </div>
    <div class="enter-box" id="enterBox">
        Press the triangle to enter
        <span class="triangle" onclick="sendEnter()">▶</span>
    </div>
    <script>
    const vid = document.getElementById("vid");
    const enter = document.getElementById("enterBox");
    function tryPlay() {{ let p = vid.play(); if (p!== undefined) {{ p.catch(() => {{ document.body.addEventListener('click', () => vid.play(), {{ once: true }}); }}); }} }}
    tryPlay();
    vid.onended = () => {{ enter.classList.add("show"); }}
    setTimeout(() => enter.classList.add("show"), 6000);
    function sendEnter() {{ window.parent.postMessage({{type: "ENTER"}}, "*"); }}
    </script>
    """, unsafe_allow_html=True)

    from streamlit.components.v1 import html
    html("""
    <script>
    window.addEventListener("message", (event) => {
        if (event.data.type === "ENTER") {
            const btn = window.parent.document.getElementById("hidden-enter");
            if (btn) btn.click();
        }
    });
    </script>
    """, height=0)

    if st.button("enter", key="hidden-enter"): go_to("login")

# =========================
# LOGIN
# =========================
elif st.session_state.page == "login":
    st.title("🔐 Welcome to SIFT")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                res = db.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("Logged in")
                go_to("dashboard")
            except Exception as e:
                st.error(f"Login failed: {e}")

    with tab2:
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_pass")
        role = st.selectbox("I am a", ["Worker", "Client"])
        if st.button("Create Account"):
            try:
                res = db.auth.sign_up({
                    "email": new_email,
                    "password": new_password,
                    "options": {"data": {"role": role.lower()}}
                })
                st.session_state.user = res.user
                st.success("Account created. Check email to verify.")
                go_to("worker_onboarding" if role == "Worker" else "dashboard")
            except Exception as e:
                st.error(f"Signup failed: {e}")

# =========================
# WORKER ONBOARDING
# =========================
elif st.session_state.page == "worker_onboarding":
    st.title("Worker Onboarding")
    user = require_user()
    user_id = user.id
    st.progress(st.session_state.step / 5)

    # STEP 1: Account
    if st.session_state.step == 1:
        st.subheader("Step 1: Account Details")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.worker_data["full_name"] = st.text_input("Full Name", value=st.session_state.worker_data.get("full_name", ""))
            st.session_state.worker_data["phone"] = st.text_input("Phone", value=st.session_state.worker_data.get("phone", ""))
        with col2:
            photo = st.file_uploader("Profile Photo", type=["jpg", "png"])
            if photo:
                file_path = f"{user_id}/avatar.{photo.name.split('.')[-1]}"
                db.storage.from_("avatars").upload(file_path, photo.getvalue(), {"upsert": "true"})
                st.session_state.worker_data["avatar_url"] = db.storage.from_("avatars").get_public_url(file_path)
                st.image(photo, width=150)
        st.button("Next", on_click=next_step, type="primary")

    # STEP 2: Industry + Profession - FIXED INDENT
    elif st.session_state.step == 2:
        st.subheader("Step 2: Industry & Trade")
        industries = [x["industry"] for x in ANZSCO]
        selected_ind = st.selectbox(
            "Industry",
            industries,
            index=industries.index(st.session_state.worker_data.get("industry", industries[0])) if st.session_state.worker_data.get("industry") in industries else 0
        )
        st.session_state.worker_data["industry"] = selected_ind

        professions = next((x["professions"] for x in ANZSCO if x["industry"] == selected_ind), [])
        selected_prof = st.selectbox(
            "Profession",
            professions,
            index=professions.index(st.session_state.worker_data.get("profession", professions[0])) if st.session_state.worker_data.get("profession") in professions else 0
        )

        if selected_prof == "Other":
            custom_prof = st.text_input(
                "Enter your profession",
                value=st.session_state.worker_data.get("custom_profession", ""),
                placeholder="e.g. Diamond Driller"
            )
            st.session_state.worker_data["custom_profession"] = custom_prof
            st.session_state.worker_data["profession"] = custom_prof if custom_prof else "Other"
        else:
            st.session_state.worker_data["profession"] = selected_prof
            st.session_state.worker_data["custom_profession"] = ""

        col1, col2 = st.columns(2)
        with col1: st.button("Back", on_click=prev_step)
        with col2:
            if selected_prof == "Other" and not st.session_state.worker_data.get("custom_profession"):
                st.button("Next", disabled=True, help="Enter your profession")
            else:
                st.button("Next", on_click=next_step, type="primary")

    # STEP 3: Experience & Resume
    elif st.session_state.step == 3:
        st.subheader("Step 3: Experience & Resume")
        resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
        if resume:
            if resume.size > 5 * 1024 * 1024:
                st.error("File must be under 5MB")
            else:
                file_path = f"{user_id}/resume.{resume.name.split('.')[-1]}"
                db.storage.from_("resumes").upload(file_path, resume.getvalue(), {"upsert": "true"})
                st.session_state.worker_data["resume_url"] = db.storage.from_("resumes").get_public_url(file_path)
                st.success("Resume uploaded ✓")

        st.session_state.worker_data["bio"] = st.text_area("Short Bio", value=st.session_state.worker_data.get("bio", ""))
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.worker_data["hourly_rate_min"] = st.number_input("Min Rate $/hr", min_value=0.0, step=0.5, value=st.session_state.worker_data.get("hourly_rate_min", 25.0))
        with col2:
            st.session_state.worker_data["hourly_rate_max"] = st.number_input("Max Rate $/hr", min_value=0.0, step=0.5, value=st.session_state.worker_data.get("hourly_rate_max", 35.0))
        col1, col2 = st.columns(2)
        with col1: st.button("Back", on_click=prev_step)
        with col2: st.button("Next", on_click=next_step, type="primary")

    # STEP 4: Tickets / Licences / ABN
    elif st.session_state.step == 4:
        st.subheader("Step 4: Tickets, Licences & ABN")
        st.session_state.worker_data["abn"] = st.text_input("ABN", value=st.session_state.worker_data.get("abn", ""), max_chars=11)
        st.session_state.worker_data["suburb"] = st.text_input("Suburb", value=st.session_state.worker_data.get("suburb", ""))
        st.session_state.worker_data["postcode"] = st.text_input("Postcode", value=st.session_state.worker_data.get("postcode", ""), max_chars=4)
        st.divider()
        with st.form("licence_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1: lic_type = st.selectbox("Type", ["White Card", "HRWL", "First Aid", "Forklift", "EWP", "Other"])
            with col2: lic_number = st.text_input("Licence Number")
            with col3: lic_expiry = st.date_input("Expiry Date", min_value=date.today())
            if st.form_submit_button("Add Licence") and lic_number:
                st.session_state.worker_data["licences"].append({"type": lic_type, "number": lic_number, "expiry": str(lic_expiry)})
                st.success(f"Added {lic_type}")

        if st.session_state.worker_data["licences"]:
            st.write("**Current Licences:**")
            for lic in st.session_state.worker_data["licences"]:
                st.write(f"- {lic['type']}: {lic['number']} ({lic['expiry']})")

        col1, col2 = st.columns(2)
        with col1: st.button("Back", on_click=prev_step)
        with col2: st.button("Next", on_click=next_step, type="primary")

    # STEP 5: Review + Submit
    elif st.session_state.step == 5:
        st.subheader("Step 5: Review & Submit")
        st.json(st.session_state.worker_data)
        col1, col2 = st.columns(2)
        with col1: st.button("Back", on_click=prev_step)
        with col2:
            if st.button("Submit Profile", type="primary"):
                try:
                    db.table('profiles').update({
                        "full_name": st.session_state.worker_data.get('full_name'),
                        "phone": st.session_state.worker_data.get('phone')
                    }).eq("id", user_id).execute()

                    worker_payload = {
                        "profile_id": user_id,
                        "industry": st.session_state.worker_data.get('industry'),
                        "profession": st.session_state.worker_data.get('profession'),
                        "bio": st.session_state.worker_data.get('bio'),
                        "abn": st.session_state.worker_data.get('abn'),
                        "hourly_rate_min": st.session_state.worker_data.get('hourly_rate_min'),
                        "hourly_rate_max": st.session_state.worker_data.get('hourly_rate_max'),
                        "suburb": st.session_state.worker_data.get('suburb'),
                        "postcode": st.session_state.worker_data.get('postcode'),
                        "avatar_url": st.session_state.worker_data.get('avatar_url'),
                        "resume_url": st.session_state.worker_data.get('resume_url'),
                        "is_available": True
                    }
                    db.table('workers').upsert(worker_payload).execute()

                    if st.session_state.worker_data['licences']:
                        lic_data = [{
                            "worker_id": user_id, "licence_type": l['type'],
                            "licence_number": l['number'], "expiry_date": l['expiry']
                        } for l in st.session_state.worker_data['licences']]
                        db.table('worker_licences').upsert(lic_data).execute()

                    st.success("Profile created!")
                    st.balloons()
                    go_to("dashboard")
                except Exception as e:
                    st.error(f"Error: {e}")

# =========================
# DASHBOARD + BOTTOM NAV
# =========================
elif st.session_state.page == "dashboard":
    user = require_user()

    try:
        profile = db.table('profiles').select('role, full_name').eq('id', user.id).single().execute().data
        worker = db.table('workers').select('industry, profession, is_available, hourly_rate_min, hourly_rate_max, avatar_url').eq('profile_id', user.id).single().execute().data
        user_role = profile['role']
        user_industry = worker.get('industry') if worker else None
    except:
        user_role = 'worker'
        user_industry = None

    st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp { padding-bottom: 80px; }

/* Mobile optimizations */
@media (max-width: 768px) {
  .stApp { padding: 0.5rem; }
  .profile-img { height: 300px !important; }
  .stButton button { height: 3rem; font-size: 16px; }
  h1 { font-size: 1.5rem !important; }
}

/* Prevent zoom on input focus iOS */
input, select, textarea { font-size: 16px !important; }

.profile-card { background: #222; border-radius: 20px; padding: 0; margin-bottom: 20px; overflow: hidden; }
.profile-img { width: 100%; height: 400px; object-fit: cover; }
.profile-info { padding: 20px; }
.star-rating { color: #FFD700; font-size: 20px; }
.day-available { background: #00ff88; color: black; padding: 10px; border-radius: 5px; text-align: center; margin: 2px; }
.day-booked { background: #ff4444; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 2px; }
</style>
""", unsafe_allow_html=True)

    if st.session_state.active_tab == "feed":
        st.title(f"🔥 {user_industry} Feed" if user_industry else "🔥 SIFT Feed")
        industries = ["All"] + [x["industry"] for x in ANZSCO]
        feed_filter = st.selectbox("Filter by Industry", industries, index=industries.index(user_industry) if user_industry in industries else 0)

        with st.expander("📸 Post your work"):
            post_content = st.text_area("What's happening on site?")
            post_pic = st.file_uploader("Upload pic", type=['jpg', 'png'], key="post_pic")
            post_industry = st.selectbox("Tag Industry", [x["industry"] for x in ANZSCO], key="post_ind")
            if st.button("Post"):
                try:
                    image_url = None
                    if post_pic:
                        path = f"{user.id}/post_{date.today()}_{post_pic.name}"
                        db.storage.from_('avatars').upload(path, post_pic.getvalue(), {'upsert': "true"})
                        image_url = db.storage.from_('avatars').get_public_url(path)
                    db.table('posts').insert({"user_id": user.id, "content": post_content, "image_url": image_url, "industry": post_industry}).execute()
                    st.success("Posted!"); st.rerun()
                except Exception as e:
                    st.error(f"Post failed: {e}")

        try:
            query = db.table('posts').select('*, profiles(full_name), workers(avatar_url, profession)').order('created_at', desc=True).limit(20)
            if feed_filter!= "All":
                query = query.eq('industry', feed_filter)
            posts = query.execute()
            for post in posts.data:
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if post['workers'] and post['workers'].get('avatar_url'):
                            st.image(post['workers']['avatar_url'], width=50)
                    with col2:
                        st.write(f"**{post['profiles']['full_name']}** | {post['workers']['profession'] if post['workers'] else ''}")
                    if post.get('image_url'): st.image(post['image_url'])
                    st.write(post['content'])
                    st.caption(f"#{post.get('industry', 'General')}")
                    st.divider()
        except:
            st.info("No posts yet. Be the first!")

    elif st.session_state.active_tab == "profile":
        st.title("👤 Profile")
        try:
            worker = db.table('workers').select('*, profiles(full_name)').eq('profile_id', user.id).single().execute().data
            ratings = db.table('ratings').select('*').eq('worker_id', user.id).execute().data
            avg_rating = sum([r['stars'] for r in ratings]) / len(ratings) if ratings else 0

            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            if worker.get('avatar_url'):
                st.markdown(f'<img src="{worker["avatar_url"]}" class="profile-img">', unsafe_allow_html=True)
            st.markdown('<div class="profile-info">', unsafe_allow_html=True)
            st.subheader(f"{worker['profiles']['full_name']} | {worker['profession']}")
            stars = '★' * int(avg_rating) + '☆' * (5 - int(avg_rating))
            st.markdown(f'<div class="star-rating">{stars} ({avg_rating:.1f})</div>', unsafe_allow_html=True)
            st.write(f"**Rate:** ${worker['hourly_rate_min']}-${worker['hourly_rate_max']}/hr")
            st.write(f"**Industry:** {worker['industry']}")

            is_avail = worker.get('is_available', True)
            if st.button("🟢 AVAILABLE" if is_avail else "🔴 UNAVAILABLE", use_container_width=True):
                db.table('workers').update({"is_available": not is_avail}).eq('profile_id', user.id).execute()
                st.rerun()
            st.markdown('</div></div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Complete onboarding first")
            if st.button("Go to Onboarding"): go_to("worker_onboarding")

    elif st.session_state.active_tab == "messages":
        st.title("💬 Messages")
        st.info("Messaging coming soon - Supabase Realtime")

    elif st.session_state.active_tab == "calendar":
        st.title("📅 4 Week Calendar")
        today = date.today()
        start = today - timedelta(days=today.weekday())
        cols = st.columns(7)
        days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        for i, d in enumerate(days):
            with cols[i]: st.write(f"**{d}**")

        for week in range(4):
            cols = st.columns(7)
            for day_idx in range(7):
                day = start + timedelta(days=week*7 + day_idx)
                with cols[day_idx]:
                    st.markdown(f'<div class="day-available">{day.day}</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("Timesheet - Geofenced Clock In")
        st.write("You must be within 100m of site to clock in")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 CLOCK IN", use_container_width=True):
                st.success("Clocked in at 7:32am")
        with col2:
            if st.button("🔴 CLOCK OUT", use_container_width=True):
                st.success("Clocked out at 4:01pm - 8.5hrs logged")

    elif st.session_state.active_tab == "settings":
        st.title("⚙ Settings")
        st.write(f"Logged in as: {user.email}")
        st.write(f"Role: {user_role}")
        if st.button("Log Out", use_container_width=True):
            db.auth.sign_out()
            for key in list(st.session_state.keys()): del st.session_state[key]
            go_to("entry"); st.rerun()

    # --- BOTTOM NAV BAR ---
    nav_cols = st.columns(5)
    tabs = [("feed", "🔥"), ("profile", "👤"), ("messages", "💬"), ("calendar", "📅"), ("settings", "⚙")]
    for i, (tab, icon) in enumerate(tabs):
        with nav_cols[i]:
            if st.button(icon, key=f"nav_{tab}", use_container_width=True):
                st.session_state.active_tab = tab
                st.rerun()