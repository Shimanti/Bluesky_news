import os
import feedparser
from atproto import Client
import google.generativeai as genai
import sys

def get_latest_ai_news():
    """Fetches the title of the latest AI news item from Google News."""
    print("📰 Fetching AI news...")
    url = "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(url)
        print(f"RSS feed parsed. Found {len(feed.entries)} entries.")
        
        if not feed.entries:
            print("❌ No entries found in RSS feed.")
            return None
            
        title = feed.entries[0].title
        print(f"✅ Latest article title: {title}")
        return title
        
    except Exception as e:
        print(f"❌ Error fetching RSS feed: {e}")
        return None

def create_bluesky_text(title):
    """Uses Gemini to create a TEXT-ONLY post about a news title."""
    print("🤖 Generating post text with Gemini...")
    
    # Check if API key exists
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return None
    
    print("✅ Gemini API key found")
    
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an AI news bot for BlueSky. Your task is to write a short, engaging, TEXT-ONLY post.
        
        RULES:
        - Your response must be under 230 characters.
        - Summarize the article title in an engaging way.
        - Include 2 relevant hashtags like #AI, #TechNews.
        - CRITICAL: DO NOT include any URL or link in your response.
        Article Title: "{title}"
        
        Generate the text-only post now:
        """
        
        response = model.generate_content(prompt)
        generated_text = response.text.strip()
        print(f"✅ Generated text ({len(generated_text)} chars): {generated_text}")
        return generated_text
        
    except Exception as e:
        print(f"❌ Error generating content with Gemini: {e}")
        return None

def test_bluesky_auth(handle, password):
    """Test BlueSky authentication separately"""
    print("🔐 Testing BlueSky authentication...")
    
    if not handle:
        print("❌ BLUESKY_HANDLE not found in environment variables")
        return False
        
    if not password:
        print("❌ BLUESKY_APP_PASSWORD not found in environment variables")
        return False
    
    print(f"✅ Handle found: {handle}")
    print("✅ App password found (hidden)")
    
    try:
        client = Client()
        print("🔄 Attempting login...")
        client.login(handle, password)
        print("✅ BlueSky login successful!")
        return client
        
    except Exception as e:
        print(f"❌ BlueSky login failed: {e}")
        print("Common issues:")
        print("- Make sure you're using an App Password, not your regular password")
        print("- Check that your handle is correct (e.g., username.bsky.social)")
        print("- Verify the App Password was created correctly in BlueSky settings")
        return False

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("🚀 Bot starting...")
    print(f"Python version: {sys.version}")
    
    # Get environment variables
    bsky_handle = os.environ.get("BLUESKY_HANDLE")
    bsky_password = os.environ.get("BLUESKY_APP_PASSWORD")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    # Debug environment variables (without showing sensitive data)
    print(f"Environment check:")
    print(f"- BLUESKY_HANDLE: {'✅ Set' if bsky_handle else '❌ Missing'}")
    print(f"- BLUESKY_APP_PASSWORD: {'✅ Set' if bsky_password else '❌ Missing'}")
    print(f"- GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Missing'}")
    
    if not all([gemini_key, bsky_handle, bsky_password]):
        print("❌ ERROR: One or more environment variables are missing. Halting.")
        sys.exit(1)
    
    # Step 1: Test BlueSky authentication first
    client = test_bluesky_auth(bsky_handle, bsky_password)
    if not client:
        print("❌ Authentication failed. Halting.")
        sys.exit(1)
    
    # Step 2: Get the news title
    article_title = get_latest_ai_news()
    if not article_title:
        print("❌ Could not find any news articles. Halting.")
        sys.exit(1)
    
    # Step 3: Generate the post text
    post_text = create_bluesky_text(article_title)
    if not post_text:
        print("❌ Could not generate post text from Gemini. Halting.")
        sys.exit(1)
    
    # Step 4: Post to BlueSky
    try:
        print("📤 Posting to BlueSky...")
        client.post(text=post_text)
        print("🎉 SUCCESS! Post has been sent to BlueSky!")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR during posting: {e}")
        sys.exit(1)
    
    print("✅ Bot finished successfully!")
