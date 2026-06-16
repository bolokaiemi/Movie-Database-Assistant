import os
import sys
# Reconfigure stdout to support unicode emoji printing in Windows terminal
sys.stdout.reconfigure(encoding='utf-8')
# Set up import path to point to root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_clean_embed_trailer, post_process_chat_reply

# Test 1: Prioritization and cleaning of database default_url (No TMDB)
print("--- TEST 1: default_url cleaning (No TMDB) ---")
result_url = get_clean_embed_trailer("Inception", "https://www.youtube.com/watch?v=YoHD9XEInc0")
print("Input standard link -> Expected embed link:")
print("Result:", result_url)
assert result_url == "https://www.youtube.com/embed/YoHD9XEInc0", "Failed converting standard link!"

result_url_empty = get_clean_embed_trailer("Avatar", "")
print("\nInput empty link -> Expected empty string (TMDB disabled):")
print("Result:", repr(result_url_empty))
assert result_url_empty == "", "Expected empty string when no trailer is stored."

# Test 2: post_process_chat_reply placeholder replacement
print("\n--- TEST 2: post_process_chat_reply placeholder replacement ---")
user_msg = "Show me the trailer for inception"
reply_placeholder = "Sure! Here is the trailer: <div style='margin-top:8px;'><iframe src='<trailer_embed_url>'></iframe></div>"
processed = post_process_chat_reply(reply_placeholder, user_msg)
print("Before:\n", reply_placeholder)
print("After:\n", processed)

# Test 3: Programmatic trailer injection fallback to local DB details page
print("\n--- TEST 3: Programmatic trailer injection fallback to local database ---")
user_msg_2 = "Can I watch the trailer for Titanic?"
reply_no_iframe = "Titanic is a great romance film about the Titanic ship."
processed_injected = post_process_chat_reply(reply_no_iframe, user_msg_2)
print("Before:\n", reply_no_iframe)
print("After:\n", processed_injected)

print("\nAll tests completed successfully!")
