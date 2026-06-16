import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_chatbot_movie_context, post_process_chat_reply

def main():
    print("=========================================")
    print("Testing Chatbot Banner Context Integration")
    print("=========================================")
    
    # 1. Fetch the context
    print("[1] Building chatbot movie context...")
    try:
        context = get_chatbot_movie_context()
        print("Success! Context retrieved.")
        
        # Verify the banner section is present
        banner_marker = "Movies Currently Featured in the Homepage Slider Banner (Carousel):"
        if banner_marker in context:
            print("[PASS] Banner movies section found in the chatbot context.")
            
            # Print a snippet of the banner section
            banner_index = context.find(banner_marker)
            print("--- Context Snippet ---")
            print(context[banner_index:banner_index + 500])
            print("-----------------------")
        else:
            print("[FAIL] Banner movies section not found in context.")
            print("Context was:")
            print(context[:500])
            
    except Exception as e:
        print("[FAIL] Error occurred during context building:", e)
        
    # 2. Test post-processing of a banner movie query
    print("\n[2] Testing reply post-processing for banner movie placeholder...")
    try:
        sample_reply = "Here is the poster for Lee Cronin's The Mummy: [Poster URL from the context]"
        processed = post_process_chat_reply(sample_reply, "Tell me about Lee Cronin's The Mummy")
        print("Original:", sample_reply)
        print("Processed:", processed)
        if "http" in processed:
            print("[PASS] Post-processing successfully replaced the poster placeholder with the actual URL.")
        else:
            print("[FAIL] Poster placeholder was not replaced with URL.")
    except Exception as e:
        print("[FAIL] Error in post-process test:", e)


if __name__ == "__main__":
    main()
