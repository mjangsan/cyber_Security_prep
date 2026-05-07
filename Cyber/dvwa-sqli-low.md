Vulnerability: SQL Injection

File: 
    /dvwa/vulnerabilities/sqli/source/low.php
    
Vulnerable line:
    $query = "SELECT ... WHERE id='$id'"

Why:
    $id comes directly from $_GET['id'] with no sanitisation

Proof:
    input 1' OR '1'='1 returns all users

Fix (Medium level):
    mysqli_real_escape_string() escapes quotes

## Why Medium blocks this

On Medium security, DVWA adds one line before the query:
```php
$id = mysqli_real_escape_string($GLOBALS["___mysqli_ston"], $_GET['id']);
```

What this does: it escapes special characters in input.
single quote ' gets turned into \' before it enters the query.

So when you type:  1' OR '1'='1
Medium sees it as: 1\' OR \'1\'=\'1

The query becomes:
SELECT first_name, last_name FROM users WHERE id='1\' OR \'1\'=\'1' LIMIT 1;

This is now broken SQL that returns nothing — means injection is neutralised.

The fix works because the quote that was "escaping out" of the string
is now escaped itself and treated as a literal character, not SQL syntax.

## What this teaches about code review

The difference between Low and Medium is exactly ONE line.
When doing OSWE code review, this is what you look for:
- Does user input get sanitised BEFORE it touches the query?
- If yes — what function is used and can it be bypassed?
- If no — it's vulnerable.

mysqli_real_escape_string is NOT perfect — it can be bypassed in
certain character encodings. But for standard UTF-8 it blocks basic SQLi.
The proper fix is prepared statements (parameterised queries):
```php
$stmt = $pdo->prepare("SELECT first_name, last_name FROM users WHERE id = ?");
$stmt->execute([$id]);
```
