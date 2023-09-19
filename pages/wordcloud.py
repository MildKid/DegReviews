import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import sqlite3

# Function to fetch reviews from SQLite database and generate a word cloud
def create_wordcloud_from_database(column_name):
    conn = sqlite3.connect('reviews.db')  # Replace 'reviews.db' with your actual database file path
    cursor = conn.cursor()

    # Fetch reviews from the selected column
    cursor.execute(f"SELECT {column_name} FROM reviews")
    reviews = cursor.fetchall()
    conn.close()

    # Combine all reviews into a single text
    text = " ".join([review[0] for review in reviews])

    # Create and generate a word cloud image based on word frequency
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    return wordcloud

# Streamlit app
st.title('Word Clouds from SQLite Database')

# Create word clouds for "liked" and "disliked" columns
liked_wordcloud = create_wordcloud_from_database('liked')
disliked_wordcloud = create_wordcloud_from_database('disliked')

# Display the word clouds
st.subheader('Word Cloud for Liked Reviews')
fig_liked, ax_liked = plt.subplots(figsize=(12, 8))
ax_liked.imshow(liked_wordcloud, interpolation='bilinear')
plt.axis("off")
st.pyplot(fig_liked)

st.subheader('Word Cloud for Disliked Reviews')
fig_disliked, ax_disliked = plt.subplots(figsize=(12, 8))
ax_disliked.imshow(disliked_wordcloud, interpolation='bilinear')
plt.axis("off")
st.pyplot(fig_disliked)
