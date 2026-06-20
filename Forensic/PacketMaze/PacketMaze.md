# 🔍 PacketMaze — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense de Rede & Análise de Tráfego (Wireshark/NetworkMiner)

---

| **Analista**          | Mauricio Robert                                                          |
|-----------------------|--------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                        |
| **Data do Relatório** | 19/06/2026                                                               |
| **Data do Incidente** | 29/04/2021 a 30/04/2021                                                  |
| **Classificação**     | CONFIDENCIAL                                                             |
| **Ferramentas**       | Wireshark · NetworkMiner · ExifTool · WhatsMyDNS (MAC Lookup)           |
| **Arquivo**           | `UNODC-GPC-001-003-JohnDoe-NetworkCapture-2021-04-29.pcapng`            |

---

## 🔍 Resumo Executivo

A análise forense de tráfego de rede da captura **`UNODC-GPC-001-003-JohnDoe-NetworkCapture-2021-04-29.pcapng`** — referente ao desafio **PacketMaze** do CyberDefenders — examinou mais de **45.000 pacotes** envolvendo o host **192.168.1.26** (MAC `c8:09:a8:57:47:93`). A captura abrange tráfego **FTP em texto claro** (incluindo a credencial **`AfricaCTF2021`** e a transferência de uma fotografia via `STOR`), resolução **DNS sobre IPv6**, handshakes **TLS 1.2** e **TLS 1.3**, navegação **HTTP/HTTPS** com redirecionamento via Cloudflare, tráfego **QUIC** e comunicações **UDP** com um host externo. A investigação respondeu a **onze questões técnicas**, reconstruindo desde a credencial de acesso ao FTP local (`192.168.1.20`) até metadados EXIF de um smartphone LG, a chave pública efêmera ECDHE de uma sessão TLS 1.2 e o *client random* de uma conexão TLS 1.3 com `protonmail.com`.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                          | Finalidade                                                                                                      |
|--------------------------------------|------------------------------------------------------------------------------------------------------------|
| **Wireshark**                        | Análise da captura PCAP — filtros de exibição, *Follow TCP Stream*, Statistics → *Conversations* e *Endpoints*  |
| **NetworkMiner**                     | Extração de arquivos transferidos via FTP (imagem JPEG) diretamente da captura de pacotes                      |
| **ExifTool**                         | Extração de metadados EXIF da imagem extraída (fabricante e modelo da câmera/dispositivo)                      |
| **WhatsMyDNS — MAC Address Lookup**  | Identificação do fabricante e país de registro do endereço MAC (OUI) do servidor FTP                            |

---

## 📋 Perguntas e Respostas

### Q1 — Qual é a senha de FTP?

> **Resposta: `AfricaCTF2021`**

**Solução:** Com o filtro `ftp` aplicado no Wireshark, o pacote **500** (`PASS AfricaCTF2021\r\n`) exibe `Request command: PASS` com `Request arg: AfricaCTF2021`, enviado do host `192.168.1.26` (porta 48794) ao servidor FTP `192.168.1.20` (porta 21). A resposta subsequente:

```
220 Welcome to Hacker FTP service.
331 Please specify the password.
PASS AfricaCTF2021
230 Login successful.
```

confirma a autenticação bem-sucedida com essa credencial, transmitida em **texto claro** — sem qualquer camada de criptografia (FTP puro, sem AUTH TLS/SSL, ambos recusados anteriormente com `530 Please login with USER and PASS`).

![Pass FTP](/Forensic/PacketMaze/images/PASS_FTP(1).png)

---

### Q2 — Qual é o endereço IPv6 do servidor DNS usado por 192.168.1.26?

> **Resposta: `fe80::c80b:adff:feaa:1db7`**

**Solução:** A janela **Statistics → Endpoints → IPv6** (com *Limit to display filter* habilitado) revela apenas dois endereços IPv6 *link-local* trafegando na captura:

```
fe80::b011:ed39:8665:3b0a  → host 192.168.1.26  (MAC c8:09:a8:57:47:93)
fe80::c80b:adff:feaa:1db7  → gateway local      (MAC ca:0b:ad:ad:20:ba)
```

A inspeção de pacotes DNS (ex.: pacote 15174, porta UDP de destino 53) confirma `fe80::c80b:adff:feaa:1db7` como destino das consultas, identificando-o como o **servidor DNS** utilizado pelo host investigado.

![IPv6](/Forensic/PacketMaze/images/IPv6_DNS_192.168.1.26(2).png)

---

### Q3 — Qual domínio o usuário está consultando no pacote 15174?

> **Resposta: `www.7-zip.org`**

**Solução:** O pacote **15174** corresponde a uma consulta DNS padrão (`Transaction ID: 0x1ad5`), enviada via UDP sobre IPv6 de `fe80::b011:ed39:8665:3b0a` (192.168.1.26) para `fe80::c80b:adff:feaa:1db7`, porta de destino 53. O campo **Queries** do pacote detalha:

```
Queries
    www.7-zip.org: type A, class IN
```

confirmando que o domínio consultado é **`www.7-zip.org`**.

![Domain](/Forensic/PacketMaze/images/Domain_Packet_15174(3).png)

---

### Q4 — Quantos pacotes UDP foram enviados de 192.168.1.26 para 24.39.217.246?

> **Resposta: `10`**

**Solução:** Com o filtro `ip.src == 192.168.1.26 && ip.dst == 24.39.217.246` aplicado e a aba **UDP** da janela **Statistics → Conversations** aberta (*Limit to display filter* habilitado), são exibidas duas conversas:

```
Porta de origem 51601 → 1 pacote  (94 bytes)
Porta de origem 53638 → 9 pacotes (846 bytes)
```

Totalizando **1 + 9 = 10 pacotes UDP** enviados de `192.168.1.26` para `24.39.217.246`.

![UDP](/Forensic/PacketMaze/images/Packets_UDP_1.26_to_217.246(4).png)

---

### Q5 — Qual é o endereço MAC do sistema sob investigação no arquivo PCAP?

> **Resposta: `c8:09:a8:57:47:93`**

**Solução:** No primeiro pacote da captura (frame 1, sem filtro aplicado), a camada **Ethernet II** identifica:

```
Source: Intel_57:47:93 (c8:09:a8:57:47:93)
Destination: ca:0b:ad:ad:20:ba (ca:0b:ad:ad:20:ba)
```

como o endereço MAC de origem do tráfego gerado pelo host `192.168.1.26` (IP de origem `192.168.1.26`, destino `13.107.21.200`), confirmando **`c8:09:a8:57:47:93`** como o endereço MAC do sistema sob investigação.

![MAC](/Forensic/PacketMaze/images/MAC_of_System_by_Investigation(5).png)

---

### Q6 — Qual foi o modelo de câmera usado para tirar a foto 20210429_152157.jpg?

> **Resposta: `LM-Q725K`**

**Solução:** O arquivo `20210429_152157.jpg` foi extraído da captura por meio do **NetworkMiner** (aba *Files*), tendo sido transferido via FTP a partir do host `192.168.1.20`. A análise dos metadados EXIF do arquivo extraído, realizada com o **ExifTool**, retornou os campos:

```
Make:  LG Electronics
Model: LM-Q725K
ExifImageWidth: 4160
FocalLength: 3.7 mm
ISO: 50
```

identificando o modelo do dispositivo utilizado para capturar a fotografia como **LM-Q725K** (LG Q7).

![Modelo Camera](/Forensic/PacketMaze/images/Camera_Model_of_Picture_2157(6).png)

---

### Q7 — Qual é a chave pública efêmera fornecida pelo servidor durante o handshake TLS na sessão com session ID `da4a0000342e4b73459d7360b4bea971cc303ac18d29b99067e46d16cc07f4ff`?

> **Resposta: `04edcc123af7b13e90ce101a31c2f996f471a7c8f48a1b81d765085f548059a550f3f4f62ca1f0e8f74d727053074a37bceb2cbdc7ce2a8994dcd76dd6834eefc5438c3b6da929321f3a1366bd14c877cc83e5d0731b7f80a6b80916efd4a23a4d`**

**Solução:** O filtro `tls.handshake.session_id == da4a0000342e4b73459d7360b4bea971cc303ac18d29b99067e46d16cc07f4ff` isola o pacote **26913** (`52.162.219.173 → 192.168.1.26`), contendo as mensagens `Server Hello`, `Certificate`, `Certificate Status`, `Server Key Exchange` e `Server Hello Done`. No bloco **EC Diffie-Hellman Server Params**:

```
Curve Type: named_curve (0x03)
Named Curve: secp384r1 (0x0018)
Pubkey Length: 97
Pubkey: 04edcc123af7b13e90ce101a31c2f996f471a7c8f48a1b81d765085f548059a550f3f4f...
Signature Algorithm: rsa_pkcs1_sha256 (0x0401)
```

expõe a chave pública **ECDHE efêmera de 97 bytes** (formato não comprimido, prefixo `0x04`) utilizada para o estabelecimento da chave de sessão TLS 1.2.

![Public Key](/Forensic/PacketMaze/images/PublicKey_TLSv1.2(7).png)

---

### Q8 — Qual foi o primeiro client random TLS 1.3 usado para estabelecer uma conexão com protonmail.com?

> **Resposta: `24e92513b97a0348f733d16996929a79be21b0b1400cd7e2862a732ce7775b70`**

**Solução:** O filtro `tls.handshake.extensions_server_name == "protonmail.com"` retorna seis `Client Hello` TLSv1.3, todos do host `192.168.1.26` para `185.70.41.35`, com `SNI=protonmail.com`. O primeiro pacote da lista, **frame 17992** (tempo relativo `218.650666933`), contém no Client Hello:

```
Version: TLS 1.2 (0x0303)
Random: 24e92513b97a0348f733d16996929a79be21b0b1400cd7e2862a732ce7775b70
Session ID: b8837ec96878f68edd37f11c4fcac5772e0438040d5dcd3c821cb70ef6c76f58
Extension: server_name (len=19) name=protonmail.com
```

correspondendo ao **primeiro client random de 32 bytes** gerado para a conexão com `protonmail.com`.

![ProtonMail](/Forensic/PacketMaze/images/Random_First_Client_"protonmail.com"(8).png)

---

### Q9 — Qual país tem registrado o fabricante do endereço MAC do servidor FTP?

> **Resposta: `United States`**

**Solução:** O servidor FTP (`192.168.1.20`) responde às requisições com o endereço MAC de origem `08:00:27:a6:1f:86` (`PCSSystemtec_a6:1f:86`), visível, por exemplo, no pacote **486** (`220 Welcome to Hacker FTP service.`). A consulta do prefixo OUI `08:00:27` na ferramenta **WhatsMyDNS — Pesquisa de Endereço MAC** retornou:

```
Prefixo de endereço: 08:00:27
Fornecedor:          PCS Systemtechnik GmbH
Código do país:      US
Endereço:            600 Suffolk St, Lowell, MA, 01854, US
```

confirmando o registro do fabricante nos **Estados Unidos (United States)**.

![Country](/Forensic/PacketMaze/images/Country_Manufactory_of_MAC(9).png)

---

### Q10 — Que horário uma pasta não padrão foi criada no servidor FTP no dia 20 de abril?

> **Resposta: `17:53`**

**Solução:** Seguindo o **Follow TCP Stream** (stream 11) referente ao comando `LIST` do FTP (modo passivo, frame de setup 522), a listagem de diretório exibe as pastas padrão do usuário — `Desktop`, `Documents`, `Downloads`, `Music`, `Pictures`, `Public`, `Templates` e `Videos` —, todas pertencentes ao UID/GID `1000:1000` e datadas de 23 de fevereiro ou 29 de abril. Uma entrada destoante:

```
dr-xr-x---  4 65534  65534  4096 Apr 20 17:53 ftp
```

pertence ao UID/GID `65534:65534` (*nobody/nogroup*) e foi criada em **20 de abril às 17:53**, caracterizando uma **pasta não padrão** no servidor FTP.

![Time](/Forensic/PacketMaze/images/Data_and_Hour_Created_ftp%2020-04(10).png)

---

### Q11 — Qual URL foi visitada pelo usuário e conectada ao endereço IP 104.21.89.171?

> **Resposta: `http://dfir.science/`**

**Solução:** Com o filtro `http` aplicado, o pacote **26257** contém a requisição `GET / HTTP/1.1` do host `192.168.1.26` para o destino `104.21.89.171`, com o campo `[Full request URI: http://dfir.science/]` explicitando a URL completa acessada. A resposta correspondente, pacote **26264** (`HTTP/1.1 301 Moved Permanently`), confirma o destino:

```
HTTP/1.1 301 Moved Permanently
Location: https://dfir.science/
Server: cloudflare
```

validando **`dfir.science`** como o domínio acessado através do IP `104.21.89.171`.

![URL](/Forensic/PacketMaze/images/URL_Visited_by_104(11).png)

---

## ⛓ Linha do Tempo de Eventos (29/04/2021 — horário PDT)

```
[18:00:51.03] INÍCIO DA CAPTURA
    Frame 1 — host 192.168.1.26 (MAC c8:09:a8:57:47:93) inicia tráfego TCP
    ↓
[18:01:26.88] SESSÃO FTP — AUTENTICAÇÃO
    PASS AfricaCTF2021 → 230 Login successful
    LIST do diretório raiz revela pasta não padrão "ftp" (uid 65534, criada 20/04 17:53)
    ↓
[18:01:51.07] NOVA SESSÃO FTP — UPLOAD DE ARQUIVO
    220 Welcome to Hacker FTP service (nova conexão)
    STOR 20210429_152157.jpg — transferência em modo passivo (PASV)
    ↓
[18:02:57.35] CONSULTA DNS SOBRE IPv6
    192.168.1.26 → fe80::c80b:adff:feaa:1db7 (porta 53)
    Query: www.7-zip.org (type A)
    ↓
[18:02:59 – 18:03:18] TRÁFEGO UDP EXTERNO
    192.168.1.26 → 24.39.217.246 — 10 pacotes UDP (portas 51601 e 53638)
    ↓
[18:04:29.68] HANDSHAKE TLS 1.3 — PROTONMAIL
    Client Hello (SNI=protonmail.com) → 185.70.41.35
    Random: 24e92513...775b70
    ↓
[18:06:39.58] NAVEGAÇÃO HTTP — REDIRECIONAMENTO
    GET / HTTP/1.1 → 104.21.89.171 (http://dfir.science/)
    301 Moved Permanently → https://dfir.science/ (Cloudflare)
    ↓
[18:07:22.38] HANDSHAKE TLS 1.2
    Server Hello + Certificate + Server Key Exchange (52.162.219.173)
    ECDHE secp384r1 — Pubkey 97 bytes (04edcc123af7...)
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|--------------------|----------|
| Senha FTP | Wireshark → filtro `ftp` (pacote 500) | `PASS AfricaCTF2021` |
| Servidor DNS IPv6 | Wireshark → Statistics → Endpoints → IPv6 | `fe80::c80b:adff:feaa:1db7` |
| Domínio consultado | Wireshark → pacote 15174 (DNS query) | `www.7-zip.org` |
| Pacotes UDP externos | Wireshark → Statistics → Conversations → UDP | `24.39.217.246` — 10 pacotes |
| MAC do host investigado | Wireshark → frame 1 (Ethernet II) | `c8:09:a8:57:47:93` |
| Modelo de câmera | NetworkMiner (extração) → ExifTool | `LM-Q725K` (LG Electronics) |
| Chave pública TLS 1.2 | Wireshark → filtro `tls.handshake.session_id` (pacote 26913) | ECDHE secp384r1, 97 bytes |
| Client Random TLS 1.3 | Wireshark → filtro `tls.handshake.extensions_server_name` (frame 17992) | `24e92513...775b70` |
| País do fabricante MAC (FTP) | WhatsMyDNS — MAC Address Lookup (OUI `08:00:27`) | United States |
| Pasta não padrão FTP | Wireshark → Follow TCP Stream (stream 11, LIST) | `/ftp` (uid 65534) — 20/04 17:53 |
| URL via IP 104.21.89.171 | Wireshark → filtro `http` (pacotes 26257/26264) | `http://dfir.science/` |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Host investigado | `192.168.1.26` (MAC `c8:09:a8:57:47:93`, Intel) | Origem de todo o tráfego analisado |
| Credencial FTP | `AfricaCTF2021` | Senha FTP capturada em texto claro (comando PASS) |
| Servidor FTP | `192.168.1.20` (MAC `08:00:27:a6:1f:86`, PCS Systemtechnik GmbH — US) | Banner: "Welcome to Hacker FTP service" |
| Pasta anômala FTP | `/ftp` (uid/gid 65534 — nobody/nogroup) | Criada em 20/04 às 17:53 |
| Arquivo transferido | `20210429_152157.jpg` | Foto via FTP — câmera LM-Q725K (LG Electronics) |
| Servidor DNS (IPv6) | `fe80::c80b:adff:feaa:1db7` | Gateway local (MAC `ca:0b:ad:ad:20:ba`) |
| Host IPv6 investigado | `fe80::b011:ed39:8665:3b0a` | Endereço link-local de `192.168.1.26` |
| Domínio consultado (DNS) | `www.7-zip.org` | Consulta DNS tipo A — pacote 15174 |
| Host externo (UDP) | `24.39.217.246` | 10 pacotes UDP recebidos de `192.168.1.26` |
| Sessão TLS 1.2 | Session ID `da4a0000...c07f4ff` | Servidor `52.162.219.173` — Pubkey ECDHE secp384r1 (97 bytes) |
| Conexão TLS 1.3 | `protonmail.com` (`185.70.41.35`) | Client Random: `24e92513...775b70` |
| Redirecionamento HTTP | `dfir.science` (`104.21.89.171`) | `301 Moved Permanently` via Cloudflare |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | Senha de FTP | `AfricaCTF2021` |
| Q2 | Servidor DNS IPv6 de 192.168.1.26 | `fe80::c80b:adff:feaa:1db7` |
| Q3 | Domínio consultado no pacote 15174 | `www.7-zip.org` |
| Q4 | Pacotes UDP de 192.168.1.26 para 24.39.217.246 | `10` |
| Q5 | MAC do sistema investigado | `c8:09:a8:57:47:93` |
| Q6 | Modelo da câmera da foto 20210429_152157.jpg | `LM-Q725K` |
| Q7 | Chave pública efêmera (Session ID da4a0000...c07f4ff) | `04edcc123af7b13e90ce101a31c2f996f471a7c8f48a1b81d765085f548059a550f3f4f62ca1f0e8f74d727053074a37bceb2cbdc7ce2a8994dcd76dd6834eefc5438c3b6da929321f3a1366bd14c877cc83e5d0731b7f80a6b80916efd4a23a4d` |
| Q8 | Primeiro Client Random TLS 1.3 (protonmail.com) | `24e92513b97a0348f733d16996929a79be21b0b1400cd7e2862a732ce7775b70` |
| Q9 | País do fabricante do MAC do servidor FTP | `United States` |
| Q10 | Horário de criação da pasta não padrão (20/04) | `17:53` |
| Q11 | URL conectada ao IP 104.21.89.171 | `http://dfir.science/` |

---

## 📚 Referências

- [CyberDefenders — PacketMaze CTF](https://cyberdefenders.org/blueteam-ctf-challenges/packet-maze/)
- [Wireshark — Display Filter Reference](https://www.wireshark.org/docs/dfref/)
- [NetworkMiner](https://www.netresec.com/?page=NetworkMiner)
- [ExifTool](https://exiftool.org/)
- [WhatsMyDNS — Pesquisa de Endereço MAC](https://whatsmydns.me/pt/mac-address-lookup)
- [IETF RFC 8446 — TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446)

---