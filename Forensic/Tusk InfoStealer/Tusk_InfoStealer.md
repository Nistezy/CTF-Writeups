# 🔍 Tusk InfoStealer — CTF Writeup
### CyberDefenders Blue Team Challenge | Análise de Campanha de InfoStealer (StealC / Danabot)

---

| **Analista**          | Mauricio Robert                                                                     |
|-----------------------|-------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                   |
| **Data do Relatório** | 11/07/2026                                                                          |
| **Data do Incidente** | Ago/2024 (fonte: Kaspersky Securelist / CyberDefenders)                            |
| **Classificação**     | CONFIDENCIAL                                                                        |
| **Ferramentas**       | VirusTotal, Brave Search, Kaspersky Securelist (relatório #113367)                  |
| **Caso CTF**          | Tusk InfoStealer — CyberDefenders Blue Team                                         |

---

## 🔍 Resumo Executivo

A análise forense do desafio **Tusk InfoStealer** (CyberDefenders Blue Team) examinou a campanha de malware **"Tusk"**, identificada e nomeada pela equipe **Kaspersky GERT** (Global Emergency Response Team), conforme detalhado no relatório técnico publicado na plataforma **Securelist** (`securelist.com/tusk-infostealers-campaign/113367/`). A investigação utilizou como fontes de evidência o artefato malicioso **`madHcNet32.dll`** submetido ao **VirusTotal**, a página técnica da Securelist descrevendo as sub-campanhas **TidyMe**, **RuneOnlineWorld** e **Voico**, além de buscas complementares via **Brave Search** para confirmação de indicadores. A campanha é atribuída a cibercriminosos de língua russa que distribuem downloaders iniciais imitando aplicações legítimas (**peerme.io**, **runeonlineworld** e **yous.ai**), hospedados no **Dropbox**, os quais entregam infostealers (**StealC** e **Danabot**) e **clippers** de criptomoeda às vítimas. Os operadores utilizam o termo **"Mammoth"** em suas mensagens de log para se referir às vítimas comprometidas. Ao todo, **nove questões técnicas** foram respondidas com base em evidências extraídas do relatório Securelist, do VirusTotal e de buscas complementares.

---

## 🛠 Ferramentas e Fontes Utilizadas

| Ferramenta / Fonte           | Finalidade                                                                                     | URL / Referência                                              |
|-------------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| **Kaspersky Securelist**       | Relatório técnico completo da campanha Tusk (sub-campanhas, IoCs, IoAs)                        | `securelist.com/tusk-infostealers-campaign/113367`             |
| **VirusTotal**                 | Análise estática do artefato `madHcNet32.dll` (hashes, tamanho, metadados)                      | `virustotal.com/gui/file/523d4eb71af86090...`                  |
| **Brave Search (IA)**          | Confirmação do serviço de nuvem usado para hospedar os payloads                                | `search.brave.com`                                              |

---

## 📋 Perguntas e Respostas

### Q1 — In KB, what is the size of the malicious file?

> **Resposta: `921.36 KB`**

**Solução:** A página de detalhes do VirusTotal para o arquivo `madHcNet.dll` (SHA-256: `523d4eb71af86090d2d8a6766315a027fdec842041d668971bfbbbd1fe826722`, detectado como malicioso por **43 de 70** fornecedores de segurança) exibe, na seção **"Basic properties"**, o campo **"File size"** destacado com o valor **921.36 KB** (943.472 bytes). O arquivo é uma DLL Win32 compilada em Delphi (Embarcadero), assinada digitalmente, porém com **assinatura inválida** ("The digital signature of the object did not verify").

![Size in KB](/Forensic/Tusk%20InfoStealer/images/File_Size_in_KB(1).png)

---

### Q2 — What word do the threat actors use in log messages to describe their victims, based on the name of an ancient hunted creature?

> **Resposta: `Mammoth`**

**Solução:** O relatório da Securelist informa que a equipe Kaspersky GERT nomeou a campanha de **"Tusk"** (presa, em inglês) porque o ator da ameaça utiliza a palavra **"Mammoth"** nas mensagens de log dos downloaders iniciais das três sub-campanhas ativas analisadas. O termo é uma gíria usada por atores de ameaça de língua russa para se referir às vítimas — mamutes eram caçados por povos antigos e suas presas comercializadas, numa analogia à exploração das vítimas comprometidas. O termo também aparece em comentário da comunidade do VirusTotal referente ao mesmo arquivo (usuário *SuperUserdo*, comentário: "Mammoth").

![Name Victim](/Forensic/Tusk%20InfoStealer/images/Threat_Actors_Name_the_Victims(2).png)

---

### Q3 — The threat actor set up a malicious website to mimic peerme.io (DAOs on MultiversX). What is the name of the malicious website created?

> **Resposta: `tidyme.io`**

**Solução:** Na primeira sub-campanha, o ator da ameaça simulou a plataforma legítima **peerme.io**, destinada à criação e gestão de **DAOs** (organizações autônomas descentralizadas) na blockchain **MultiversX**. O site malicioso criado para imitar essa plataforma é **`tidyme[.]io`**, que substitui o botão legítimo "Create your Team now" por um botão **"Download"**. Ao clicar, uma requisição é enviada ao servidor com o **User-Agent** como argumento, que determina qual versão do arquivo malicioso (TidyMe.exe) será enviada de acordo com o sistema operacional da vítima.

![DAOs](/Forensic/Tusk%20InfoStealer/images/DAOs_First_Sub_Campaign(3).png)

---

### Q4 — Which cloud storage service did the campaign operators use to host malware samples for both macOS and Windows OS versions?

> **Resposta: `Dropbox`**

**Solução:** Conforme confirmado tanto pelo relatório da Securelist quanto pela busca complementar via **Brave Search (IA)**, todas as sub-campanhas ativas identificadas hospedam o downloader inicial no **Dropbox**. Os atacantes utilizam essa plataforma confiável para distribuir os componentes de downloader inicial e arquivos RAR protegidos por senha contendo os payloads de segundo estágio (**HijackLoader**, **StealC** e **Danabot**), tanto para vítimas macOS quanto Windows.


![Cloud Storag](/Forensic/Tusk%20InfoStealer/images/Cloud_Service_Used_for_Campaign(4).png)

---

### Q5 — What is the password for decompression found in the configuration file (config.json)?

> **Resposta: `newfile2024`**

**Solução:** O executável malicioso `tidyme.exe` contém um arquivo de configuração chamado **`config.json`** com URLs codificadas em base64 e uma senha utilizada para descompactar dados arquivados, empregada para baixar os payloads de segundo estágio:

```json
{
  "archive": "aHR0cHM6Ly93d3cuZHJvcGJveC5jb20vc2NsL2ZpL2N3NmpzYnA5ODF4eTg4dHpr...",
  "password": "newfile2024",
  "bytes": "aHR0cDovL3Rlc3Rsb2FkLnB5dGhvbmFueXdoZXJlLmNvbS9nZXRieXRlcy9m"
}
```

O campo **`password`** contém o valor **"newfile2024"**, utilizado para extrair o arquivo RAR protegido por senha (`updateload.rar`) baixado do Dropbox.

![Password](/Forensic/Tusk%20InfoStealer/images/Password_for_Descompression(5).png)

---

### Q6 — What is the name of the function responsible for retrieving the field archive from the configuration file?

> **Resposta: `downloadAndExtractArchive`**

**Solução:** A funcionalidade principal do downloader está armazenada no arquivo **`preload.js`**, em duas funções: `downloadAndExtractArchive` e `loadFile`. A função **`downloadAndExtractArchive`** é responsável por recuperar o campo **"archive"** do arquivo de configuração — um link do Dropbox codificado —, decodificá-lo e armazenar o arquivo baixado no caminho `%TEMP%/archive-<RANDOM_STRING>`. O arquivo baixado é um RAR protegido por senha, extraído com o valor do campo `password`, após o que todos os arquivos `.exe` do arquivo são executados.

![Function](/Forensic/Tusk%20InfoStealer/images/Funcition_Stored(6).png)

---

### Q7 — In the third sub-campaign, the attacker mimicked an AI translator project. What are the names of the legitimate and malicious translators?

> **Resposta: `yous.ai` (legítimo) e `voico.io` (malicioso)**

**Solução:** Na terceira sub-campanha, o ator da ameaça simulou um projeto legítimo de tradutor com IA chamado **YOUS**, cujo site original é **`yous.ai`**. O site malicioso criado para imitar essa plataforma é **`voico[.]io`**, cuja interface (`Voico.exe`) reproduz fielmente o layout de reuniões, chamadas e chats com tradução baseada em IA do site legítimo, distribuindo o downloader inicial correspondente a esta sub-campanha.

![Tranlate Site](/Forensic/Tusk%20InfoStealer/images/Third_Campaing_Correct_and_Malicious_Translate_Site(7).png
)
---

### Q8 — What are the IP addresses of the StealC C2 servers used in the campaign?

> **Resposta: `46.8.238.240` e `23.94.225.177`**

**Solução:** O downloader é responsável por entregar amostras adicionais de malware à máquina da vítima, principalmente os infostealers **StealC** e **Danabot**. A tabela **"Network IoCs"** do relatório Securelist lista os endereços IP **46.8.238.240** e **23.94.225.177**, ambos identificados como **servidores C2 do StealC**, além de outros IPs utilizados como C2 genéricos (89.169.52.59, 81.191.37.7, 194.116.217.148, 85.28.47.139) e para download de arquivos madHcCtrl (77.91.77.200).

![IP C2](/Forensic/Tusk%20InfoStealer/images/Steal_C2_IPs_Used(8).png)

---

### Q9 — What is the address of the Ethereum cryptocurrency wallet used in this campaign?

> **Resposta: `0xaf0362e215Ff4e004F30e785e822F7E20b99723A`**

**Solução:** A seção **"Cryptocurrency wallet addresses"** do relatório Securelist lista os endereços de carteiras associados à campanha, utilizados pelo malware **clipper** para substituir endereços de destino copiados pela vítima. O endereço de carteira **Ethereum (ETH)** identificado é **`0xaf0362e215Ff4e004F30e785e822F7E20b99723A`**, que recebeu um total de **9.137 ETH** em transações observadas entre 4 de março e 31 de julho, conforme o próprio relatório. Também foram listadas duas carteiras BTC (`1DSWHiAW1iSFYVb86WQQUPn57iQ6W1DjGo` e `bc1qqkvgqtpwq6g59xgwr2sccvmudejfxwyl8g9xg0`).

![Crypto Wallet](/Forensic/Tusk%20InfoStealer/images/Crypto_Wallet_ETH(9).png)

---

## ⛓ Fluxo do Ataque (Kill Chain)

```
[FASE 1 — ENGENHARIA SOCIAL / IMITAÇÃO DE MARCA]
    Sub-campanha 1: tidyme.io imita peerme.io (DAOs / MultiversX)
    Sub-campanha 2: runeonlineworld.io imita projeto de jogo legítimo
    Sub-campanha 3: voico.io imita yous.ai (tradutor com IA)
    Vítima clica em "Download" → requisição enviada com User-Agent
    Servidor entrega downloader adequado ao SO (Windows/macOS)
    ↓
[FASE 2 — DOWNLOADER INICIAL (TidyMe.exe / RuneOnlineWorld.exe / Voico.exe)]
    Aplicação Electron com config.json embutido:
        archive  → link Dropbox (base64) do updateload.rar
        password → "newfile2024"
        bytes    → link (base64) para payload adicional
    preload.js:
        downloadAndExtractArchive() → baixa e extrai o RAR protegido
        loadFile() → baixa "bytes", decodifica e grava .exe
    ↓
[FASE 3 — HOSPEDAGEM NA NUVEM]
    Todos os downloaders iniciais hospedados no Dropbox
    Evita bloqueios de perímetro por usar plataforma confiável
    ↓
[FASE 4 — ENTREGA DO PAYLOAD FINAL]
    updateload.exe / bytes.exe / madHcNet32.dll executados
    Infostealers entregues: StealC e Danabot
    Módulo adicional: Clipper (substitui endereços de wallet copiados)
    ↓
[FASE 5 — COMANDO E CONTROLE (C2)]
    StealC C2: 46.8.238.240 e 23.94.225.177
    C2 genéricos adicionais: 89.169.52.59, 81.191.37.7, 194.116.217.148, 85.28.47.139
    ↓
[RESULTADO — EXFILTRAÇÃO E ROUBO DE FUNDOS]
    Credenciais de browsers e carteiras de criptomoeda roubadas
    Clipper substitui endereço de destino: 0xaf0362e215Ff4e004F30e785e822F7E20b99723A
    Carteira ETH recebeu 9.137 ETH em transações rastreadas
    Vítimas referidas nos logs como "Mammoth"
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|--------------------|----------|
| Tamanho do arquivo malicioso | VirusTotal → `madHcNet.dll` (aba *Details*) | `921.36 KB` (943.472 bytes) |
| Palavra usada para as vítimas | Securelist → Summary / VirusTotal Community | `Mammoth` |
| Site malicioso (Sub-campanha 1) | Securelist → "First sub-campaign (TidyMe)" | `tidyme.io` (imita peerme.io) |
| Serviço de hospedagem em nuvem | Securelist + Brave Search (IA) | `Dropbox` |
| Senha de descompactação | Securelist → `config.json` | `newfile2024` |
| Função de download do archive | Securelist → `preload.js` | `downloadAndExtractArchive` |
| Tradutor legítimo x malicioso (Sub-campanha 3) | Securelist → "Third sub-campaign (Voico)" | `yous.ai` / `voico.io` |
| IPs de C2 do StealC | Securelist → tabela "Network IoCs" | `46.8.238.240`, `23.94.225.177` |
| Carteira Ethereum da campanha | Securelist → tabela "Cryptocurrency wallet addresses" | `0xaf0362e215Ff4e004F30e785e822F7E20b99723A` |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Valor | Contexto |
|------|-------|----------|
| Arquivo malicioso | `madHcNet32.dll` (943.472 bytes / 921.36 KB) | SHA-256: `523d4eb71af86090d2d8a6766315a027fdec842041d668971bfbbbd1fe826722` |
| Termo de campanha | `Mammoth` | Gíria usada nos logs dos downloaders para se referir às vítimas |
| Site malicioso (Sub-campanha 1) | `tidyme.io` | Imita peerme.io (DAOs na blockchain MultiversX) |
| Site malicioso (Sub-campanha 2) | `runeonlineworld.io` | Campanha "RuneOnlineWorld" |
| Site malicioso (Sub-campanha 3) | `voico.io` | Imita yous.ai (tradutor com IA) |
| Serviço de hospedagem | `Dropbox` | Hospeda downloaders iniciais e arquivos RAR de 2º estágio (macOS/Windows) |
| Senha de descompactação | `newfile2024` | Campo "password" do `config.json` |
| Função de download | `downloadAndExtractArchive` | Localizada em `preload.js` — recupera o campo "archive" |
| C2 StealC | `46.8.238.240` / `23.94.225.177` | Servidores de comando e controle do infostealer StealC |
| C2 genéricos | `89.169.52.59`, `81.191.37.7`, `194.116.217.148`, `85.28.47.139` | Infraestrutura adicional de C2 da campanha |
| Download madHcCtrl | `77.91.77.200` | Servidor de distribuição de arquivos madHcCtrl |
| Carteira ETH | `0xaf0362e215Ff4e004F30e785e822F7E20b99723A` | Recebeu 9.137 ETH em transações rastreadas pela Kaspersky |
| Carteira BTC | `1DSWHiAW1iSFYVb86WQQUPn57iQ6W1DjGo` | Wallet observada no malware clipper |
| Carteira BTC | `bc1qqkvgqtpwq6g59xgwr2sccvmudejfxwyl8g9xg0` | Wallet observada no malware clipper — 0.0209 BTC recebido |
| Malware entregue | StealC, Danabot, Clipper | Infostealers e módulo de sequestro de área de transferência |
| Técnica (MITRE ATT&CK) | `T1566` | Phishing |
| Técnica (MITRE ATT&CK) | `T1204` | User Execution |
| Técnica (MITRE ATT&CK) | `T1027` | Obfuscated Files or Information |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | Tamanho do arquivo malicioso (em KB) | `921.36 KB` |
| Q2 | Palavra usada nos logs para descrever as vítimas | `Mammoth` |
| Q3 | Nome do site malicioso que imita peerme.io | `tidyme.io` |
| Q4 | Serviço de nuvem usado para hospedar os payloads | `Dropbox` |
| Q5 | Senha de descompactação no config.json | `newfile2024` |
| Q6 | Função que recupera o campo "archive" | `downloadAndExtractArchive` |
| Q7 | Tradutores legítimo e malicioso (3ª sub-campanha) | `yous.ai` / `voico.io` |
| Q8 | IPs dos servidores C2 do StealC | `46.8.238.240`, `23.94.225.177` |
| Q9 | Endereço da carteira Ethereum da campanha | `0xaf0362e215Ff4e004F30e785e822F7E20b99723A` |

---

## 📚 Referências

- [Kaspersky Securelist — Tusk: unraveling a complex infostealer campaign](https://securelist.com/tusk-infostealers-campaign/113367/)
- [VirusTotal — madHcNet.dll](https://virustotal.com/gui/file/523d4eb71af86090d2d8a6766315a027fdec842041d668971bfbbbd1fe826722)
- [CyberDefenders — Tusk InfoStealer CTF Lab](https://cyberdefenders.org/blueteam-ctf-challenges/)
- [MITRE ATT&CK T1566 — Phishing](https://attack.mitre.org/techniques/T1566/)
- [MITRE ATT&CK T1204 — User Execution](https://attack.mitre.org/techniques/T1204/)
- [MITRE ATT&CK T1027 — Obfuscated Files or Information](https://attack.mitre.org/techniques/T1027/)

---