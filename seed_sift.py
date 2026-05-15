import json
import toml
from supabase import create_client
import random

# =========================
# LOAD SECRETS FROM .streamlit/secrets.toml
# =========================
try:
    secrets = toml.load('.streamlit/secrets.toml')
    SUPABASE_URL = secrets["SUPABASE_URL"]
    SUPABASE_SERVICE_KEY = secrets["SUPABASE_SERVICE_KEY"]  # You need to add this to secrets.toml
except Exception as e:
    print("ERROR: Could not load .streamlit/secrets.toml")
    print("Make sure you have SUPABASE_URL and SUPABASE_SERVICE_KEY in there")
    exit(1)

if not SUPABASE_URL.startswith("https://"):
    print(f"ERROR: Invalid SUPABASE_URL: {SUPABASE_URL}")
    exit(1)

db = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =========================
# ANZSCO DATA
# =========================
ANZSCO = [
  {"industry": "Construction", "professions": ["Carpenter", "Plumber", "Electrician", "Bricklayer", "Labourer"]},
  {"industry": "Mining", "professions": ["Drill Operator", "Shotfirer", "Underground Miner", "Dump Truck Operator", "Maintenance Fitter"]},
  {"industry": "Manufacturing", "professions": ["Machine Operator", "Welder", "Fitter", "Boilermaker", "CNC Machinist"]},
  {"industry": "Transport & Logistics", "professions": ["Truck Driver", "Forklift Operator", "Courier", "Warehouse Operator", "Crane Operator"]},
  {"industry": "Healthcare & Social Assistance", "professions": ["Aged Care Worker", "Disability Support Worker", "Enrolled Nurse", "Personal Care Assistant", "Community Support Worker"]},
  {"industry": "Agriculture", "professions": ["Farm Hand", "Station Hand", "Machinery Operator", "Livestock Worker", "Horticulture Worker"]},
  {"industry": "Hospitality", "professions": ["Chef", "Cook", "Kitchen Hand", "Waitstaff", "Barista"]},
  {"industry": "Civil & Infrastructure", "professions": ["Plant Operator", "Roadworker", "Pipelayer", "Traffic Controller", "Formworker"]},
  {"industry": "Oil & Gas", "professions": ["Rigger", "Scaffolder", "Pipefitter", "Insulator", "Process Technician"]},
  {"industry": "Electrical & Communications", "professions": ["Electrician", "Data Cabler", "Telecommunications Technician", "Lineworker", "Solar Installer"]}
]

SUBURBS = ['Melbourne', 'Sydney', 'Brisbane', 'Perth', 'Adelaide', 'Gold Coast', 'Newcastle', 'Canberra']
POST_CONTENT = [
    "Finished a big job today. Site was chaos but we got it done.",
    "Looking for next gig. Available from Monday. DM me if you need a {profession}.",
    "New gear arrived. This should speed things up.",
    "Sunrise starts hit different. {industry} life.",
    "Knocked off early. Beer time.",
    "Tough day but good crew. That's what matters.",
    "Anyone hiring {profession}s in {suburb}? Hit me up.",
    "Just wrapped up a 12hr shift. Who else is cooked?",
    "Tools down for the week. Weekend starts now.",
    "Client loved the work. That's a win."
]

print(f"Connecting to: {SUPABASE_URL}")
print("Starting SIFT seed...")
created_users = []

for ind_idx, industry_data in enumerate(ANZSCO):
    industry = industry_data["industry"]
    print(f"\n=== {industry} ===")
    
    for prof_idx, profession in enumerate(industry_data["professions"]):
        idx = ind_idx * 5 + prof_idx + 1
        email = f"worker{idx}@demo.com"
        password = "Demo1234!"
        full_name = f"{profession} {idx}"
        
        try:
            # 1. Create auth user
            res = db.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"role": "worker"}
            })
            user_id = res.user.id
            print(f"Created auth: {email}")
            
            # 2. Create profile
            db.table('profiles').insert({
                "id": user_id,
                "role": "worker",
                "full_name": full_name,
                "phone": f"04{random.randint(10000000, 99999999)}"
            }).execute()
            
            # 3. Create worker
            avatar_url = f"https://i.pravatar.cc/400?img={idx}"
            suburb = random.choice(SUBURBS)
            db.table('workers').insert({
                "profile_id": user_id,
                "industry": industry,
                "profession": profession,
                "bio": f"Experienced {profession} with {random.randint(3,15)}+ years in {industry}. Based in {suburb}.",
                "hourly_rate_min": 35 + random.randint(0, 20),
                "hourly_rate_max": 55 + random.randint(0, 30),
                "suburb": suburb,
                "postcode": str(random.randint(3000, 3999)),
                "avatar_url": avatar_url,
                "is_available": random.choice([True, True, False])
            }).execute()
            
            # 4. Create 2 feed posts
            for i in range(2):
                content = random.choice(POST_CONTENT).format(profession=profession, industry=industry, suburb=suburb)
                image_url = f"https://picsum.photos/seed/{user_id}{i}/600/400" if i == 0 else None
                db.table('posts').insert({
                    "user_id": user_id,
                    "content": content,
                    "industry": industry,
                    "image_url": image_url
                }).execute()
            
            # 5. Add rating
            db.table('ratings').insert({
                "worker_id": user_id,
                "client_id": user_id,
                "stars": random.randint(3, 5),
                "comment": random.choice(["Solid worker", "Reliable", "Good bloke", "Turns up on time", "Quality work"])
            }).execute()
            
            created_users.append({"email": email, "industry": industry, "profession": profession})
            print(f"  ✓ {profession}")
            
        except Exception as e:
            print(f"  ✗ Failed {email}: {e}")

print(f"\n=== DONE ===")
print(f"Created {len(created_users)} workers")
print(f"\nLogin with any email: worker1@demo.com to worker50@demo.com")
print(f"Password for all: Demo1234!")