import os
import feedparser
from atproto import Client
import google.generativeai as genai

def create_bluesky_text(title):
    """Uses Gemini to create a TEXT-ONLY post about a news title."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    # This prompt is now extremely simple and clear.
    prompt = f"""
    You are an AI news bot for BlueSky. Your task is to write a short, engaging, TEXT-ONLY post.
    
    RULES:
    - Your response must be under 290 characters.
    - Summarize the article title in an engaging way.
    - Include 2-3 relevant hashtags like #AI, #TechNews.
    - CRITICAL: DO NOT include any URL or link in your response.

    Article Title: "{title}"
    
    Generate the text-only post now:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None

def get_last_post_text(client, handle):
    """Fetches the text content of the most recent post to prevent duplicates."""
    try:
        response = client.get_author_feed(handle, limit=1)
        if not response.feed: return None
        # Return the raw text of the last post
        return response.feed[0].post.record.text
    except Exception as e:
        print(f"Could not retrieve last post text: {e}")
    return None

if __name__ == "__main__":
    print("Bot starting...")
    bsky_handle = os.environ.get("BLUESKY_HANDLE")
    bsky_password = os.environ.get("BLUESKY_APP_PASSWORD")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not all([gemini_key, bsky_handle, bsky_password]):
        print("ERROR: Environment variables are not set. Halting.")
    else:
        title, link = get_latest_ai_news()
        if not title:
            print("Could not find any news articles. Halting.")
        else:
            print(f"Found latest article title: {title}")
            
            client = Client()
            client.login(bsky_handle, bsky_password)
            print("✅ Step 1: Successfully logged into BlueSky.")
            
            # Generate the new text first
            new_post_text = create_bluesky_text(title)

            if new_post_text:
                print(f"✅ Step 2: Generated text from Gemini:\n{new_post_text}")
                
                # Check for duplicates by comparing the new text to the last post's text
                last_post_text = get_last_post_text(client, bsky_handle)
                
                # We need to clean up the last post text to compare apples to apples
                # The API returns the text with the URL, so we split and take the first part
                if last_post_text and "https" in last_post_text:
                    last_post_text = last_post_text.split("https")[0].strip()

                if new_post_text == last_post_text:
                    print("This exact post has already been made. Halting.")
                else:
                    # THE SIMPLEST POST COMMAND POSSIBLE
                    client.post(text=new_post_text)
                    print("✅ Step 3: SUCCESS! Text-only post has been sent to BlueSky!")
            else:
                print("Could not generate post text from Gemini. Halting for this run.")
    
    print("Bot finished.")
