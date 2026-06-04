import sys
import os

# Add parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import detect_language

def run_tests():
    test_cases = [
        # English
        ("Can you recommend a good sci-fi movie?", "en"),
        ("Hi there, how are you doing today?", "en"),
        ("Tell me about Titanic.", "en"),
        
        # German
        ("Kannst du mir einen guten Film empfehlen?", "de"),
        ("Hallo, wie geht es dir?", "de"),
        ("Zeig mir den Trailer für Inception.", "de"),
        
        # French
        ("Pouvez-vous me conseiller un bon film?", "fr"),
        ("Bonjour, comment ça va?", "fr"),
        ("Je voudrais voir la bande-annonce.", "fr"),
        
        # Spanish
        ("¿Puedes recomendarme una película de acción?", "es"),
        ("Hola, ¿cómo estás?", "es"),
        ("Quiero ver el tráiler de Titanic.", "es")
    ]
    
    passed = 0
    total = len(test_cases)
    
    print("Running Language Detection Verification Tests...")
    print("-" * 50)
    for idx, (text, expected) in enumerate(test_cases, 1):
        detected = detect_language(text)
        status = "PASSED" if detected == expected else "FAILED"
        if status == "PASSED":
            passed += 1
        print(f"[{idx}/{total}] Text: '{text}'")
        print(f"      Expected: {expected} | Detected: {detected} | Result: {status}")
        print("-" * 50)
        
    print(f"Results: {passed}/{total} tests passed.")
    if passed == total:
        print("ALL TESTS PASSED SUCCESSFULLY! 🎉")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED! ❌")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
