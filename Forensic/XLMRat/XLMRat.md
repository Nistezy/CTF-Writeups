# 🧠 XLMRat Malware Analysis

## 📌 Overview
This writeup documents the forensic analysis of a multi-stage malware infection involving obfuscated PowerShell/VBScript and a .NET payload identified as AsyncRAT.

---

## 🌐 Stage 1 — Network Analysis

![Wireshark](images/wireshark_http.png)

- **C2 IP:** 45.126.209.4  
- **Port:** 222 (non-standard)  
- **URI:** `/mdm.jpg`

📌 The payload was disguised as an image (masquerading).

---

## 🌍 WHOIS Analysis

![WHOIS](images/whois.png)

- **Provider:** ReliableSite.Net LLC  
- **Location:** Singapore  

---

## 🧬 Stage 2 — Obfuscated Payload

![Obfuscated Script](images/obfuscated_script.png)

- Payload split into multiple fragments  
- Encoded in HEX  
- Uses replacement tricks (`_`, `#`)  

---

## 🔧 Decoding Process (CyberChef)

![CyberChef](images/cyberchef_decode.png)

### Steps:
1. Remove `_` / `#`
2. Convert HEX → bytes
3. Rebuild executable

### Result:
- `malware.exe`
- PE32 (.NET)
- 65 KB

---

## 🧾 Hash

```txt
SHA-256:
1eb7b02e18f67420f42b1d94e74f3b6289d92672a0fb1786c30c03d68e81d798