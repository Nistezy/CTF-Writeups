# 🔍 Carnage — CTF Writeup
### TryHackMe | Análise de Tráfego Malicioso | Squirrelwaffle · Qakbot · Cobalt Strike C2

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 31/07/2026                                                                             |
| **Data da Captura**   | 24/09/2021 (`carnage.pcap`)                                                            |
| **Alvo/Caso**         | `carnage.pcap` — TryHackMe · Carnage (tryhackme.com/room/c2carnage)                   |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Wireshark · VirusTotal (Community)                                                    |
| **Host Vítima**       | `10.9.23.102`                                                                          |
| **Plataforma**        | TryHackMe — Network Forensics / Malware Traffic Analysis                              |

---

## 🔍 Resumo Executivo

Este relatório documenta a análise forense da captura de tráfego **carnage.pcap**, referente ao desafio **Carnage** do TryHackMe, que reproduz uma infecção real por **Squirrelwaffle**, seguida da entrega de **Qakbot** e do estabelecimento de infraestrutura de comando e controle (C2) via **Cobalt Strike**. A investigação, conduzida integralmente com **Wireshark** e consultas ao **VirusTotal**, reconstrói a cadeia completa do ataque: o download inicial de um ZIP malicioso hospedado em `attirenepal.com`, contendo uma planilha maliciosa (`chart-1530076591.xls`) usada como isca; o tráfego de segundo estágio para múltiplos domínios comprometidos via TLS (`thietbiagt.com`, `finejewels.com.au`, `new.americold.com`); o beacon de pós-infecção para `maldivehost.net`; a identificação de dois servidores **Cobalt Strike** (`185.106.96.158` e `185.125.204.174`) associados aos domínios `survmeter[.]live` e `securitybusinpuff[.]com`; a verificação de IP externo via `api.ipify.org`; e evidências de atividade de **malspam** via SMTP. Ao todo, **vinte questões técnicas** foram respondidas com base em evidências extraídas diretamente dos pacotes capturados.

---

## 🛠 Ferramentas e Fontes Utilizadas

| Ferramenta                | Finalidade                                                                          | Arquivo / Referência                          |
|----------------------------|--------------------------------------------------------------------------------------|-----------------------------------------------|
| **Wireshark**              | Inspeção de pacotes, Follow TCP/HTTP Stream, filtros (`http`, `smtp`, `dns`, `tls.handshake`) | `carnage.pcap`                                |
| **VirusTotal (Community)** | Verificação de reputação de IPs e confirmação de servidores Cobalt Strike C2         | `185.106.96.158`, `185.125.204.174`           |

---

## 📋 Estágios da Investigação

### FASE 1 — Estágio Inicial: Download do Payload Malicioso

> **2021-09-24 16:44:38 UTC · Wireshark · Filtro: `http`**

**Q1 — What was the date and time for the first HTTP connection to the malicious IP?**

> 🚩 **Resposta: `2021-09-24 16:44:38`**

**Evidência:** O primeiro pacote HTTP do fluxo (frame 1735), filtrado por `http`, é uma requisição GET para o IP malicioso `85.187.128.24`. O campo "Arrival Time" confirma o timestamp `Sep 24, 2021 16:44:38.990412000 UTC`.

![HTTP Connection](/Forensic/Carnage/images/First_HTTP_Connection(1).png)
*Figura 1 — Frame 1735, primeira conexão HTTP ao IP malicioso 85.187.128.24 em 2021-09-24 16:44:38 UTC*

**Q2 — What is the name of the zip file that was downloaded?**

> 🚩 **Resposta: `documents.zip`**

**Evidência:** A requisição `GET /incidunt-consequatur/documents.zip HTTP/1.1` (frame 1735) evidencia o download, confirmado pelo cabeçalho `content-disposition: attachment; filename=documents.zip` na resposta (frame 1841).

![Zip Name](/Forensic/Carnage/images/Name_of_zip_Download(2).png)
*Figura 2 — Requisição GET evidenciando o download do arquivo documents.zip*

**Q3 — What was the domain hosting the malicious zip file?**

> 🚩 **Resposta: `attirenepal.com`**

**Evidência:** No Follow HTTP Stream (`tcp.stream eq 73`), o cabeçalho `Host: attirenepal.com` da requisição GET confirma o domínio responsável por hospedar `documents.zip`, resolvido para `85.187.128.24`.

![Domain Name .zip](/Forensic/Carnage/images/Domain_Host_Malicious_zip(3).png)
*Figura 3 — Follow HTTP Stream destacando o cabeçalho Host: attirenepal.com*

**Q4 — Without downloading the file, what is the name of the file in the zip file?**

> 🚩 **Resposta: `chart-1530076591.xls`**

**Evidência:** Inspecionando os bytes brutos do corpo da resposta HTTP diretamente no Wireshark (assinatura `PK` do formato ZIP), o nome do arquivo interno `chart-1530076591.xls` aparece em texto claro logo após a assinatura, sem necessidade de extrair o ZIP.

![Archive in Zip](/Forensic/Carnage/images/Name_of_Archive_in_zip(4).png)
*Figura 4 — Confirmação do arquivo interno chart-1530076591.xls, identificado sem download do ZIP*

**Q5 — What is the name of the webserver of the malicious IP from which the zip file was downloaded?**

> 🚩 **Resposta: `LiteSpeed`**

**Evidência:** No Follow TCP Stream do fluxo 73, o cabeçalho de resposta `server: LiteSpeed` identifica o software web utilizado pelo host malicioso `85.187.128.24`.

![Name WebServer](/Forensic/Carnage/images/Name_of_WebServer(5).png)
*Figura 5 — Cabeçalho server: LiteSpeed identificado no Follow TCP Stream*

**Q6 — What is the version of the webserver from the previous question?**

> 🚩 **Resposta: `PHP/7.2.34`**

**Evidência:** Complementando o cabeçalho Server, a resposta HTTP inclui `x-powered-by: PHP/7.2.34`, caracterizando a pilha do servidor web malicioso.

![Version WebServer](/Forensic/Carnage/images/Version_of_WebServer(6).png)
*Figura 6 — Cabeçalho x-powered-by: PHP/7.2.34 destacado no Follow TCP Stream*

---

### FASE 2 — Domínios Maliciosos Adicionais e Certificados TLS

> **Wireshark · Filtro: `tls.handshake.type == 1`**

**Q7 — Malicious files were downloaded to the victim host from multiple domains. What were the three domains involved with this activity?**

> 🚩 **Resposta: `thietbiagt.com`, `finejewels.com.au`, `new.americold.com`**

**Evidência:** Filtrando por `tls.handshake.type == 1` (Client Hello), três handshakes TLS distintos revelam, na extensão SNI, os domínios acima — infraestrutura comprometida usada para entrega de payloads adicionais.

![Malicious Multiples Domains](/Forensic/Carnage/images/Malicious_Multiples_Domains(7).png)
*Figura 7 — Três handshakes TLS Client Hello destacando os domínios thietbiagt.com, finejewels.com.au e new.americold.com*

**Q8 — Which certificate authority issued the SSL certificate to the first domain from the previous question?**

> 🚩 **Resposta: `Go Daddy Secure Certificate Authority - G2`**

**Evidência:** O primeiro domínio cronologicamente é `finejewels.com.au` (frame 2427). O certificado apresentado no handshake (frame 2436) mostra `id-at-commonName=finejewels.com.au`, emitido por uma cadeia cujo intermediário identifica `Go Daddy Secure Certificate Authority - G2`.

![Certificate Malicious Domain](/Forensic/Carnage/images/Certificate_of_First_Malicious_Domais(8).png)
*Figura 8 — Cadeia de certificados TLS destacando a emissão por Go Daddy Secure Certificate Authority - G2*

---

### FASE 3 — Infraestrutura de Comando e Controle: Cobalt Strike

> **VirusTotal (Community) · IPs: 185.106.96.158 / 185.125.204.174**

**Q9 — What are the two IP addresses of the Cobalt Strike servers?**

> 🚩 **Resposta: `185.106.96.158`, `185.125.204.174`**

**Evidência:** A aba Community do VirusTotal confirma comentários da comunidade (usuário `drb_ra`) identificando explicitamente "Cobalt Strike Server Found" para `185.106.96.158` (portas 443, 80, 8888) e `185.125.204.174` (portas 4444, 8080).

![Two IP address of Cobalt Strike](/Forensic/Carnage/images/Two_IPs_of_Cobalt_Strike(9).png)
*Figura 9 — VirusTotal (Community) confirmando os dois servidores Cobalt Strike*

**Q10 — What is the Host header for the first Cobalt Strike IP address from the previous question?**

> 🚩 **Resposta: `ocsp.verisign.com`**

**Evidência:** Filtrando por `ip.dst == 185.106.96.158 && http.request.method`, a requisição `GET /spfooh/cacerts.crl HTTP/1.1` revela o cabeçalho `Host: ocsp.verisign.com` — um Host header falsificado (**domain fronting**) característico de perfis maleáveis do Cobalt Strike.

![Host Header](/Forensic/Carnage/images/Host_Header(10).png)
*Figura 10 — Requisição HTTP ao Cobalt Strike (185.106.96.158) com Host: ocsp.verisign.com*

**Q11 — What is the domain name for the first IP address of the Cobalt Strike server?**

> 🚩 **Resposta: `survmeter[.]live`**

**Evidência:** Os comentários da comunidade no VirusTotal para `185.106.96.158` detalham configurações de C2 Cobalt Strike associadas ao domínio `survmeter[.]live` (path `/gscp[.]R/`, POST URI `/supprq/sa/`).

![DNS Cobalt Strike IP 1](/Forensic/Carnage/images/First_IP_Cobalt_Strike_Domain_Name(11).png)
*Figura 11 — VirusTotal confirmando o domínio survmeter[.]live associado a 185.106.96.158*

**Q12 — What is the domain name of the second Cobalt Strike server IP?**

> 🚩 **Resposta: `securitybusinpuff[.]com`**

**Evidência:** De forma análoga, os comentários da comunidade no VirusTotal para `185.125.204.174` identificam o C2 Server `securitybusinpuff[.]com` (path `/jquery-3[.]3[.]1[.]min[.]js`).

![DNS Cobalt Strike IP 2](/Forensic/Carnage/images/Second_IP_Cobalt_Strike_Domain_Name(12).png)
*Figura 12 — VirusTotal confirmando o domínio securitybusinpuff[.]com associado a 185.125.204.174*

---

### FASE 4 — Tráfego de Pós-Infecção (Beacon Squirrelwaffle/Qakbot)

> **Wireshark · Filtro: `http.request.method == "POST"`**

**Q13 — What is the domain name of the post-infection traffic?**

> 🚩 **Resposta: `maldivehost.net`**

**Evidência:** Filtrando por `http.request.method == "POST"`, uma sequência extensa de requisições `POST /zLIisQRWZI9/<string aleatória>` é enviada ao IP `208.91.128.6`. O cabeçalho `Host: maldivehost.net` (frame 10257) identifica o domínio responsável por esse check-in.

![DNS Post Infection](/Forensic/Carnage/images/Domain_Name_Post_Infection_Trafic(13).png)
*Figura 13 — Requisições POST ao domínio pós-infecção maldivehost.net (208.91.128.6)*

**Q14 — What are the first eleven characters that the victim host sends out to the malicious domain involved in the post-infection traffic?**

> 🚩 **Resposta: `zLIisQRWZI9`**

**Evidência:** O caminho da URI de cada requisição POST inicia com o identificador fixo `/zLIisQRWZI9/`, seguido de uma string variável em Base64 — os onze caracteres fixos observados de forma consistente em todos os frames da conversa.

![URL](/Forensic/Carnage/images/First_Eleven_Caracters_that_Victim_Send(14).png)
*Figura 14 — Os onze caracteres iniciais "zLIisQRWZI9" extraídos da URI enviada ao domínio malicioso*

**Q15 — What was the length for the first packet sent out to the C2 server?**

> 🚩 **Resposta: `281 bytes`**

**Evidência:** O primeiro pacote da sequência POST ao domínio de pós-infecção é o frame 3822 (t=153.653113s), com `Length = 281 bytes`, valor que se repete de forma consistente nas requisições subsequentes de check-in.

![Size in bytes](/Forensic/Carnage/images/Size_Length_for_First_Packet_to_C2(15).png)
*Figura 15 — Primeiro pacote POST ao C2 (frame 3822) com comprimento de 281 bytes*

**Q16 — What was the Server header for the malicious domain from the previous question?**

> 🚩 **Resposta: `Apache/2.4.49 (cPanel) OpenSSL/1.1.1l mod_bwlimited/1.4`**

**Evidência:** Filtrando por `ip.src == 208.91.128.6 and http`, as respostas `HTTP/1.1 200 OK` do servidor `maldivehost.net` expõem o cabeçalho `server: Apache/2.4.49 (cPanel) OpenSSL/1.1.1l mod_bwlimited/1.4`, complementado por `x-powered-by: PHP/5.6.40`.

![Server Header](/Forensic/Carnage/images/Server_Header_for_Malicious_Domain(16).png)
*Figura 16 — Cabeçalho Server do domínio malicioso maldivehost.net (208.91.128.6)*

---

### FASE 5 — Verificação de IP Externo e Atividade de Malspam

> **Wireshark · Filtros: `dns.flags.response == 0`, `smtp`**

**Q17 — What was the date and time when the DNS query for the IP check domain occurred?**

> 🚩 **Resposta: `2021-09-24 17:00:04 UTC`**

**Evidência:** Filtrando por `dns.flags.response == 0` (apenas consultas), o frame 24147 registra uma consulta DNS tipo A. O campo "UTC Arrival Time" confirma o timestamp `Sep 24, 2021 17:00:04.093354000 UTC`.

![Time of API Check](/Forensic/Carnage/images/Time_of_API_Check_IP_Address(17).png)
*Figura 17 — Frame 24147, consulta DNS de verificação de IP em 2021-09-24 17:00:04 UTC*

**Q18 — What was the domain in the DNS query from the previous question?**

> 🚩 **Resposta: `api.ipify.org`**

**Evidência:** A árvore de detalhes do frame 24147 mostra, na seção Queries, o nome consultado `api.ipify.org, type A, class IN` — serviço público legítimo de consulta de IP externo, abusado pelo malware para checagem de geolocalização/IP da vítima.

![DNS API](/Forensic/Carnage/images/Domain_Name_of_API(18).png)
*Figura 18 — Consulta DNS ao domínio api.ipify.org, utilizado para verificação do IP da vítima*

**Q19 — What was the first MAIL FROM address observed in the traffic?**

> 🚩 **Resposta: `farshin@mailfa.com`**

**Evidência:** Filtrando por `smtp`, o frame 28576 contém o comando `MAIL FROM:<farshin@mailfa.com>`, correspondendo ao primeiro remetente observado na atividade de malspam capturada na sessão.

![First Email](/Forensic/Carnage/images/First_Email_From_Address(19).png)
*Figura 19 — Comando SMTP MAIL FROM destacando o endereço farshin@mailfa.com*

**Q20 — How many packets were observed for the SMTP traffic?**

> 🚩 **Resposta: `1439 pacotes`**

**Evidência:** A janela **Statistics → Protocol Hierarchy** do Wireshark mostra, para o protocolo SMTP, `1439 pacotes` (100,0% dos pacotes exibidos pelo filtro `smtp`).

![How Many SMTP Packets Have](/Forensic/Carnage/images/How_Many_Packets_Have_in_SMTP(20).png)
*Figura 20 — Protocol Hierarchy Statistics confirmando 1439 pacotes SMTP*

---

## ⛓ Linha do Tempo do Incidente

```
[16:44:38 UTC] FASE 1 — ESTÁGIO INICIAL (HTTP)
    GET /incidunt-consequatur/documents.zip → 85.187.128.24 (attirenepal.com)
    Servidor: LiteSpeed / PHP 7.2.34
    Conteúdo do ZIP: chart-1530076591.xls (planilha isca)
    ↓
[t+~89s]        FASE 2 — DOMÍNIOS TLS DE 2º ESTÁGIO
    Client Hello (SNI): finejewels.com.au, thietbiagt.com, new.americold.com
    Certificado: Go Daddy Secure Certificate Authority - G2
    ↓
[±16:44–17:00]  FASE 3 — C2 COBALT STRIKE
    185.106.96.158 → survmeter[.]live (Host falso: ocsp.verisign.com)
    185.125.204.174 → securitybusinpuff[.]com
    Confirmado via VirusTotal Community (drb_ra)
    ↓
[t=153.65s]     FASE 4 — BEACON PÓS-INFECÇÃO
    POST /zLIisQRWZI9/<base64> → maldivehost.net (208.91.128.6)
    Primeiro pacote: 281 bytes · Servidor: Apache/2.4.49 (cPanel)
    ↓
[17:00:04 UTC]  FASE 5 — VERIFICAÇÃO DE IP + MALSPAM
    Consulta DNS → api.ipify.org (checagem de IP externo da vítima)
    SMTP MAIL FROM: farshin@mailfa.com · 1439 pacotes SMTP no total
    ↓
COMPROMETIMENTO CONFIRMADO — cadeia Squirrelwaffle → Qakbot → Cobalt Strike C2
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Estágio Inicial | Wireshark (`http`) | Download de `documents.zip` via `attirenepal.com` (85.187.128.24, LiteSpeed/PHP 7.2.34) contendo `chart-1530076591.xls` |
| Domínios TLS | Wireshark (`tls.handshake.type == 1`) | `thietbiagt.com`, `finejewels.com.au`, `new.americold.com` — certificado emitido por Go Daddy G2 |
| C2 Cobalt Strike | VirusTotal (Community) | `185.106.96.158` (survmeter[.]live) e `185.125.204.174` (securitybusinpuff[.]com); domain fronting com `ocsp.verisign.com` |
| Pós-Infecção | Wireshark (`http.request.method == "POST"`) | Beacon para `maldivehost.net` (208.91.128.6) com URI fixa `/zLIisQRWZI9/` |
| Recon/Malspam | Wireshark (`dns`, `smtp`) | Consulta a `api.ipify.org`; malspam com `MAIL FROM: farshin@mailfa.com` (1439 pacotes SMTP) |

---

## 🚨 Indicadores e Artefatos Técnicos (IoCs)

| Tipo | Valor | Contexto |
|------|-------|----------|
| Host vítima | `10.9.23.102` | Máquina infectada, origem de todo o tráfego malicioso analisado |
| IP malicioso (zip) | `85.187.128.24` | Serviu `documents.zip` via HTTP (`attirenepal.com`), servidor LiteSpeed / PHP 7.2.34 |
| Domínio (zip) | `attirenepal.com` | Hospedou o arquivo `documents.zip` contendo `chart-1530076591.xls` |
| Arquivo isca | `chart-1530076591.xls` | Planilha maliciosa dentro do ZIP, provável vetor de macro |
| Domínios TLS (2º estágio) | `thietbiagt.com`, `finejewels.com.au`, `new.americold.com` | Infraestrutura comprometida usada para download de payloads adicionais |
| CA do certificado | Go Daddy Secure Certificate Authority - G2 | Emissora do certificado SSL de `finejewels.com.au` |
| IP C2 Cobalt Strike #1 | `185.106.96.158` | Domínio `survmeter[.]live` — portas 443, 80, 8888; Host header falso `ocsp.verisign.com` |
| IP C2 Cobalt Strike #2 | `185.125.204.174` | Domínio `securitybusinpuff[.]com` — portas 4444, 8080 |
| Domínio pós-infecção | `maldivehost.net` (208.91.128.6) | Beacon `POST /zLIisQRWZI9/<base64>`, servidor Apache/2.4.49 (cPanel) |
| Serviço abusado | `api.ipify.org` | Consulta de IP externo da vítima em 2021-09-24 17:00:04 UTC |
| Malspam | `farshin@mailfa.com` | Primeiro remetente MAIL FROM observado; 1439 pacotes SMTP no total |

---

## ✅ Resumo das Respostas (Q1–Q20)

| # | Pergunta (resumo) | Resposta |
|---|--------------------|----------|
| Q1 | Data/hora da 1ª conexão HTTP maliciosa | `2021-09-24 16:44:38` |
| Q2 | Nome do arquivo ZIP baixado | `documents.zip` |
| Q3 | Domínio que hospedou o ZIP | `attirenepal.com` |
| Q4 | Arquivo interno do ZIP | `chart-1530076591.xls` |
| Q5 | Webserver do IP malicioso | `LiteSpeed` |
| Q6 | Versão do webserver | `PHP/7.2.34` |
| Q7 | Três domínios de 2º estágio | `thietbiagt.com`, `finejewels.com.au`, `new.americold.com` |
| Q8 | CA do certificado do 1º domínio | `Go Daddy Secure Certificate Authority - G2` |
| Q9 | IPs dos servidores Cobalt Strike | `185.106.96.158`, `185.125.204.174` |
| Q10 | Host header do 1º IP Cobalt Strike | `ocsp.verisign.com` |
| Q11 | Domínio do 1º servidor Cobalt Strike | `survmeter[.]live` |
| Q12 | Domínio do 2º servidor Cobalt Strike | `securitybusinpuff[.]com` |
| Q13 | Domínio do tráfego pós-infecção | `maldivehost.net` |
| Q14 | 11 primeiros caracteres enviados | `zLIisQRWZI9` |
| Q15 | Tamanho do 1º pacote ao C2 | `281 bytes` |
| Q16 | Server header do domínio pós-infecção | `Apache/2.4.49 (cPanel) OpenSSL/1.1.1l mod_bwlimited/1.4` |
| Q17 | Data/hora da consulta DNS de IP check | `2021-09-24 17:00:04 UTC` |
| Q18 | Domínio da consulta DNS | `api.ipify.org` |
| Q19 | 1º endereço MAIL FROM | `farshin@mailfa.com` |
| Q20 | Total de pacotes SMTP | `1439 pacotes` |

---

## 📚 Referências

- [TryHackMe — Carnage](https://tryhackme.com/room/c2carnage)
- Wireshark — Análise de `carnage.pcap` (Follow TCP/HTTP Stream, filtros `http`, `smtp`, `dns`, `tls.handshake.type`, `http.request.method`)
- [VirusTotal — Community (IP Address)](https://www.virustotal.com/gui/ip-address) — consultas para `185.106.96.158` e `185.125.204.174`
- [MITRE ATT&CK T1566.001 — Phishing: Spearphishing Attachment](https://attack.mitre.org/techniques/T1566/001/)
- [MITRE ATT&CK T1071.001 — Application Layer Protocol: Web Protocols](https://attack.mitre.org/techniques/T1071/001/)
- [MITRE ATT&CK T1071.003 — Application Layer Protocol: Mail Protocols](https://attack.mitre.org/techniques/T1071/003/)
- [MITRE ATT&CK T1071.004 — Application Layer Protocol: DNS](https://attack.mitre.org/techniques/T1071/004/)
- [MITRE ATT&CK T1071 — Application Layer Protocol (Cobalt Strike Malleable C2)](https://attack.mitre.org/techniques/T1071/)

---