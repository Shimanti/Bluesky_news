import os
import feedparser
from atproto import Client  # This is the correct, simple import now
import google.generativeai as genai

# This prompt is clean and has proven to work well.
def create_bluesky_text(title):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    You are an AI news bot for BlueSky writing text that appears ABOVE a link card.
    RULES:
    - Your response must be under 290 characters.
    - Summarize the article title in an engaging way.
    - Include 2-3 relevant hashtags like #AI, #TechNews.
    - DO NOT include the URL. It will be in the link card.
    Article Title: "{title}"
    Generate the summary text now:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None

# This function is correct.
def get_last_posted_link(client, handle):
    try:
        response = client.get_author_feed(handle, limit=1)
        if not response.feed: return None
        latest_post = response.feed[0].post
        # We check the embed for the link card's URI
        if hasattr(latest_post.embed, 'external') and hasattr(latest_post.embed.external, 'uri'):
            return latest_post.embed.external.uri
    except Exception as e:
        print(f"Could not retrieve last post: {e}")
    return None

# --- THE CLEAN, MODERN WAY TO POST A LINK CARD ---
def post_to_bluesky(client, text_body, article_url):
    """Posts text and a rich link card to BlueSky."""
    try:
        # Step 1: The library needs to look at the URL first to create the embed
        response = client.app.bsky.embed.external.get(uri=article_url)
        embed = response.embed
        
        # Step 2: Post the text AND the generated embed card
        client.post(text=text_body, embed=embed)
        print("Successfully posted to BlueSky with a link card!")
    except Exception as e:
        print(f"Error posting to BlueSky: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Bot starting...")
    bsky_handle = os.environ.get("BLUESKY_HANDLE")
    bsky_password = os.environ.get("BLUESKY_APP_PASSWORD")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not all([gemini_key, bsky_handle, bsky_password]):
        print("ERROR: Make sure all environment variables are set.")
    else:
        title, link = get_latest_ai_news()
        if not (title and link):
            print("Could not find any news articles.")
        else:
            print(f"Found latest article: {title} ({link})")
            
            client = Client()
            client.login(bsky_handle, bsky_password)
            
            last_link = get_last_posted_link(client, bsky_handle)
            if link == last_link:
                print("This article has already been posted. No new content to share.")
            else:
                print("New article found. Generating post...")
                post_text = create_bluesky_text(title)

                if post_text:
                    print(f"Generated text (Length: {len(post_text)}):\n{post_text}")
                    post_to_bluesky(client, post_text, link)
                else:
                    print("Could not generate post text from Gemini.")
    
    print("Bot finished.")
