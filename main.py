# main.py

import feedparser
import os
from atproto import Client
import google.generativeai as genai

# --- Part A: Fetch the News ---
def get_latest_ai_news():
    """Fetches the latest AI news item from Google News RSS feed."""
    url = "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    if not feed.entries:
        return None, None
    # Get the most recent article
    latest_article = feed.entries[0]
    return latest_article.title, latest_article.link

 # main.py (continued...)

# --- Part B: Summarize with Gemini ---
def create_bluesky_post(title, link):
    """Uses Gemini to create a BlueSky post from a news title and link."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash') # Using the fast and cheap model

    prompt = f"""
    You are an AI news bot for the social media platform BlueSky.
    Your task is to create a short, engaging post about a new AI article.

    RULES:
    - The post must be under 300 characters.
    - Be informative and slightly enthusiastic.
    - Include 2-3 relevant hashtags like #AI, #ArtificialIntelligence, #TechNews.
    - ALWAYS include the full link to the article at the end.

    Article Title: "{title}"
    Article Link: {link}

    Now, generate the BlueSky post:
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None   

# main.py (continued...)

# --- Part C: Post to BlueSky ---
def post_to_bluesky(text):
    """Logs into BlueSky and sends a post."""
    client = Client()
    try:
        client.login(
            os.environ.get("BLUESKY_HANDLE"),
            os.environ.get("BLUESKY_APP_PASSWORD")
        )
        # The library automatically finds URLs and turns them into rich media cards!
        client.send_post(text)
        print("Successfully posted to BlueSky!")
    except Exception as e:
        print(f"Error posting to BlueSky: {e}")

 # main.py (continued...)

# --- Part D: Main Execution ---
if __name__ == "__main__":
    print("Bot starting...")

    # Check for credentials
    if not all([os.environ.get("GEMINI_API_KEY"), os.environ.get("BLUESKY_HANDLE"), os.environ.get("BLUESKY_APP_PASSWORD")]):
        print("ERROR: Make sure GEMINI_API_KEY, BLUESKY_HANDLE, and BLUESKY_APP_PASSWORD are set as environment variables.")
    else:
        title, link = get_latest_ai_news()

        if title and link:
            print(f"Found article: {title}")
            post_text = create_bluesky_post(title, link)

            if post_text:
                print(f"Generated post:\n{post_text}")
                post_to_bluesky(post_text)
            else:
                print("Could not generate post text.")
        else:
            print("Could not find any news articles.")
    
    print("Bot finished.")       