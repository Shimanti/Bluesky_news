import os
import feedparser
import httpx  # Switched from requests to httpx
from atproto import Client, models
import google.generativeai as genai

# --- NEW Part: URL Shortener using CleanURI (More Robust) ---
def shorten_url(long_url):
    """Shortens a URL using the CleanURI API."""
    api_url = "https://cleanuri.com/api/v1/shorten"
    try:
        # Use a POST request with the URL as data
        with httpx.Client(timeout=10.0) as client:
            response = client.post(api_url, data={'url': long_url})
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            # The result is in JSON format
            result_json = response.json()
            short_url = result_json.get("result_url")

            if short_url:
                print(f"Successfully shortened URL to: {short_url}")
                return short_url
            else:
                print("CleanURI API did not return a short URL.")
                return long_url # Fallback if JSON is weird

    except httpx.RequestError as e:
        print(f"An exception occurred while shortening URL: {e}")
        return long_url  # Fallback to the long URL if the API call fails

# --- MODIFIED Part: Gemini Post Generation (Stricter Prompt) ---
def create_bluesky_text(title):
    """Uses Gemini to create ONLY the text part of a BlueSky post."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an AI news bot for BlueSky. Your task is to write a very short, concise summary of an AI article title.

    **CRITICAL RULE: Your entire response, including hashtags, MUST be under 240 characters. This is a hard limit.**

    - Be informative and engaging.
    - Include 2-3 relevant hashtags like #AI, #TechNews.
    - DO NOT include the URL in your response. The URL will be added separately.
    - EXAMPLE of a good response: "Google's new AI can write poetry! The model shows surprising creative flair, raising new questions about machine artistry. #AI #GoogleAI #Poetry"

    Article Title: "{title}"

    Generate the post text now, obeying the strict character limit.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if len(text) > 240:
            print("Warning: Gemini response exceeded 240 characters. Truncating.")
            text = text[:237] + "..."
        return text
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None

# --- Part C: Get Last Post and Post to BlueSky (Unchanged) ---
def get_last_posted_link(client, handle):
    try:
        response = client.get_author_feed(handle, limit=1)
        if not response.feed: return None
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

# --- Main Execution (Unchanged) ---
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
                print("New article found. Generating and assembling post...")
                post_text_only = create_bluesky_text(title)
                if post_text_only:
                    print(f"Generated text part:\n{post_text_only}")
                    short_link = shorten_url(link)
                    final_post = f"{post_text_only}\n{short_link}"
                    print(f"Final post to be sent (Length: {len(final_post)} chars):\n{final_post}")
                    if len(final_post) > 300:
                        print("ERROR: Final generated post is still over 300 characters. Skipping post.")
                    else:
                        post_to_bluesky(client, final_post)
                else:
                    print("Could not generate post text from Gemini.")
    
    print("Bot finished.")
