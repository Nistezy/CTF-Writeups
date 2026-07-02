# 🔍 RedLine Stealer — CTF Writeup
### CyberDefenders Blue Team Challenge | Análise Estática e Comportamental de Malware · Threat Intelligence

---

| **Analista**          | Mauricio Robert                                                                                  |
|-----------------------|--------------------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                                |
| **Data do Relatório** | 02/07/2026                                                                                       |
| **Data da Análise**   | 02/07/2026                                                                                        |
| **Classificação**     | CONFIDENCIAL                                                                                       |
| **Amostra**           | `WEXTRACT.EXE.MUI` (`248fcc901aff4e4b4c48c91e4d78a939bf681c9a1bc24addc3551b32768f907b`)            |
| **Ferramentas**       | VirusTotal · MalwareBazaar (YARA) · ThreatFox · Hybrid Analysis · ANY.RUN                          |
| **Plataforma**        | CyberDefenders Blue Team CTF — RedLine Stealer                                                     |

---

## 🔍 Resumo Executivo

Este writeup documenta a análise estática e comportamental de uma amostra de malware identificada como **RedLine Stealer**, submetida ao desafio CTF da plataforma **CyberDefenders (Blue Team)**. O arquivo analisado apresenta-se disfarçado como componente legítimo do Windows/Internet Explorer (**Win32 Cabinet Self-Extractor**), com nome interno `Wextract` e nome de arquivo `WEXTRACT.EXE.MUI`, criado em **2022-05-24** e submetido pela primeira vez ao VirusTotal em **2023-10-06**.

A análise revelou que a amostra é classificada pela Microsoft como **`Trojan:Win32/RedlineInfr`** e por **60 de 71** fornecedores de antivírus como maliciosa. O RedLine Stealer é um infostealer avançado que rouba credenciais de navegadores, carteiras de criptomoedas, dados de FTP, VPN e sessões de aplicativos, exfiltrando-os para um servidor **C2 em `77.91.124.55:19071`** (Rússia/Ucrânia, AS203727 byon). A DLL abusada para acesso a APIs privilegiadas foi identificada como **`ADVAPI32.dll`** (MITRE ATT&CK T1129).

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                | Finalidade                                                                                          |
|-----------------------------|-------------------------------------------------------------------------------------------------------|
| **VirusTotal**              | Análise estática — hashes, detecções, metadados, histórico, relações e comportamento MITRE ATT&CK    |
| **MalwareBazaar (YARA)**    | Identificação da regra YARA da amostra, autor e sightings históricos                                  |
| **ThreatFox**                | Consulta de IOCs (ip:port C2), malware alias, nível de confiança e país de origem                     |
| **Hybrid Analysis**          | Análise dinâmica — árvore de processos, DNS requests, Contacted Hosts, DLLs carregadas, indicadores MITRE |
| **ANY.RUN**                  | Sandbox complementar para confirmação de comportamento e técnicas MITRE ATT&CK                        |

---

## 📋 Análise Investigativa — Perguntas e Respostas

### Q1 — Categoria do malware classificada pela Microsoft

> **Resposta: `Trojan`**

**Solução:** A aba **Detection** do VirusTotal para o hash `248fcc901aff4e4b4c48c91e4d78a939bf681c9a1bc24addc3551b32768f907b` exibiu a entrada da Microsoft destacada na listagem de fornecedores:

```
Microsoft: Trojan:Win32/RedlineInfr
```

A categoria **Trojan** identifica o tipo primário de malware — especificamente `Trojan:Win32/RedlineInfr`, a assinatura da Microsoft para o RedLine Stealer/Infostealer. Classificação consistente com outros fornecedores: TrendMicro (`Trojan.Win32.RELINE.TL0101E326ZZ`), McAfee (`Trojan:Win/RedlinePacker.D`), Trellix (`Artemis!18CBE55C3B28`), entre outros.

![Categoria Microsoft](/Forensic/Red%20Stealer/images/Microsoft_Category(Trojan)(1).png)
*Figura 1 — VirusTotal Detection exibindo `Microsoft: Trojan:Win32/RedlineInfr` destacado na listagem de fornecedores.*

---

### Q2 — Nome do arquivo (amostra analisada)

> **Resposta: `WEXTRACT.EXE.MUI`**

**Solução:** A aba **Details** do VirusTotal exibe o cabeçalho com o nome da amostra e a seção *Names*:

| Campo             | Valor                                    |
|--------------------|---------------------------------------------|
| Nome Principal      | `WEXTRACT.EXE.MUI`                          |
| Internal Name       | `Wextract`                                    |
| Original Name       | `WEXTRACT.EXE.MUI`                            |
| Description         | Win32 Cabinet Self-Extractor                  |
| Product              | Internet Explorer                              |
| File Version         | 11.00.17763.1 (WinBuild.160101.0800)          |
| File Size            | 1.83 MB (1.917.440 bytes)                     |

O malware mascara-se como um componente legítimo do Internet Explorer (Win32 Cabinet Self-Extractor), usando o nome `WEXTRACT.EXE.MUI` para aparentar ser um arquivo MUI (Multilingual User Interface) do Windows — técnica de **mascaramento (Masquerading, T1036)** para evasão de defesas.

![Nome do Arquivo](/Forensic/Red%20Stealer/images/Name_of_This_Archive(2).png)
*Figura 2 — VirusTotal Details exibindo o nome `WEXTRACT.EXE.MUI`, Internal Name `Wextract` e metadados da amostra.*

---

### Q3 — Data da primeira submissão ao VirusTotal

> **Resposta: `2023-10-06 04:41:50 UTC`**

**Solução:** A seção **History** na aba Details do VirusTotal exibiu o histórico completo:

| Evento                  | Data/Hora (UTC)          |
|---------------------------|-----------------------------|
| Creation Time              | 2022-05-24 22:49:06 UTC     |
| First Seen In The Wild     | 2023-10-07 07:20:23 UTC     |
| **First Submission**       | **2023-10-06 04:41:50 UTC** |
| Last Submission             | 2026-06-07 02:50:26 UTC     |
| Last Analysis                | 2026-06-28 15:50:21 UTC     |

O campo *First Submission* confirma a data e hora exata em que a amostra foi submetida pela primeira vez ao VirusTotal — aproximadamente 10 meses após sua criação (2022-05-24) e 1 dia antes de ser vista pela primeira vez em estado selvagem (*In The Wild*: 2023-10-07).

![Primeira Submissão](/Forensic/Red%20Stealer/images/First_Submission_of_Malware(3).png)
*Figura 3 — VirusTotal Details → History com o campo `First Submission: 2023-10-06 04:41:50 UTC` destacado.*

---

### Q4 — MITRE ATT&CK ID da técnica de Exfiltração/Coleta de Dados

> **Resposta: `T1005`**

**Solução:** A aba **Behavior** do VirusTotal exibiu o mapeamento completo de MITRE ATT&CK Tactics and Techniques. Na coluna **Collection (TA0009)**, a técnica destacada é:

```
Data from Local System — T1005
```

A técnica **T1005 (Data from Local System)**, classificada na tática *Collection* (TA0009), descreve a coleta de dados do sistema local antes da exfiltração — comportamento central do RedLine Stealer, que busca e coleta credenciais armazenadas em navegadores (cookies, senhas), carteiras de criptomoedas, dados de VPN e FTP para posterior transmissão ao C2. Consistente com o comportamento de infostealer confirmado pelos sandboxes (VMRay: MALWARE; C2AE: STEALER MALWARE).

![MITRE ATT&CK T1005](/Forensic/Red%20Stealer/images/MITRE_ATT&CK_ID_Extrafilation_Data(4).png)
*Figura 4 — VirusTotal Behavior MITRE ATT&CK exibindo "Data from Local System — T1005" na coluna Collection.*

---

### Q5 — Domínio de mídia social relacionado à amostra

> **Resposta: `facebook.com`**

**Solução:** A análise de rede no **Hybrid Analysis** para a mesma amostra revelou, na seção *DNS Requests*, o domínio de mídia social contatado:

```
facebook.com          -> 57.144.180.1   (MarkMonitor, Inc. | Belgium)
connect.facebook.net  -> 57.144.180.128 (MarkMonitor, Inc. | Belgium)
fbcdn.net              -> 57.144.180.1   (MarkMonitor, Inc. | Belgium)
```

O processo `iexplore.exe` (Internet Explorer — processo mascarado) realiza requisições DNS para `facebook.com` e domínios relacionados (`connect.facebook.net`, `fbcdn.net`). Essa comunicação pode ser usada pelo malware para verificar conectividade de rede ou disfarçar tráfego malicioso sob domínios legítimos.

![Domínio de Mídia Social](/Forensic/Red%20Stealer/images/Domain_Relationed_if_Social_Media(5).png)
*Figura 5 — Hybrid Analysis DNS Requests exibindo `facebook.com` destacado como domínio de mídia social contatado.*

---

### Q6 — IP e porta do servidor C2 relacionado ao malware

> **Resposta: `77.91.124.55:19071`**

**Solução:** A análise de rede no Hybrid Analysis revelou, na seção **Contacted Hosts**, a conexão principal do processo `applaunch.exe` (PID 5264) com o servidor de Comando e Controle:

| Campo             | Valor                          |
|---------------------|-----------------------------------|
| IP Address           | `77.91.124.55`                     |
| Port/Protocol         | `19071` / TCP                       |
| Associated Process     | `applaunch.exe` (PID 5264)          |
| Details                | Russian Federation                    |

Esta combinação IP:porta foi confirmada também no **ThreatFox** (IOC ID `1167880`), que registra `77.91.124.55:19071` como `botnet_cc` (bot C2) para o RedLine Stealer, com nível de confiança **100%**, país UA (Ucrânia — AS203727 byon), visto pela primeira vez em 2023-09-27.

![IP e Porta C2](/Forensic/Red%20Stealer/images/IP_and_Port_Relationed_if_this_Malware(6).png)
*Figura 6 — Hybrid Analysis Contacted Hosts: `77.91.124.55:19071` (applaunch.exe) confirmado como servidor C2.*

---

### Q7 — Nome da regra YARA criada por Varp0s

> **Resposta: `detect_Redline_Stealer`**

**Solução:** A pesquisa no **MalwareBazaar** (`bazaar.abuse.ch`) pela regra YARA associada à amostra revelou a página de entrada da regra `detect_Redline_Stealer`:

| Campo         | Valor                            |
|-----------------|--------------------------------------|
| YARA Rule         | `detect_Redline_Stealer`             |
| Author              | `Varp0s`                               |
| Firstseen            | 2023-06-06 07:56:56 UTC                |
| Lastseen              | 2026-07-02 19:34:09 UTC                |
| Sightings              | 9.670 amostras detectadas              |

A regra YARA `detect_Redline_Stealer` foi criada pelo pesquisador **Varp0s** e é amplamente utilizada para identificar amostras do RedLine Stealer no MalwareBazaar, com **9.670 sightings** desde junho de 2023 até julho de 2026.

![Regra YARA](/Forensic/Red%20Stealer/images/Rule_YARA_Name_by_Varp0s(7).png)
*Figura 7 — MalwareBazaar YARA Rule Database exibindo `detect_Redline_Stealer` — Author: Varp0s, 9.670 sightings.*

---

### Q8 — Alias do malware registrado no ThreatFox

> **Resposta: `RECORDSTEALER`**

**Solução:** A consulta ao **ThreatFox** (`threatfox.abuse.ch/ioc/1167880/`) para o IOC `77.91.124.55:19071` revelou, além dos dados de rede, o campo *Malware alias*:

| Campo             | Valor                          |
|---------------------|-----------------------------------|
| IOC ID                | 1167880                            |
| IOC                    | `77.91.124.55:19071`               |
| IOC Type                | `ip:port`                             |
| Threat Type              | `botnet_cc`                            |
| Malware                    | RedLine Stealer                          |
| **Malware alias**           | **`RECORDSTEALER`**                     |
| Confidence Level             | 100% (alta)                              |
| Country                        | UA (Ucrânia)                              |
| ASN                              | AS203727 byon                              |

O alias `RECORDSTEALER` é o nome alternativo pelo qual o RedLine Stealer é conhecido em algumas fontes de threat intelligence — também referido como **RecordBreaker** em outras plataformas.

![Alias do Malware](/Forensic/Red%20Stealer/images/Malware_alias_by_ThreatFox(8).png)
*Figura 8 — ThreatFox IOC Database exibindo "Malware alias: RECORDSTEALER" para o C2 `77.91.124.55:19071`.*

---

### Q9 — DLL abusada pelo malware para escalonamento de privilégios (T1129)

> **Resposta: `ADVAPI32.dll`**

**Solução:** A análise dos **Indicators** no Hybrid Analysis revelou a seção expandida *"Looks up procedures from modules"* com o ATT&CK ID **T1129 (Shared Modules)**. A lista de chamadas de procedimento mostra múltiplas referências ao módulo:

```
?l5001600b09e936c@ADVAPI32.dll
?0e000f006091936c@ADVAPI32.dll
?0e000f00bc9f936c@ADVAPI32.dll
?l100l200e0a7936c@ADVAPI32.dll
[... múltiplas referências a @ADVAPI32.dll ...]
```

O **ADVAPI32.dll** (Advanced API Services Library) é uma DLL fundamental do Windows que fornece acesso a funcionalidades avançadas do sistema operacional — registro do Windows, autenticação (LSA), criptografia (CryptoAPI), gerenciamento de serviços e controle de acesso. O abuso desta DLL — mapeado para **T1129 (Shared Modules)** — permite ao RedLine Stealer acessar funções privilegiadas como `SetFileSecurity`, `OpenSCManager` e operações de registro (`RegOpenKey`/`RegQueryValue`).

![DLL Abusada](/Forensic/Red%20Stealer/images/dll_Abused_by_Malware_for_Privilege_Escalation(9).png)
*Figura 9 — Hybrid Analysis Indicators exibindo múltiplas referências a `@ADVAPI32.dll` — ATT&CK ID T1129 (Shared Modules).*

---

## 🧬 Perfil Completo da Amostra

| Propriedade              | Valor                                                                     |
|-----------------------------|--------------------------------------------------------------------------|
| Família                       | RedLine Stealer (alias: RECORDSTEALER / RecordBreaker)                     |
| Tipo                            | Infostealer / Trojan                                                          |
| SHA-256                          | `248fcc901aff4e4b4c48c91e4d78a939bf681c9a1bc24addc3551b32768f907b`            |
| MD5                                | `18cbe55c3b28754916f1cbf4dfc95cf9`                                              |
| SHA-1                                | `7ccfb7678c34d6a2bedc040da04e2b5201be453b`                                        |
| Imphash                                | `646167cce332c1c252cdcb1839e0cf48`                                                  |
| File Type                                | Win32 EXE (PE32, executable)                                                          |
| File Size                                  | 1.83 MB (1.917.440 bytes)                                                               |
| Nome Arquivo                                 | `WEXTRACT.EXE.MUI`                                                                        |
| Nome Interno                                   | `Wextract`                                                                                   |
| Disfarce                                          | Win32 Cabinet Self-Extractor (Internet Explorer 11.0)                                          |
| Criação                                             | 2022-05-24 22:49:06 UTC                                                                           |
| Primeira Submissão VT                                 | 2023-10-06 04:41:50 UTC                                                                              |
| Detecções VT                                             | 60/71 fornecedores (malicious/phishing/trojan/evader)                                                  |
| Categoria Microsoft                                         | `Trojan:Win32/RedlineInfr`                                                                                |
| Regra YARA                                                     | `detect_Redline_Stealer` (autor: Varp0s, 9.670 sightings)                                                    |
| C2 IP:Porta                                                       | `77.91.124.55:19071` (TCP) — Rússia/Ucrânia, AS203727 byon                                                     |
| DLL Privilege Esc.                                                   | `ADVAPI32.dll` (T1129 — Shared Modules)                                                                           |
| Domínio Mídia Social                                                    | `facebook.com` (conectado via iexplore.exe)                                                                          |
| MITRE Exfiltração                                                          | T1005 — Data from Local System (Collection)                                                                             |

---

## ⛓ Fluxo Comportamental do Malware

```
[FASE 1 — DISFARCE E EXECUÇÃO]
    Arquivo: WEXTRACT.EXE.MUI (mascarado como Win32 Cabinet Self-Extractor / IE11)
    Internal Name: Wextract | Masquerading (T1036)
    ↓
[FASE 2 — PERSISTÊNCIA E EVASÃO]
    Modify Registry (T1112) | Boot/Logon Autostart (T1547)
    Scheduled Task/Job (T1053) | Obfuscated Files or Information (T1027)
    ↓
[FASE 3 — ESCALONAMENTO / MÓDULOS COMPARTILHADOS]
    Shared Modules (T1129) → ADVAPI32.dll
    Process Injection (T1055) — 10 técnicas detectadas
    ↓
[FASE 4 — COLETA DE CREDENCIAIS]
    Input Capture (T1056) | Credentials in Files (T1081)
    Data from Local System (T1005) — navegadores, wallets, VPN, FTP
    ↓
[FASE 5 — COMUNICAÇÃO ENCOBERTA / DISCOVERY]
    iexplore.exe → DNS requests: facebook.com, connect.facebook.net,
    fbcdn.net, accounts.youtube.com (tráfego legítimo como disfarce)
    System Information Discovery (T1082) — 13 técnicas
    ↓
[FASE 6 — EXFILTRAÇÃO / C2]
    applaunch.exe (PID 5264) → 77.91.124.55:19071 (TCP)
    Application Layer Protocol (T1071) | Uncommonly Used Port (T1065)
    Confirmado no ThreatFox: botnet_cc, RedLine Stealer / RECORDSTEALER
```

---

## 🗺 Mapeamento Investigativo

| Pergunta                          | Fonte de Evidência                                     | Artefato / Resposta                        |
|--------------------------------------|-------------------------------------------------------------|------------------------------------------------|
| Categoria Microsoft                    | VirusTotal → Detection                                        | `Trojan`                                          |
| Nome do arquivo                          | VirusTotal → Details → Names                                    | `WEXTRACT.EXE.MUI`                                  |
| Data primeira submissão                    | VirusTotal → Details → History                                    | `2023-10-06 04:41:50 UTC`                              |
| MITRE ID exfiltração/coleta                  | VirusTotal → Behavior → MITRE ATT&CK                                | `T1005`                                                   |
| Domínio de mídia social                        | Hybrid Analysis → Network Analysis → DNS Requests                     | `facebook.com`                                              |
| IP:porta do C2                                   | Hybrid Analysis → Contacted Hosts + ThreatFox                            | `77.91.124.55:19071`                                          |
| Nome da regra YARA (Varp0s)                        | MalwareBazaar → YARA Rule                                                   | `detect_Redline_Stealer`                                        |
| Alias do malware                                     | ThreatFox → IOC 1167880                                                       | `RECORDSTEALER`                                                    |
| DLL abusada (T1129)                                     | Hybrid Analysis → Indicators → Shared Modules                                  | `ADVAPI32.dll`                                                      |

---

## 🚨 Indicadores de Comprometimento (IOCs)

| Tipo             | Indicador                                                             | Contexto                                                       |
|---------------------|-------------------------------------------------------------------------|----------------------------------------------------------------|
| SHA-256                | `248fcc901aff4e4b4c48c91e4d78a939bf681c9a1bc24addc3551b32768f907b`         | Hash principal da amostra — 60/71 detecções VT                     |
| MD5                      | `18cbe55c3b28754916f1cbf4dfc95cf9`                                           | MD5 da amostra WEXTRACT.EXE.MUI                                       |
| SHA-1                      | `7ccfb7678c34d6a2bedc040da04e2b5201be453b`                                     | SHA-1 da amostra                                                          |
| IP C2                         | `77.91.124.55`                                                                   | Servidor C2 — Russian Federation / UA (AS203727 byon)                       |
| Porta C2                        | `19071/TCP`                                                                        | Porta do C2 — comunicação via `applaunch.exe`                                 |
| IOC C2                             | `77.91.124.55:19071`                                                                 | ThreatFox IOC ID 1167880 — botnet_cc, confiança 100%                            |
| Processo C2                          | `applaunch.exe` (PID 5264)                                                              | Processo que estabelece conexão com o C2                                          |
| Processo Masquerading                   | `iexplore.exe`                                                                             | Processo mascarado usado para DNS/web requests                                       |
| Arquivo                                    | `WEXTRACT.EXE.MUI`                                                                            | Nome do arquivo malicioso (disfarce como IE11 MUI)                                      |
| Domínio                                      | `facebook.com`                                                                                  | Domínio de mídia social contatado (iexplore.exe)                                          |
| Domínio                                        | `connect.facebook.net` / `fbcdn.net`                                                              | Subdomínios Facebook contatados durante execução                                             |
| Domínio                                          | `accounts.youtube.com`                                                                              | Domínio Google/YouTube contatado (cobertura de tráfego)                                        |
| DLL                                                 | `ADVAPI32.dll`                                                                                         | DLL abusada para acesso a APIs privilegiadas (T1129)                                              |
| Regra YARA                                            | `detect_Redline_Stealer`                                                                                 | MalwareBazaar — autor: Varp0s, 9.670 sightings                                                       |
| Família                                                  | RedLine Stealer / RECORDSTEALER                                                                            | Família e alias confirmados pelo ThreatFox                                                             |

---

## ✅ Resumo das Flags

| # | Pergunta                                       | Flag / Resposta                       |
|---|---------------------------------------------------|-------------------------------------------|
| Q1 | Categoria do malware (Microsoft)                     | `Trojan`                                       |
| Q2 | Nome do arquivo da amostra                             | `WEXTRACT.EXE.MUI`                               |
| Q3 | Data da primeira submissão ao VirusTotal                 | `2023-10-06 04:41:50 UTC`                          |
| Q4 | MITRE ATT&CK ID de exfiltração/coleta de dados              | `T1005`                                              |
| Q5 | Domínio de mídia social relacionado                           | `facebook.com`                                         |
| Q6 | IP e porta do servidor C2                                        | `77.91.124.55:19071`                                      |
| Q7 | Nome da regra YARA criada por Varp0s                                | `detect_Redline_Stealer`                                    |
| Q8 | Alias do malware no ThreatFox                                        | `RECORDSTEALER`                                                |
| Q9 | DLL abusada para escalonamento de privilégios                          | `ADVAPI32.dll`                                                   |

---

## 📚 Referências

- [CyberDefenders — RedLine Stealer CTF](https://cyberdefenders.org/)
- [VirusTotal — Análise da amostra](https://www.virustotal.com/gui/file/248fcc901aff4e4b4c48c91e4d78a939bf681c9a1bc24addc3551b32768f907b)
- [MalwareBazaar — YARA Rule detect_Redline_Stealer](https://bazaar.abuse.ch/browse/yara/detect_Redline_Stealer/)
- [ThreatFox — IOC 77.91.124.55:19071](https://threatfox.abuse.ch/ioc/1167880/)
- [Hybrid Analysis — Sandbox Report](https://hybrid-analysis.com/sample/248fcc901aff4e4b4c48c91e4d78a939bf681c9a1bc24addc3551b32768f907b)
- [MITRE ATT&CK — T1005 Data from Local System](https://attack.mitre.org/techniques/T1005/)
- [MITRE ATT&CK — T1129 Shared Modules](https://attack.mitre.org/techniques/T1129/)
- [Microsoft Security Intelligence — Trojan:Win32/RedlineInfr](https://www.microsoft.com/en-us/wdsi/threats/)
- [ANY.RUN — RedLine Stealer Analysis](https://any.run/)

---