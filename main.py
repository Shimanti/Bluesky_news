import os
import sys
import traceback
import feedparser
from atproto import Client
import google.generativeai as genai

def log_step(step_name, status="START"):
    """Log each step clearly"""
    if status == "START":
        print(f"\n🔄 STEP: {step_name}")
    elif status == "SUCCESS":
        print(f"✅ SUCCESS: {step_name}")
    elif status == "ERROR":
        print(f"❌ ERROR: {step_name}")

def get_latest_ai_news():
    """Fetches the title of the latest AI news item from Google News."""
    log_step("Fetching AI news from RSS")
    
    url = "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"
    
    try:
        print(f"📡 Requesting RSS from: {url}")
        feed = feedparser.parse(url)
        
        print(f"📊 Feed status: {getattr(feed, 'status', 'Unknown')}")
        print(f"📊 Found {len(feed.entries)} entries")
        
        if hasattr(feed, 'bozo') and feed.bozo:
            print(f"⚠️ RSS parsing warning: {feed.bozo_exception}")
        
        if not feed.entries:
            log_step("No RSS entries found", "ERROR")
            return None
            
        title = feed.entries[0].title
        link = feed.entries[0].link
        print(f"📰 Latest article: {title[:100]}...")
        log_step("RSS fetch", "SUCCESS")
        return title, link
        
    except Exception as e:
        log_step(f"RSS fetch failed: {e}", "ERROR")
        print(f"Full error: {traceback.format_exc()}")
        return None

def create_bluesky_text(title):
    """Uses Gemini to create a TEXT-ONLY post about a news title."""
    log_step("Generating post with Gemini AI")
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        log_step("Gemini API key missing", "ERROR")
        return None
    
    print(f"🔑 Gemini API key found (length: {len(gemini_key)})")
    
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an AI news bot for BlueSky. Write a short, engaging, TEXT-ONLY post.
        
        RULES:
        - Under 230 characters
        - Summarize the article title engagingly
        - Include 2 hashtags like #AI #TechNews
        - NO URLs or links
        
        Article Title: "{title}"
        
        Generate the post:
        """
        
        print("🤖 Sending request to Gemini...")
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            log_step("Gemini returned empty response", "ERROR")
            return None
            
        generated_text = response.text.strip()
        print(f"📝 Generated ({len(generated_text)} chars): {generated_text}")
        
        if len(generated_text) > 300:  # BlueSky limit
            print("⚠️ Text too long, truncating...")
            generated_text = generated_text[:297] + "..."
        
        log_step("Gemini text generation", "SUCCESS")
        return generated_text
        
    except Exception as e:
        log_step(f"Gemini generation failed: {e}", "ERROR")
        print(f"Full error: {traceback.format_exc()}")
        return None

def post_to_bluesky(text, handle, password):
    """Post to BlueSky with detailed error handling"""
    log_step("Posting to BlueSky")
    
    if not handle or not password:
        log_step("BlueSky credentials missing", "ERROR")
        return False
    
    print(f"🔑 Handle: {handle}")
    print(f"🔑 Password: {'*' * len(password)} (length: {len(password)})")
    
    try:
        print("🔄 Creating BlueSky client...")
        client = Client()
        
        print("🔄 Attempting login...")
        client.login(handle, password)
        print("✅ Login successful!")
        
        print(f"📤 Posting text: {text}")
        result = client.post(text=text)
        print(f"📮 Post result: {result}")
        
        log_step("BlueSky posting", "SUCCESS")
        return True
        
    except Exception as e:
        log_step(f"BlueSky posting failed: {e}", "ERROR")
        print(f"Full error: {traceback.format_exc()}")
        
        # Specific error guidance
        error_str = str(e).lower()
        if "authentication" in error_str or "login" in error_str:
            print("\n🔍 AUTHENTICATION TROUBLESHOOTING:")
            print("1. Make sure you're using an App Password, not your regular password")
            print("2. Go to BlueSky Settings → Privacy & Security → App Passwords")
            print("3. Create a new App Password for this bot")
            print("4. Use the FULL handle format: username.bsky.social")
        elif "rate" in error_str or "limit" in error_str:
            print("\n🔍 RATE LIMIT TROUBLESHOOTING:")
            print("1. You may be posting too frequently")
            print("2. Try reducing the frequency of your bot")
        
        return False

def main():
    """Main execution with comprehensive error handling"""
    print("=" * 50)
    print("🚀 BLUESKY AI NEWS BOT STARTING")
    print("=" * 50)
    
    # System info
    print(f"🐍 Python: {sys.version}")
    print(f"📂 Working directory: {os.getcwd()}")
    
    # Environment check
    log_step("Checking environment variables")
    bsky_handle = os.environ.get("BLUESKY_HANDLE")
    bsky_password = os.environ.get("BLUESKY_APP_PASSWORD")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    print(f"BLUESKY_HANDLE: {'✅ Set' if bsky_handle else '❌ Missing'}")
    print(f"BLUESKY_APP_PASSWORD: {'✅ Set' if bsky_password else '❌ Missing'}")
    print(f"GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Missing'}")
    
    if not all([bsky_handle, bsky_password, gemini_key]):
        print("\n❌ FATAL: Missing required environment variables")
        print("Make sure these are set in your GitHub Secrets:")
        print("- BLUESKY_HANDLE (e.g., username.bsky.social)")
        print("- BLUESKY_APP_PASSWORD (from BlueSky app settings)")
        print("- GEMINI_API_KEY (from Google AI Studio)")
        sys.exit(1)
    
    log_step("Environment check", "SUCCESS")
    
    # Step 1: Get news
    article_title = get_latest_ai_news()
    if not article_title:
        print("❌ FATAL: Could not fetch news article")
        sys.exit(1)
    
    # Step 2: Generate post
    post_text = create_bluesky_text(article_title)
    if not post_text:
        print("❌ FATAL: Could not generate post text")
        sys.exit(1)
    
    # Step 3: Post to BlueSky
    success = post_to_bluesky(post_text, bsky_handle, bsky_password)
    if not success:
        print("❌ FATAL: Could not post to BlueSky")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 BOT COMPLETED SUCCESSFULLY!")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)
