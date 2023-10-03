import streamlit as st
import sqlite3
import extra_streamlit_components as stx
import datetime
import time
import pytz
import uuid

st.set_page_config(
    page_title="Deg Reviews",
    page_icon="https://lh4.googleusercontent.com/e0kLySme0jMVKoZagipGvpe-0kCosciRduao76aJFaEg5rfs0US4ynV470U9vNTZ-w91mAY3dJD3XoSejfrw2us=w16383",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Report a bug': "https://oursu.susqu.org/nav/feedback",
        'About': "# Built by [OurSU](https://oursu.susqu.org)"
    }
)

# Create a connection to the SQLite database:
conn = sqlite3.connect("/data/reviews.db") #Prod
#conn = sqlite3.connect("reviews.db") #Dev

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
        [ADD LATER]
    )
''')

#Set Time Zone
est = pytz.timezone('US/Eastern')

# Define the meal schedule
meal_schedule = {
    "Breakfast": {
        "Mon - Fri": ["12:00AM", "10:15AM"], #default: 7AM-10:15AM
        "Sat - Sun": ["8:00AM", "10:15AM"]
    },
    "Lunch": {
        "Mon - Sun": ["11:00AM", "1:30PM"]
    },
    "Light Lunch": {
        "Mon - Fri": ["1:30PM", "2:15PM"]
    },
    "Dinner": {
        "Mon - Thu": ["4:00PM", "7:30PM"], #default: 4PM-7:30PM
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
##@st.cache_resource(experimental_allow_widgets=True)  # Enable widget replay
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# Calculate the expiration date (300 days from now)
expiration_date = datetime.datetime.now() + datetime.timedelta(days=300)
# Convert the expiration date to an ISO-formatted string
expiration_date_str = expiration_date.isoformat()

# Create a function to generate a user_uuid 
def get_user_uuid():
    user_uuid = cookie_manager.get("oursu_deg_user_uuid")
    if not user_uuid:
        # Generate a new UUID
        new_uuid = str(uuid.uuid4())
        # Set the UUID cookie with a long expiration date
        cookie_manager.set("oursu_deg_user_uuid", new_uuid, expires_at=expiration_date)
        user_uuid = new_uuid
    return user_uuid

# Main function.
def main():
    user_uuid = get_user_uuid()

    current_meal = None
    for meal in meal_schedule:
        if is_mealtime(meal):
            current_meal = meal
            break

    # Set the title with the current mealtime. Also handles other text changes.
    if current_meal is None:
        st.title(f"Submit a Review")
        this_meal = "this meal"
    else:
        st.title(f"Submit a Review for {current_meal}!")
        this_meal = current_meal.lower()

    # Check if a corresponding cookie exists for the current date and meal
    meal_cookie = cookie_manager.get(cookie=f"{datetime.date.today()}_{current_meal}")
    meal_cookie_exists = meal_cookie is not None

    # Update submitted_for_meal based on the existence of the cookie
    submitted_for_meal = meal_cookie_exists
    
    disable_fields = not is_mealtime(current_meal) or submitted_for_meal

    with st.form("review_form"):
        st.subheader("Rate Your Meal Enjoyment")
        rating = st.slider("Select a rating", 1, 5, 3, key="rating", disabled=disable_fields)  # Slider from 1 to 5, default 3
        st.subheader("Tell Us About Your Meal")
        what_they_ate = st.text_area(f"Please list what you ate for {this_meal} today in the Dining Hall:", key="what_they_ate", disabled=disable_fields, max_chars=120)
        liked = st.text_area("What did you like about the meal?", key="liked", disabled=disable_fields, on_change=None, max_chars=260)
        disliked = st.text_area("What did you dislike about the meal?", key="disliked", disabled=disable_fields, on_change=None, max_chars=260)
        
        submitted = st.form_submit_button(label='Submit Review', disabled=disable_fields)
        if submitted:
            # Validate input length
            if len(liked) < 10 or len(disliked) <= 0 or len(what_they_ate) < 10: #add more sections here
                st.error("Your feedback must be at least 10 characters long.")
                return

            # Filter out bad words
            prohibited_words = ["fuck", "bitch", "slur3"]
            if any(word in liked.lower() for word in prohibited_words) or any(word in disliked.lower() for word in prohibited_words): #add more sections here
                st.error("Your feedback contains inappropriate language.")
                return
            #Run the following:               
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Store the data in the database, including the user UUID, meal, and timestamp
            cursor.execute("INSERT INTO reviews (user_uuid, timestamp, meal, rating, liked, disliked, what_they_ate) VALUES (?, ?, ?, ?, ?, ?)",
                        (user_uuid, timestamp, current_meal, rating, liked, disliked, what_they_ate))
            conn.commit()  # Commit the transaction to save the data

            # Set a cookie to indicate that the user has submitted a review for this meal today
            cookie_manager.set(f"{datetime.date.today()}_{current_meal}", "submitted", max_age=72000)

            st.toast('Submitting...')
            time.sleep(3)
            st.toast('Review sucessfully submitted.', icon='✔')
            time.sleep(2)
            st.rerun()
    
    if not is_mealtime(current_meal):
        st.warning("It's not mealtime. You can't submit a review right now. Come back later!")
    elif meal_cookie_exists:
        st.info(f"You have already submitted a review for {this_meal} today. Send feedback to O&M Dining directly:")
        col1, col2, col3 = st.columns(3)
        col2.link_button("O&M Dining Survey", "https://oursu.susqu.org/dining/survey", type="secondary")


    #Debug
    #st.write(submitted)
    #st.write(f"disable_fields: {disable_fields}")
    #st.write(f"{datetime.date.today()}_{current_meal}")
    #st.write(cookie_manager.get(cookie="2023-10-02_Dinner"))
    #st.write(f"meal_cookie: {meal_cookie}")
    #st.write(f"meal_cookie_exists: {meal_cookie_exists}")
    #st.write(cookie_manager.get(cookie=f"{datetime.date.today()}_{current_meal}") == None)
    #st.write(f"submitted_for_meal: {submitted_for_meal}")


if __name__ == "__main__":
    main()

# Close the database connection when done
conn.close()
