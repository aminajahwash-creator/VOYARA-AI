
import os
import json
import sqlite3
from pathlib import Path
from datetime import date, timedelta
import re
from urllib.parse import urlencode, quote_plus

import streamlit as st
from dotenv import load_dotenv

# ==========================================
# VOYARA AI - YOUR PERSONAL TRAVEL CONCIERGE
# ==========================================

load_dotenv()

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "voyara.db"



MODELS = [
    "claude-sonnet-4-6",
]



st.set_page_config(
    page_title="VOYARA AI | Travel Concierge",
    page_icon="✈️",
    layout="wide",
)

# ==========================================
# WEBSITE DESIGN
# ==========================================

st.markdown("""
<style>
:root {color-scheme: dark;}
.stApp {
    background: radial-gradient(ellipse at 85% 2%, rgba(101,89,232,.30), transparent 32%),
                radial-gradient(ellipse at 10% 36%, rgba(51,212,207,.13), transparent 34%),
                linear-gradient(145deg, #0b1232 0%, #111b44 56%, #101935 100%);
    color: #f7f9ff;
}
.block-container {max-width: 1200px; padding-top: 1.8rem; padding-bottom: 3rem;}
h1,h2,h3 {color:#f7f9ff !important; letter-spacing:-.025em;}
p, label {color:#e2e8ff;}
.hero {
    background: linear-gradient(110deg, rgba(101,89,232,.35), rgba(17,27,68,.92) 58%, rgba(51,212,207,.16));
    border:1px solid rgba(161,164,255,.38); border-radius:26px;
    padding:34px 38px; margin-bottom:22px;
    box-shadow:0 18px 55px rgba(0,0,0,.20);
}
.hero h1 {font-size:clamp(34px,5vw,52px); margin-bottom:5px;}
.hero p {color:#dbe5ff; font-size:16px;}
.eyebrow {font-size:12px!important; letter-spacing:.2em; color:#55e5d8!important; font-weight:800;}
.glow {background:linear-gradient(95deg,#f8f9ff,#bcb5ff 52%,#52e7dd);
       -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;}
[data-testid="stChatMessage"], [data-testid="stMetric"] {
    background:rgba(25,37,83,.82); border:1px solid rgba(141,143,231,.27);
    border-radius:17px; padding:12px;
}
[data-testid="stTabs"] button {font-weight:650;}
.stButton > button, .stDownloadButton > button, .stLinkButton > a {
    border-radius:12px; transition:transform .16s ease, box-shadow .16s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {transform:translateY(-1px);}
.stButton > button[kind="primary"], .stFormSubmitButton button[kind="primary"] {
    background:linear-gradient(100deg,#6559e8,#8676f6)!important;
    color:white!important; border:1px solid #a99cff!important;
    box-shadow:0 6px 24px rgba(101,89,232,.22);
}
[data-testid="stForm"], [data-testid="stExpander"] {
    border-radius:18px; border-color:rgba(147,160,240,.30);
}
[data-testid="stProgress"] > div > div {background:linear-gradient(90deg,#6559e8,#33d4cf);}
.section-intro {color:#bfcafa;font-size:15px;margin-top:-6px;}
.mini-label {color:#60e3d8;font-weight:750;letter-spacing:.08em;font-size:12px;}
@media(max-width:640px){.hero{padding:22px}.block-container{padding-top:1rem}}

/* VOYARA 2.1 — motion and interactive polish */
@keyframes auroraFloat {0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
@keyframes gentleEnter {from{opacity:0;transform:translateY(13px)}to{opacity:1;transform:translateY(0)}}
@keyframes glowPulse {0%,100%{box-shadow:0 8px 24px rgba(101,89,232,.20)}50%{box-shadow:0 8px 34px rgba(51,212,207,.22)}}
.hero {animation:gentleEnter .65s ease-out both;position:relative;overflow:hidden;}
.hero:after {content:'✦';position:absolute;right:8%;top:18%;font-size:68px;color:rgba(51,212,207,.18);animation:auroraFloat 5s ease-in-out infinite;pointer-events:none;}
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:5px;scroll-behavior:smooth;}
[data-testid="stTabs"] button[role="tab"] {border-radius:12px 12px 0 0;padding:12px 10px;transition:background .2s,transform .2s,color .2s;}
[data-testid="stTabs"] button[role="tab"]:hover {background:rgba(101,89,232,.22);transform:translateY(-3px);}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {background:rgba(101,89,232,.22);color:#a8fff5!important;}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {animation:gentleEnter .38s ease-out both;}
[data-testid="stFormSubmitButton"] button[kind="primary"],
[data-testid="stButton"] button[kind="primary"],
.stButton button[data-testid="baseButton-primary"] {background:linear-gradient(105deg,#6559e8,#8c67f5,#33bcb9)!important;color:#fff!important;border:1px solid #a99cff!important;animation:glowPulse 3s ease-in-out infinite;}
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {filter:brightness(1.13);transform:translateY(-2px);}
[data-testid="stExpander"] {transition:transform .18s ease,border-color .18s ease;}
[data-testid="stExpander"]:hover {border-color:rgba(51,212,207,.65);}
.voyara-bubble {background:linear-gradient(110deg,rgba(101,89,232,.23),rgba(51,212,207,.10));border:1px solid rgba(129,166,244,.40);border-radius:18px;padding:18px 20px;margin:13px 0 19px;animation:gentleEnter .45s ease-out both;}
.voyara-bubble strong{color:#c7fff7;}
.voyara-step {font-size:12px;letter-spacing:.13em;text-transform:uppercase;color:#66e3d9;font-weight:800;}
@media(prefers-reduced-motion:reduce){.hero,.hero:after,[data-testid="stTabs"] [data-baseweb="tab-panel"],.voyara-bubble,[data-testid="stFormSubmitButton"] button[kind="primary"]{animation:none!important;}*{scroll-behavior:auto!important;}}
</style>
""", unsafe_allow_html=True)


# ==========================================
# OOP CLASSES
# ==========================================

class TravelAssistant:
    """Parent class demonstrating abstraction."""

    def instructions(self):
        raise NotImplementedError(
            "Child classes must provide instructions."
        )


class PlanningAssistant(TravelAssistant):
    """Child class for detailed travel planning."""

    def instructions(self):
        return """
You are VOYARA, an expert personal travel planner.

Create a genuinely useful, destination-specific travel plan.

Include:
1. Trip overview and travel priorities.
2. Day-by-day itinerary with morning, afternoon and evening.
3. Three specific hotel candidates or suitable neighborhoods.
4. Explain why each hotel candidate fits the traveler.
5. Explain what hotel amenities and prices require verification.
6. Flight strategy: direct versus connecting flights.
7. Detailed budget allocation in the traveler-selected currency that adds up correctly.
8. Attractions, food, local transport and practical tips.
9. Mobility options based on preference: self-drive rental, private chauffeur,
   airport transfer or public transport; distinguish estimates from live offers.
10. Respect the traveler's Travel DNA, pace, accessibility, dietary and flight preferences.
11. For each day use a heading like "Day 1 — ..." followed by morning,
    afternoon and evening recommendations with estimated daily spending.
12. Ways to improve the trip without exceeding the budget.

Use clear Markdown headings and specific recommendations.

IMPORTANT:
You have no live hotel, airline or booking API.
Do not invent current prices, availability, ratings,
flight schedules, breakfast inclusions or visa rules.
Label all financial figures as planning estimates.
Never claim a booking or payment was completed.
"""


class ConciergeAssistant(TravelAssistant):
    """Child class for ongoing customer conversations."""

    def instructions(self):
        return """
You are VOYARA, a friendly and intelligent travel concierge.

Talk naturally, like a professional travel agent.

The customer can ask for changes as many times as needed.

Give specific recommendations, alternatives and reasons.
Consider their destination, budget, travel dates and interests.

For hotel requests:
Suggest actual named hotel candidates when reasonably known,
but never pretend to have verified their current availability,
ratings, breakfast policy or prices.

For flight requests:
Explain direct and connecting flight trade-offs.
Never invent live schedules or fares.

For itinerary changes:
Explain the proposed change and budget implications.
Do not claim the stored plan has changed automatically.

Ask no more than one useful follow-up question.

Never pretend to make bookings, approve financing,
contact a hotel, or process a payment.
"""


class EmergencyAssistant(TravelAssistant):
    """Child class for travel emergencies."""

    def instructions(self):
        return """
You are VOYARA's travel emergency assistant.

Be calm, practical and safety-focused.

For immediate danger or serious medical emergencies,
tell the traveler to contact local emergency services now.

Provide clear steps for:
- Lost passports
- Medical emergencies
- Lost baggage
- Missed flights
- Cancelled flights
- Unsafe situations
- Hotel problems

Do not invent emergency phone numbers.
Do not claim to call police, hospitals or embassies.
Do not request payment information.
"""


# ==========================================
# GEMINI AI CONNECTION WITH BACKUP
# ==========================================


@st.cache_resource
def get_ai_client():
    api_key = (
        os.getenv("ANTHROPIC_API_KEY")
        or st.secrets.get("ANTHROPIC_API_KEY", "")
    )
    if not api_key:
        return None

    try:
        from anthropic import Anthropic
        return Anthropic(api_key=api_key, timeout=60.0, max_retries=0)
    except Exception as error:
        print("VOYARA CLAUDE CLIENT ERROR:", error, flush=True)
        return None







def ask_ai(prompt, assistant, max_tokens=1600):
    client = get_ai_client()
    if client is None:
        print("VOYARA CLAUDE ERROR: API client unavailable.", flush=True)
        return None, None

    model = MODELS[0]

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=assistant.instructions(),
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        answer = "\n".join(
            block.text
            for block in response.content
            if block.type == "text"
        ).strip()

        if answer:
            return answer, model

        print("VOYARA CLAUDE ERROR: Empty response.", flush=True)

    except Exception as error:
        print("VOYARA CLAUDE ERROR:", error, flush=True)

    return None, None






# ==========================================
# SQLITE DATABASE
# ==========================================

def connect_db():
    connection = sqlite3.connect(DB_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS voyara_saved_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            destination TEXT NOT NULL,
            trip_json TEXT NOT NULL,
            plan_text TEXT NOT NULL
        )
    """)

    connection.commit()
    return connection


def save_trip(trip, plan):
    with connect_db() as connection:
        connection.execute(
            """
            INSERT INTO voyara_saved_plans
            (destination, trip_json, plan_text)
            VALUES (?, ?, ?)
            """,
            (
                trip["destination"],
                json.dumps(trip),
                plan,
            ),
        )
        connection.commit()


def load_saved_trips():
    with connect_db() as connection:
        return connection.execute(
            """
            SELECT id, created_at, destination,
                   trip_json, plan_text
            FROM voyara_saved_plans
            ORDER BY id DESC
            """
        ).fetchall()


def delete_trip(trip_id):
    with connect_db() as connection:
        connection.execute(
            "DELETE FROM voyara_saved_plans WHERE id = ?",
            (trip_id,),
        )
        connection.commit()


# ==========================================
# TRAVEL AND BUDGET FUNCTIONS
# ==========================================

def trip_summary(trip):
    return f"""
Departure city: {trip["origin"]}
Destination: {trip["destination"]}
Travelers: {trip["travelers"]}
Departure date: {trip["departure"]}
Return date: {trip["return"]}
Total budget: {trip.get("currency", "AED")} {trip["budget"]:,} (denominated in this currency; no FX conversion)
Travel style: {trip["style"]}
Hotel preference: {trip["hotel"]}
Flight preference: {trip["flight"]}
Interests: {", ".join(trip["interests"])}
Travel pace: {trip.get("pace", "Balanced")}
Travel DNA: {trip.get("travel_dna", "Curious Wanderer")}
Top priority: {trip.get("priority", "Best experience")}
Travel party: {trip.get("party_type", "Not specified")}
Flight cabin: {trip.get("cabin", "Economy")}
Dietary and access preferences: {", ".join(trip.get("special_preferences", [])) or "None specified"}
Mobility preference: {trip.get("mobility", "Not specified")}
Airport pickup requested: {"Yes" if trip.get("airport_pickup") else "No"}
Additional requests: {trip["notes"]}
"""


def budget_allocation(budget):
    categories = [
        ("Flights", 30),
        ("Accommodation", 30),
        ("Food", 15),
        ("Attractions", 10),
        ("Local transport", 8),
        ("Emergency reserve", 7),
    ]

    result = []

    for category, percentage in categories:
        amount = round(budget * percentage / 100)
        result.append((category, amount))

    remaining = budget - sum(
        amount for _, amount in result[:-1]
    )

    result[-1] = ("Emergency reserve", remaining)

    return result


def fallback_plan(trip):
    budget = trip["budget"]

    rows = "\n".join(
        f"| {category} | {amount:,} |"
        for category, amount in budget_allocation(budget)
    )

    return f"""
## Your {trip["destination"]} Travel Framework

**Travelers:** {trip["travelers"]}

**Dates:** {trip["departure"]} to {trip["return"]}

**Total budget:** {trip.get("currency", "AED")} {budget:,}

AI-generated destination recommendations are temporarily
unavailable. This is a planning framework, not a verified
hotel or flight search.

### Illustrative Budget

| Category | Estimated amount |
|---|---:|
{rows}

### Mobility Planning

Preferred transportation: **{trip.get("mobility", "Not specified")}**.
Compare provider availability, pickup conditions, insurance and total costs.

### Hotel Planning

Your preference is **{trip["hotel"]}**.

Compare hotel location, total price, cancellation terms,
breakfast policy and transport connections using a
live booking provider.

### Flight Planning

Your preference is **{trip["flight"]}**.

Compare baggage allowance, connections, total travel
time and cancellation conditions.

### Suggested Daily Structure

**Arrival day:** Airport transfer, check-in and nearby activities.

**Middle days:** Group nearby attractions together
and allow time for meals and relaxation.

**Final day:** Check out and allow sufficient time
for the airport transfer.

### Next Step

Try regenerating your trip when the AI service is available
for a detailed destination-specific itinerary.
"""


def fallback_concierge(message, trip):
    text = message.lower()

    destination = (
        trip["destination"]
        if trip else "your destination"
    )

    if any(word in text for word in [
        "emergency", "hospital", "injured",
        "unsafe", "danger", "medical"
    ]):
        return """
**Your safety comes first.**

If someone is in immediate danger or needs urgent
medical attention, contact local emergency services now.

If you are safe, tell me your location and what happened.

VOYARA cannot place emergency calls.
"""

    if any(word in text for word in [
        "hotel", "breakfast", "room", "stay"
    ]):
        return f"""
I can help you evaluate hotels in **{destination}**.

The main factors are location, total cost, breakfast,
cancellation conditions and transport access.

I cannot verify current hotel availability or prices
without a live hotel-search integration.

**Which matters most to you: location, breakfast,
or the lowest total price?**
"""

    if any(word in text for word in [
        "flight", "airline", "direct", "layover"
    ]):
        return """
For flights, compare:

- Total journey time
- Direct versus connecting routes
- Baggage allowance
- Cancellation and change rules
- Total cost

These are comparison criteria, not live flight offers.
"""

    if any(word in text for word in [
        "tabby", "installment", "instalment",
        "payment", "pay later"
    ]):
        return """
VOYARA can estimate installment amounts.

Actual Tabby availability depends on the merchant,
customer eligibility, provider approval and terms.

VOYARA cannot approve financing or process payments.
"""

    return f"""
I can help you improve your **{destination}** trip.

AI personalization is temporarily unavailable.

You can still review your itinerary, budget,
hotel preferences and saved trips.
"""


# ==========================================
# VOYARA 2.0 - TRAVEL INTELLIGENCE
# ==========================================

CURRENCIES = ["AED", "USD", "EUR", "GBP", "SAR"]
MOBILITY_OPTIONS = ["Public transport", "Self-drive rental", "Private chauffeur", "Airport transfer"]


def money(amount, currency="AED"):
    return f"{currency} {amount:,.0f}"


def travel_persona(pace, interest, priority):
    if interest == "Luxury & Relaxation":
        return "The Elegant Explorer"
    if interest == "Adventure & Discovery":
        return "The Bold Discoverer"
    if pace == "Relaxed":
        return "The Mindful Wanderer"
    return "The Curious Wanderer"


def trip_export(trip, plan):
    return (f"# VOYARA AI | {trip['destination']}\n\n"
            f"{trip_summary(trip)}\n\n---\n\n{plan}\n\n"
            "---\nPlanning estimates only. No booking or payment is confirmed.\n")


def day_sections(plan):
    """Best-effort split of AI Markdown day headings; preserves original if absent."""
    pattern = re.compile(r"(?im)^(?:#{1,4}\s*|\*\*)?(day\s+\d+\b[^\n]*)")
    matches = list(pattern.finditer(plan))
    if not matches:
        return [], plan
    intro = plan[:matches[0].start()].strip()
    days = []
    for i, match in enumerate(matches):
        stop = matches[i+1].start() if i+1 < len(matches) else len(plan)
        content = plan[match.start():stop].strip()
        days.append((match.group(1).strip(" *#:-"), content))
    return days, intro


# ==========================================
# SESSION STATE
# ==========================================

if "trip" not in st.session_state:
    st.session_state.trip = None

if "plan" not in st.session_state:
    st.session_state.plan = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_model" not in st.session_state:
    st.session_state.last_model = None

if "readiness" not in st.session_state:
    st.session_state.readiness = {}

if "approved_plan" not in st.session_state:
    st.session_state.approved_plan = False


# ==========================================
# HEADER
# ==========================================

st.markdown("""
<div class="hero">
    <p class="eyebrow">✦ YOUR INTELLIGENT TRAVEL UNIVERSE</p>
    <h1 class="glow">✈️ VOYARA AI</h1>
    <p style="font-size:22px;font-weight:700;margin:4px 0">Your World. Reimagined.</p>
    <p>Discover extraordinary journeys, powered by intelligence.</p>
    <p style="font-size:13px;opacity:.86">You Dream It. We Plan It. You Approve It.</p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Personalized travel planning • AI Concierge • "
    "Emergency guidance • Saved trips"
)


# ==========================================
# APPLICATION TABS
# ==========================================

tab_plan, tab_hotels, tab_chat, tab_review, tab_sos, tab_ready, tab_saved = st.tabs([
    "🌍 Plan My Trip",
    "🏨 Hotels & Mobility",
    "💬 AI Concierge",
    "✅ Review & Approve",
    "🆘 Travel SOS",
    "🧳 Travel Readiness",
    "📚 My Saved Trips",
])


# ==========================================
# TAB 1 - PLAN MY TRIP
# ==========================================

with tab_plan:

    st.header("🌍 Plan Your Dream Trip")
    st.markdown("""<div class="voyara-bubble"><span class="voyara-step">Your co-pilot is here ✈️</span><br><strong>Hey, future explorer!</strong> Tell me where you're dreaming of going. I'll help with the fun stuff, the practical stuff, and the <em>wait, did I forget my passport?</em> stuff. 😄</div>""", unsafe_allow_html=True)

    st.write(
        "Tell VOYARA your preferences and discover "
        "a smarter way to plan your next adventure."
    )

    with st.form("travel_form"):

        left, right = st.columns(2)

        with left:

            origin = st.text_input(
                "Departure City",
                value="",
                placeholder="e.g. Dubai",
            )

            destination = st.text_input(
                "Where do you want to travel?",
                value="",
                placeholder="e.g. Paris",
            )

            currency = st.selectbox("💱 Budget currency", CURRENCIES, index=0)
            budget_text = st.text_input(
                f"Total trip budget ({currency})",
                value="",
                placeholder=f"Enter amount in {currency} (e.g. 15000)",
                help="Choose the denomination of your budget. VOYARA does not convert exchange rates.",
            )

            interests = st.multiselect(
                "Your Interests",
                [
                    "Beaches",
                    "Shopping",
                    "Food",
                    "History",
                    "Museums",
                    "Adventure",
                    "Nature",
                    "Art",
                    "Family Activities",
                    "Relaxation",
                    "Nightlife",
                ],
                default=[],
            )

        with right:

            travelers = st.number_input(
                "Number of Travelers",
                min_value=1,
                max_value=30,
                value=1,
            )
            party_type = st.selectbox("Traveling as", ["Solo", "Couple", "Family", "Friends", "Business"])
            cabin = st.selectbox("Flight cabin", ["Economy", "Premium Economy", "Business", "First Class"])

            style = st.selectbox(
                "Travel Style",
                [
                    "Budget-Friendly",
                    "Balanced",
                    "Comfort",
                    "Luxury",
                    "Family-Friendly",
                    "Romantic",
                    "Adventure",
                ],
            )

            hotel = st.selectbox(
                "Hotel Preference",
                [
                    "Near Attractions",
                    "Best Value",
                    "Breakfast Included",
                    "Luxury",
                    "Near Public Transport",
                    "Family-Friendly",
                ],
            )

            flight = st.selectbox(
                "Flight Preference",
                [
                    "Best Overall Value",
                    "Direct Flights Preferred",
                    "Lowest Total Fare",
                    "Shortest Travel Time",
                ],
            )

        st.markdown("### 🧬 VOYARA Travel DNA")
        st.caption("Tell us how you like to explore — your AI itinerary will reflect your personality.")
        dna1, dna2, dna3 = st.columns(3)
        with dna1:
            pace = st.selectbox("Travel pace", ["Balanced", "Relaxed", "Fast-paced"])
        with dna2:
            dna_interest = st.selectbox("Your travel personality", ["Culture & Food", "Adventure & Discovery", "Luxury & Relaxation"])
        with dna3:
            priority = st.selectbox("Top priority", ["Best experience", "Save money", "Convenience"])
        special_preferences = st.multiselect(
            "Dietary & accessibility preferences (optional)",
            ["Halal-friendly dining", "Vegetarian", "Vegan", "Wheelchair accessibility",
             "Minimal walking", "Kid-friendly", "Quiet accommodation"],
        )
        st.markdown("### 🚘 VOYARA Mobility")
        m1, m2 = st.columns(2)
        with m1:
            mobility = st.selectbox("Transportation at destination", MOBILITY_OPTIONS, index=0)
        with m2:
            airport_pickup = st.checkbox("Include airport pickup planning", value=False)

        st.subheader("📅 Choose Your Travel Dates")

        col1, col2 = st.columns(2)

        with col1:
            departure = st.date_input(
                "Departure Date",
                value=None,
                min_value=date.today(),
            )

        with col2:
            returning = st.date_input(
                "Return Date",
                value=None,
                min_value=date.today(),
            )

        notes = st.text_area(
            "Special Requests",
            placeholder=(
                "Breakfast, accessibility, children, "
                "special occasions, preferred hotel area..."
            ),
        )

        submitted = st.form_submit_button(
            "✨ Plan My Trip",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        if not origin.strip() or not destination.strip():
            st.error(
                "Please enter your departure city and destination."
            )

        elif not budget_text.strip():
            st.error("Please enter your trip budget.")
        elif not budget_text.strip().replace(",", "").isdigit() or int(budget_text.replace(",", "")) <= 0:
            st.error("Enter a positive whole-number budget (for example 15000).")
        elif departure is None or returning is None:
            st.error("Please choose both departure and return dates.")
        elif departure < date.today():
            st.error("Departure date cannot be in the past.")
        elif returning <= departure:
            st.error(
                "Your return date must be after your departure date."
            )

        else:

            trip = {
                "origin": origin.strip(),
                "destination": destination.strip(),
                "budget": int(budget_text.replace(",", "")),
                "currency": currency,
                "party_type": party_type,
                "cabin": cabin,
                "pace": pace,
                "travel_dna": travel_persona(pace, dna_interest, priority),
                "dna_interest": dna_interest,
                "priority": priority,
                "special_preferences": special_preferences,
                "mobility": mobility,
                "airport_pickup": airport_pickup,
                "travelers": int(travelers),
                "style": style,
                "hotel": hotel,
                "flight": flight,
                "interests": interests,
                "departure": departure.isoformat(),
                "return": returning.isoformat(),
                "notes": notes.strip(),
            }

            st.session_state.trip = trip
            st.session_state.messages = []
            st.session_state.approved_plan = False
            st.session_state.readiness = {}

            prompt = (
                "Create a detailed personalized travel plan.\n\n"
                + trip_summary(trip)
            )

            with st.spinner(
                "VOYARA is preparing your personalized trip..."
            ):

                answer, model = ask_ai(
                    prompt,
                    PlanningAssistant(),
                    max_tokens=2300,
                )

            if answer:
                st.session_state.plan = answer
                st.session_state.last_model = model

            
            else:
                st.session_state.plan = None
                st.session_state.last_model = None

                st.warning(
                    "Claude could not generate your itinerary. Your trip details are saved. Please try again. "
                    "Your trip details are saved. "
                    "Please try generating your itinerary again."
                )
  

    if st.session_state.trip and st.session_state.plan:

        trip = st.session_state.trip

        st.divider()

        st.header(
            f"✈️ Your {trip['destination']} Adventure"
        )

        a, b, c = st.columns(3)

        a.metric(
            "Total Budget",
            money(trip["budget"], trip.get("currency", "AED")),
        )

        b.metric(
            "Travelers",
            str(trip["travelers"]),
        )

        nights = (
            date.fromisoformat(trip["return"])
            - date.fromisoformat(trip["departure"])
        ).days

        c.metric("Nights", str(nights))

        if st.session_state.last_model:
            st.caption(
                "Personalized using "
                + st.session_state.last_model
            )

        st.markdown("### 🧬 Your Travel DNA")
        st.info(f"**{trip.get('travel_dna', 'Curious Wanderer')}** · "
                f"{trip.get('pace', 'Balanced')} pace · {trip.get('priority', 'Best experience')}")

        st.markdown("""<div class="voyara-bubble"><span class="voyara-step">Your trip is taking shape</span><br><strong>I've put together your first adventure!</strong> Think of this as our starting point, not a homework assignment. Explore the days below, then tell me what you love (or what makes you say <em>absolutely not</em> 😂).</div>""", unsafe_allow_html=True)
        st.markdown("### 📅 Your itinerary")
        days, intro = day_sections(st.session_state.plan)
        if days:
            if intro:
                st.markdown(intro)
            for index, (heading, day_content) in enumerate(days):
                with st.expander(f"🗓️ {heading}", expanded=index == 0):
                    st.markdown(day_content)
            with st.expander("📄 View full itinerary as one document"):
                st.markdown(st.session_state.plan)
        else:
            st.markdown(st.session_state.plan)

        st.markdown("### 📊 AI Budget Intelligence")
        st.caption("Illustrative allocation only — not live quotes or a verified trip total.")
        currency_now = trip.get("currency", "AED")
        budget_rows = budget_allocation(trip["budget"])
        for category, allocated in budget_rows:
            pct = allocated / trip["budget"]
            c_label, c_bar, c_amount = st.columns([2, 4, 2])
            c_label.write(category)
            c_bar.progress(min(1.0, pct))
            c_amount.write(money(allocated, currency_now))
        st.caption("If AI suggestions exceed the budget, revise the itinerary before booking."
                   " Figures are planning estimates in the selected currency.")

        st.download_button(
            "📥 Download my itinerary (.md)",
            data=trip_export(trip, st.session_state.plan),
            file_name="voyara_" + re.sub(r"[^a-z0-9]+", "_", trip["destination"].lower()).strip("_") + ".md",
            mime="text/markdown",
            use_container_width=True,
        )

        st.markdown("""<div class="voyara-bubble"><span class="voyara-step">Let's make it yours</span><br><strong>Not quite your vibe?</strong> Tap one of my magic tweaks below. No awkward conversations with a travel agent required. 😉</div>""", unsafe_allow_html=True)
        st.markdown("### ✨ One-click AI trip refinement")
        refine_cols = st.columns(5)
        refinements = [
            ("💸 Cheaper", "Make this itinerary more affordable while preserving key experiences."),
            ("💎 Luxury", "Upgrade comfort and luxury while staying within the stated budget."),
            ("🍽️ Halal", "Prioritize halal-friendly dining and note that venues must be verified."),
            ("🧘 Relaxed", "Reduce walking and make the schedule more relaxed."),
            ("🎢 Adventure", "Include more adventurous activities suitable for the destination."),
        ]
        chosen_refinement = None
        for col, (label, instruction) in zip(refine_cols, refinements):
            if col.button(label, key="refine_" + label, use_container_width=True):
                chosen_refinement = instruction
        if chosen_refinement:
            with st.spinner("VOYARA is refining your journey..."):
                revised, revised_model = ask_ai(
                    "TRIP:\n" + trip_summary(trip) + "\nCURRENT PLAN:\n" +
                    st.session_state.plan[:11000] + "\nCHANGE REQUEST:\n" +
                    chosen_refinement + "\nReturn a complete revised day-by-day plan. "
                    "All prices are unverified planning estimates.",
                    PlanningAssistant(), max_tokens=2600,
                )
            if revised:
                st.session_state.plan = revised
                st.session_state.last_model = revised_model
                st.session_state.approved_plan = False
                st.rerun()
            else:
                st.warning("AI is unavailable; your original itinerary is unchanged.")

        st.divider()

        # ==================================
        # INSTALLMENT ESTIMATOR
        # ==================================

        st.subheader("💳 Flexible Payment Planning")

        st.write(
            "Explore how your travel budget might "
            "be divided into smaller payments."
        )

        amount = st.number_input(
            f"Amount to divide into payments ({currency_now})",
            min_value=0,
            max_value=trip["budget"],
            value=trip["budget"],
            step=1,
        )

        payments = st.selectbox(
            "Number of Payments",
            [2, 3, 4],
            index=2,
        )

        per_payment = amount / payments

        st.metric(
            "Illustrative Payment Amount",
            f"{currency_now} {per_payment:,.2f}",
        )

        st.caption(
            "Illustration only. VOYARA does not offer "
            "Tabby financing, approve installments, "
            "or collect payments. Actual eligibility, "
            "fees and terms depend on the provider."
        )

        save_col, retry_col = st.columns(2)

        with save_col:

            if st.button(
                "💾 Save My Trip",
                use_container_width=True,
            ):

                save_trip(
                    trip,
                    st.session_state.plan,
                )

                st.success("Your trip has been saved!")

        with retry_col:

            if st.button(
                "🔄 Regenerate With AI",
                use_container_width=True,
            ):

                with st.spinner("Trying available AI models..."):

                    answer, model = ask_ai(
                        "Create a fresh detailed travel plan:\n"
                        + trip_summary(trip),
                        PlanningAssistant(),
                        max_tokens=2300,
                    )

                if answer:
                    st.session_state.plan = answer
                    st.session_state.last_model = model
                    st.session_state.approved_plan = False
                    st.rerun()

                else:
                    st.warning(
                        "The AI models are temporarily unavailable. "
                        "Your current plan has been preserved."
                    )


# ==========================================
# TAB 2 - HOTELS AND EXTERNAL BOOKING
# ==========================================

with tab_hotels:
    st.header("🏨 Find Your Ideal Hotel")
    st.markdown("""<div class="voyara-bubble"><span class="voyara-step">Stay + ride, sorted</span><br><strong>Let's find your home away from home.</strong> Then we'll sort out how you get there — because dragging three suitcases across a new city is not the vacation aesthetic. 🧳😂</div>""", unsafe_allow_html=True)
    st.write("Explore hotel choices and compare them on a live booking site. VOYARA provides planning advice; availability and prices are checked on the provider's website.")

    if st.session_state.trip:
        current_trip = st.session_state.trip
        destination_search = current_trip["destination"]
        arrival = current_trip["departure"]
        departure_hotel = current_trip["return"]
        st.info(f"Your trip: {destination_search} • {arrival} to {departure_hotel} • {current_trip['travelers']} traveler(s)")
    else:
        destination_search = st.text_input("Destination to search", value="", placeholder="Enter a city", key="hotel_destination")
        arrival = ""
        departure_hotel = ""
        st.caption("Create a trip first to use your travel dates and traveler count automatically.")

    st.subheader("🔎 Search Hotels & Compare Prices")
    if destination_search.strip():
        params = {"ss": destination_search.strip()}
        if arrival and departure_hotel:
            params.update({"checkin": arrival, "checkout": departure_hotel, "group_adults": current_trip["travelers"], "no_rooms": 1})
        booking_url = "https://www.booking.com/searchresults.html?" + urlencode(params)
        hotels_url = "https://www.google.com/travel/hotels?q=" + quote_plus(destination_search.strip() + " hotels")
        x, y = st.columns(2)
        with x:
            st.link_button("🏨 Browse hotels on Booking.com", booking_url, use_container_width=True)
        with y:
            st.link_button("🔍 Compare hotels on Google Travel", hotels_url, use_container_width=True)

    st.caption("External sites handle live rates, availability, bookings and payments. Always confirm dates, guest count, breakfast and cancellation terms before paying.")

    st.divider()
    st.markdown("## 🚘 VOYARA Mobility — Your Stay. Your Ride.")
    st.markdown("""<div class="voyara-bubble"><span class="voyara-step">Your ride concierge 🚘</span><br><strong>I've got your arrival covered.</strong> Tell me how you'd like to get around. I'll help narrow down your ride, then give you places to explore actual providers — not just a giant wall of advice.</div>""", unsafe_allow_html=True)
    mobility_choice = st.selectbox("Choose your ride", MOBILITY_OPTIONS, index=2, key="mobility_tab_choice")
    ride_a, ride_b = st.columns(2)
    with ride_a:
        pickup_place = st.text_input("Pickup location", placeholder="e.g. Paris CDG Airport")
        luggage = st.number_input("Number of suitcases", min_value=0, max_value=30, value=1)
    with ride_b:
        dropoff_place = st.text_input("Drop-off location", placeholder="e.g. Hotel in Le Marais")
        passengers = st.number_input("Passengers", min_value=1, max_value=30,
                                     value=min(30, st.session_state.trip.get("travelers", 1)) if st.session_state.trip else 1)
    if destination_search.strip():
        city = destination_search.strip()
        if "chauffeur" in mobility_choice.lower():
            suggestion = "A private chauffeur sounds perfect if you want door-to-door comfort. Ask providers about meet-and-greet, waiting time, luggage capacity and the total fare."
            provider_links = [
                ("🚘 Explore Blacklane chauffeur bookings", "https://www.blacklane.com/en/"),
                ("🚗 Find chauffeur services in " + city, "https://www.google.com/search?q=" + quote_plus("book private chauffeur " + city)),
                ("📍 Compare local chauffeur companies", "https://www.google.com/maps/search/?api=1&query=" + quote_plus("private chauffeur " + city)),
            ]
        elif "rental" in mobility_choice.lower() or "self" in mobility_choice.lower():
            suggestion = "Road-trip energy! 🚗 Compare pickup locations, insurance, deposits, driving-license requirements and fuel policies before choosing a car."
            provider_links = [
                ("🚙 Browse rental cars on Rentalcars.com", "https://www.rentalcars.com/"),
                ("🚗 Search rental cars in " + city, "https://www.google.com/search?q=" + quote_plus("rental cars " + city + " airport booking")),
                ("📍 Find local rental desks", "https://www.google.com/maps/search/?api=1&query=" + quote_plus("car rental " + city)),
            ]
        elif "airport" in mobility_choice.lower() or "transfer" in mobility_choice.lower():
            suggestion = "Airport pickup: one less thing to worry about after a flight! ✈️ Check the exact terminal, flight tracking, waiting time and whether the fare covers all passengers and bags."
            provider_links = [
                ("🛬 Explore Welcome Pickups transfers", "https://www.welcomepickups.com/"),
                ("🚘 Explore Blacklane airport transfers", "https://www.blacklane.com/en/"),
                ("📍 Find airport transfers in " + city, "https://www.google.com/search?q=" + quote_plus("book airport transfer " + city)),
            ]
        else:
            suggestion = "Great choice for exploring like a local! 🚇 Compare airport connections, passes, accessibility and your hotel's nearest station."
            provider_links = [
                ("🚇 Find public transport routes", "https://www.google.com/maps/search/?api=1&query=" + quote_plus("public transport " + city)),
                ("🗺️ Search official transport information", "https://www.google.com/search?q=" + quote_plus("official public transport " + city)),
            ]
        st.info(suggestion)
        st.markdown("#### 🔗 Ready to compare real options?")
        for label, url in provider_links:
            st.link_button(label, url, use_container_width=True)
        st.caption("These open provider websites or searches; prices, local coverage, availability and bookings must be confirmed there. VOYARA has not reserved a vehicle.")
    else:
        st.info("Tell me your destination first and I'll show you relevant transport search links. 🗺️")
    st.markdown("#### 🤝 Want me to narrow it down for you?")
    if st.button("✨ Help me choose my ride", type="primary", key="mobility_recommend"):
        if not destination_search.strip():
            st.warning("First, enter your destination or create a trip.")
        else:
            mobility_context = trip_summary(st.session_state.trip) if st.session_state.trip else f"Destination: {destination_search}"
            mobility_prompt = (mobility_context + f"\nTransport type: {mobility_choice}\n"
                f"Pickup: {pickup_place or 'Not specified'}\nDrop-off: {dropoff_place or 'Not specified'}\n"
                f"Passengers: {passengers}\nSuitcases: {luggage}\n"
                "Act like a warm, witty, practical personal travel agent. Start with your recommended ride type and why. "
                "Give two alternatives and a short comparison of convenience, luggage fit, and estimated budget impact. "
                "Then tell me exactly what to enter on the provider booking site. End with one useful question. "
                "Never invent live rates, availability, completed bookings or provider links.")
            with st.spinner("🚘 Your ride concierge is thinking..."):
                mobility_answer, _ = ask_ai(mobility_prompt, ConciergeAssistant(), max_tokens=1050)
            if mobility_answer:
                st.session_state.mobility_advice = mobility_answer
            else:
                st.session_state.mobility_advice = "I couldn't reach my AI co-pilot just now. The provider links above are ready when you are! 💜"
    if st.session_state.get("mobility_advice"):
        with st.chat_message("assistant", avatar="🚘"):
            st.markdown(st.session_state.mobility_advice)
    st.divider()
    st.markdown("**Quick hotel tips:** Compare total stay costs, location, breakfast, and cancellation rules — not just the prettiest photo. 😉")

    if st.session_state.trip:
        st.subheader("💬 Ask for personalized hotel recommendations")
        hotel_question = st.text_area("What matters most to you?", value="Recommend three named hotels that suit my trip, budget and hotel preference. Explain their location and why each is a good fit.", key="hotel_question")
        if st.button("✨ Get AI Hotel Recommendations", type="primary"):
            with st.spinner("Looking at your preferences..."):
                hotel_answer, hotel_model = ask_ai("TRIP DETAILS:\n" + trip_summary(st.session_state.trip) + "\nCUSTOMER REQUEST:\n" + hotel_question + "\nDo not invent current hotel prices, amenities, or availability.", ConciergeAssistant(), max_tokens=950)
            if hotel_answer:
                st.markdown(hotel_answer)
                st.caption(f"AI recommendations by {hotel_model}; verify all hotel details on the provider's website.")
            else:
                st.info("AI recommendations aren't available right now. You can still compare real hotel listings using the links above.")


# ==========================================
# TAB 2 - AI CONCIERGE
# ==========================================

with tab_chat:

    st.header("💬 Your Personal AI Concierge")
    st.markdown("""<div class="voyara-bubble"><span class="voyara-step">Always on your side 💬</span><br><strong>Hi again! I'm your travel co-pilot.</strong> Change your mind 47 times if you want — that's what I'm here for. 😄 Tell me what isn't working, and I'll help you choose a better option.</div>""", unsafe_allow_html=True)

    st.write(
        "Not satisfied with a recommendation? "
        "Keep talking to VOYARA until you find "
        "a travel plan that suits you."
    )

    if st.session_state.trip:

        trip = st.session_state.trip

        st.caption(
            f"Planning your {trip['destination']} trip "
            f"with a {money(trip['budget'], trip.get('currency', 'AED'))} budget."
        )

    else:

        st.info(
            "You can start chatting now, or create "
            "a trip first so VOYARA knows your preferences."
        )

    st.markdown("**Try asking VOYARA:**")
    q1, q2, q3 = st.columns(3)
    quick_request = None
    if q1.button("🏨 Better hotel options", use_container_width=True):
        quick_request = "Suggest three named hotels suitable for my budget and preferences, with reasons. Tell me what I must verify before booking."
    if q2.button("✈️ Compare flights", use_container_width=True):
        quick_request = "Help me compare direct versus connecting flights for this trip, with practical trade-offs. Do not invent fares."
    if q3.button("✨ Improve my itinerary", use_container_width=True):
        quick_request = "Suggest specific improvements to my current itinerary without increasing my total budget."

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_message = st.chat_input(
        "Tell VOYARA what you'd like to improve..."
    )

    user_message = user_message or quick_request

    if user_message:

        st.session_state.messages.append({
            "role": "user",
            "content": user_message,
        })

        with st.chat_message("user"):
            st.markdown(user_message)

        if st.session_state.trip:

            context = trip_summary(
                st.session_state.trip
            )

        else:

            context = "No travel plan has been created yet."

        history = "\n".join(
            f"{item['role']}: {item['content']}"
            for item in st.session_state.messages[-10:]
        )

        prompt = f"""
TRAVEL DETAILS:
{context}

CURRENT ITINERARY:
{st.session_state.plan[:6000]}

CONVERSATION:
{history}

Answer the latest customer message.
Give useful recommendations and explain why.
"""

        with st.chat_message("assistant"):

            with st.spinner(
                "VOYARA is thinking about your request..."
            ):

                answer, model = ask_ai(
                    prompt,
                    ConciergeAssistant(),
                    max_tokens=1200,
                )

            if answer:

                st.markdown(answer)

                st.caption(
                    f"Powered by {model}. "
                    "Recommendations are not verified live offers."
                )

            else:

                answer = fallback_concierge(
                    user_message,
                    st.session_state.trip,
                )

                st.caption(
                    "AI personalization is temporarily unavailable. "
                    "Showing limited planning guidance."
                )

                st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
        })

    if st.button("🗑️ New Conversation"):

        st.session_state.messages = []
        st.rerun()


# ==========================================
# REVIEW AND APPROVE YOUR PLAN
# ==========================================

with tab_review:
    st.header("✅ Review & Approve Your Trip")
    st.caption("Final boarding call! ✈️ Let's make sure your plan feels right before you approve the proposal.")
    if not st.session_state.trip or not st.session_state.plan:
        st.info("Create a trip in Plan My Trip to review it here.")
    else:
        current_trip = st.session_state.trip
        st.markdown(f"**{current_trip['origin']} → {current_trip['destination']}** | {current_trip['departure']} to {current_trip['return']} | **{money(current_trip['budget'], current_trip.get('currency', 'AED'))}**")
        with st.expander("📋 Read full proposed itinerary", expanded=False):
            st.markdown(st.session_state.plan)
        st.write("Not happy with something? Open **💬 AI Concierge** to discuss hotels, flights, activities and changes before approval.")
        st.warning("Approval means you accept this **proposed travel plan**. It does not reserve flights or hotels, charge money or confirm a booking.")
        approve = st.checkbox("I have reviewed the plan and understand that prices and bookings must be verified externally.", key="approval_check")
        if st.button("✅ Approve My Proposed Plan", type="primary", disabled=not approve):
            st.session_state.approved_plan = True
            st.success("Your proposed itinerary is approved for planning! No reservation or payment has been made.")
        if st.session_state.approved_plan:
            st.success("Status: Approved planning itinerary")
            if st.button("💾 Save Approved Trip", key="save_approved"):
                save_trip(current_trip, st.session_state.plan)
                st.success("Saved to My Saved Trips.")
            st.caption("Next, use Hotels & Booking to check live options with an external provider.")


# ==========================================
# TAB 3 - TRAVEL SOS
# ==========================================

with tab_sos:

    st.header("🆘 VOYARA Travel SOS")
    st.caption("I'm here to help you find the next step. In immediate danger, call local emergency services first.")

    st.warning(
        "If you are in immediate danger or need urgent "
        "medical attention, contact local emergency "
        "services immediately. VOYARA cannot place calls."
    )

    emergency = st.selectbox(
        "What happened?",
        [
            "Lost Passport",
            "Medical Emergency",
            "Missed Flight",
            "Cancelled Flight",
            "Lost Baggage",
            "Unsafe Situation",
            "Hotel Problem",
        ],
    )

    location = st.text_input(
        "Where are you now? (City / Country)"
    )

    details = st.text_area(
        "Tell VOYARA what happened",
        placeholder="Describe your situation...",
    )

    emergency_fallbacks = {
        "Lost Passport": (
            "Contact your embassy or consulate for "
            "emergency travel documents. Report the "
            "loss to local authorities where required."
        ),
        "Medical Emergency": (
            "For urgent medical symptoms, contact local "
            "emergency services immediately. Notify "
            "your travel insurer when safe."
        ),
        "Missed Flight": (
            "Contact the airline immediately through "
            "its official app, counter or support number. "
            "Ask about rebooking and baggage."
        ),
        "Cancelled Flight": (
            "Contact your airline for rebooking or refund "
            "options. Keep notifications and receipts."
        ),
        "Lost Baggage": (
            "Report the missing baggage to the airline "
            "before leaving the airport. Keep your "
            "baggage report reference number."
        ),
        "Unsafe Situation": (
            "Move to a safer location if possible and "
            "contact local emergency services. Inform "
            "a trusted person of your location."
        ),
        "Hotel Problem": (
            "Speak to hotel management, document the "
            "problem and contact your booking provider "
            "if the issue is unresolved."
        ),
    }

    if st.button(
        "🆘 Get Emergency Guidance",
        type="primary",
    ):

        prompt = f"""
Travel emergency: {emergency}
Location: {location or "Not provided"}
Details: {details or "Not provided"}

Give clear, safety-first instructions.
Do not invent emergency phone numbers.
"""

        with st.spinner("Preparing guidance..."):

            answer, model = ask_ai(
                prompt,
                EmergencyAssistant(),
                max_tokens=900,
            )

        if answer:
            st.markdown(answer)

        else:
            st.markdown(
                emergency_fallbacks[emergency]
            )

        st.caption(
            "Guidance only. VOYARA cannot contact "
            "emergency responders, airlines or embassies."
        )


# ==========================================
# TRAVEL READINESS - PERSONAL CHECKLIST
# ==========================================

with tab_ready:
    st.header("🧳 Travel Readiness Check")
    st.write("Get ready for takeoff with a practical checklist. Your progress is saved for this browser session.")
    if st.session_state.trip:
        st.info("Preparing for " + st.session_state.trip["destination"] +
                " · " + st.session_state.trip["departure"])
    checks = [
        "Check passport validity",
        "Verify visa / entry requirements with official sources",
        "Review travel insurance",
        "Confirm flight and accommodation details",
        "Plan airport transfers and local transport",
        "Prepare medicines and essentials",
        "Save emergency contacts and important documents",
        "Check luggage allowance and pack bags",
    ]
    for i, item in enumerate(checks):
        st.checkbox(item, key=f"readiness_{i}")
    completed = sum(bool(st.session_state.get(f"readiness_{i}", False)) for i in range(len(checks)))
    st.progress(completed / len(checks))
    st.caption(f"{completed} of {len(checks)} steps completed")
    st.warning("Visa and entry rules depend on nationality, destination and travel dates. "
               "Always confirm them with official government or embassy sources.")


# ==========================================
# TAB 4 - MY SAVED TRIPS
# ==========================================

with tab_saved:

    st.header("📚 My Saved Trips & Digital Passport")
    st.caption("Your collection of planned destinations — stamps do not indicate verified travel.")

    saved_trips = load_saved_trips()

    if not saved_trips:

        st.info(
            "No saved trips yet. Create your first "
            "travel plan and click Save My Trip."
        )

    if saved_trips:
        st.markdown("### 🛂 Your Digital Passport")
        unique_destinations = []
        for saved_row in saved_trips:
            if saved_row[2] not in unique_destinations:
                unique_destinations.append(saved_row[2])
        st.metric("Destinations planned", len(unique_destinations))
        stamp_cols = st.columns(3)
        for idx, place in enumerate(unique_destinations):
            with stamp_cols[idx % 3]:
                st.markdown("#### 🌍 " + place)
                st.caption("✦ VOYARA PASSPORT · PLANNED")
        st.divider()

    for row in saved_trips:

        trip_id, created_at, destination, trip_json, plan_text = row

        with st.expander(
            f"✈️ {destination} | {created_at} | Trip #{trip_id}"
        ):

            try:
                stored_trip = json.loads(trip_json)
            except (ValueError, TypeError):
                stored_trip = None

            st.markdown(plan_text)

            col_load, col_delete = st.columns(2)

            with col_load:

                if st.button(
                    "📋 Load This Trip",
                    key=f"load_{trip_id}",
                    use_container_width=True,
                ):

                    if stored_trip:

                        st.session_state.trip = stored_trip
                        st.session_state.plan = plan_text
                        st.session_state.messages = []
                        st.session_state.approved_plan = False

                        st.success(
                            "Trip loaded! Open Plan My Trip "
                            "to view your saved itinerary."
                        )

                    else:
                        st.error(
                            "This saved trip could not be loaded."
                        )

            with col_delete:

                if st.button(
                    "🗑️ Delete Trip",
                    key=f"delete_{trip_id}",
                    use_container_width=True,
                ):

                    delete_trip(trip_id)
                    st.rerun()


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "✦ VOYARA AI 2.0 | University Project Prototype | "
    "Travel recommendations are not confirmed bookings. "
    "Never enter payment card details or passwords in chat."
)
