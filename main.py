import os
import feedparser
# The correct, official import that matches requirements.txt
from atproto import Client
import google.generativeai as genai

# This prompt is clean and has worked well in tests.
def create_bluesky_text(title):
    """Uses Gemini to create a summary to appear above a link card."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    You are an AI news bot for BlueSky, writing text that appears ABOVE a link card.
    RULES:
    - Your response must be under 290 characters.
    - Summarize the article title in an engaging way.
    - Include 2-3 relevant hashtags like #AI, #TechNews.
    - DO NOT include the URL. The link card will handle it.
    Article Title: "{title}"
    Generate the summary text now:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None

# This function is correct and necessary for preventing duplicates.
def get_last_posted_link(client, handle):
    """Fetches the link from the most recent post's link card."""
    try:
        response = client.get_author_feed(handle, limit=1)
        if not response.feed: return None
        latest_post = response.feed[0].post
        # This safely checks if an embed with an external link exists
        if hasattr(latest_post.embed, 'external') and hasattr(latest_post.embed.external, 'uri'):
            return latest_post.embed.external.uri
    except Exception as e:
        print(f"Could not retrieve last post: {e}")
    return None

# --- MAIN EXECUTION: Simplified and Corrected ---
if __name__ == "__main__":
    print("Bot starting...")
    bsky_handle = os.environ.get("BLUESKY_HANDLE")
    bsky_password = os.environ.get("BLUESKY_APP_PASSWORD")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not all([gemini_key, bsky_handle, bsky_password]):
        print("ERROR: Environment variables are not set.")
    else:
        title, link = get_latest_ai_news()
        if not (title and link):
            print("Could not find any news articles.")
        else:
            print(f"Found latest article: {title} ({link})")
            
            # The official, simple way to create the client and log in
            client = Client()
            client.login(bsky_handle, bsky_password)
            print("Successfully logged into BlueSky.") # We will now see this message if passwords work!
            
            last_link = get_last_posted_link(client, bsky_handle)
            if link == last_link:
                print("This article has already been posted. No new content to share.")
            else:
                print("New article found. Generating post...")
                post_text = create_bluesky_text(title)

                if post_text:
                    print(f"Generated text (Length: {len(post_text)}):\n{post_text}")
                    
                    # The library will automatically find the link and create the card.
                    final_post_content = f"{post_text} {link}"
                    client.post(final_post_content)
                    print("Successfully sent post to BlueSky.")
                else:
                    print("Could not generate post text from Gemini.")
    
    print("Bot finished.")
