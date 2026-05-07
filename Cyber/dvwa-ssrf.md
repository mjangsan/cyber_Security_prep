#  SSRF (Server-Side Request Forgery) - Notes

##  What is SSRF?

SSRF (Server-Side Request Forgery) is a vulnerability where an attacker can make the **server send requests on their behalf**.

Instead of the attacker directly accessing resources, the **server becomes the attacker’s proxy**.

---

##  Core Idea

> User input → used in request function → server makes request

Example:

```php
$file = $_POST['file'];
echo file_get_contents($file);



## Why is this dangerous?
Because file_get_contents() supports:
 Local files
 Remote URLs
 PHP wrappers
So attacker controls what the server reads or requests

## Vulnerable Code Pattern
$user_input → file_get_contents()
$user_input → curl_exec()
$user_input → fopen()
If input is not validated → SSRF

## Example Vulnerable Code
$file = trim($_POST['file']);
echo htmlentities(file_get_contents($file));

 Exploitation
1.  Local File Read (LFI)
/etc/passwd
file:///etc/passwd

2.  SSRF (Internal Requests)
http://127.0.0.1
http://localhost
http://192.168.1.1
 Access internal services not exposed publicly

3.  Cloud Metadata Attack
http://169.254.169.254/latest/meta-data/
 Used in AWS / cloud environments to extract credentials

4.  PHP Wrappers (Advanced)
php://filter/convert.base64-encode/resource=index.php
 Reads source code in base64

5.  Internal Port Scanning
http://127.0.0.1:22
http://127.0.0.1:3306
http://127.0.0.1:8080
 Response differences = open/closed ports

## Understanding file:///
Format:
file://<host>/<path>
Example:
file:///etc/passwd

Breakdown:
file: → protocol
// → URL format
(empty host)
/etc/passwd → file path

👉 /// = // (URL) + / (root path)

## Common Mistakes
| Mistake                      | Why wrong                |
| ---------------------------- | ------------------------ |
| `file:/etc/passwd`           | invalid format           |
| `file:/../../etc/passwd`     | malformed URL            |
| using `../../` unnecessarily | no base path restriction |

## Key Insight
If code is:
file_get_contents($input);
 You don’t need traversal
 Direct path works:
 /etc/passwd

## Prevention
1.  Block URLs

if (filter_var($input, FILTER_VALIDATE_URL)) {
    die("Invalid input");
}

2.  Restrict Directory

$base = "/var/www/files/";
$file = realpath($base . $input);

if (strpos($file, $base) !== 0) {
    die("Access denied");
}
3.  Whitelist (Best)

$allowed = ['file1.txt', 'file2.txt'];

if (!in_array($input, $allowed)) {
    die("Invalid file");
}

## Real-World Impact
 Credential theft
 Cloud takeover
 Internal network discovery
 Sensitive file disclosure
 Remote Code Execution (chained)

## 
Whenever you see:user_input → request/file function
Ask:
Can I control the destination?
Can I use URL?
Can I use wrappers?
 If yes → SSRF

 ## One-Line Summary
SSRF lets you turn the server into your own request engine.

## Practice Payloads

/etc/passwd
file:///etc/passwd
http://127.0.0.1
http://169.254.169.254
php://filter/convert.base64-encode/resource=index.php

🔚 Conclusion
SSRF is simple in code but powerful in impact.
The real skill is:


Understanding input flow


Knowing supported protocols



