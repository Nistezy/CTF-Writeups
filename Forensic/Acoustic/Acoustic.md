# 🔍 Acoustic — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense VoIP · SIP Enumeration · RTP Audio Analysis

---

| **Analista**          | Mauricio Robert                                                                                  |
|-----------------------|--------------------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                                |
| **Data do Relatório** | 30/06/2026                                                                                       |
| **Data do Incidente** | 2010 (captura: `Voip-trace.pcap`)                                                                |
| **Classificação**     | CONFIDENCIAL                                                                                     |
| **Ferramentas**       | Wireshark · NetworkMiner 3.1 · PowerShell (`Select-String`) · Wireshark RTP Player               |
| **Arquivo**           | `Voip-trace.pcap` (1.188.934 bytes) + `log.txt` (2.010.252 bytes)                              |

---

## 🔍 Resumo Executivo

A análise forense de tráfego do desafio **Acoustic** (CyberDefenders Blue Team) investigou o arquivo `Voip-trace.pcap` (4.447 pacotes totais), revelando um ataque sistemático de **enumeração e força bruta contra um servidor PBX Asterisk** utilizando o toolkit **SIPVicious**. O atacante (`172.25.105.3`) varreu **2.652 ramais** do servidor alvo (`172.25.105.40`, identificado como `Asterisk PBX 1.6.0.10-FONCORE-r40`), descobriu que o ramal **100 não requer autenticação**, e utilizou o módulo **svcrack.py** especificamente contra os ramais 100, 101, 102, 103 e 111 para crackear senhas. O ataque também expôs credenciais de autenticação HTTP básica (`maint:password`) e a senha do ramal 555 (`1234`). Em paralelo, foi identificada uma ligação VoIP legítima cujo áudio RTP foi reconstruído, revelando a **frase secreta: Mexico**. A investigação respondeu a **quatorze questões técnicas** abrangendo protocolo de transporte, codecs RTP, análise de timestamps e recuperação de áudio.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                         | Finalidade                                                                                                         |
|------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **Wireshark**                      | Análise do PCAP — filtros SIP/RTP, Protocol Hierarchy Statistics, inspeção de pacotes, Follow TCP Stream          |
| **Wireshark RTP Player**           | Reconstrução e reprodução do áudio da chamada VoIP (Telephony → RTP → RTP Streams → Play)                        |
| **NetworkMiner 3.1**               | Extração de credenciais HTTP da captura — aba *Credentials* identificou `maint:password`                           |
| **PowerShell (`Select-String`)**   | Análise do `log.txt` — contagem de ramais escaneados e identificação de números de 11 dígitos discados             |

---

## 📋 Perguntas e Respostas

### Q1 — Qual protocolo de transporte foi utilizado pelo ataque?

> **Resposta: `UDP`**

**Solução:** A janela **Statistics → Protocol Hierarchy** do Wireshark exibiu a distribuição completa de protocolos na captura:

```
User Datagram Protocol    70.9%   3154 pacotes   25232 bytes
  Session Initiation Protocol  0.4%    19 pacotes   11173 bytes
  Real-Time Transport Protocol 70.0%  3113 pacotes  515888 bytes
    RFC 2833 RTP Event          2.8%   125 pacotes
    Real-time Transport Control 0.5%    21 pacotes
Transmission Control Protocol 29.0%  1291 pacotes
  HTTP                          4.1%   184 pacotes
```

Com **70.9% dos pacotes trafegando sobre UDP** — incluindo todo o tráfego SIP (enumeração e força bruta) e RTP (áudio da chamada) — o protocolo de transporte utilizado no ataque é **UDP**.

![Protocolo de Transporte](/Forensic/Acoustic/images/Protocol_Transport_Explored_UDP(1).png)

---

### Q2 — Qual é o nome do conjunto de ferramentas (suite) utilizado pelo atacante?

> **Resposta: `SIPVicious`**

**Solução:** A análise do primeiro pacote SIP da captura (frame 1, `OPTIONS sip:100@172.25.105.40`) revelou no campo **User-Agent** do cabeçalho SIP:

```
User-Agent: UNfriendly-scanner - for demo purposes
```

Combinando esse indicador com o padrão de varredura sistemática e a análise do `log.txt` via PowerShell, confirmou-se o uso do toolkit **SIPVicious** — suite de auditoria/ataque VoIP composta pelos módulos `svmap.py` (descoberta), `svwar.py` (enumeração de ramais), `svcrack.py` (força bruta de senhas) e `svreport.py`. O campo "UNfriendly-scanner" é a assinatura padrão do módulo `svmap.py` da SIPVicious em modo demonstração.

![Ferramentas Usadas no Ataque](/Forensic/Acoustic/images/Name_of_Suite(2).png)

---

### Q3 — Qual é o User-Agent do sistema vítima?

> **Resposta: `Asterisk PBX 1.6.0.10-FONCORE-r40`**

**Solução:** O frame 2 da captura (`Status: 200 OK (OPTIONS)`) — resposta do servidor ao probe inicial do atacante — contém no cabeçalho **User-Agent** da mensagem SIP de resposta:

```
User-Agent: Asterisk PBX 1.6.0.10-FONCORE-r40
Allow: INVITE, ACK, CANCEL, OPTIONS, BYE, REFER, SUBSCRIBE, NOTIFY
Supported: replaces, timer
Contact: <sip:172.25.105.40>
Contact URI: sip:172.25.105.40
```

O campo **`Asterisk PBX 1.6.0.10-FONCORE-r40`** identifica o software e versão exata do servidor VoIP comprometido — Asterisk 1.6.0.10 com o pacote FONCORE r40, distribuição customizada do Asterisk PBX.

![User-Agent Vitima](/Forensic/Acoustic/images/User_Agent_Victim_System(3).png)

---

### Q4 — Qual ferramenta `.py` foi utilizada especificamente contra as extensões 100, 101, 102, 103 e 111?

> **Resposta: `svcrack.py`**

**Solução:** A análise diferencial do tráfego SIP identificou um padrão distinto: enquanto a maioria dos ramais (2.652 no total) foi abordada apenas com mensagens `REGISTER` (enumeração via `svwar.py`), os ramais **100, 101, 102, 103 e 111** receberam adicionalmente tentativas `INVITE` com múltiplas respostas `401 Unauthorized` seguidas de `ACK` com credenciais — padrão característico de força bruta de senha via SIP DIGEST Authentication. Essa técnica é implementada pelo módulo **`svcrack.py`** da SIPVicious, conforme documentado na wiki oficial (github.com/EnableSecurity/sipvicious/wiki/SVCrack-Usage).

![Ferramenta Python](/Forensic/Acoustic/images/Tool.py_Usage_in_Attack(4).png)

---

### Q5 — Qual extensão do honeypot NÃO requer autenticação?

> **Resposta: `100`**

**Solução:** Filtrando os pacotes SIP com o display filter `sip`, a sequência de mensagens do ramal **100** diverge dos demais: enquanto ramais como 555 respondem `401 Unauthorized` antes de aceitar o `REGISTER`, o ramal **100** retorna `200 OK (REGISTER)` diretamente — sem emitir o challenge `401 Unauthorized` com `WWW-Authenticate`. Isso confirma que o ramal **100** está configurado sem senha/autenticação no servidor Asterisk (`type=friend` sem `secret` definido), tornando-o acessível a qualquer cliente SIP sem credenciais.

![Extensão sem Autenticacao](/Forensic/Acoustic/images/Request_if_Dont_Need_Authorization(5).png)

---

### Q6 — Quantas extensões foram escaneadas no total?

> **Resposta: `2652`**

**Solução:** Utilizando PowerShell para analisar o `log.txt` (2.010.252 bytes), o script contou os registros únicos de tentativas REGISTER:

```powershell
Select-String -Path "log.txt" -Pattern "REGISTER sip:.*@honey.pot" |
  ForEach-Object { $_.Matches.Groups[1].Value } |
  Sort-Object -Unique | Measure-Object | Select-Object -ExpandProperty Count
# Resultado: 2652
```

O atacante tentou registrar **2.652 ramais distintos** no servidor PBX — varredura característica do módulo `svwar.py` com range de extensões configurado.

![Todas as Extencoes](/Forensic/Acoustic/images/Many_Request_of_Extensions(6).png)

---

### Q7 — Existe um trace de um cliente SIP real na captura. Qual é o seu User-Agent? (duas palavras separadas por espaço)

> **Resposta: `Zoiper rev.6751`**

**Solução:** O arquivo `log.txt` contém registros de um servidor honeypot externo. Entre as entradas, duas mensagens SIP (`INVITE` e `REGISTER`) originadas de `89.42.194.X` exibem o campo:

```
User-Agent: Zoiper rev.6751
```

O **Zoiper** é um softphone SIP legítimo (cliente VoIP real) — distinto das mensagens automatizadas do SIPVicious. A versão `rev.6751` é uma build antiga do Zoiper, confirmando uma chamada real de um usuário legítimo para o honeypot, em contraste com o tráfego automatizado do atacante.

![Cliente SIP Real](/Forensic/Acoustic/images/Real_SIP_Client(7).png)

---

### Q8 — Múltiplos números de telefone reais foram discados. Qual foi o número de 11 dígitos mais recente discado pela extensão 101?

> **Resposta: `00112524021`**

**Solução:** O PowerShell foi utilizado para filtrar o `log.txt` por mensagens `INVITE` originadas do ramal 101, ordenadas por timestamp:

```powershell
Select-String -Path "log.txt" -Pattern "INVITE" -Context 0,3 |
  Select-String "sip" |
  Where-Object { $_ -match "101" }
```

As entradas retornadas mostraram os INVITEs do ramal 101 com destinos de 11 dígitos:

```
log.txt:89526:INVITE sip:00114382889XXX@honey.pot...
log.txt:89564:INVITE sip:00113232228XXX@honey.pot...
log.txt:89601:INVITE sip:00112524021XXX@honey.pot...
log.txt:89780:INVITE sip:00112524021XXX@honey.pot...
```

O número **`00112524021`** é o mais recente (linha 89780) discado pela extensão 101 — número de telefone internacional com prefixo `001` (EUA) + `12524021`.

![Numero de 11 Digitos](/Forensic/Acoustic/images/11-Digit_Number(8).png)

---

### Q9 — Quais são as credenciais padrão utilizadas na autenticação básica HTTP tentada?

> **Resposta: `maint:password`**

**Solução:** O **NetworkMiner 3.1** (aba *Credentials*) processou o `Voip-trace.pcap` e extraiu as credenciais de autenticação HTTP capturadas na sessão TCP. A entrada destacada em azul mostrou:

```
Client:   172.25.105.43
Server:   172.25.105.40 [Restricted Area]
Protocol: HTTP
Username: maint
Password: password
```

As credenciais **`maint:password`** são as credenciais padrão do painel de administração FreePBX (interface web do Asterisk), indicando que o atacante tentou autenticação HTTP Basic com as credenciais default — que ainda estavam ativas no servidor comprometido.

![Credenciais](/Forensic/Acoustic/images/Default_Credentials(9).png)

---

### Q10 — Qual é a senha da conta 555?

> **Resposta: `1234`**

**Solução:** O Follow TCP Stream (stream 91) da sessão HTTP capturada revelou a resposta da interface FreePBX (`sip_custom.conf`) contendo a configuração completa do ramal 555:

```
[555]
type=friend
username=555
secret=1234
host=dynamic
extension=from-trunk
context=from-trunk
```

O campo **`secret=1234`** é a senha SIP do ramal 555 — exposta em texto claro na resposta HTTP do painel de administração FreePBX, confirmando o comprometimento total da configuração do PBX.

![Senha](/Forensic/Acoustic/images/Password_of_Account_555(12).png)

---

### Q11 — Qual é o tempo de amostragem (sampling time) do codec utilizado?

> **Resposta: `0.125 ms`**

**Solução:** Os pacotes RTP carregam o codec **ITU-T G.711 PCMU** com taxa de amostragem de **8000 Hz**. O tempo de amostragem (período entre amostras) é calculado como o inverso da taxa:

```
Ts = 1 / 8000 Hz = 0.000125 s = 0.125 ms
```

O cálculo foi confirmado pela análise dos timestamps RTP: pacotes consecutivos possuem incremento de **160 unidades de timestamp** (correspondente a 20ms de áudio = 160 amostras × 0.125ms/amostra). A calculadora Windows registrou o valor **160** como total de amostras por pacote RTP, e o Notepad confirmou: `Ts = 1/8000 = 0.000125 → s = 0.125 ms`.

![Tempo de Amostrangem](/Forensic/Acoustic/images/Sampling_Time_Duration(11).png)

---

### Q12 — Qual é o codec (tipo de payload RTP) utilizado na chamada?

> **Resposta: `ITU-T G.711 PCMU`**

**Solução:** A inspeção de qualquer pacote RTP da stream de áudio (ex.: frame 1310) no Wireshark revelou, na camada **Real-Time Transport Protocol**:

```
Payload type: ITU-T G.711 PCMU (0)
```

O **G.711 PCMU** (Pulse Code Modulation, µ-law) é o codec de voz mais comum em VoIP — comprime áudio de 8 bits a 8000 Hz, gerando 64 kbps de banda. O payload type **0** é o identificador padrão definido pelo RFC 3551. A presença deste codec em todos os 3.113 pacotes RTP confirma que toda a chamada foi codificada em G.711 PCMU.

![codec](/Forensic/Acoustic/images/Codec_RTP_Payloa(12).png)

---

### Q13 — Qual é o valor do campo de timestamp no cabeçalho RTP de sincronização?

> **Resposta: `269660`**

**Solução:** Filtrando os pacotes RTP com `rtp` no Wireshark e localizando os pacotes **RTP EVENT** (RFC 2833 — eventos DTMF), a inspeção do frame correspondente revelou o campo de timestamp RTP destacado:

```
Real-Time Transport Protocol
    Version: RFC 1889 Version (2)
    Padding: False
    Extension: False
    Payload type: telephone-event (101)
    Sequence number: 7384
    Extended sequence number: 72840
    Timestamp: 269660          ← campo de sincronização
    Extended timestamp: 4295236976
    Synchronization Source Identifier: 0xa254e017 (2723471383)
```

O valor **`269660`** no campo **Timestamp** do cabeçalho RTP é utilizado para sincronização de streams — indica o instante temporal (em unidades de clock do codec, 8000 Hz) correspondente ao início do frame RTP de evento DTMF.

![Cabecalho de Sinc.](/Forensic/Acoustic/images/Header_of_Sync_RTP(13).png)

---

### Q14 — Qual é a frase secreta obtida a partir da escuta do áudio RTP?

> **Resposta: `Mexico`**

**Solução:** Utilizando **Telephony → RTP → RTP Streams** no Wireshark, foram identificadas as duas streams de áudio da chamada:

```
Source: 172.25.105.3   → Destination: 172.25.105.40  (SSRC: 0xa254e017)
Source: 172.25.105.40  → Destination: 172.25.105.3   (SSRC: 0xa42fe598)
```

O **RTP Player** foi aberto (`Play Streams`), exibindo as formas de onda de ambos os canais. Após reprodução do áudio reconstruído, a conversa revelou a frase dita durante a chamada. O Notepad foi utilizado para registrar o resultado:

```
Secret Phrase -> Mexico
```

A palavra **`Mexico`** é a frase secreta pronunciada na conversa VoIP interceptada — demonstrando que o protocolo RTP sem criptografia permite a reconstrução completa de chamadas apenas a partir de uma captura de tráfego de rede.

![Frase Secreta](/Forensic/Acoustic/images/Secret_Phrase_Mexico(14).png)

---

## ⛓ Fluxo do Ataque VoIP

```
[FASE 1 — DISCOVERY (svmap.py)]
    172.25.105.3 → 172.25.105.40
    OPTIONS sip:100@172.25.105.40
    User-Agent: UNfriendly-scanner (SIPVicious svmap)
    Servidor responde: 200 OK
    Sistema identificado: Asterisk PBX 1.6.0.10-FONCORE-r40
    ↓
[FASE 2 — ENUMERAÇÃO DE RAMAIS (svwar.py)]
    172.25.105.3 → 172.25.105.40
    REGISTER + SUBSCRIBE para 2.652 ramais distintos
    Ramal 100: responde 200 OK sem challenge → sem autenticação!
    Demais ramais: 401 Unauthorized
    ↓
[FASE 3 — FORÇA BRUTA (svcrack.py)]
    Alvo: ramais 100, 101, 102, 103, 111
    INVITE → 401 Unauthorized → ACK com credenciais
    Ramal 555: senha 1234 descoberta (via HTTP panel)
    ↓
[FASE 4 — EXPLORAÇÃO HTTP (FreePBX Admin)]
    172.25.105.43 → 172.25.105.40:80
    HTTP Basic Auth: maint:password (credenciais padrão)
    Acesso ao painel FreePBX → leitura de sip_custom.conf
    Configuração completa exposta: secret=1234 para ramal 555
    ↓
[PARALELO — LIGAÇÃO REAL INTERCEPTADA]
    Chamada SIP legítima via Zoiper rev.6751
    Codec: ITU-T G.711 PCMU (PT=0), 8000 Hz, 0.125ms/amostra
    Áudio RTP reconstruído via Wireshark RTP Player
    Frase secreta capturada: "Mexico"
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato / Resposta |
|----------|--------------------|---------------------|
| Protocolo de transporte | Wireshark → Statistics → Protocol Hierarchy | UDP (70.9% dos pacotes) |
| Nome do suite de ataque | Wireshark → campo SIP User-Agent (frame 1) + log.txt | SIPVicious |
| User-Agent da vítima | Wireshark → SIP 200 OK (frame 2) | Asterisk PBX 1.6.0.10-FONCORE-r40 |
| Ferramenta .py usada | Análise padrão INVITE+401 nos ramais alvo | svcrack.py |
| Extensão sem autenticação | Wireshark → filtro `sip` → ramal 100 → 200 OK direto | 100 |
| Total de extensões escaneadas | PowerShell `Select-String` no log.txt | 2652 |
| User-Agent do cliente SIP real | log.txt → campo User-Agent | Zoiper rev.6751 |
| Número de 11 dígitos mais recente | PowerShell → INVITE do ramal 101 (log.txt linha 89780) | 00112524021 |
| Credenciais HTTP padrão | NetworkMiner 3.1 → aba Credentials | maint:password |
| Senha do ramal 555 | Wireshark → Follow TCP Stream 91 (FreePBX HTTP) | 1234 |
| Tempo de amostragem | Cálculo: 1/8000 Hz = 0.125ms | 0.125 ms |
| Codec RTP | Wireshark → pacote RTP → Payload type | ITU-T G.711 PCMU (0) |
| Timestamp RTP de sincronização | Wireshark → filtro `rtp` → campo Timestamp | 269660 |
| Frase secreta do áudio | Wireshark → Telephony → RTP Player → áudio | Mexico |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| IP atacante | `172.25.105.3` | Origem de toda a varredura SIPVicious |
| IP vítima (PBX) | `172.25.105.40` | Servidor Asterisk PBX 1.6.0.10-FONCORE-r40 |
| Suite de ataque | SIPVicious | Toolkit VoIP para enumerar, descobrir e crackear credenciais SIP |
| Módulo de enumeração | `svwar.py` | Varrreu 2.652 ramais via REGISTER/SUBSCRIBE |
| Módulo de força bruta | `svcrack.py` | Alvo: extensões 100, 101, 102, 103, 111 |
| Ramal desprotegido | `100` | Sem autenticação — `200 OK` sem `WWW-Authenticate` |
| Credencial HTTP | `maint:password` | Padrão FreePBX — acesso total ao painel administrativo |
| Senha ramal 555 | `1234` | Exposta no sip_custom.conf via HTTP |
| Cliente SIP legítimo | `Zoiper rev.6751` | Softphone real — chamada interceptada |
| Número discado (recente) | `00112524021` | 11 dígitos, ramal 101, linha 89780 do log.txt |
| Codec interceptado | ITU-T G.711 PCMU (PT=0) | 8000 Hz, 64 kbps, 0.125ms/amostra |
| Frase secreta | `Mexico` | Extraída do áudio RTP reconstruído |
| Técnica (MITRE ATT&CK) | `T1595.001` | Active Scanning: Scanning IP Blocks (svmap/svwar) |
| Técnica (MITRE ATT&CK) | `T1110.001` | Brute Force: Password Guessing (svcrack) |
| Técnica (MITRE ATT&CK) | `T1040` | Network Sniffing (interceptação de áudio RTP) |
| Técnica (MITRE ATT&CK) | `T1078.001` | Valid Accounts: Default Accounts (maint:password) |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | Protocolo de transporte utilizado | `UDP` |
| Q2 | Nome do conjunto de ferramentas do atacante | `SIPVicious` |
| Q3 | User-Agent do sistema vítima | `Asterisk PBX 1.6.0.10-FONCORE-r40` |
| Q4 | Ferramenta .py usada contra extensões 100–103 e 111 | `svcrack.py` |
| Q5 | Extensão sem autenticação | `100` |
| Q6 | Total de extensões escaneadas | `2652` |
| Q7 | User-Agent do cliente SIP real | `Zoiper rev.6751` |
| Q8 | Número de 11 dígitos mais recente (ramal 101) | `00112524021` |
| Q9 | Credenciais padrão da autenticação HTTP | `maint:password` |
| Q10 | Senha da conta 555 | `1234` |
| Q11 | Tempo de amostragem do codec | `0.125 ms` |
| Q12 | Codec/tipo de payload RTP | `ITU-T G.711 PCMU` |
| Q13 | Valor do timestamp no cabeçalho RTP de sincronização | `269660` |
| Q14 | Frase secreta obtida do áudio RTP | `Mexico` |

---

## 📚 Referências

- [CyberDefenders — Acoustic CTF](https://cyberdefenders.org/blueteam-ctf-challenges/acoustic/)
- [SIPVicious Wiki — EnableSecurity](https://github.com/EnableSecurity/sipvicious/wiki)
- [SVCrack Usage](https://github.com/EnableSecurity/sipvicious/wiki/SVCrack-Usage)
- [Wireshark VoIP Analysis](https://wiki.wireshark.org/VoIP_calls)
- [RFC 3261 — SIP: Session Initiation Protocol](https://www.rfc-editor.org/rfc/rfc3261)
- [RFC 3551 — RTP Profile for Audio/Video Conferences](https://www.rfc-editor.org/rfc/rfc3551)
- [ITU-T G.711 — PCMU/PCMA Codec](https://www.itu.int/rec/T-REC-G.711/)
- [MITRE ATT&CK T1110.001 — Brute Force: Password Guessing](https://attack.mitre.org/techniques/T1110/001/)
- [MITRE ATT&CK T1040 — Network Sniffing](https://attack.mitre.org/techniques/T1040/)

---