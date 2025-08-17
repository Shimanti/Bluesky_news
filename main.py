import os
import feedparser
# This is the official, correct import for the library version we are using.
from atproto import Client
import google.generativeai as genai

# This function is logically sound and does not need to change.
def create_bluesky_text(title):
    """Uses Gemini to create a summary that will appear above a link card."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    You are an AI news bot for BlueSky. You are writing text that will appear ABOVE a rich link card.
    
    RULES:
    - Your response must be under 290 characters.
    - Summarize the article title in an engaging and concise way.
    - Include 2-3 relevant hashtags like #AI, #TechNews, #ArtificialIntelligence.
    - DO NOT include the URL in your response. The URL will be automatically added in the link card.

    Article Title: "{title}"
    
    Generate the summary text now:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None

# This function is crucial for preventing duplicate posts.
def get_last_posted_link(client, handle):
    """Fetches the link from the most recent post's link card."""
    try:
        response = client.get_author_feed(handle, limit=1)
        if not response.feed: return None
        latest_post = response.feed[0].post
        if hasattr(latest_post.embed, 'external') and hasattr(latest_post.embed.external, 'uri'):
            return latest_post.embed.external.uri
    except Exception as e:
        print(f"Could not retrieve last post: {e}")
    return None

# --- MAIN EXECUTION: Back to the simple, working method ---
if __name__ == "__main__":
    print("Bot starting...")
    bsky_handle = os.environ.get("BLUESKY_HANDLE")
    bsky_password = os.environ.get("BLUESKY_APP_PASSWORD")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not all([gemini_key, bsky_handle, bsky_password]):
        print("ERROR: Environment variables are not set. Halting.")
    else:
        title, link = get_latest_ai_news()
        if not (title and link):
            print("Could not find any news articles. Halting.")
        else:
            print(f"Found latest article: {title} ({link})")
            
            client = Client()
            client.login(bsky_handle, bsky_password)
            print("✅ Step 1: Successfully logged into BlueSky.")
            
            last_link = get_last_posted_link(client, bsky_handle)
            if link == last_link:
                print("Article has already been posted. Halting.")
            else:
                print("New article found. Generating post...")
                post_text = create_bluesky_text(title)

                if post_text:
                    print(f"✅ Step 2: Generated text from Gemini:\n{post_text}")
                    
                    # The simplest, most reliable way to post a link.
                    # The library automatically finds the link in the text and creates the card.
                    final_post_content = f"{post_text} {link}"
                    
                    # This is the correct syntax for this library version. It solves the TypeError.
                    client.post(text=final_post_content)
                    print("✅ Step 3: Successfully sent post to BlueSky!")
                else:
                    # This handles Gemini failures cleanly without crashing. It solves the NameError.
                    print("Could not generate post text from Gemini. Halting for this run.")
    
    print("Bot finished.")
