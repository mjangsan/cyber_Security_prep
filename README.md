# Security Research & Notes

> Transitioning from 5+ years Automation SDET → Application Security.  
> This repo documents my hands-on learning — labs, CVE analysis, tools I build, and code review practice.

---

## About Me

I spent 5 years building test automation frameworks — Selenium, Playwright, Python, Jenkins, API testing.  
I'm now applying that scripting and systematic thinking to web application security.

**Current focus:** Web app pentesting, source code review, OSWE preparation  
**Background:** Automation SDET → AppSec transition  
**Certifications in progress:** OSWE (OffSec Web Expert)

---

## What's in This Repo

```
security-notes/
│
├── portswigger/          # Lab notes — what I learned, not just solutions
│   ├── sqli.md
│   ├── xss.md
│   ├── ssrf.md
│   └── ...
│
├── dvwa/                 # DVWA source code analysis — PHP code review practice
│   ├── dvwa-sqli-low.md
│   ├── dvwa-xss-low.md
│   └── ...
│
├── cve-analysis/         # Real vulnerability breakdowns — code to exploit
│   ├── cve-analysis-01.md
│   ├── cve-analysis-02.md
│   └── ...
│
├── tools/                # Scripts I built — automation background applied to security
│   ├── web-vuln-checker/ # OWASP Top 10 automated checker (Python)
│   └── ...
│
└── writeups/             # CTF and HTB machine writeups
    └── ...
```

---

## Tools I Built

### web-vuln-checker
A Python CLI tool that checks a target URL for common web vulnerabilities.

**Checks:**
- SQL injection (error-based detection)
- Reflected XSS (unencoded reflection detection)
- Command injection
- Missing security headers (CSP, X-Frame-Options, etc.)
- Basic IDOR detection (sequential ID enumeration)

**Built using:** Python, requests, argparse  
**Why I built it:** Direct transfer from my automation SDET background — same logic as a test framework, different payloads.

```bash
python checker.py --url http://target.com --check sqli,xss,headers
```

> More tools added as I learn — each one solves a real testing problem.

---

## CVE Analysis

I read real vulnerability writeups and break down exactly what was vulnerable in the source code and why.

| # | CVE | Type | Language | Key finding |
|---|-----|------|----------|-------------|
| 01 | [CVE-XXXX-XXXXX] | [SQLi / XSS / RCE] | PHP | [One line: what was the vulnerable function] |
| 02 | [CVE-XXXX-XXXXX] | [type] | Python | [One line summary] |

> Format for each: vulnerable code → why it's dangerous → what the fix looks like

---

## PortSwigger Progress

Tracking completion across all modules relevant to OSWE and bug bounty.

| Module | Status | Key takeaway |
|--------|--------|--------------|
| SQL Injection | ✅ Complete | Blind time-based, union-based, filter bypass |
| Authentication | ✅ Complete | MFA bypass, password reset flaws, brute force |
| XSS | ✅ Complete | DOM-based, CSP bypass, event handler injection |
| SSRF | 🔄 In progress | Internal service access, blind SSRF via OOB |
| XXE | 🔄 In progress | File read, SSRF via XXE, blind OOB |
| Access Control | ⬜ Upcoming | — |
| Business Logic | ⬜ Upcoming | — |
| File Upload | ⬜ Upcoming | — |
| SSTI | ⬜ Upcoming | — |
| Deserialization | ⬜ Upcoming | — |
| CORS | ⬜ Upcoming | — |
| OAuth / JWT | ⬜ Upcoming | — |
| GraphQL | ⬜ Upcoming | — |
| Prototype Pollution | ⬜ Upcoming | — |

---

## DVWA Source Code Review Log

Practising the OSWE core skill: read the code, find the vulnerability **before** testing it.

| Page | Security level | Vulnerability found | Vulnerable function |
|------|---------------|---------------------|----------------------|
| SQL Injection | Low | SQLi | `$query = "...WHERE id='$id'"` |
| SQL Injection | Medium | Partial bypass | `mysqli_real_escape_string` — numeric bypass |
| XSS Reflected | Low | XSS | `echo $_GET['name']` unencoded |
| File Inclusion | Low | LFI | `include($_GET['page'])` |
| File Upload | Low | RCE | No extension or content-type check |
| Command Injection | Low | RCE | `shell_exec($_GET['ip'])` |

> Each entry has a matching .md file in /dvwa/ with full details and fix analysis.

---

## Background — Why Automation → Security

My automation work directly transfers:

| Automation SDET skill | Security application |
|-----------------------|----------------------|
| Selenium / Playwright scripting | Custom security tooling in Python |
| API test frameworks | API security testing, auth bypass |
| CI/CD pipeline (Jenkins) | Security pipeline integration (SAST/DAST) |
| Systematic test case design | Structured pentest methodology |
| Bug reproduction and reporting | Vulnerability writeups and PoC documentation |

The mindset is the same — find where the system behaves unexpectedly. The payloads are different.

---

## Contact

- LinkedIn: 
- Email: mjangsan1@gmail.com
- Bug bounty: 

---

*Updated regularly as I progress. Last updated: APR-2026*
