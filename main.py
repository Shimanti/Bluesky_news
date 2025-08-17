import os
import feedparser
from atproto import Client, models
import google.generativeai as genai

# --- A simpler, more direct prompt for Gemini ---
def create_bluesky_text(title):
    """Uses Gemini to create a summary to appear above a link card."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an AI news bot for BlueSky. You are writing text that will appear ABOVE a link preview card.
    
    RULES:
    - Your response must be under 290 characters.
    - Summarize the article title in an engaging way.
    - Include 2-3 relevant hashtags like #AI, #TechNews, #ArtificialIntelligence.
    - DO NOT include the URL in your response. It will be added automatically.

    Article Title: "{title}"
    
    Generate the summary text now:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None

# --- Get Last Post ---
def get_last_posted_link(client, handle):
    """Fetches the link from the most recent post's link card."""
    try:
        response = client.get_author_feed(handle, limit=1)
        if not response.feed: return None
        latest_post = response.feed[0].post
        if latest_post.embed and isinstance(latest_post.embed, models.AppBskyEmbedExternal.Main):
            return latest_post.embed.external.uri
    except Exception as e:
        print(f"Could not retrieve last post: {e}")
    return None

# --- MODIFIED Part: The Final Fix is Here ---
def post_to_bluesky(client, text_body, original_article_url):
    """Sends a post to BlueSky, letting it create a rich link card."""
    try:
        # THE FIX: We removed `text=` from the function call.
        # The library automatically finds the URL in the string and creates the card.
        client.send_post(f"{text_body} {original_article_url}")
        print("Successfully posted to BlueSky with a link card!")
    except Exception as e:
        print(f"Error posting to BlueSky: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    print("Bot starting...")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    bsky_handle = os.environ.get("BLUESKY_HANDLE")
    bsky_password = os.environ.get("BLUESKY_APP_PASSWORD")

    if not all([gemini_key, bsky_handle, bsky_password]):
        print("ERROR: Make sure all environment variables are set.")
    else:
        title, link = get_latest_ai_news()
        if not (title and link):
            print("Could not find any news articles.")
        else:
            print(f"Found latest article: {title}")
            
            client = Client()
            client.login(bsky_handle, bsky_password)
            
            last_link = get_last_posted_link(client, bsky_handle)
            if link == last_link:
                print("This article has already been posted. No new content to share.")
            else:
                print("New article found. Generating post...")
                post_text = create_bluesky_text(title)

                if post_text:
                    print(f"Generated text part (Length: {len(post_text)}):\n{post_text}")
                    
                    if len(post_text) > 300:
                        print("ERROR: Generated text is still over 300 characters. Skipping.")
                    else:
                        post_to_bluesky(client, post_text, link)
                else:
                    print("Could not generate post text from Gemini.")
    
    print("Bot finished.")
