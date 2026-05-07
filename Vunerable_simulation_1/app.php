<?php
/**
 * Sim 1 — Vulnerable PHP App (OSWE Format)
 * ==========================================
 * A realistic-looking "student portal" app.
 * Contains intentional vulns — find them in 90 min (code only).
 * Then confirm each with payloads in the next 90 min.
 *
 * Setup:
 *   php -S 127.0.0.1:8080
 *   Visit http://127.0.0.1:8080/vulnerable_app.php
 */

session_start();

// ── Fake DB (no MySQL needed) ──────────────────────────────
$users = [
    "admin" => ["password" => "5f4dcc3b5aa765d61d8327deb882cf99", "role" => "admin"], // md5("password")
    "alice"  => ["password" => "7abdccbea8473767e91378e37850d296", "role" => "user"],  // md5("alice123")
    "bob"    => ["password" => "3782b671390b01a8b68fe05e8a6ad00b", "role" => "user"],  // md5("bob456")
];

$notes = [
    1 => ["owner" => "alice", "content" => "Buy groceries"],
    2 => ["owner" => "alice", "content" => "Secret project notes — API key: sk-1234ABCD"],
    3 => ["owner" => "bob",   "content" => "Bob's private note"],
    4 => ["owner" => "admin", "content" => "Admin credentials backup: admin/SuperSecret99"],
];

// ── Router ────────────────────────────────────────────────
$action = $_GET['action'] ?? 'home';

switch ($action) {
    case 'login':    handle_login($users); break;
    case 'logout':   handle_logout(); break;
    case 'dashboard': handle_dashboard($notes); break;
    case 'note':     handle_note($notes); break;
    case 'search':   handle_search($notes); break;
    case 'profile':  handle_profile(); break;
    case 'upload':   handle_upload(); break;
    case 'admin':    handle_admin($users); break;
    case 'ping':     handle_ping(); break;
    default:         handle_home(); break;
}


// ════════════════════════════════════════════════════════════
// HANDLERS
// ════════════════════════════════════════════════════════════

// ── Home ──────────────────────────────────────────────────
function handle_home() {
    echo render_layout("Home", '
        <h2>Welcome to StudyPortal</h2>
        <p><a href="?action=login">Login</a></p>
    ');
}

// ── Login ─────────────────────────────────────────────────
// VULN 1: No CSRF token on login form
// VULN 2: Username reflected directly into error message (XSS)
// VULN 3: Weak hashing — MD5 with no salt
function handle_login($users) {
    $error = "";

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $username = $_POST['username'] ?? '';
        $password = $_POST['password'] ?? '';
        $hash     = md5($password);  // VULN 3: MD5, no salt

        if (isset($users[$username]) && $users[$username]['password'] === $hash) {
            $_SESSION['user'] = $username;
            $_SESSION['role'] = $users[$username]['role'];
            header("Location: ?action=dashboard");
            exit;
        } else {
            // VULN 2: $username echoed raw — reflected XSS
            $error = "<p style='color:red'>Invalid login for user: $username</p>";
        }
    }

    echo render_layout("Login", "
        <h2>Login</h2>
        $error
        <form method='POST' action='?action=login'>
            <input name='username' placeholder='Username'><br><br>
            <input name='password' type='password' placeholder='Password'><br><br>
            <button type='submit'>Login</button>
        </form>
    ");
}

// ── Logout ────────────────────────────────────────────────
function handle_logout() {
    session_destroy();
    header("Location: ?action=home");
    exit;
}

// ── Dashboard ─────────────────────────────────────────────
// VULN 4: IDOR — note_id not validated against session user
function handle_dashboard($notes) {
    require_login();
    $user = $_SESSION['user'];

    $my_notes = array_filter($notes, fn($n) => $n['owner'] === $user);

    $list = "";
    foreach ($my_notes as $id => $note) {
        $list .= "<li><a href='?action=note&id=$id'>Note #$id</a></li>";
    }

    echo render_layout("Dashboard", "
        <h2>Welcome, $user</h2>
        <h3>Your Notes</h3>
        <ul>$list</ul>
        <p><a href='?action=search'>Search Notes</a> |
           <a href='?action=upload'>Upload File</a> |
           <a href='?action=profile'>Profile</a> |
           <a href='?action=ping'>Ping Tool</a></p>
        " . (is_admin() ? "<p><a href='?action=admin'>Admin Panel</a></p>" : "") . "
        <p><a href='?action=logout'>Logout</a></p>
    ");
}

// ── Note Viewer ───────────────────────────────────────────
// VULN 4: IDOR — no ownership check, any logged-in user can view any note
function handle_note($notes) {
    require_login();

    $id = $_GET['id'] ?? 0;
    $id = (int)$id;

    // Missing: if ($notes[$id]['owner'] !== $_SESSION['user']) { die("Forbidden"); }

    if (!isset($notes[$id])) {
        die("Note not found.");
    }

    $note = $notes[$id];
    echo render_layout("Note #$id", "
        <h2>Note #$id</h2>
        <p><strong>Owner:</strong> {$note['owner']}</p>
        <p><strong>Content:</strong> {$note['content']}</p>
        <p><a href='?action=dashboard'>Back</a></p>
    ");
}

// ── Search ────────────────────────────────────────────────
// VULN 5: Stored/Reflected XSS — search term echoed raw
// VULN 6: If using real DB this would be SQLi — shown in comment
function handle_search($notes) {
    require_login();

    $q      = $_GET['q'] ?? '';
    $results = [];

    // Simulated: in real app this would be:
    // $sql = "SELECT * FROM notes WHERE content LIKE '%" . $q . "%'"; // SQLi
    foreach ($notes as $id => $note) {
        if ($note['owner'] === $_SESSION['user'] && stripos($note['content'], $q) !== false) {
            $results[] = "#$id: " . $note['content'];
        }
    }

    $result_html = $results
        ? "<ul>" . implode("", array_map(fn($r) => "<li>$r</li>", $results)) . "</ul>"
        : "<p>No results for: $q</p>";  // VULN 5: $q not escaped

    echo render_layout("Search", "
        <h2>Search Notes</h2>
        <form method='GET' action=''>
            <input type='hidden' name='action' value='search'>
            <input name='q' value='$q' placeholder='Search...'> <!-- VULN 5: $q in value attr -->
            <button type='submit'>Search</button>
        </form>
        $result_html
    ");
}

// ── Profile ───────────────────────────────────────────────
// VULN 7: Mass assignment — user controls what goes into $_SESSION
// VULN 8: No re-auth required to change sensitive fields
function handle_profile() {
    require_login();

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        // VULN 7: All POST params merged into session without whitelist
        foreach ($_POST as $key => $value) {
            $_SESSION[$key] = $value;  // attacker can set $_SESSION['role'] = 'admin'
        }
        $msg = "<p style='color:green'>Profile updated.</p>";
    }

    $user = $_SESSION['user'];
    $role = $_SESSION['role'];

    echo render_layout("Profile", "
        " . ($msg ?? '') . "
        <h2>Profile — $user</h2>
        <p>Role: $role</p>
        <form method='POST' action='?action=profile'>
            <input name='display_name' placeholder='Display name'><br><br>
            <button type='submit'>Update</button>
        </form>
    ");
}

// ── File Upload ───────────────────────────────────────────
// VULN 9: Unrestricted file upload — no extension or MIME check
// VULN 10: File saved to webroot — direct execution possible
function handle_upload() {
    require_login();

    $msg = "";
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['file'])) {
        $file     = $_FILES['file'];
        $filename = basename($file['name']);           // VULN 10: no sanitization
        $dest     = __DIR__ . "/uploads/" . $filename; // VULN 10: webroot

        // VULN 9: No type check — .php, .phtml, .phar all accepted
        if (move_uploaded_file($file['tmp_name'], $dest)) {
            $msg = "<p style='color:green'>Uploaded: <a href='uploads/$filename'>$filename</a></p>";
        } else {
            $msg = "<p style='color:red'>Upload failed. (Create /uploads/ dir first)</p>";
        }
    }

    echo render_layout("Upload", "
        <h2>Upload File</h2>
        $msg
        <form method='POST' enctype='multipart/form-data' action='?action=upload'>
            <input type='file' name='file'><br><br>
            <button type='submit'>Upload</button>
        </form>
    ");
}

// ── Admin Panel ───────────────────────────────────────────
// VULN 11: Role check done client-side style — only checks session,
//          but session['role'] can be overwritten via VULN 7 (profile)
function handle_admin($users) {
    require_login();

    // This check is bypassable via VULN 7
    if ($_SESSION['role'] !== 'admin') {
        die(render_layout("Forbidden", "<h2>403 — Admins only.</h2>"));
    }

    $list = "";
    foreach ($users as $uname => $data) {
        $list .= "<tr><td>$uname</td><td>{$data['password']}</td><td>{$data['role']}</td></tr>";
    }

    echo render_layout("Admin", "
        <h2>Admin Panel — All Users</h2>
        <table border='1' cellpadding='6'>
            <tr><th>Username</th><th>Password Hash</th><th>Role</th></tr>
            $list
        </table>
    ");
}

// ── Ping Tool ─────────────────────────────────────────────
// VULN 12: OS Command Injection — user input passed to shell_exec
function handle_ping() {
    require_login();

    $output = "";
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $host = $_POST['host'] ?? '';

        // VULN 12: No sanitization — semicolons, pipes, backticks all work
        $cmd    = "ping -c 2 " . $host;
        $output = shell_exec($cmd);
        $output = "<pre>" . htmlspecialchars($output) . "</pre>";
        // Note: htmlspecialchars on OUTPUT only — input still hits the shell
    }

    echo render_layout("Ping Tool", "
        <h2>Ping Tool</h2>
        <form method='POST' action='?action=ping'>
            <input name='host' placeholder='e.g. 127.0.0.1' size='40'>
            <button type='submit'>Ping</button>
        </form>
        $output
    ");
}


// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

function require_login() {
    if (empty($_SESSION['user'])) {
        header("Location: ?action=login");
        exit;
    }
}

function is_admin() {
    return ($_SESSION['role'] ?? '') === 'admin';
}

function render_layout($title, $body) {
    return "<!DOCTYPE html>
<html>
<head>
  <title>StudyPortal — $title</title>
  <style>
    body { font-family: monospace; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #0f0f0f; color: #ccc; }
    h2 { color: #4af; }
    a { color: #4af; }
    input, button { padding: 6px 10px; background: #1a1a1a; color: #ccc; border: 1px solid #333; }
    button { cursor: pointer; color: #4af; }
    table { border-collapse: collapse; width: 100%; }
    th { background: #1a1a1a; }
  </style>
</head>
<body>
  $body
</body>
</html>";
}
?>