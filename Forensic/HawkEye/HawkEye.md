# 🦅 HawkEye Keylogger — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense de Rede

---

| **Analista**        | Mauricio Robert                                      |
|---------------------|------------------------------------------------------|
| **Organização**     | Faculdade Impacta                                    |
| **Data do Relatório** | 01/06/2026                                         |
| **Data do Incidente** | 04/10/2019                                         |
| **Classificação**   | CONFIDENCIAL                                         |
| **Ferramentas**     | Wireshark · NetworkMiner · VirusTotal · AbuseIPDB · CyberChef |
| **Arquivo**         | `stealer.pcap`                                       |

---

## 🔍 Resumo Executivo

Um funcionário do departamento financeiro foi vítima de uma campanha de phishing que resultou no download e execução do keylogger **HawkEye v8.0** no sistema Windows (`BEIJING-5CD1-PC`). O malware foi baixado a partir do servidor `217.182.138.150` (França — OVH SAS), registrou credenciais bancárias e de e-mail, e exfiltrou os dados roubados via **SMTP a cada 10 minutos** para o endereço `sales.del@macwinlogistics.in`. O servidor de e-mail de destino está localizado nos **Estados Unidos** (GoDaddy, Arizona).

---

## 🛠 Ferramentas Utilizadas

| Ferramenta       | Finalidade                                                                 |
|------------------|----------------------------------------------------------------------------|
| **Wireshark**    | Análise principal do PCAP — estatísticas, filtros, seguimento de streams   |
| **NetworkMiner** | Extração de arquivos, credenciais capturadas e metadados de hosts          |
| **VirusTotal**   | Identificação do malware, hash MD5, família e variante                     |
| **AbuseIPDB**    | Verificação de reputação dos IPs maliciosos identificados na captura        |
| **CyberChef**    | Decodificação de Base64 e análise de payloads dos e-mails SMTP             |

---

## 📋 Perguntas e Respostas

### Q1 — Quantos pacotes possui a captura?

> **Resposta: `4003`**

**Solução:** Abrindo o arquivo `stealer.pcap` no Wireshark, acessou-se *Statistics → Capture File Properties*. O campo **"Pacotes"** exibe o total de **4.003 pacotes**. Esse número é confirmado também na barra de status inferior da interface.

```
Statistics → Capture File Properties → Pacotes: 4003
```

---

### Q2 — A que horas foi capturado o primeiro pacote (UTC)?

> **Resposta: `2019-04-10 17:37:07`**

**Solução:** Em *Statistics → Capture File Properties*, o campo **"Primeiro pacote"** exibe o timestamp:

```
Arrival Time: Apr 10, 2019 17:37:07.129730000 UTC
```

A captura foi iniciada às 17h37 UTC do dia 10 de abril de 2019, coincidindo com o momento em que a vítima abriu o e-mail de phishing e disparou a infecção.

---

### Q3 — Qual é a duração da captura?

> **Resposta: `01:03:41`**

**Solução:** O campo **"Decorrido"** nas propriedades do arquivo de captura indica:

```
Elapsed: 01:03:41
```

Esse período engloba todo o ciclo de infecção: download do malware, execução, coleta de credenciais e múltiplas rodadas de exfiltração via SMTP.

---

### Q4 — Qual é o computador mais ativo no nível de enlace?

> **Resposta: `00:08:02:1c:47:ae`**

**Solução:** Em *Statistics → Endpoints → Ethernet*, o endereço MAC **`00:08:02:1c:47:ae`** aparece com o maior volume de tráfego: **3.523 pacotes** (39,37% de TX + 47,02% RX). Este endereço pertence ao sistema `BEIJING-5CD1-PC`, a máquina vítima comprometida.

---

### Q5 — Fabricante da NIC do sistema mais ativo no nível de enlace?

> **Resposta: `Hewlett-Packard`**

**Solução:** A pesquisa do prefixo OUI `00:08:02` no banco de dados IEEE revela que este bloco pertence à **Hewlett-Packard Company**. O NetworkMiner identifica automaticamente o fabricante ao analisar o MAC `00:08:02:1c:47:ae`.

---

### Q6 — Onde fica a sede da empresa fabricante da NIC?

> **Resposta: `Palo Alto`**

**Solução:** A Hewlett-Packard Company foi fundada em 1939 e tem sede histórica em **Palo Alto, Califórnia, EUA**. Confirmado via pesquisa web sobre "Hewlett-Packard location".

---

### Q7 — Quantos computadores da organização estão envolvidos na captura?

> **Resposta: `3`**

**Solução:** Em *Statistics → Endpoints → IPv4*, são identificados os hosts com endereços IP privados pertencentes à rede da organização:

- `10.4.10.132` — BEIJING-5CD1-PC (máquina vítima — 2.010 pacotes)
- `10.4.10.4` — Servidor/DC interno (Dell — 1.776 pacotes)
- `10.4.10.2` — Outro host interno

Os demais IPs visíveis na aba Ethernet (como `Netgear_b6:93:f1`, `Broadcast`, `IPv4mcast_*`) são endereços de broadcast/multicast e não representam computadores individuais da organização. Total: **3 computadores**.

---

### Q8 — Qual é o nome do computador mais ativo no nível de rede?

> **Resposta: `BEIJING-5CD1-PC`**

**Solução:** O tráfego **NBNS (NetBIOS Name Service)** e DNS revelam o hostname do host `10.4.10.132` como **`BEIJING-5CD1-PC`**. Com 2.010 pacotes (50,2%), é o host mais ativo da captura. Confirmado também na aba "Hosts" do NetworkMiner.

Filtro Wireshark utilizado:
```
ip.dst_host == "10.4.10.132"
```

---

### Q9 — Qual é o IP do servidor DNS da organização?

> **Resposta: `10.4.10.4`**

**Solução:** Filtrando tráfego DNS no Wireshark (`dns`), todas as queries do host `10.4.10.132` são enviadas para o IP **`10.4.10.4`**, que também aparece como servidor DNS nas respostas. O filtro por MAC da vítima (`eth.addr==00:08:02:1c:47:ae && dns`) confirma este comportamento.

---

### Q10 — Qual domínio a vítima consulta no pacote 204?

> **Resposta: `proforma-invoices.com`**

**Solução:** Navegando diretamente ao pacote 204 no Wireshark (filtro: `dns.qry.name == "proforma-invoices.com"`), observa-se uma **Standard DNS Query do tipo A** para o domínio **`proforma-invoices.com`**. O nome usa engenharia social — "proforma invoice" é documento comercial comum, usado para enganar funcionários financeiros.

---

### Q11 — Qual é o IP do domínio da questão anterior?

> **Resposta: `217.182.138.150`**

**Solução:** A resposta DNS para o domínio `proforma-invoices.com` retorna o endereço IPv4:

```
proforma-invoices.com: type A, class IN, addr 217.182.138.150
```

Requisições HTTP subsequentes para download do keylogger são direcionadas para este IP.

---

### Q12 — A qual país pertence o IP da questão anterior?

> **Resposta: `France`**

**Solução:** A consulta de geolocalização do IP `217.182.138.150` no site WhatIsMyIPAddress revela:

```
ISP:     OVH SAS
Country: France
Region:  Hauts-de-France
City:    Roubaix
```

O IP pertence à **OVH SAS**, um dos maiores provedores de hosting europeus, com datacenter em Roubaix, **França**. A OVH é frequentemente utilizada por atores maliciosos por oferecer hospedagem de baixo custo na Europa.

---

### Q13 — Qual sistema operacional o computador da vítima executa?

> **Resposta: `Windows NT 6.1`**

**Solução:** O campo **User-Agent** presente nas requisições HTTP da vítima revela a string:

```
Windows NT 6.1
```

Confirmado pelo NetworkMiner na aba "Parameters", que exibe o OS fingerprint da máquina. `Windows NT 6.1` corresponde ao **Windows 7**.

---

### Q14 — Qual é o nome do arquivo malicioso baixado?

> **Resposta: `tkraw_Protected99.exe`**

**Solução:** Aplicando o filtro no Wireshark:

```
http.request.uri contains "tkraw_Protected99.exe"
```

Identifica-se a requisição GET:
```
GET /proforma/tkraw_Protected99.exe HTTP/1.1
```

O arquivo foi baixado do servidor `217.182.138.150` (proforma-invoices.com) via HTTP na porta 80. O nome `tkraw` é característico do HawkEye Keylogger. O arquivo `.exe` é disfarçado para parecer documento legítimo.

---

### Q15 — Qual é o hash MD5 do arquivo baixado?

> **Resposta: `71826BA081E303866CE2A2534491A2F7`**

**Solução:** O arquivo `tkraw_Protected99.exe` foi extraído da captura pelo **NetworkMiner** (aba "Files"). O hash MD5 é exibido nas propriedades do arquivo:

```
MD5: 71826BA081E303866CE2A2534491A2F7
```

A verificação no **VirusTotal** confirma a detecção como **HawkEye Keylogger**. O arquivo é um PE32 executável de aproximadamente **2 MB**.

---

### Q16 — Qual software executa o servidor web que hospeda o malware?

> **Resposta: `LiteSpeed`**

**Solução:** A resposta HTTP do servidor `217.182.138.150` inclui o header:

```
Server: LiteSpeed
```

O **LiteSpeed Web Server** é um servidor de alto desempenho frequentemente utilizado em hospedagens compartilhadas, onde atacantes alugam espaço para distribuir malware.

---

### Q17 — Qual é o IP público do computador da vítima?

> **Resposta: `173.66.146.112`**

**Solução:** O endereço IP público da vítima é revelado no conteúdo dos e-mails SMTP exfiltrados pelo HawkEye. No NetworkMiner (aba "Parameters" → host `10.4.10.132`), o campo:

```
Public IP address 1 : 173.66.146.112
```

O keylogger captura e reporta o IP externo da máquina vítima nos logs enviados ao atacante.

---

### Q18 — Em qual país está o servidor de e-mail para o qual os dados são enviados?

> **Resposta: `United States`**

**Solução:** O tráfego SMTP de exfiltração conecta ao servidor `23.229.162.69`. A geolocalização deste IP no WhatIsMyIPAddress confirma:

```
ISP:          GoDaddy.com LLC
Country:      United States
State/Region: Arizona
City:         Tempe
```

O servidor SMTP do atacante está hospedado na infraestrutura da **GoDaddy**, em **Tempe, Arizona — EUA**. O domínio `secureserver.net` é infraestrutura da GoDaddy, frequentemente usada para hospedar servidores de e-mail de baixo custo.

---

### Q19 — Qual software executa o servidor de e-mail para o qual os dados são enviados?

> **Resposta: `Exim 4.91`**

**Solução:** O banner SMTP exibido durante o handshake da primeira conexão de exfiltração revela:

```
220 p3plcpnl0413.prod.phx3.secureserver.net ESMTP Exim 4.91 #1 Wed, 10 Apr 2019 13:38:15 -0700
```

**Exim 4.91** é um agente de transferência de e-mail (MTA) open-source amplamente utilizado em servidores Linux. Esta versão possui vulnerabilidades conhecidas (CVE-2019-10149), indicando servidor desatualizado.

---

### Q20 — Para qual conta de e-mail as informações são enviadas?

> **Resposta: `sales.del@macwinlogistics.in`**

**Solução:** O tráfego SMTP da captura revela o destinatário dos dados exfiltrados no campo `RCPT TO`:

```
RCPT TO:<sales.del@macwinlogistics.in>
```

Este é o e-mail do operador do ataque, configurado no HawkEye como destino para os logs de keylogging e credenciais roubadas.

---

### Q21 — Qual é a senha usada pelo malware para enviar o e-mail?

> **Resposta: `Sales@23`**

**Solução:** Durante a autenticação SMTP, o malware realiza login com credenciais codificadas em **Base64**. O campo `AUTH login User` exibe o valor codificado. Decodificando no **CyberChef** (operação "From Base64"):

```
Encoded: c2FsZXMuZGVsQG1hY3dpbmxvZ2lzdGljcy5pbg==
Decoded: Sales@23
```

Estas credenciais hardcoded são características do HawkEye — o malware traz embutidas as informações do servidor SMTP do operador.

---

### Q22 — Qual variante do malware exfiltrou os dados?

> **Resposta: `HawkEye Keylogger — Reborn v9`**

**Solução:** O subject dos e-mails SMTP exfiltrados e o conteúdo decodificado via CyberChef (Base64 → texto) revelam:

```
HawkEye Keylogger - Reborn v9
Passwords Logs
roman.mcguire \ BEIJING-5CD1-PC
```

A análise do hash no VirusTotal confirma a família **HawkEye Keylogger**, variante **Reborn v9**.

---

### Q23 — Quais são as credenciais de acesso ao Bank of America?

> **Resposta: `roman.mcguire : P@ssw0rd$`**

**Solução:** O corpo dos e-mails SMTP exfiltrados contém os logs em Base64. Decodificando no CyberChef, identifica-se:

```
URL          : https://www.bankofamerica.com/
Web Browser  : Chrome
User Name    : roman.mcguire
Password     : P@ssw0rd$
```

Essas credenciais foram capturadas pelo keylogger enquanto o usuário acessava sua conta bancária no Chrome.

---

### Q24 — De quantos em quantos minutos os dados coletados são exfiltrados?

> **Resposta: `10`**

**Solução:** Analisando os timestamps das sessões SMTP na captura com o filtro `ip.addr == 23.229.162.69 && smtp`, os pacotes de exfiltração ocorrem em **intervalos regulares de 10 minutos**. A diferença entre os pacotes `250 OK` (confirmação de envio) consecutivos comprova o padrão:

```
13:38 UTC → 250 OK (1ª exfiltração)
13:48 UTC → 250 OK (2ª exfiltração)  ← Δt = 10 min
13:58 UTC → 250 OK (3ª exfiltração)  ← Δt = 10 min
14:08 UTC → 250 OK (4ª exfiltração)  ← Δt = 10 min
14:18 UTC → 250 OK (5ª exfiltração)  ← Δt = 10 min
14:28 UTC → 250 OK (6ª exfiltração)  ← Δt = 10 min
14:38 UTC → 250 OK (7ª exfiltração)  ← Δt = 10 min
```

O HawkEye possui um temporizador configurável (padrão: 10 min) que dispara o envio de e-mail com os logs acumulados. Na captura de ~63 minutos foram observados **~7 ciclos** de exfiltração completos.

---

## ⛓ Cadeia de Infecção (Kill Chain)

```
[1] PHISHING
    E-mail fraudulento com link/anexo para proforma-invoices.com
    ↓
[2] DOWNLOAD
    Vítima acessa o link → baixa tkraw_Protected99.exe via HTTP (porta 80)
    Servidor: 217.182.138.150 | LiteSpeed | França (OVH SAS)
    ↓
[3] EXECUÇÃO
    Arquivo .exe disfarçado é executado em BEIJING-5CD1-PC
    OS: Windows NT 6.1 (Windows 7)
    ↓
[4] KEYLOGGING / COLETA
    HawkEye captura teclas, credenciais de browsers, FTP, e-mail clients
    Credenciais Bank of America: roman.mcguire:P@ssw0rd$
    ↓
[5] EXFILTRAÇÃO
    Dados enviados via SMTP a cada 10 min para sales.del@macwinlogistics.in
    MTA: Exim 4.91 | Servidor: UAE
    ↓
[6] PERSISTÊNCIA
    HawkEye adiciona entrada no registro (Run key) para sobreviver reinicialização
```

---

## 🗺 Mapeamento MITRE ATT&CK

| ID | Técnica | Tática |
|----|---------|--------|
| T1566.002 | Phishing: Spearphishing Link | Initial Access |
| T1204.002 | User Execution: Malicious File | Execution |
| T1056.001 | Input Capture: Keylogging | Collection |
| T1555.003 | Credentials from Web Browsers | Credential Access |
| T1041 | Exfiltration Over C2 Channel (SMTP) | Exfiltration |
| T1547.001 | Registry Run Keys / Startup Folder | Persistence |
| T1036.005 | Masquerading: Match Legitimate Name | Defense Evasion |
| T1071.003 | Application Layer Protocol: Mail | Command & Control |

---

## 🚨 Indicadores de Comprometimento (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Host Vítima | `BEIJING-5CD1-PC` (`10.4.10.132`) | MAC: `00:08:02:1c:47:ae` — NIC Hewlett-Packard |
| IP C2 Malware | `217.182.138.150` | Servidor LiteSpeed — França (OVH SAS) — hospeda `tkraw_Protected99.exe` |
| Domínio C2 | `proforma-invoices.com` | Domínio malicioso de distribuição do HawkEye |
| Arquivo Malicioso | `tkraw_Protected99.exe` | HawkEye Reborn v9 — ~2 MB |
| MD5 | `71826BA081E303866CE2A2534491A2F7` | Hash do executável confirmado no VirusTotal |
| IP Público Vítima | `173.66.146.112` | IP externo do sistema comprometido |
| E-mail Exfiltração | `sales.del@macwinlogistics.in` | Conta SMTP de destino dos dados roubados |
| Senha SMTP Malware | `Sales@23` | Credencial SMTP hardcoded no malware |
| Servidor SMTP | `p3plcpnl0413.prod.phx3.secureserver.net` | Exim 4.91 — UAE |
| Credencial Bancária | `roman.mcguire : P@ssw0rd$` | Bank of America — capturada pelo keylogger |
| Intervalo C2 | 10 minutos | Frequência de exfiltração SMTP |
| Servidor DNS Org | `10.4.10.4` | Servidor DNS interno da organização |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|-----------------|
| Q1 | Nº de pacotes | `4003` |
| Q2 | Timestamp do 1º pacote | `2019-04-10 17:37:07` |
| Q3 | Duração da captura | `01:03:41` |
| Q4 | MAC mais ativo (enlace) | `00:08:02:1c:47:ae` |
| Q5 | Fabricante NIC | `Hewlett-Packard` |
| Q6 | Sede do fabricante | `Palo Alto` |
| Q7 | Computadores na captura | `3` |
| Q8 | Nome do PC mais ativo | `BEIJING-5CD1-PC` |
| Q9 | IP servidor DNS | `10.4.10.4` |
| Q10 | Domínio — pacote 204 | `proforma-invoices.com` |
| Q11 | IP do domínio malicioso | `217.182.138.150` |
| Q12 | País do IP malicioso | `France` |
| Q13 | OS da vítima | `Windows NT 6.1` |
| Q14 | Nome do arquivo malicioso | `tkraw_Protected99.exe` |
| Q15 | MD5 do malware | `71826BA081E303866CE2A2534491A2F7` |
| Q16 | Servidor web do C2 | `LiteSpeed` |
| Q17 | IP público da vítima | `173.66.146.112` |
| Q18 | País servidor de e-mail | `United States` |
| Q19 | Software servidor SMTP | `Exim 4.91` |
| Q20 | E-mail de exfiltração | `sales.del@macwinlogistics.in` |
| Q21 | Senha SMTP do malware | `Sales@23` |
| Q22 | Variante do malware | `HawkEye Keylogger — Reborn v9` |
| Q23 | Credenciais Bank of America | `roman.mcguire : P@ssw0rd$` |
| Q24 | Intervalo de exfiltração | `10 minutos` |

---

## 📚 Referências

- [MITRE ATT&CK — T1566.002 Spearphishing Link](https://attack.mitre.org/techniques/T1566/002/)
- [MITRE ATT&CK — T1056.001 Keylogging](https://attack.mitre.org/techniques/T1056/001/)
- [CyberDefenders — HawkEye CTF](https://cyberdefenders.org/)
- [VirusTotal](https://www.virustotal.com/)
- [AbuseIPDB](https://www.abuseipdb.com/)
- [CyberChef](https://gchq.github.io/CyberChef/)

---

*Writeup elaborado por Mauricio Robert — Faculdade Impacta | Junho 2026*
