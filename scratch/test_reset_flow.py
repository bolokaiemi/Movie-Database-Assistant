import os
import sys
import json

# Setup sys.path to root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from werkzeug.security import check_password_hash
import sqlite3

def run_test():
    print("=========================================")
    print("Testing Secure Login & Reset Flow API")
    print("=========================================")
    
    # 1. Get database client
    client = app.test_client()
    
    # 2. Test login with correct default credentials
    print("[1] Testing normal login with 'Admin' / 'Admin.123'...")
    res = client.post('/api/login', json={'username': 'Admin', 'password': 'Admin.123'})
    data = json.loads(res.data)
    print("    Response:", data)
    assert data['success'] == True, "Failed default login"
    
    # 3. Test forgot password flow
    print("[2] Requesting forgot password reset code for 'Admin'...")
    res = client.post('/api/forgot_password', json={'username': 'Admin'})
    data = json.loads(res.data)
    print("    Response:", data)
    assert data['success'] == True, "Failed forgot password request"
    
    # Retrieve the reset code from the DB
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "movies.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT reset_code, reset_expiry FROM admin_credentials WHERE username = 'Admin'")
    code, expiry = cur.fetchone()
    conn.close()
    print(f"    Code retrieved from DB: {code} (expires at {expiry})")
    assert code is not None, "Reset code was not saved in database"
    
    # 4. Test resetting password with invalid code
    print("[3] Attempting password reset with invalid code...")
    res = client.post('/api/reset_password', json={
        'username': 'Admin',
        'reset_code': '000000',
        'new_password': 'NewPassword123'
    })
    data = json.loads(res.data)
    print("    Response:", data)
    assert data['success'] == False, "Password reset should have failed with invalid code"
    
    # 5. Test resetting password with valid code
    print("[4] Attempting password reset with correct code...")
    res = client.post('/api/reset_password', json={
        'username': 'Admin',
        'reset_code': code,
        'new_password': 'NewPassword123'
    })
    data = json.loads(res.data)
    print("    Response:", data)
    assert data['success'] == True, "Failed password reset"
    
    # 6. Test login with old password (should fail)
    print("[5] Verifying old password 'Admin.123' no longer works...")
    res = client.post('/api/login', json={'username': 'Admin', 'password': 'Admin.123'})
    data = json.loads(res.data)
    print("    Response:", data)
    assert data['success'] == False, "Old password should not work"
    
    # 7. Test login with new password (should succeed)
    print("[6] Verifying new password 'NewPassword123' works...")
    res = client.post('/api/login', json={'username': 'Admin', 'password': 'NewPassword123'})
    data = json.loads(res.data)
    print("    Response:", data)
    assert data['success'] == True, "New password failed to authenticate"
    
    # 8. Restore original default password for the user's convenience
    print("[7] Restoring default credentials 'Admin.123'...")
    from werkzeug.security import generate_password_hash
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    hashed = generate_password_hash('Admin.123')
    cur.execute("UPDATE admin_credentials SET password_hash = ? WHERE username = 'Admin'", (hashed,))
    conn.commit()
    conn.close()
    print("    Restored!")
    
    print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_test()
