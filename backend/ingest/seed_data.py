"""
seed_data.py — Static fallback data used when MITRE / NVD APIs are unavailable.
Contains a curated subset of real-world malware, techniques, CVEs, and assets
so the demo works completely offline.
"""

MALWARE = [
    {"id": "MAL-001", "name": "WannaCry",      "type": "Ransomware",  "description": "Ransomware worm exploiting EternalBlue"},
    {"id": "MAL-002", "name": "NotPetya",       "type": "Wiper",       "description": "Destructive wiper disguised as ransomware"},
    {"id": "MAL-003", "name": "Emotet",         "type": "Trojan",      "description": "Banking trojan / malware-as-a-service loader"},
    {"id": "MAL-004", "name": "Cobalt Strike",  "type": "RAT",         "description": "Commercial penetration testing tool abused by attackers"},
    {"id": "MAL-005", "name": "Mirai",          "type": "Botnet",      "description": "IoT botnet used for massive DDoS attacks"},
    {"id": "MAL-006", "name": "BlackCat",       "type": "Ransomware",  "description": "Rust-based ransomware-as-a-service (ALPHV)"},
    {"id": "MAL-007", "name": "Lazarus Loader", "type": "Loader",      "description": "Initial access loader used by Lazarus Group (DPRK)"},
]

TECHNIQUES = [
    {"id": "T1190", "name": "Exploit Public-Facing Application", "tactic": "Initial Access",   "description": "Exploit weakness in internet-facing software"},
    {"id": "T1566", "name": "Phishing",                          "tactic": "Initial Access",   "description": "Send malicious emails to gain access"},
    {"id": "T1059", "name": "Command and Scripting Interpreter",  "tactic": "Execution",        "description": "Abuse shells like PowerShell, bash, cmd"},
    {"id": "T1486", "name": "Data Encrypted for Impact",         "tactic": "Impact",           "description": "Encrypt data to extort victims"},
    {"id": "T1078", "name": "Valid Accounts",                    "tactic": "Defense Evasion",  "description": "Use stolen credentials to blend in"},
    {"id": "T1021", "name": "Remote Services",                   "tactic": "Lateral Movement", "description": "Use RDP, SSH, SMB to move laterally"},
    {"id": "T1071", "name": "Application Layer Protocol",        "tactic": "Command & Control", "description": "Use HTTP/S, DNS for C2 communication"},
    {"id": "T1110", "name": "Brute Force",                       "tactic": "Credential Access", "description": "Guess passwords through automated attempts"},
    {"id": "T1027", "name": "Obfuscated Files or Information",   "tactic": "Defense Evasion",  "description": "Encode or encrypt payloads to avoid detection"},
    {"id": "T1055", "name": "Process Injection",                 "tactic": "Privilege Escalation", "description": "Inject code into running processes"},
]

CVES = [
    {"id": "CVE-2017-0144", "cvss": 9.3,  "description": "EternalBlue — SMBv1 RCE in Windows (WannaCry/NotPetya)"},
    {"id": "CVE-2021-44228", "cvss": 10.0, "description": "Log4Shell — RCE in Apache Log4j via JNDI injection"},
    {"id": "CVE-2021-34527", "cvss": 8.8,  "description": "PrintNightmare — Windows Print Spooler RCE"},
    {"id": "CVE-2020-1472",  "cvss": 10.0, "description": "Zerologon — Netlogon privilege escalation"},
    {"id": "CVE-2022-30190", "cvss": 7.8,  "description": "Follina — MSDT RCE triggered via Office documents"},
    {"id": "CVE-2023-23397", "cvss": 9.8,  "description": "Outlook zero-click NTLM hash theft"},
    {"id": "CVE-2019-0708",  "cvss": 9.8,  "description": "BlueKeep — Pre-auth RCE in Windows RDP"},
]

ASSETS = [
    {"id": "ASSET-001", "name": "Windows Server 2019", "type": "Server",   "os": "Windows"},
    {"id": "ASSET-002", "name": "Apache Web Server",   "type": "WebServer","os": "Linux"},
    {"id": "ASSET-003", "name": "Corporate Workstation","type": "Endpoint", "os": "Windows"},
    {"id": "ASSET-004", "name": "Active Directory DC",  "type": "Server",   "os": "Windows"},
    {"id": "ASSET-005", "name": "IoT Gateway",          "type": "IoT",      "os": "Embedded Linux"},
    {"id": "ASSET-006", "name": "Exchange Mail Server", "type": "Server",   "os": "Windows"},
]

# Relationships: (malware_id, technique_id)
MALWARE_USES_TECHNIQUE = [
    ("MAL-001", "T1190"), ("MAL-001", "T1486"), ("MAL-001", "T1021"),
    ("MAL-002", "T1190"), ("MAL-002", "T1486"), ("MAL-002", "T1078"),
    ("MAL-003", "T1566"), ("MAL-003", "T1059"), ("MAL-003", "T1071"),
    ("MAL-004", "T1078"), ("MAL-004", "T1021"), ("MAL-004", "T1055"), ("MAL-004", "T1027"),
    ("MAL-005", "T1110"), ("MAL-005", "T1071"),
    ("MAL-006", "T1566"), ("MAL-006", "T1486"), ("MAL-006", "T1027"),
    ("MAL-007", "T1566"), ("MAL-007", "T1059"), ("MAL-007", "T1055"),
]

# Relationships: (technique_id, cve_id)
TECHNIQUE_EXPLOITS_CVE = [
    ("T1190", "CVE-2017-0144"), ("T1190", "CVE-2021-44228"),
    ("T1190", "CVE-2019-0708"), ("T1190", "CVE-2021-34527"),
    ("T1566", "CVE-2022-30190"), ("T1566", "CVE-2023-23397"),
    ("T1078", "CVE-2020-1472"),
    ("T1021", "CVE-2019-0708"), ("T1021", "CVE-2017-0144"),
]

# Relationships: (cve_id, asset_id)
CVE_AFFECTS_ASSET = [
    ("CVE-2017-0144", "ASSET-001"), ("CVE-2017-0144", "ASSET-003"), ("CVE-2017-0144", "ASSET-004"),
    ("CVE-2021-44228", "ASSET-002"),
    ("CVE-2021-34527", "ASSET-001"), ("CVE-2021-34527", "ASSET-003"),
    ("CVE-2020-1472",  "ASSET-004"),
    ("CVE-2022-30190", "ASSET-003"),
    ("CVE-2023-23397", "ASSET-006"),
    ("CVE-2019-0708",  "ASSET-001"), ("CVE-2019-0708",  "ASSET-003"),
]

# Relationships: (malware_id, asset_id)
MALWARE_TARGETS_ASSET = [
    ("MAL-001", "ASSET-001"), ("MAL-001", "ASSET-003"),
    ("MAL-002", "ASSET-001"), ("MAL-002", "ASSET-004"),
    ("MAL-003", "ASSET-003"), ("MAL-003", "ASSET-006"),
    ("MAL-004", "ASSET-001"), ("MAL-004", "ASSET-004"),
    ("MAL-005", "ASSET-005"),
    ("MAL-006", "ASSET-001"), ("MAL-006", "ASSET-004"),
    ("MAL-007", "ASSET-006"),
]
