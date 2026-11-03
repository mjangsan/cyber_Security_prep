// DVWA Command Injection Low — find this:
shell_exec('ping ' . $target); // $target = raw user input

// Why it’s dangerous:
Unsanitized user input ($target) being concatenated into a shell command. This leads to OS Command Injection.

// Payload: 
127.0.0.1; cat /etc/passwd

