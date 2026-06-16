import json
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app

def run_tests():
    print("=========================================")
    print("Testing Secure Booking Cancellation Flow API (Flask Test Client)")
    print("=========================================")

    # Initialize flask test client
    client = app.test_client()

    # 1. Simulate a purchase
    print("\n[1] Creating a test purchase...")
    import random
    ticket_code = f"TEST-CANCEL-{random.randint(1000, 9999)}"
    payload_purchase = {
        "user_id": 1,
        "movie_id": 1,
        "qr_code_link": ticket_code,
        "popcorn_size": "None",
        "drink_size": "None",
        "concessions_total": 0.0,
        "has_ticket": True
    }
    r = client.post("/api/purchase", json=payload_purchase)
    res_data = json.loads(r.data.decode("utf-8"))
    print("    Response:", res_data)
    assert res_data.get("success") == True

    # 2. Verify booking before cancellation
    print("\n[2] Verifying booking exists and is ACTIVE...")
    r = client.post("/api/verify_booking", json={"ticket_code": ticket_code})
    res_data = json.loads(r.data.decode("utf-8"))
    details = res_data.get("details")
    print("    Details:", details)
    assert res_data.get("success") == True
    assert details.get("status") == "active"
    assert details.get("ticket_code") == ticket_code

    # 3. Cancel the booking
    print("\n[3] Cancelling the booking...")
    r = client.post("/api/cancel_booking", json={"ticket_code": ticket_code})
    res_data = json.loads(r.data.decode("utf-8"))
    print("    Response:", res_data)
    assert res_data.get("success") == True

    # 4. Verify booking is now CANCELLED
    print("\n[4] Re-verifying booking status...")
    r = client.post("/api/verify_booking", json={"ticket_code": ticket_code})
    res_data = json.loads(r.data.decode("utf-8"))
    details = res_data.get("details")
    print("    Details:", details)
    assert res_data.get("success") == True
    assert details.get("status") == "cancelled"

    # 5. Verify cancelling again fails
    print("\n[5] Attempting to cancel already cancelled booking...")
    r = client.post("/api/cancel_booking", json={"ticket_code": ticket_code})
    res_data = json.loads(r.data.decode("utf-8"))
    print("    Response:", res_data)
    assert res_data.get("success") == False
    assert "already cancelled" in res_data.get("message").lower()

    print("\n[SUCCESS] ALL CANCELLATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print("\n[FAILURE] A test assertion failed:", e)
        sys.exit(1)
