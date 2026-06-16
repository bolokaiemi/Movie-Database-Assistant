import sys
import os
import json

# Ensure sys.stdout uses utf-8 encoding to prevent Windows console emoji errors
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, detect_language

def run_tests():
    print("=========================================")
    print("Testing Smart Language Auto-Switching API")
    print("=========================================")

    # Test 1: Language Detection Helpers for Cues
    print("\n[1] Testing detect_language() helper with explicit cues...")
    
    de_cue = detect_language("Please explain the showtimes in German")
    print(f"    - 'Please explain the showtimes in German' -> Detected: {de_cue}")
    assert de_cue == "de", "Failed to detect German cue!"

    es_cue = detect_language("responder en español please")
    print(f"    - 'responder en español please' -> Detected: {es_cue}")
    assert es_cue == "es", "Failed to detect Spanish cue!"

    fr_cue = detect_language("Could you explain this in French?")
    print(f"    - 'Could you explain this in French?' -> Detected: {fr_cue}")
    assert fr_cue == "fr", "Failed to detect French cue!"

    it_cue = detect_language("Explain this in Italian")
    print(f"    - 'Explain this in Italian' -> Detected: {it_cue}")
    assert it_cue == "it", "Failed to detect Italian cue!"

    en_cue = detect_language("Write your response in English")
    print(f"    - 'Write your response in English' -> Detected: {en_cue}")
    assert en_cue == "en", "Failed to detect English cue!"

    print("    [PASS] detect_language() helper functions pass all cues tests.")

    # Test 2: Chat API integration with Mock Client
    print("\n[2] Testing /chat API endpoint language synchronization...")
    client = app.test_client()

    # German test
    print("    - Sending: 'Explain the movie Inception in German language.'")
    resp_de = client.post("/chat", json={
        "message": "Explain the movie Inception in German language.",
        "history": []
    })
    data_de = json.loads(resp_de.data)
    print(f"      Response status: {resp_de.status_code}")
    print(f"      Returned language code: {data_de.get('language')}")
    print(f"      Snippet: {data_de.get('reply')[:120]}...")
    assert data_de.get("language") == "de", "Expected 'de' language code in API reply!"

    # Spanish test
    print("    - Sending: 'Hola! Responder en español por favor.'")
    resp_es = client.post("/chat", json={
        "message": "Hola! Responder en español por favor.",
        "history": []
    })
    data_es = json.loads(resp_es.data)
    print(f"      Response status: {resp_es.status_code}")
    print(f"      Returned language code: {data_es.get('language')}")
    print(f"      Snippet: {data_es.get('reply')[:120]}...")
    assert data_es.get("language") == "es", "Expected 'es' language code in API reply!"

    # French test
    print("    - Sending: 'Explique en français s'il vous plaît.'")
    resp_fr = client.post("/chat", json={
        "message": "Explique en français s'il vous plaît.",
        "history": []
    })
    data_fr = json.loads(resp_fr.data)
    print(f"      Response status: {resp_fr.status_code}")
    print(f"      Returned language code: {data_fr.get('language')}")
    print(f"      Snippet: {data_fr.get('reply')[:120]}...")
    assert data_fr.get("language") == "fr", "Expected 'fr' language code in API reply!"

    # Italian test
    print("    - Sending: 'Explain the movie Inception in Italian language.'")
    resp_it = client.post("/chat", json={
        "message": "Explain the movie Inception in Italian language.",
        "history": []
    })
    data_it = json.loads(resp_it.data)
    print(f"      Response status: {resp_it.status_code}")
    print(f"      Returned language code: {data_it.get('language')}")
    print(f"      Snippet: {data_it.get('reply')[:120]}...")
    assert data_it.get("language") == "it", "Expected 'it' language code in API reply!"

    print("\n[SUCCESS] ALL LANGUAGE AUTO-SWITCHING TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
