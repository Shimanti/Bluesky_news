import os
import feedparser
import requests
from atproto import Client, models
import google.generativeai as genai

# --- NEW Part: URL Shortener using is.gd (More Reliable) ---
def shorten_url(long_url):
    """Shortens a URL using the is.gd API."""
    api_url = f"https://is.gd/create.php?format=simple&url={long_url}"
    try:
        response = requests.get(api_url, timeout=5) # Added a 5-second timeout
        response.raise_for_status() # This will raise an error if the request fails (e.g., 4xx or 5xx)
        short_url = response.text
        print(f"Successfully shortened URL to: {short_url}")
        return short_url
    except requests.exceptions.RequestException as e:
        print(f"An exception occurred while shortening URL: {e}")
        return long_url # Fallback to the long URL if API fails

# --- MODIFIED Part: Gemini Post Generation (Stricter Prompt) ---
def create_bluesky_text(title):
    """Uses Gemini to create ONLY the text part of a BlueSky post."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # This prompt is now much more aggressive about the length limit.
    prompt = f"""
    You are an AI news bot for BlueSky. Your task is to write a very short, concise summary of an AI article title.

    **CRITICAL RULE: Your entire response, including hashtags, MUST be under 240 characters. This is a hard limit.**

    - Be informative and engaging.
    - Include 2-3 relevant hashtags like #AI, #TechNews.
    - DO NOT include the URL in your response. The URL will be added separately.
    - EXAMPLE of a good response: "Google's new AI can write poetry! The model, named 'Bard', shows surprising creative flair, raising new questions about machine artistry. #AI #GoogleAI #Poetry"

    Article Title: "{title}"

    Generate the post text now, obeying the strict character limit.
    """
    try:
        response = model.generate_content(prompt)
        # We will also add a manual trim just in case Gemini ignores the prompt
        text = response.text.strip()
        if len(text) > 240:
            print("Warning: Gemini response exceeded 240 characters. Truncating.")
            # Trim to 237 chars and add "..."
            text = text[:237] + "..."
        return text
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None

# --- Part C: Get Last Post and Post to BlueSky (Unchanged) ---
def get_last_posted_link(client, handle):
    try:
        response = client.get_author_feed(handle, limit=1)
        if not response.feed:
            return None
        latest_post = response.feed[0].post
        if latest_post.embed and isinstance(latest_post.embed, models.AppBskyEmbedExternal.Main):
            return latest_post.embed.external.uri
    except Exception as e:
        print(f"Could not retrieve last post: {e}")
    return None

def post_to_bluesky(client, text):
    try:
        client.send_post(text)
        print("Successfully posted to BlueSky!")
    except Exception as e:
        print(f"Error posting to BlueSky: {e}")

# --- MODIFIED Part: Main Execution (Slightly cleaner assembly) ---
if __name__ == "__main__":
    print("Bot starting...")
    # ... [rest of the script is the same] ...
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
                print("New article found. Generating and assembling post...")
                
                post_text_only = create_bluesky_text(title)

                if post_text_only:
                    print(f"Generated text part:\n{post_text_only}")
                    
                    short_link = shorten_url(link)
                    
                    final_post = f"{post_text_only}\n{short_link}" # Simplified the assembly
                    print(f"Final post to be sent (Length: {len(final_post)} chars):\n{final_post}")

                    if len(final_post) > 300:
                        print("ERROR: Final generated post is still over 300 characters. Skipping post.")
                    else:
                        post_to_bluesky(client, final_post)
                else:
                    print("Could not generate post text from Gemini.")
    
    print("Bot finished.")
