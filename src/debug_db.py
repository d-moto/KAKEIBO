from database import Database

def test_settings():
    db = Database()
    print("Initial API Key:", db.get_setting("gemini_api_key"))
    
    test_key = "TEST_API_KEY_12345"
    print(f"Setting API Key to: {test_key}")
    db.set_setting("gemini_api_key", test_key)
    
    saved_key = db.get_setting("gemini_api_key")
    print(f"Retrieved API Key: {saved_key}")
    
    if saved_key == test_key:
        print("SUCCESS: API Key saved and retrieved correctly.")
    else:
        print("FAILURE: API Key mismatch.")

if __name__ == "__main__":
    test_settings()
