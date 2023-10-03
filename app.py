import streamlit as st
import sqlite3
import extra_streamlit_components as stx
import datetime
import time
import pytz
import uuid  # Import the UUID module

st.set_page_config(
    page_title="Deg Reviews",
    page_icon="https://lh4.googleusercontent.com/e0kLySme0jMVKoZagipGvpe-0kCosciRduao76aJFaEg5rfs0US4ynV470U9vNTZ-w91mAY3dJD3XoSejfrw2us=w16383",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "# Built by [OurSU](oursu.susqu.org)"
    }
)


# Create a connection to the SQLite database:
#conn = sqlite3.connect("/data/reviews.db") #Prod
conn = sqlite3.connect("reviews.db") #Dev

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

#Set Time Zone
est = pytz.timezone('US/Eastern')

# Define the meal schedule
meal_schedule = {
    "Breakfast": {
        "Mon - Fri": ["7:00AM", "10:15AM"],
        "Sat - Sun": ["8:00AM", "10:15AM"]
    },
    "Lunch": {
        "Mon - Sun": ["11:00AM", "1:30PM"]
    },
    "Light Lunch": {
        "Mon - Fri": ["1:30PM", "2:15PM"]
    },
    "Dinner": {
        "Mon - Thu": ["7:00PM", "7:30PM"],
        "Fri": ["4:00PM", "7:15PM"],
        "Sat - Sun": ["4:30PM", "7:15PM"]
    }
}

# Create a function to check mealtime
def is_mealtime(meal):
    current_time = datetime.datetime.now(est).time()
    print("Current Time:", current_time)
    if meal in meal_schedule:
        for days, times in meal_schedule[meal].items():
            start_time = datetime.datetime.strptime(times[0], "%I:%M%p").time()
            end_time = datetime.datetime.strptime(times[1], "%I:%M%p").time()
            print(f"Checking {meal} - Start Time: {start_time}, End Time: {end_time}")
            if current_time >= start_time and current_time <= end_time:
                return True
                
    return False


# Create a function to track user submissions for the day using cookies
@st.cache_resource(experimental_allow_widgets=True)  # Enable widget replay
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# Calculate the expiration date (300 days from now)
expiration_date = datetime.datetime.now() + datetime.timedelta(days=300)
# Convert the expiration date to an ISO-formatted string
expiration_date_str = expiration_date.isoformat()

def get_user_uuid():
    user_uuid = cookie_manager.get(cookie="oursu_deg_user_uuid")
    if not user_uuid:
        # Generate a new UUID
        new_uuid = str(uuid.uuid4())
        # Set the UUID cookie with a long expiration date
        cookie_manager.set("oursu_deg_user_uuid", new_uuid, expires_at=expiration_date)
        user_uuid = new_uuid
    return user_uuid

# # Initialize a session state variable for submitting.
if 'submission_successful' not in st.session_state:
    st.session_state.submission_successful = False

def main():
    user_uuid = get_user_uuid()

    # Determine the current mealtime
    current_meal = None
    for meal in meal_schedule:
        if is_mealtime(meal):
            current_meal = meal
            break

    # Set the title with the current mealtime
    if current_meal is None:
        st.title(f"Submit a Review")
    else:
        st.title(f"Submit a Review for {current_meal}!")



    # Check if the user has already submitted a review for the current meal
    meal_cookie_value = cookie_manager.get(f"{datetime.date.today()}_{current_meal}")
    submitted_for_meal = (meal_cookie_value == "submitted")

    # Disable fields if the user can't submit or has already submitted
    disable_fields = submitted_for_meal or not is_mealtime(current_meal) or st.session_state.submission_successful

    # Collect user's rating
    st.subheader("Rate Your Meal Enjoyment")
    rating = st.slider("Select a rating", 1, 5, 3, key="rating", disabled=disable_fields)  # Slider from 1 to 5, default 3
    # Collect user's feedback
    st.subheader("Tell Us About Your Meal")
    ate_list = st.text_area("Please list what you ate for this meal?", key="ate_list", disabled=disable_fields)
    liked = st.text_area("What did you like about the meal?", key="liked", disabled=disable_fields)
    disliked = st.text_area("What did you dislike about the meal?", key="disliked", disabled=disable_fields)

    #DEBUG
    st.write(f"Current Meal: ",{current_meal})
    st.write(f"is_mealtime: ", {is_mealtime(current_meal)})
    st.write(f"submitted_for_meal: ", {submitted_for_meal})
    
    if not is_mealtime(current_meal):
        st.warning("It's not mealtime. You can't submit a review right now.")
    elif submitted_for_meal:
        st.warning("You have already submitted a review for this meal today.")
    else:
        # Submit button
        if st.button("Submit Review", key="submit"):

            # Validate input length
            if len(liked) < 10 or len(disliked) < 9 or len(ate_list) <7:
                st.error("Your feedback must be at least 10 characters long.")
                return

            if len(liked) > 300 or len(disliked) > 250 or len(ate_list) > 250:
                st.error("Your feedback cannot exceed 250 characters.")
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
            
            disable_fields = True
            st.toast('Submitting...')
            time.sleep(1)
            st.success('This is a success message!', icon="✅")

            


    if (st.session_state.submission_successful): 
        st.write("**Review submitted successfully!**")


if __name__ == "__main__":
    main()

# Close the database connection when done
conn.close()
