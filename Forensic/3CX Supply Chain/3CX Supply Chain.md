# 🔍 3CX Supply Chain Attack — CTF Writeup
### CyberDefenders Blue Team Challenge | Análise Forense de Ataque de Cadeia de Suprimentos · Lazarus Group

---

| **Analista**          | Mauricio Robert                                                                                  |
|-----------------------|--------------------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                                |
| **Data do Relatório** | 07/07/2026                                                                                       |
| **Data do Incidente** | 13/03/2023 (criação do malware)                                                                    |
| **Classificação**     | CONFIDENCIAL                                                                                       |
| **Caso CTF**          | 3CX Supply Chain Attack — CyberDefenders Blue Team                                                  |
| **Ferramentas**       | VirusTotal · Tria.ge (Recorded Future) · Brave Search                                               |

---

## 🔍 Resumo Executivo

Este writeup documenta a análise forense do desafio **3CX Supply Chain Attack** do CyberDefenders, que reconstrói um dos incidentes de segurança mais significativos de 2023. O ataque comprometeu o instalador oficial do **3CX Desktop App** (versão 18.12.416 para Windows), um software de comunicação empresarial amplamente utilizado, transformando-o em um vetor de distribuição de malware — um ataque clássico de **supply chain**.

O instalador malicioso (`.msi`), criado em **13/03/2023**, depositava duas DLLs trojanas no diretório de instalação do 3CX: **`ffmpeg.dll`** e **`d3dcompiler_47.dll`**. A DLL `ffmpeg.dll` utiliza o algoritmo de criptografia **RC4** para ofuscar comunicações e emprega técnicas anti-análise contra o hipervisor **VMware**. Ambas as DLLs são classificadas como **trojans** e utilizam a técnica MITRE ATT&CK **T1574 (Hijack Execution Flow)** para execução via DLL hijacking. O ataque foi atribuído ao grupo APT **Lazarus**, atores patrocinados pelo estado norte-coreano.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                  | Finalidade                                                                                              |
|--------------------------------|------------------------------------------------------------------------------------------------------------|
| **VirusTotal**                    | Análise estática e comportamental — detecções, metadados, técnicas MITRE ATT&CK, categoria de ameaça e criptografia usada pelo malware |
| **Tria.ge (Recorded Future)**        | Sandbox dinâmica — identificação das DLLs depositadas pelo `.msi`, hashes SHA-256, caminhos de instalação e comportamento do instalador |
| **Brave Search**                       | Pesquisa de threat intelligence — atribuição do ataque ao grupo Lazarus, características do NukeSped RAT e histórico de campanhas do APT |
| **CyberDefenders**                        | Plataforma CTF — contexto do desafio e validação das respostas investigativas                                     |

---

## 📋 Análise Investigativa — Perguntas e Respostas

### Q1 — Quantas versões do 3CX rodando em Windows foram sinalizadas como malware?

> **Resposta: `2`**

**Solução:** A investigação no VirusTotal e no Tria.ge identificou duas versões do 3CX Desktop App para Windows comprometidas, ambas testadas em ambientes distintos (`windows10-2004-x64` e `windows11-ltsc_2024-x64`), com o mesmo instalador `3CXDesktopApp-18.12.416.msi` (SHA-256: `59e1edf4d82fae4978e97512b0331b7e...`). Ambas as versões continham as DLLs trojanas depositadas no diretório de instalação `C:\Users\Admin\AppData\Local\Programs\3CXDesktopApp\app-18.12.416\`, caracterizando o comprometimento da cadeia de distribuição do software.

![Duas Versões Windows](/Forensic/3CX%20Supply%20Chain/images/2_Versions_of_Running_on_Windows(1).png)
*Figura 1 — Tria.ge exibindo as duas versões analisadas do `3CXDesktopApp-18.12.416.msi` (windows10-2004-x64 e windows11-ltsc_2024-x64).*

---

### Q2 — Qual é a data e hora UTC de criação do malware `.msi`?

> **Resposta: `2023-03-13 06:33` (06:33:26 UTC)**

**Solução:** A seção *Details → History* no VirusTotal para o arquivo `3CXDesktopApp-18.12.416.msi` (SHA-256: `59e1edf4d82fae4978e97512b0331b7eb21dd4b838b850ba46794d9c7a2c0983`) exibiu:

```
Creation Time:      2023-03-13 06:33:26 UTC
Signature Date:      2023-03-13 06:34:00 UTC
First Seen In The Wild: 2023-03-29 21:10:08 UTC
First Submission:     2023-03-22 06:39:15 UTC
```

A *Signature Date* registrada é apenas **34 segundos** após a criação — indicando que o arquivo foi assinado digitalmente imediatamente após sua geração, consistente com um processo automatizado de build malicioso.

![Data de Criação](/Forensic/3CX%20Supply%20Chain/images/Data_of_Creation_of_Malware(2).png)
*Figura 2 — VirusTotal Details exibindo `Creation Time: 2023-03-13 06:33:26 UTC` do instalador `.msi` malicioso.*

---

### Q3 — Quais DLLs maliciosas foram depositadas pelo arquivo `.msi`?

> **Resposta: `ffmpeg.dll`, `d3dcompiler_47.dll`**

**Solução:** O **Tria.ge** (Recorded Future Sandbox) listou os arquivos depositados pelo instalador no caminho `C:\Users\Admin\AppData\Local\Programs\3CXDesktopApp\app-18.12.416\`:

| Arquivo                 | Tamanho    | SHA-256                                                             |
|---------------------------|--------------|--------------------------------------------------------------------|
| `d3dcompiler_47.dll`         | 4,9 MB          | `11be1803e2e307b647a8a7e02d128335c448ff741bf06bf52b332e0bbf423b03`     |
| `ffmpeg.dll` (Copied)          | 2,7 MB          | `7986bbaee8940da11ce089383521ab420c443ab7b15ed42aed91fd31ce833896`       |

Ambas foram sinalizadas como maliciosas com altas taxas de detecção no VirusTotal.

![DLLs Depositadas](/Forensic/3CX%20Supply%20Chain/images/dll_if_Runing_with_Malware(3).png)
*Figura 3 — Tria.ge listando os arquivos depositados pelo `.msi`, incluindo `ffmpeg.dll` e `d3dcompiler_47.dll` com seus hashes SHA-256.*

---

### Q4 — Qual é o ID da técnica MITRE ATT&CK utilizada pelo `.msi` para carregar a DLL maliciosa?

> **Resposta: `T1574`**

**Solução:** A análise comportamental no VirusTotal do arquivo `.msi` mapeou, na fase **Execution (TA0002)**, a técnica destacada:

```
T1574 — Hijack Execution Flow
```

Isso indica que o malware substitui DLLs legítimas esperadas pela aplicação 3CX (`ffmpeg.dll` e `d3dcompiler_47.dll`) por versões trojanas, aproveitando o mecanismo de carregamento de DLLs do Windows (**DLL Search Order Hijacking / DLL Side-Loading**) para executar código malicioso no contexto do processo legítimo do 3CX.

![MITRE T1574](/Forensic/3CX%20Supply%20Chain/images/MITRE_ATT&CK_Techinique_dll_Hijacking(4).png)
*Figura 4 — VirusTotal Behavior mapeando a técnica `T1574 (Hijack Execution Flow)` na fase de Execution do `.msi` malicioso.*

---

### Q5 — Qual é a categoria de ameaça (threat category) das duas DLLs maliciosas?

> **Resposta: `Trojan`**

**Solução:** A análise de ambas as DLLs no VirusTotal confirmou a categoria **Trojan** para os dois arquivos. Para a `d3dcompiler_47.dll`:

| Campo                  | Valor                              |
|---------------------------|---------------------------------------|
| Popular threat label         | `trojan.marte/nukesped`                  |
| Threat categories               | `trojan`                                    |
| Family labels                     | `marte`, `nukesped`, `supplychainagent`        |
| Detecções VT                        | 43/68                                            |

Classificação similar de trojan foi atribuída pelos vendors para a `ffmpeg.dll`. Ambas foram identificadas como trojans de acesso remoto (RAT) da família **NukeSped**.

![Categoria de Ameaça](/Forensic/3CX%20Supply%20Chain/images/Theat_Category_of_dll(5).png)
*Figura 5 — VirusTotal exibindo `Threat Category: Trojan` e `Popular Threat Label: trojan.marte/nukesped` para a `d3dcompiler_47.dll`.*

---

### Q6 — Qual é o ID MITRE para a técnica de evasão de virtualização/sandbox usada pelas duas DLLs maliciosas?

> **Resposta: `T1497`**

**Solução:** A análise comportamental de ambas as DLLs no VirusTotal Behavior mapeou a técnica **T1497 — Virtualization/Sandbox Evasion** com **3 ocorrências** em cada arquivo. Para a `d3dcompiler_47.dll` e para a `ffmpeg.dll`, a subtécnica destacada foi:

```
T1497.001 — System Checks (1 ocorrência)
```

Isso indica que o malware realiza verificações do ambiente de execução para detectar se está sendo analisado em sandbox antes de prosseguir com seu payload malicioso.

![Virtualization/Sandbox Evasion](/Forensic/3CX%20Supply%20Chain/images/Virtualization_Evasion_dll(6).png)
*Figura 6 — VirusTotal Behavior de ambas as DLLs exibindo a técnica `T1497 (Virtualization/Sandbox Evasion)` com 3 ocorrências.*

---

### Q7 — Qual hipervisor é alvo das técnicas anti-análise no arquivo `ffmpeg.dll`?

> **Resposta: `VMware`**

**Solução:** Na análise comportamental do VirusTotal para a `ffmpeg.dll` (SHA-256: `7986bbaee8940da11ce089383521ab420c443ab7b15ed42aed91fd31ce833896`), a seção *Malware Behavior Catalog Tree → Anti-Behavioral Analysis → Anti-Analysis* listou:

```
Reference anti-VM strings targeting VMWare
Reference analysis tools strings
```

Isso confirma que a `ffmpeg.dll` contém strings e verificações direcionadas especificamente ao hipervisor **VMware** — técnica comum para detectar ambientes de análise e evitar execução do payload real quando em ambiente virtualizado.

![Anti-VMware](/Forensic/3CX%20Supply%20Chain/images/Type_of_Scan_Virtualization_App(7).png)
*Figura 7 — VirusTotal Behavior Catalog da `ffmpeg.dll` exibindo "Reference anti-VM strings targeting VMWare" em Anti-Analysis.*

---

### Q8 — Qual algoritmo de criptografia é utilizado pelo arquivo `ffmpeg.dll`?

> **Resposta: `RC4`**

**Solução:** A seção *Malware Behavior Catalog Tree → Cryptography* da `ffmpeg.dll` no VirusTotal detalhou os algoritmos criptográficos utilizados:

```
Generate Pseudo-random Sequence → RC4 PRGA (C0021.004)
Encrypt Data → RC4 (C0027.009)
Encryption Key → RC4 KSA (C0028.002)
Cryptographic Hash → SHA1 (C0029.002), SHA256 (C0029.003)
```

O algoritmo **RC4** (Rivest Cipher 4) é amplamente utilizado pelo grupo Lazarus em suas ferramentas (incluindo o NukeSped RAT) para cifrar comunicações com o C2 e ofuscar strings, dificultando a análise estática.

![Criptografia RC4](/Forensic/3CX%20Supply%20Chain/images/Tyoe_of_Cryptography_Malware_Used(8).png)
*Figura 8 — VirusTotal Behavior Catalog da `ffmpeg.dll` exibindo RC4 PRGA, RC4 Encrypt Data e RC4 KSA na seção Cryptography.*

---

### Q9 — Qual grupo é responsável por este ataque?

> **Resposta: `Lazarus`**

**Solução:** A atribuição ao grupo **Lazarus** foi confirmada por múltiplas fontes de threat intelligence. O VirusTotal identificou a `d3dcompiler_47.dll` como `trojan.marte/nukesped` — sendo o **NukeSped** (também chamado BLINDINGCAN) um RAT desenvolvido e utilizado exclusivamente pelo grupo Lazarus (HIDDEN COBRA / Andariel), patrocinado pela Coreia do Norte.

A pesquisa complementar confirmou:

> *"NukeSped is a sophisticated Remote Access Trojan (RAT) and backdoor malware attributed to the Lazarus Group, a North Korean state-sponsored Advanced Persistent Threat (APT) actor also known as HIDDEN COBRA or Andariel."*

O ataque 3CX foi amplamente atribuído ao Lazarus pela Mandiant, CrowdStrike e outros vendors de segurança.

![Grupo Lazarus](/Forensic/3CX%20Supply%20Chain/images/Malware_Write_by_Lazarus_Group(9).png)
*Figura 9 — Pesquisa confirmando a atribuição do NukeSped/d3dcompiler_47.dll ao grupo Lazarus (HIDDEN COBRA) e análise do VirusTotal.*

---

## 🧬 Perfil Completo do Ataque

| Propriedade                       | Valor                                                                       |
|--------------------------------------|----------------------------------------------------------------------------|
| Instalador malicioso                     | `3CXDesktopApp-18.12.416.msi` — 97,80 MB                                       |
| SHA-256 (.msi)                              | `59e1edf4d82fae4978e97512b0331b7eb21dd4b838b850ba46794d9c7a2c0983`               |
| Criação do malware                             | 2023-03-13 06:33:26 UTC                                                            |
| Assinatura digital                                | 2023-03-13 06:34:00 UTC (34s após criação)                                             |
| Primeira submissão VT                                | 2023-03-22 06:39:15 UTC                                                                    |
| Primeiro avistamento in the wild                       | 2023-03-29 21:10:08 UTC                                                                       |
| Versões Windows comprometidas                             | 2 (windows10-2004-x64 / windows11-ltsc_2024-x64)                                                  |
| DLL maliciosa 1                                              | `ffmpeg.dll` — 2,7 MB — RC4 + anti-VMware                                                            |
| SHA-256 (ffmpeg.dll)                                            | `7986bbaee8940da11ce089383521ab420c443ab7b15ed42aed91fd31ce833896`                                       |
| DLL maliciosa 2                                                    | `d3dcompiler_47.dll` — 4,93 MB — trojan.marte/nukesped                                                       |
| SHA-256 (d3dcompiler_47.dll)                                          | `11be1803e2e307b647a8a7e02d128335c448ff741bf06bf52b332e0bbf423b03`                                              |
| Caminho de instalação                                                     | `C:\Users\Admin\AppData\Local\Programs\3CXDesktopApp\app-18.12.416\`                                              |
| Técnica MITRE (carregamento DLL)                                             | T1574 — Hijack Execution Flow                                                                                        |
| Categoria de ameaça                                                             | Trojan (marte, nukesped, supplychainagent)                                                                              |
| Técnica MITRE (evasão)                                                            | T1497 — Virtualization/Sandbox Evasion (T1497.001 System Checks)                                                          |
| Hipervisor alvo                                                                      | VMware                                                                                                                        |
| Algoritmo de criptografia                                                               | RC4 (PRGA + KSA)                                                                                                                 |
| Grupo APT responsável                                                                      | Lazarus Group (HIDDEN COBRA / Andariel) — MITRE G0032                                                                              |
| Família de malware                                                                            | NukeSped (BLINDINGCAN)                                                                                                                 |
| YARA rule match                                                                                  | `Windows_Trojan_SuddenIcon_bdae76c9` (Elastic Security)                                                                                    |

---

## ⛓ Fluxo do Ataque

```
[FASE 1 — COMPROMETIMENTO DA CADEIA DE SUPRIMENTOS]
    Build malicioso do instalador 3CXDesktopApp-18.12.416.msi
    Criação: 2023-03-13 06:33:26 UTC → Assinatura digital: +34s
    ↓
[FASE 2 — DISTRIBUIÇÃO]
    Instalador oficial 3CX comprometido distribuído a +600.000 empresas
    First Seen In The Wild: 2023-03-29
    ↓
[FASE 3 — DROP DE DLLs MALICIOSAS]
    Instalação em: C:\Users\Admin\AppData\Local\Programs\3CXDesktopApp\app-18.12.416\
    → ffmpeg.dll (2,7 MB) | d3dcompiler_47.dll (4,9 MB)
    ↓
[FASE 4 — DLL HIJACKING / EXECUÇÃO]
    T1574 — Hijack Execution Flow
    DLLs legítimas substituídas por versões trojan.marte/nukesped
    ↓
[FASE 5 — EVASÃO DE DEFESAS]
    T1497 — Virtualization/Sandbox Evasion (System Checks)
    Anti-VM strings direcionadas ao hipervisor VMware (ffmpeg.dll)
    ↓
[FASE 6 — CRIPTOGRAFIA E C2]
    ffmpeg.dll → RC4 PRGA/KSA para cifrar comunicações C2
    SHA1/SHA256 para verificação de integridade interna
    ↓
[FASE 7 — ATRIBUIÇÃO]
    NukeSped (BLINDINGCAN) RAT → Lazarus Group (HIDDEN COBRA / Andariel)
    APT patrocinado pela Coreia do Norte — confirmado por Mandiant/CrowdStrike
```

---

## 🗺 Mapeamento Investigativo

| Pergunta                              | Fonte de Evidência                              | Resposta                                    |
|------------------------------------------|-----------------------------------------------------|--------------------------------------------------|
| Versões Windows sinalizadas                  | Tria.ge — múltiplas execuções                          | `2`                                                  |
| Data/hora de criação do `.msi`                  | VirusTotal → Details → History                            | `2023-03-13 06:33:26 UTC`                              |
| DLLs depositadas                                   | Tria.ge — arquivos depositados                                | `ffmpeg.dll`, `d3dcompiler_47.dll`                       |
| Técnica MITRE de carregamento de DLL                  | VirusTotal → Behavior → Execution                                | `T1574`                                                     |
| Categoria de ameaça das DLLs                             | VirusTotal → Detection                                              | `Trojan`                                                       |
| Técnica MITRE de evasão de sandbox                          | VirusTotal → Behavior → Stealth                                        | `T1497`                                                           |
| Hipervisor alvo (anti-análise)                                 | VirusTotal → Behavior Catalog → Anti-Analysis                              | `VMware`                                                             |
| Algoritmo de criptografia (ffmpeg.dll)                            | VirusTotal → Behavior Catalog → Cryptography                                  | `RC4`                                                                   |
| Grupo responsável pelo ataque                                        | Threat Intel / Brave Search + VirusTotal                                          | `Lazarus`                                                                  |

---

## 🚨 Indicadores e Artefatos Técnicos (IOCs)

| Tipo                      | Valor                                                                    | Contexto                                                |
|------------------------------|-------------------------------------------------------------------------|--------------------------------------------------------|
| Instalador malicioso              | `3CXDesktopApp-18.12.416.msi`                                              | 97,80 MB — vetor inicial do supply chain attack             |
| SHA-256 (.msi)                       | `59e1edf4d82fae4978e97512b0331b7eb21dd4b838b850ba46794d9c7a2c0983`             | Instalador 3CX comprometido — versão 18.12.416                 |
| Criação do malware                     | `2023-03-13 06:33:26 UTC`                                                        | Creation Time extraído do VirusTotal Details                     |
| Versões Windows comprometidas             | 2 versões                                                                          | Ambas testadas no Tria.ge (win10 e win11)                           |
| DLL maliciosa 1                              | `ffmpeg.dll`                                                                         | 2,7 MB — trojan NukeSped com RC4 e anti-VMware                        |
| SHA-256 (ffmpeg.dll)                            | `7986bbaee8940da11ce089383521ab420c443ab7b15ed42aed91fd31ce833896`                     | Depositada em `app-18.12.416\ffmpeg.dll`                                 |
| DLL maliciosa 2                                     | `d3dcompiler_47.dll`                                                                     | 4,93 MB — trojan.marte/nukesped — 43/68 detecções VT                       |
| SHA-256 (d3dcompiler_47.dll)                            | `11be1803e2e307b647a8a7e02d128335c448ff741bf06bf52b332e0bbf423b03`                        | Depositada em `app-18.12.416\d3dcompiler_47.dll`                             |
| Caminho de instalação                                       | `C:\Users\Admin\AppData\Local\Programs\3CXDesktopApp\app-18.12.416\`                        | Diretório de instalação das DLLs maliciosas                                    |
| Técnica MITRE (carregamento DLL)                                | T1574 — Hijack Execution Flow                                                                | DLL Side-Loading / DLL Search Order Hijacking                                     |
| Categoria de ameaça                                                | Trojan                                                                                          | Família: marte, nukesped, supplychainagent                                          |
| Técnica MITRE (evasão)                                                | T1497 — Virtualization/Sandbox Evasion                                                            | T1497.001 (System Checks) — 3 ocorrências em cada DLL                                |
| Hipervisor alvo                                                          | VMware                                                                                              | Anti-VM strings na ffmpeg.dll detectadas pelo VirusTotal                              |
| Algoritmo de criptografia                                                    | RC4 (PRGA + KSA)                                                                                     | Usado pela ffmpeg.dll para cifrar comunicações C2                                       |
| Hashes criptográficos                                                          | SHA1, SHA256                                                                                          | Usados para verificação de integridade interna                                             |
| Grupo APT responsável                                                             | Lazarus Group (HIDDEN COBRA / Andariel)                                                                 | APT patrocinado pela Coreia do Norte — MITRE G0032                                            |
| Família de malware                                                                   | NukeSped (BLINDINGCAN)                                                                                    | RAT exclusivo do Lazarus — exfiltração + persistência                                            |
| YARA rule match                                                                         | `Windows_Trojan_SuddenIcon_bdae76c9`                                                                        | Ruleset Elastic Security — github.com/elastic/protections-artifacts                                |

---

## ✅ Resumo das Flags

| # | Pergunta                                                          | Flag / Resposta                       |
|---|------------------------------------------------------------------------|-------------------------------------------|
| Q1 | Quantas versões do 3CX Windows foram sinalizadas                          | `2`                                            |
| Q2 | Data/hora UTC de criação do `.msi`                                            | `2023-03-13 06:33`                                |
| Q3 | DLLs maliciosas depositadas                                                      | `ffmpeg.dll`, `d3dcompiler_47.dll`                    |
| Q4 | MITRE ID de carregamento de DLL maliciosa                                          | `T1574`                                                  |
| Q5 | Categoria de ameaça das DLLs                                                          | `Trojan`                                                    |
| Q6 | MITRE ID de evasão de virtualização/sandbox                                              | `T1497`                                                        |
| Q7 | Hipervisor alvo das técnicas anti-análise                                                    | `VMware`                                                          |
| Q8 | Algoritmo de criptografia usado pela `ffmpeg.dll`                                                | `RC4`                                                                |
| Q9 | Grupo responsável pelo ataque                                                                        | `Lazarus`                                                             |

---

## 📚 Referências

- [VirusTotal — 3CXDesktopApp-18.12.416.msi](https://virustotal.com/gui/file/59e1edf4d82fae4978e97512b0331b7eb21dd4b838b850ba46794d9c7a2c0983)
- [VirusTotal — d3dcompiler_47.dll](https://virustotal.com/gui/file/11be1803e2e307b647a8a7e02d128335c448ff741bf06bf52b332e0bbf423b03)
- [VirusTotal — ffmpeg.dll](https://virustotal.com/gui/file/7986bbaee8940da11ce089383521ab420c443ab7b15ed42aed91fd31ce833896)
- [Tria.ge (Recorded Future) — Análise sandbox](https://tria.ge/260627-mc49nahz6z/behavioral1)
- [Elastic Security — YARA Rules](https://github.com/elastic/protections-artifacts)
- [MITRE ATT&CK — Lazarus Group (G0032)](https://attack.mitre.org/groups/G0032/)
- [MITRE ATT&CK — T1574 Hijack Execution Flow](https://attack.mitre.org/techniques/T1574/)
- [MITRE ATT&CK — T1497 Virtualization/Sandbox Evasion](https://attack.mitre.org/techniques/T1497/)
- [CyberDefenders — 3CX Supply Chain CTF](https://cyberdefenders.org/blueteam-ctf-challenges/3cx-supply-chain/)

---