import streamlit as st
import sqlite3
import extra_streamlit_components as stx
import datetime

st.set_page_config(
    page_title="Deg Reviews",
    page_icon="https://lh4.googleusercontent.com/e0kLySme0jMVKoZagipGvpe-0kCosciRduao76aJFaEg5rfs0US4ynV470U9vNTZ-w91mAY3dJD3XoSejfrw2us=w16383",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "# Built by OurSU."
    }
)

# Create a connection to the SQLite database
conn = sqlite3.connect("/data/reviews.db")
#conn = sqlite3.connect("reviews.db")

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
        "Mon - Fri": ["12:00AM", "10:00AM"],
        "Sat - Sun": ["8:00AM", "10:00AM"]
    },
    "Lunch": {
        "Mon - Sun": ["11:00AM", "1:30PM"]
    },
    "Light Lunch": {
        "Mon - Fri": ["1:30PM", "2:00PM"]
    },
    "Dinner": {
        "Mon - Thu": ["4:00PM", "7:15PM"],
        "Fri": ["4:00PM", "7:00PM"],
        "Sat - Sun": ["4:30PM", "7:00PM"]
    }
}

# Create a function to check mealtime
def is_mealtime(meal):
    current_time = datetime.datetime.now().time()
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

# Calculate the expiration date (300 days from now)
expiration_date = datetime.datetime.now() + datetime.timedelta(days=300)
# Convert the expiration date to an ISO-formatted string
expiration_date_str = expiration_date.isoformat()

cookie_manager = get_cookie_manager()

if not cookie_manager.get("saved_user_uuid"):
    # Generate a new UUID
    import uuid  # Import the UUID module
    new_uuid = str(uuid.uuid4())
    # Set "user_uuid_cookie" with the new UUID
    cookie_manager.set("oursu_degreviews_user_uuid", new_uuid, expires_at=expiration_date)
    
# Get the value of "user_uuid" from the cookies
user_uuid = cookie_manager.get("oursu_degreviews_user_uuid")

def main():

    # Determine the current mealtime
    current_meal = None
    for meal in meal_schedule:
        if is_mealtime(meal):
            current_meal = meal
            break

    # Set the title with the current mealtime
    st.title(f"Submit a Review for {current_meal} Meal")

    # Collect user's rating
    st.subheader("Rate Your Meal Enjoyment")
    rating = st.slider("Select a rating", 1, 5, 2, key="rating", disabled=not is_mealtime(current_meal))  # Slider from 1 to 5

    # Collect user's feedback
    st.subheader("Tell Us What You Liked and Disliked")
    liked = st.text_area("What did you like about the meal?", key="liked", disabled=not is_mealtime(current_meal))
    disliked = st.text_area("What did you dislike about the meal?", key="disliked", disabled=not is_mealtime(current_meal))

    # Check if the user has already submitted a review for the current meal
    submitted_for_meal = cookie_manager.get(f"{datetime.date.today()}_{current_meal}")

    # Disable fields if the user can't submit or has already submitted
    disable_fields = submitted_for_meal or not is_mealtime(current_meal)
    
    #Session State Debug
    st.write(st.session_state)
    
    if not is_mealtime(current_meal):
        st.warning("It's not mealtime. You can't submit a review right now.")
    elif submitted_for_meal:
        st.warning("You have already submitted a review for this meal today.")
    else:
        # Submit button
        if st.button("Submit Review", key="submit"):

            # Validate input length
            if len(liked) < 8 or len(disliked) < 8:
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
            
            # Get the current date and time
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Store the data in the database, including the user UUID, meal, and timestamp
            cursor.execute("INSERT INTO reviews (user_uuid, timestamp, meal, rating, liked, disliked) VALUES (?, ?, ?, ?, ?, ?)",
                        (user_uuid, timestamp, current_meal, rating, liked, disliked))
            conn.commit()  # Commit the transaction to save the data

            # Set a cookie to indicate that the user has submitted a review for this meal today
            cookie_manager.set(f"{datetime.date.today()}_{current_meal}", "submitted", max_age=72000)

            st.success(f"Review submitted successfully for {current_meal} Meal!")

    # Display all cookies for debugging
        cookies = cookie_manager.get_all()
        st.write("All Cookies:")
        st.write(cookies)
    # Other Debug Info
        st.write("Current Meal: ",{current_meal})
        st.write("Date: ",{datetime.date.today()})
        st.write("Datetime: ",{datetime.datetime.now()})
        st.write("Submitted for meal: ",{submitted_for_meal})
        st.write("is_mealtime: ", {is_mealtime})


if __name__ == "__main__":
    main()

# Close the database connection when done
conn.close()
