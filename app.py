
import os
import json
import sqlite3
from pathlib import Path
from datetime import date, timedelta
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
    "gemini-3.5-flash-lite",
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
.stApp {
    background: linear-gradient(160deg, #061326, #102b4e 65%, #071529);
    color: #f4f7ff;
}
.block-container {
    max-width: 1150px;
    padding-top: 2rem;
}
h1, h2, h3 {
    color: #ffffff !important;
}
.hero {
    background: linear-gradient(110deg, #12375b, #0b2038);
    border: 1px solid #365778;
    border-radius: 22px;
    padding: 30px;
    margin-bottom: 25px;
}
.hero h1 {
    font-size: 44px;
    margin-bottom: 8px;
}
.hero p {
    color: #c8d7e9;
    font-size: 17px;
}
[data-testid="stChatMessage"] {
    background: #10243e;
    border: 1px solid #294461;
    border-radius: 15px;
}
[data-testid="stMetric"] {
    background: #142c49;
    border: 1px solid #34506b;
    border-radius: 14px;
    padding: 14px;
}
.stButton > button {
    border-radius: 12px;
}
.stButton > button[kind="primary"] {
    background: #fa5252;
    color: white;
    border: none;
}
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
7. Detailed AED budget allocation that adds up correctly.
8. Attractions, food, local transport and practical tips.
9. Ways to improve the trip without exceeding the budget.

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
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        return None

    try:
        from google import genai

        return genai.Client(
            api_key=api_key,
            http_options={"timeout": 20000},
        )

    except Exception as error:
        print("VOYARA CLIENT ERROR:", error, flush=True)
        return None


def ask_ai(prompt, assistant, max_tokens=1600):
    client = get_ai_client()

    if client is None:
        return None, None

    try:
        from google.genai import types
    except ImportError:
        return None, None

    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=assistant.instructions(),
                    temperature=0.65,
                    max_output_tokens=max_tokens,
                ),
            )

            answer = (response.text or "").strip()

            if answer:
                return answer, model

        except Exception as error:
            print(
                f"VOYARA AI ERROR [{model}]: {error}",
                flush=True,
            )

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
Total budget: AED {trip["budget"]:,}
Travel style: {trip["style"]}
Hotel preference: {trip["hotel"]}
Flight preference: {trip["flight"]}
Interests: {", ".join(trip["interests"])}
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

**Total budget:** AED {budget:,}

AI-generated destination recommendations are temporarily
unavailable. This is a planning framework, not a verified
hotel or flight search.

### Illustrative Budget

| Category | AED |
|---|---:|
{rows}

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

if "approved_plan" not in st.session_state:
    st.session_state.approved_plan = False


# ==========================================
# HEADER
# ==========================================

st.markdown("""
<div class="hero">
    <h1>✈️ VOYARA AI</h1>
    <p>You Dream It. We Plan It. You Approve It.</p>
    <p>Your intelligent personal travel concierge.</p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Personalized travel planning • AI Concierge • "
    "Emergency guidance • Saved trips"
)


# ==========================================
# APPLICATION TABS
# ==========================================

tab_plan, tab_hotels, tab_chat, tab_review, tab_sos, tab_saved = st.tabs([
    "🌍 Plan My Trip",
    "🏨 Hotels & Booking",
    "💬 AI Concierge",
    "✅ Review & Approve",
    "🆘 Travel SOS",
    "📚 My Saved Trips",
])


# ==========================================
# TAB 1 - PLAN MY TRIP
# ==========================================

with tab_plan:

    st.header("🌍 Plan Your Dream Trip")

    st.write(
        "Tell VOYARA your preferences and discover "
        "a smarter way to plan your next adventure."
    )

    with st.form("travel_form"):

        left, right = st.columns(2)

        with left:

            origin = st.text_input(
                "Departure City",
                value="Dubai",
            )

            destination = st.text_input(
                "Where do you want to travel?",
                value="Paris",
            )

            budget = st.number_input(
                "Total Budget (AED)",
                min_value=500,
                value=15000,
                step=500,
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
                default=["Shopping", "Food"],
            )

        with right:

            travelers = st.number_input(
                "Number of Travelers",
                min_value=1,
                max_value=30,
                value=2,
            )

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

        st.subheader("📅 Choose Your Travel Dates")

        col1, col2 = st.columns(2)

        with col1:
            departure = st.date_input(
                "Departure Date",
                value=date.today() + timedelta(days=30),
                min_value=date.today(),
            )

        with col2:
            returning = st.date_input(
                "Return Date",
                value=date.today() + timedelta(days=35),
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

        elif returning <= departure:
            st.error(
                "Your return date must be after your departure date."
            )

        else:

            trip = {
                "origin": origin.strip(),
                "destination": destination.strip(),
                "budget": int(budget),
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
                st.session_state.plan = fallback_plan(trip)
                st.session_state.last_model = None

                st.info(
                    "AI planning is temporarily unavailable. "
                    "Your travel framework is ready, and you "
                    "can regenerate it later."
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
            f"AED {trip['budget']:,}",
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

        st.markdown(st.session_state.plan)

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
            "Amount to divide into payments (AED)",
            min_value=0,
            max_value=trip["budget"],
            value=trip["budget"],
            step=100,
        )

        payments = st.selectbox(
            "Number of Payments",
            [2, 3, 4],
            index=2,
        )

        per_payment = amount / payments

        st.metric(
            "Illustrative Payment Amount",
            f"AED {per_payment:,.2f}",
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
    st.write("Explore hotel choices and compare them on a live booking site. VOYARA provides planning advice; availability and prices are checked on the provider's website.")

    if st.session_state.trip:
        current_trip = st.session_state.trip
        destination_search = current_trip["destination"]
        arrival = current_trip["departure"]
        departure_hotel = current_trip["return"]
        st.info(f"Your trip: {destination_search} • {arrival} to {departure_hotel} • {current_trip['travelers']} traveler(s)")
    else:
        destination_search = st.text_input("Destination to search", value="Paris", key="hotel_destination")
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
    st.markdown("**How VOYARA helps you choose:**")
    st.markdown("- **Near attractions:** Save time on sightseeing and transport.\n- **Best value:** Compare the total stay cost, not only the nightly rate.\n- **Breakfast included:** Verify the specific room rate includes breakfast.\n- **Flexible cancellation:** Check the provider's exact conditions.")

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

    st.write(
        "Not satisfied with a recommendation? "
        "Keep talking to VOYARA until you find "
        "a travel plan that suits you."
    )

    if st.session_state.trip:

        trip = st.session_state.trip

        st.caption(
            f"Planning your {trip['destination']} trip "
            f"with an AED {trip['budget']:,} budget."
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
    if not st.session_state.trip or not st.session_state.plan:
        st.info("Create a trip in Plan My Trip to review it here.")
    else:
        current_trip = st.session_state.trip
        st.markdown(f"**{current_trip['origin']} → {current_trip['destination']}** | {current_trip['departure']} to {current_trip['return']} | **AED {current_trip['budget']:,}**")
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
# TAB 4 - MY SAVED TRIPS
# ==========================================

with tab_saved:

    st.header("📚 My Saved Trips")

    saved_trips = load_saved_trips()

    if not saved_trips:

        st.info(
            "No saved trips yet. Create your first "
            "travel plan and click Save My Trip."
        )

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
    "✈️ VOYARA AI | University Project Prototype | "
    "Travel recommendations are not confirmed bookings. "
    "Never enter payment card details or passwords in chat."
)
