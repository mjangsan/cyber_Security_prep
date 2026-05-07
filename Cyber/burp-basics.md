# burp-basics

Burp Proxy sits between the browser and server to capture and modify HTTP requests and responses.
I set Burp as my browser proxy, opened DVWA SQLi, entered `id=1`, and intercepted the request in Proxy.
The raw HTTP request showed the parameter clearly: `GET /dvwa/vulnerabilities/sqli/?id=1&Submit=Submit`.
This confirmed how user input is sent to the server and where injection can be tested.
Repeater lets me edit the `id` value and resend the request multiple times to test different payloads quickly.
