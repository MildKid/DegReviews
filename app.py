import streamlit as st
import sqlite3
import extra_streamlit_components as stx
import datetime
import uuid
import webbrowser
import pytz  # Import the pytz library for time zone handling
from langdetect import detect  # Import the langdetect library for language detection

# Create a connection to the SQLite database
conn = sqlite3.connect("/data/reviews.db")
# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Create a table to store reviews if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_uuid TEXT,
        timestamp TEXT,
        meal TEXT,
        rating INTEGER,
        liked TEXT,
        disliked TEXT
    )
''')

# Define the meal schedule
meal_schedule = {
    "Breakfast": {
        "Mon - Fri": ["7:00AM", "10:09AM"],
        "Sat - Sun": ["8:00AM", "10:09AM"]
    },
    "Lunch": {
        "Mon - Sun": ["11:00AM", "1:39PM"]
    },
    "Light Lunch": {
        "Mon - Fri": ["1:30PM", "2:09PM"]
    },
    "Dinner": {
        "Mon - Thu": ["3:07PM", "7:20PM"],
        "Fri": ["4:00PM", "7:09PM"],
        "Sat - Sun": ["4:30PM", "7:09PM"]
    }
}

# Define the Eastern Standard Time (EST) timezone
est = pytz.timezone('US/Eastern')

# Create a function to check mealtime with the EST timezone
def is_mealtime(meal):
    current_time = datetime.datetime.now(est).time()
    if meal in meal_schedule:
        for days, times in meal_schedule[meal].items():
            start_time = datetime.datetime.strptime(times[0], "%I:%M%p").time()
            end_time = datetime.datetime.strptime(times[1], "%I:%M%p").time()
            if current_time >= start_time and current_time <= end_time:
                return True
    return False

# Create a function to track user submissions for the day using cookies
@st.cache_resource(experimental_allow_widgets=True)  # Enable widget replay
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# Initialize a session state variable for user UUID
if 'user_uuid' not in st.session_state:
    st.session_state.user_uuid = None

def main():
    # Access the user UUID from session state
    user_uuid = st.session_state.user_uuid

    # Determine the current mealtime
    current_meal = None
    for meal in meal_schedule:
        if is_mealtime(meal):
            current_meal = meal
            break

    # Set the title with the current mealtime
    st.title(f"Submit a Review for {current_meal} Meal at {datetime.datetime.now(est).time()}")

    # Generate a UUID for the user if not already assigned
    if user_uuid is None:
        user_uuid = str(uuid.uuid4())  # Generate a new UUID
        # Set a cookie to store the user's UUID for future visits (expires in 30 days)
        cookie_manager.set("user_uuid", user_uuid, max_age=26000000)
        # Store the user UUID in session state
        st.session_state.user_uuid = user_uuid

    # Collect user's rating
    st.subheader("Rate Your Meal Enjoyment")
    rating = st.slider("Select a rating", 1, 5, 3, key="rating", disabled=not is_mealtime(current_meal))  # Slider from 1 to 5

    # Collect user's feedback
    st.subheader("Tell Us What You Liked and Disliked")
    liked = st.text_area("What did you like about the meal?", key="liked", disabled=not is_mealtime(current_meal))
    disliked = st.text_area("What did you dislike about the meal?", key="disliked", disabled=not is_mealtime(current_meal))

    # Check if the user has already submitted a review for the current meal
    submitted_for_meal = cookie_manager.get(f"{user_uuid}_{current_meal}")

    # Disable fields if the user can't submit or has already submitted
    disable_fields = submitted_for_meal or not is_mealtime(current_meal)

    if not is_mealtime(current_meal):
        st.warning("It's not mealtime. You can't submit a review right now.")
    elif submitted_for_meal:
        st.warning("You have already submitted a review for this meal today.")
    else:
        # Submit button
        if st.button("Submit Review", key="submit", disabled=disable_fields):
            # Check if it's mealtime
            if current_meal is None:
                st.warning("It's not mealtime. You can't submit a review right now.")
                return

            # Validate input length
            if len(liked) < 24 or len(disliked) < 10:
                st.error("Your feedback must be at least 10 characters long.")
                return

            if len(liked) > 300 or len(disliked) > 300:
                st.error("Your feedback cannot exceed 300 characters.")
                return

            # Filter out slurs (you can customize this list)
            prohibited_words = ["slur1", "slur2", "slur3"]
            if any(word in liked.lower() for word in prohibited_words) or any(word in disliked.lower() for word in prohibited_words):
                st.error("Your feedback contains inappropriate language.")
                return

            # Check if input is legible English
            if not is_legible_english(liked) or not is_legible_english(disliked):
                st.error("Your feedback does not appear to be legible.")
                return

            # Get the current date and time
            timestamp = datetime.datetime.now(est).strftime("%Y-%m-%d %H:%M:%S")

            # Store the data in the database, including the user UUID, meal, and timestamp
            cursor.execute("INSERT INTO reviews (user_uuid, timestamp, meal, rating, liked, disliked) VALUES (?, ?, ?, ?, ?, ?)",
                        (user_uuid, timestamp, current_meal, rating, liked, disliked))
            conn.commit()  # Commit the transaction to save the data

            # Set a cookie to indicate that the user has submitted a review for this meal today
            cookie_manager.set(f"{user_uuid}_{current_meal}", "submitted", max_age=72000)

            st.success(f"Review submitted successfully for {current_meal} Meal!")

            # Redirect the user to Google.com after submission
            webbrowser.open("https://www.google.com")

def is_legible_english(text):
    # You can customize this logic further if needed
    try:
        detected_lang = detect(text)
        return detected_lang == "en"
    except:
        return False

if __name__ == "__main__":
    main()

# Close the database connection when done
conn.close()