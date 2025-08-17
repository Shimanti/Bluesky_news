import os
import feedparser
from atproto import Client
import google.generativeai as genai

def get_latest_ai_news():
    """Fetches the title of the latest AI news item from Google News."""
    # This function was missing, causing the NameError. It is now restored.
    url = "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    if not feed.entries:
        return None
    # Return only the title of the most recent article
    return feed.entries[0].title

def create_bluesky_text(title):
    """Uses Gemini to create a TEXT-ONLY post about a news title."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
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

# --- MAIN EXECUTION: The simplest possible working script ---
if __name__ == "__main__":
    print("Bot starting...")
    bsky_handle = os.environ.get("BLUESKY_HANDLE")
    bsky_password = os.environ.get("BLUESKY_APP_PASSWORD")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not all([gemini_key, bsky_handle, bsky_password]):
        print("ERROR: Environment variables are not set. Halting.")
    else:
        # Step 1: Get the news title.
        article_title = get_latest_ai_news()
        
        if article_title:
            print(f"Found article title: {article_title}")
            
            # Step 2: Generate the post text.
            post_text = create_bluesky_text(article_title)

            if post_text:
                print(f"Generated text from Gemini:\n{post_text}")
                
                # Step 3: Log in and post.
                try:
                    client = Client()
                    client.login(bsky_handle, bsky_password)
                    print("✅ Login Successful.")
                    
                    client.post(text=post_text)
                    print("✅ SUCCESS! Post has been sent to BlueSky!")
                
                except Exception as e:
                    print(f"CRITICAL ERROR during login or posting: {e}")

            else:
                print("Could not generate post text from Gemini. Halting.")
        else:
            print("Could not find any news articles. Halting.")
    
    print("Bot finished.")
