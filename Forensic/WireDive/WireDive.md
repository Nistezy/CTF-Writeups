# 🌊 WireDive — CTF Writeup

### CyberDefenders Blue Team Challenge | Network Forensics & Reverse Shell Analysis

---

| **Analista**          | Mauricio Robert                                      |
| --------------------- | ---------------------------------------------------- |
| **Organização**       | Faculdade Impacta                                    |
| **Data do Relatório** | 15/07/2026                                           |
| **Data do Incidente** | 16/04/2020                                           |
| **Classificação**     | CONFIDENCIAL                                         |
| **Ferramentas**       | Wireshark · NetworkMiner · Zui (Zeek/Brim)           |
| **Arquivos**          | dhcp.pcapng · dns.pcapng · smb.pcapng · shell.pcapng |

---

## 🔍 Resumo Executivo

A análise forense das capturas revelou um comprometimento completo de um host Linux (**Ubuntu 18.04 — Bionic Beaver**) através de uma **reverse shell via netcat**.

O ataque envolveu:

* Atribuição de IP via DHCP
* Resolução DNS contendo flag
* Acesso SMB com arquivo sensível
* Execução de shell reversa
* Elevação de privilégio com senha em texto claro
* Exfiltração do arquivo `/etc/passwd`

---

## 📋 Perguntas e Respostas

### Q1 — What IP address is requested by the client?

> **Resposta:** `192.168.2.244`

**Análise:** Identificado via estatísticas de endpoints do Wireshark durante o fluxo DHCP.

---

### Q2 — What is the transaction ID for the DHCP release?

> **Resposta:** `0x9f8fa557`

**Análise:** Extraído do pacote DHCP Release (frame 176).

---

### Q3 — What is the MAC address of the client?

> **Resposta:** `00:0c:29:82:f5:94`

**Análise:** Obtido do cabeçalho Ethernet nos pacotes DHCP.

---

### Q4 — What is the response for the lookup for flag.fruitinc.xyz?

> **Resposta:** `ACOOLDNSFLAG`

**Análise:** Registro TXT retornado na resposta DNS.

---

### Q5 — Which root server responds to the google.com query?

> **Resposta:** `e.root-servers.net`

**Análise:** Identificado na cadeia de resolução DNS.

---

### Q6 — What is the path of the file that is opened?

> **Resposta:** `HelloWorld\TradeSecrets.txt`

**Análise:** Observado em requisição SMB2 Create.

---

### Q7 — What was the hex status code when the user SAMBA\jtomato logs in?

> **Resposta:** `0xc000006d`

**Análise:** STATUS_LOGON_FAILURE na autenticação SMB.

---

### Q8 — What is the tree that is being browsed?

> **Resposta:** `\\192.168.2.10\public`

**Análise:** Identificado via Tree Connect SMB.

---

### Q9 — What is the flag in the file?

> **Resposta:** `flag<OneSuperDuperSecret>`

**Análise:** Extraído via Follow TCP Stream do SMB.

---

### Q10 — What port is the shell listening on?

> **Resposta:** `4444`

**Análise:** Identificado nos logs Zeek (`conn.log`).

---

### Q11 — What is the port for the second shell?

> **Resposta:** `9999`

**Análise:** Segunda conexão TCP identificada.

---

### Q12 — What version of netcat is installed?

> **Resposta:** `1.10-41.1`

**Análise:** Detectado via requisição HTTP do apt.

---

### Q13 — What file is added to the second shell?

> **Resposta:** `/etc/passwd`

**Análise:** Exfiltrado via redirecionamento para netcat.

---

### Q14 — What password is used to elevate the shell?

> **Resposta:** `*umR@Q%4V&RC`

**Análise:** Capturada em texto claro via `sudo -S`.

---

### Q15 — What is the codename of the target system's OS version?

> **Resposta:** `Bionic Beaver`

**Análise:** Identificado via User-Agent + OSINT.

---

### Q16 — How many users are on the target system?

> **Resposta:** `31`

**Análise:** Contagem das entradas em `/etc/passwd`.

---

## ⛓ Linha do Tempo do Ataque

```
DHCP → IP 192.168.2.244 atribuído
    ↓
DNS → flag via TXT (ACOOLDNSFLAG)
    ↓
SMB → acesso ao share público
    ↓
Leitura de TradeSecrets.txt → flag extraída
    ↓
Reverse shell (porta 4444)
    ↓
Instalação do netcat
    ↓
Elevação de privilégio (senha exposta)
    ↓
Segunda shell (porta 9999)
    ↓
Exfiltração de /etc/passwd
```

---

## 🚨 Indicadores de Comprometimento (IOCs)

| Tipo          | Valor                        |
| ------------- | ---------------------------- |
| IP cliente    | 192.168.2.244                |
| MAC           | 00:0c:29:82:f5:94            |
| DNS flag      | flag.fruitinc.xyz            |
| SMB share     | \192.168.2.10\public         |
| Porta shell 1 | 4444                         |
| Porta shell 2 | 9999                         |
| Senha         | *umR@Q%4V&RC                 |
| OS            | Ubuntu 18.04 (Bionic Beaver) |

---

## 🧠 Conclusão

O ataque demonstra uma cadeia completa de comprometimento:

* Reconhecimento via DHCP/DNS
* Acesso lateral via SMB
* Execução remota com netcat
* Elevação de privilégio insegura
* Exfiltração de dados sensíveis

A presença de senha em texto claro e ausência de controles de rede foram fatores críticos para o sucesso do ataque.

---