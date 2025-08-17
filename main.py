import os
import feedparser
from atproto import Client
import google.generativeai as genai

def sanitize_text(text):
    """Removes any @ mentions from the text to prevent resolution errors."""
    words = text.split()
    sanitized_words = [word for word in words if not word.startswith('@')]
    return ' '.join(sanitized_words)

def create_bluesky_text(title):
    """Uses Gemini to create a summary that will appear above a link card."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    # Updated prompt to explicitly forbid @ mentions as a first line of defense.
    prompt = f"""
    You are an AI news bot for BlueSky. You are writing text that will appear ABOVE a rich link card.
    
    RULES:
    - Your response must be under 290 characters.
    - Summarize the article title in an engaging and concise way.
    - Include 2-3 relevant hashtags like #AI, #TechNews, #ArtificialIntelligence.
    - CRITICAL: DO NOT include any @ mentions or user handles in your response.

    Article Title: "{title}"
    
    Generate the summary text now:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None

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
                raw_post_text = create_bluesky_text(title)

                if raw_post_text:
                    print(f"✅ Step 2: Generated raw text from Gemini:\n{raw_post_text}")
                    
                    # --- THE FINAL FIX IS HERE ---
                    # We clean the text before using it.
                    sanitized_text = sanitize_text(raw_post_text)
                    print(f"✅ Step 3: Sanitized text (mentions removed):\n{sanitized_text}")
                    
                    final_post_content = f"{sanitized_text} {link}"
                    
                    client.post(text=final_post_content)
                    print("✅ Step 4: SUCCESS! Post has been sent to BlueSky!")
                else:
                    print("Could not generate post text from Gemini. Halting for this run.")
    
    print("Bot finished.")
