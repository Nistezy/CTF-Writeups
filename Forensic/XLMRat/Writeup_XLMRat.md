# 🐭 Malware Investigation — XLMRat (AsyncRAT via PowerShell Dropper)

## 📌 Overview

Este writeup apresenta a análise forense de um ataque de malware baseado em **XLMRat**, no cenário *Blue Team CTF Challenges*.

A investigação revelou um comprometimento completo da máquina vítima, desde o download de um dropper ofuscado em PowerShell até a execução de um RAT (Remote Access Trojan) identificado como **AsyncRAT**, com comunicação C2 ativa capturada via Wireshark.

---

## 🎯 Objetivo

* Identificar o vetor de infecção inicial
* Analisar o dropper PowerShell ofuscado
* Decodificar o payload hexadecimal embutido
* Identificar a família do malware via VirusTotal
* Rastrear a infraestrutura C2
* Extrair IOCs

---

## 🧠 Resumo do Ataque

O atacante utilizou um servidor remoto (**45.126.209.4**) para hospedar e distribuir o malware:

1. 🔗 Download de um arquivo disfarçado de imagem (`mdm.jpg`) via PowerShell
2. 🧩 Deofuscação de script VBScript com array de 88 fragmentos
3. 💻 Execução de `Invoke-Expression` para baixar o payload real
4. 🔣 Conversão de string hexadecimal em executável PE (`.exe`)
5. 📡 Comunicação C2 com servidor remoto
6. 🐀 Execução do AsyncRAT na máquina comprometida

---

## ⏱️ Timeline do Ataque

| Fase            | Evento                                              |
| --------------- | --------------------------------------------------- |
| Inicial         | Requisição HTTP GET para `/mdm.jpg` no C2           |
| Dropper         | Download e execução de script PowerShell ofuscado   |
| Deofuscação     | Reconstrução do comando via array VBScript          |
| Payload         | Decodificação de HEX para binário PE (.exe)         |
| Persistência    | Escrita de arquivos `.ps1`, `.bat`, `.vbs` em disco |
| C2              | Comunicação TCP com servidor 45.126.209.4:222       |
| Execução        | AsyncRAT ativo como Stub.exe / XLMRatq3             |

---

## 🔍 Análise Técnica

---

### 🌐 Infraestrutura C2 — Host Provider

A consulta WHOIS do IP **45.126.209.4** revelou que o servidor pertence à **ReliableSite.Net LLC**, empresa de hospedagem registrada nos EUA com infraestrutura na Ásia (SG).

![Host Provider WHOIS](/Forensic/XLMRat/images/Host_Provider.png)

📌 Detalhes do IP:

* **IP:** `45.126.209.4`
* **Provedor:** ReliableSite.Net LLC
* **País registrado:** US (endereço físico: Miami, FL 33142)
* **Geoloc:** 25.7975441, -80.2322913
* **Porta C2 utilizada:** `222`

---

### 📥 Primeiro Estágio — URL de Instalação do Malware

A análise do tráfego Wireshark (arquivo `236-XLMRat.pcap`) revelou a requisição HTTP inicial para download do dropper:

![URL First Stage](/Forensic/XLMRat/images/URL_First_Stage_of_the_malware_instaled.png)

📌 Detalhes da requisição:

* **Método:** `GET /mdm.jpg HTTP/1.1`
* **Host:** `45.126.209.4:222`
* **User-Agent:** `Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; Win64; x64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729)`
* **Servidor:** Apache/2.4.58 (Win64) OpenSSL/3.1.3 PHP/8.0.30
* **Resposta:** `HTTP/1.1 200 OK`, `Content-Type: text/plain`
* **Tamanho:** 1974 bytes

O arquivo `mdm.jpg` é, na verdade, um **script PowerShell ofuscado** — não uma imagem legítima.

---

### 🔣 Decodificação do Lolbin / PowerShell Ofuscado

O script VBScript recebido cria um array chamado `LZeuX` com **88 fragmentos de texto**. O laço `For` reconstrói a variável `OodjR`, que ao final forma o comando PowerShell real:
![Decode Lolbin](/Forensic/XLMRat/images/Decode_Lolbin.png)
📌 Variáveis principais reconstruídas:

* `$A123` = `IeX(NeW-OBJeCT NeT.W`
* `$B456` = `eBClIeNT).DOWNLO`
* `$C789` = URL com substituição de `VAN` → `ADSTRING`

**Truque de substituição:**

O PowerShell executa `.RePlaCe('VAN','ADSTRING')` para montar a URL real antes de invocar o download. Isso evita detecção por assinaturas estáticas.

---

### 💻 Código do Lolbin — Script Malicioso Completo

O payload recebido via TCP contém o script PowerShell completo responsável por:

1. Converter o HEX em bytes
2. Carregar o assembly via `[Reflection.Assembly]`
3. Escrever arquivos auxiliares em disco (`Conted.ps1`, `Conted.bat`, `Conted.vbs`)
4. Configurar agendamento e execução oculta

![Lolbin](/Forensic/XLMRat/images/Lolbin_Malware_code.png)

📌 Caminhos utilizados:

* `C:\Users\Public\Conted.ps1`
* `C:\Users\Public\Conted.bat`
* `C:\Users\Public\Conted.vbs`

---

### 🔄 Fluxo TCP — Descriptografia do Malware

O fluxo TCP completo capturado no Wireshark mostra a sequência de download e execução:

![Fluxo TCP Decrypt](/Forensic/XLMRat/images/Fluxo_TCP_Decrypte_malware.png)

📌 Comportamento observado:

* Download do payload via `DownloadString`
* Conversão de HEX para bytes via `$hexString_bbb`
* Uso de `[Reflection.Assembly]::$HM($pe)` para carregar em memória
* Invocação via `RegSvcs.exe` (LOLBIN nativo do Windows)

---

### 🔧 Transformação HEX em Malware

O script utiliza `$hexString_bbb` separado por `_` e converte cada token via `[byte][convert]::ToInt32($_, 16)` para montar o PE em memória:

![Transform HEX in Malware](/Forensic/XLMRat/images/Transform_HEX_in_Malware.png)

O cabeçalho `4D 5A` (MZ) confirma que o resultado decodificado é um **executável Windows PE**.

---

### 🗑️ Deleção de Arquivos — Limpeza de Rastros

Após a execução, o malware elimina arquivos temporários utilizados durante o processo de infecção:

![Delete Archives](/Forensic/XLMRat/images/Delete_Archives.png)

---

### 🧪 Decodificação do mdm.png via ChatGPT

O arquivo `mdm.txt` (payload HEX extraído) foi analisado, confirmando:

![mdm png decode](/Forensic/XLMRat/images/mdm.png_decode.png)

* **Tipo:** Windows Portable Executable (PE)
* **Tamanho:** 66.560 bytes
* **SHA-256:** `1eb7b02e18f67420f42b1d94e74f3b6289d92672a0fb1786c30c03d68e81d798`

---

### 🕒 Data de Criação do Malware

Metadados extraídos via VirusTotal (aba Details):

![Time of Creation](/Forensic/XLMRat/images/Time_of_creation_of_malware.png)

📌 Histórico:

* **Creation Time:** `2023-10-30 15:08:44 UTC`
* **First Seen In The Wild:** `2024-01-11 18:17:54 UTC`
* **First Submission:** `2024-01-11 16:36:37 UTC`
* **Last Submission:** `2026-05-26 09:29:46 UTC`
* **Tamanho do arquivo:** 65.00 KB (66.560 bytes)
* **Nomes conhecidos:** `Stub.exe`, `XLMRatq3`, `payload_extracted.exe`, `hexString_bbb.exe`

---

### 🦠 Família do Malware — Classificação VirusTotal (Alibaba)

O VirusTotal classificou o hash com **61/71 detecções**:

![Family Malware by Alibaba](/Forensic/XLMRat/images/Family_malware_by_alibaba.png)

📌 Detecções relevantes:

| Vendor            | Classificação                        |
| ----------------- | ------------------------------------ |
| AhnLab-V3         | Malware/Win.Generic.C4980844         |
| Alibaba           | Backdoor:MSIL/AsyncRat.a2786761      |
| BitDefender       | Gen:Variant.AsyncRat.Marte.6         |
| CrowdStrike       | Win/malicious_confidence\_100% (W)   |
| DrWeb             | BackDoor.AsyncRATNET.2               |
| ESET-NOD32        | MSIL/AsyncRAT.A Trojan               |
| Kaspersky         | HEUR:Backdoor.MSIL.SheetRat.gen      |
| Fortinet          | MSIL/AsyncRAT.A!tr                   |

* **Popular threat label:** `trojan.asyncrat/msil`
* **Threat categories:** trojan · dropper · banker
* **Family labels:** asyncrat · msil · marte

---

## 📡 Evidências Forenses

* Tráfego HTTP com download de dropper disfarçado de `.jpg`
* Script PowerShell com ofuscação via array VBScript (88 fragmentos)
* Conversão de string hexadecimal para PE em memória
* LOLBIN `RegSvcs.exe` utilizado como host de execução
* Arquivos `.ps1`, `.bat`, `.vbs` escritos em `C:\Users\Public\`
* Comunicação C2 na porta `222` com `45.126.209.4`
* 61/71 detecções no VirusTotal confirmando AsyncRAT

---

## 🧬 MITRE ATT&CK

| Técnica                          | ID          | Descrição                                      |
| -------------------------------- | ----------- | ---------------------------------------------- |
| Phishing / Drive-by Download     | T1566 / T1189 | Entrega do dropper via link externo           |
| Obfuscated Files or Information  | T1027       | Script VBScript com array ofuscado             |
| PowerShell                       | T1059.001   | Execução via `Invoke-Expression`               |
| Signed Binary Proxy Execution    | T1218.009   | LOLBIN `RegSvcs.exe` para carregar o payload   |
| Ingress Tool Transfer            | T1105       | Download do payload via `DownloadString`       |
| Application Layer Protocol: Web  | T1071.001   | C2 sobre HTTP na porta 222                     |
| Remote Access Tools              | T1219       | AsyncRAT como backdoor                         |
| Indicator Removal                | T1070       | Deleção de arquivos temporários                |

---

## 🚨 Indicadores de Comprometimento (IOCs)

* **IP C2:** `45.126.209.4`
* **Porta C2:** `222`
* **URL dropper:** `http://45.126.209.4:222/mdm.jpg`
* **Provedor de hospedagem:** ReliableSite.Net LLC
* **SHA-256 (payload):** `1eb7b02e18f67420f42b1d94e74f3b6289d92672a0fb1786c30c03d68e81d798`
* **MD5:** `88e8cee73f454bc1fa6b3a7741a3bd7d`
* **SHA-1:** `38a2b1c29b916fa296e3d48e03ddf33a7fbead0`
* **Nomes do executável:** `Stub.exe`, `XLMRatq3`, `payload_extracted.exe`
* **Família:** AsyncRAT (MSIL)
* **Arquivos criados:**
  * `C:\Users\Public\Conted.ps1`
  * `C:\Users\Public\Conted.bat`
  * `C:\Users\Public\Conted.vbs`
* **LOLBIN utilizado:** `C:\Windows\Microsoft.NET\Framework\v4.0.30319\RegSvcs.exe`
* **Data de criação do malware:** `2023-10-30 15:08:44 UTC`