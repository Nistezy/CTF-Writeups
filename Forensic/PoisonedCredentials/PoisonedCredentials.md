# 🔍 PoisonedCredentials — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense de Rede & LLMNR/NBNS Poisoning

---

| **Analista**          | Mauricio Robert                                                          |
|-----------------------|--------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                        |
| **Data do Relatório** | 22/06/2026                                                               |
| **Data do Incidente** | 22/06/2026 (captura: PoisonedCredentials.pcap)                          |
| **Classificação**     | CONFIDENCIAL                                                             |
| **Ferramentas**       | Wireshark                                                                |
| **Arquivo**           | `PoisonedCredentials.pcap` — 269 pacotes                                |

---

## 🔍 Resumo Executivo

A análise forense de tráfego de rede realizada sobre a captura **`PoisonedCredentials.pcap`** evidencia um ataque clássico de **LLMNR Poisoning** (Link-Local Multicast Name Resolution Poisoning), técnica que explora consultas de resolução de nomes local para capturar credenciais **NTLMv2** de vítimas na rede. A captura contém **269 pacotes** que documentam toda a cadeia do ataque: da consulta LLMNR mal digitada gerada pela vítima até a entrega do hash NTLMv2 da conta comprometida ao atacante via SMB. A investigação identificou a máquina atacante, as **duas vítimas** que receberam respostas envenenadas, a **conta de usuário comprometida** (`cybercactus.local\janesmith`) e o **hostname da máquina-alvo** acessada via SMB (`AccountingPC`). Ao todo, **cinco questões técnicas** foram respondidas com base em evidências extraídas diretamente do pcap. A técnica é amplamente reproduzida com ferramentas como **Responder** (Impacket) e não requer posição privilegiada na rede — apenas visibilidade no segmento de broadcast/multicast da vítima.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta      | Finalidade                                                                                                    |
|-----------------|---------------------------------------------------------------------------------------------------------------|
| **Wireshark**   | Análise da captura PCAP — filtros de exibição LLMNR/NBNS/SMB2, Statistics → Conversations, inspeção de pacotes e decodificação de protocolos |

---

## 📋 Perguntas e Respostas

### Q1 — Qual foi a consulta incorreta feita pela máquina 192.168.232.162?

> **Resposta: `fileshaare`**

**Solução:** Com o filtro `ip.src == 192.168.232.162 && (llmnr || nbns)` aplicado, a captura exibe múltiplas consultas LLMNR dos tipos A e AAAA originadas de `192.168.232.162` em direção ao endereço multicast `224.0.0.252`. O detalhe do **pacote 70** (Transaction ID: `0x9b15`) revela o campo **Query Name: `fileshaare`**, evidenciando que o usuário digitou incorretamente `fileshaare` (com dois 'a') em vez de `fileshare`. O pacote confirma:

```
Link-local Multicast Name Resolution (query)
    Transaction ID: 0x9b15
    Flags: 0x0000  Standard query
    Questions: 1
    Queries
        Name: fileshaare
        Type: AAAA (28) (IPv6 Address)
        Class: IN (0x0001)
```

Essa consulta errônea, sem resposta autoritativa via DNS convencional, propagou-se via LLMNR na rede local — criando a oportunidade perfeita para o ataque de **envenenamento (poisoning)**.

![Consulta Incorreta](/Forensic/PoisonedCredentials/images/Error_Querry_of_192.168.232.162(1).png)

---

### Q2 — Qual é o endereço IP da máquina atuando como entidade desonesta (rogue)?

> **Resposta: `192.168.232.215`**

**Solução:** A janela **Statistics → Conversations → IPv4** (com *Limit to display filter* habilitado) revela duas conversas entre a rogue entity e as vítimas:

```
192.168.232.215 ↔ 192.168.232.176  →  31 pacotes · 4 kB  (A→B: 31 pkts / B→A: 0 bytes)
192.168.232.215 ↔ 192.168.232.162  →  17 pacotes · 2 kB
```

O fato de `192.168.232.215` ser a **única origem de respostas não solicitadas** (`Unsolicited: True`) em ambas as conversas confirma sua natureza ofensiva. A confirmação definitiva vem do **pacote 171**, que exibe a resposta LLMNR enviada de `192.168.232.215` para `192.168.232.176`:

```
Link-local Multicast Name Resolution (response)
    Transaction ID: 0x4a65
    Flags: 0x8000  Standard query response, No error
    Answers
        fileshare: type A, class IN, addr 192.168.232.215
        [Unsolicited: True]
```

O campo `[Unsolicited: True]` — resposta enviada sem que o host de destino tenha realizado a consulta — é a assinatura característica do ataque de **LLMNR Poisoning ativo**.

![Maquina Desonesta](/Forensic/PoisonedCredentials/images/Rougue_Entity(2).png)
---

### Q3 — Qual é o IP da segunda máquina que recebeu respostas envenenadas da entidade desonesta?

> **Resposta: `192.168.232.176`**

**Solução:** As estatísticas de Conversas IPv4 mostram duas vítimas distintas recebendo respostas da rogue entity: `192.168.232.162` (consulta original por `fileshaare`) e `192.168.232.176`. O **pacote 171** confirma que `192.168.232.215` enviou uma resposta LLMNR não solicitada diretamente para `192.168.232.176` (campo `Dst: 192.168.232.176`), com a resolução A envenenada:

```
Ethernet II, Src: VMware 44:ca:ef (00:0c:29:44:ca:ef)
                  Dst: VMware 9c:01:34 (00:0c:29:9c:01:34)
Internet Protocol Version 4
    Src: 192.168.232.215
    Dst: 192.168.232.176
LLMNR Response
    Answers: fileshare → 192.168.232.215 [Unsolicited: True]
```

Ao receber essa resposta forjada, `192.168.232.176` tentou autenticar-se via SMB no endereço `192.168.232.215` (a rogue entity), entregando suas credenciais NTLMv2 ao atacante.

![Segunda Maquina Desonesta](/Forensic/PoisonedCredentials/images/Second_Rougue_Entity(3).png)

---

### Q4 — Qual é o nome de usuário da conta comprometida pelo atacante?

> **Resposta: `janesmith`**

**Solução:** Com o filtro `ip.src == 192.168.232.215` aplicado, o **pacote 242** (`SMB2 Session Setup Request, NTLMSSP AUTH`) originado de `192.168.232.215` para `192.168.232.176` contém no bloco **NTLM Secure Service Provider** os campos que expõem a conta comprometida:

```
NTLMSSP Identifier: NTLMSSP
NTLMSSP Message Type: NTLMSSP_AUTH (0x00000003)
Lan Manager Response: 753b0a58034242e0b2702c0e52c3bf31...
NTLM Response [truncated]: 0312c8aeaedcc76acf103bcada22c2b9...
Domain name: cybercactus.local
User name:   janesmith
```

A conta **`cybercactus.local\janesmith`** enviou sua resposta NTLMv2 ao recurso falso oferecido pela rogue entity, entregando ao atacante o hash NTLMv2 passível de **crack offline** com ferramentas como Hashcat ou John the Ripper — comprometendo assim o acesso à conta.

![User SMB](/Forensic/PoisonedCredentials/images/Account_Compromissed(4).png)

---

### Q5 — Qual é o hostname da máquina acessada pelo atacante via SMB?

> **Resposta: `AccountingPC`**

**Solução:** Com o filtro `smb2` aplicado, o **pacote 241** (`Session Setup Response, NTLMSSP CHALLENGE`) originado de `192.168.232.215` contém no bloco **NTLM Secure Service Provider** atributos Target Info que revelam a máquina-alvo:

```
Target Name: CYBERCACTUS
NTLMSSP Message Type: NTLMSSP_CHALLENGE (0x00000002)
Target Info
    Attribute: NetBIOS domain name: CYBERCACTUS
    Attribute: NetBIOS computer name: ACCOUNTINGPC
    Attribute: DNS computer name: AccountingPC.cybercactus.local
    Attribute: DNS domain name: cybercactus.local
    Attribute: DNS tree name: cybercactus.local
    Attribute: Timestamp
Version 10.0 (Build 19041); NTLM Current Revision 15
```

O atributo `NetBIOS computer name: ACCOUNTINGPC` e o FQDN `AccountingPC.cybercactus.local` identificam o hostname da máquina cujo compartilhamento SMB foi falsamente oferecido pelo atacante — apontando **`AccountingPC`** como o alvo da movimentação lateral dentro do domínio `cybercactus.local`.

![Nome da Maquina Acessada Via SMB](/Forensic/PoisonedCredentials/images/Host_Machine_Name(5).png)

---

## ⛓ Linha do Tempo do Ataque

```
[FASE 1 — RECONHECIMENTO PASSIVO]
    192.168.232.215 monitora passivamente consultas LLMNR/NBNS
    na sub-rede 192.168.232.0/24
    ↓
[FASE 2 — CONSULTA ERRÔNEA DA VÍTIMA 1]
    192.168.232.162 → 224.0.0.252 (multicast)
    LLMNR Query: "fileshaare" (tipo A e AAAA)
    Sem resposta autoritativa via DNS → propagação LLMNR
    ↓
[FASE 3 — ENVENENAMENTO (POISONING)]
    192.168.232.215 responde a 192.168.232.162:
    LLMNR Response: "fileshaare → 192.168.232.215" [Unsolicited: True]
    ↓
    192.168.232.215 responde a 192.168.232.176 (vítima 2):
    LLMNR Response: "fileshare → 192.168.232.215" [Unsolicited: True]
    ↓ Pacote 171 — LLMNR response não solicitada para 192.168.232.176
    ↓
[FASE 4 — CAPTURA DE HASH NTLMv2]
    192.168.232.176 tenta autenticar-se no recurso SMB falso
    SMB2 Negotiate → Session Setup NTLMSSP_NEGOTIATE
    192.168.232.215 responde com NTLMSSP_CHALLENGE (pacote 241)
    Target: CYBERCACTUS | Machine: AccountingPC.cybercactus.local
    ↓ Pacote 242 — NTLMSSP_AUTH
    192.168.232.176 envia NTLMSSP AUTH:
        Domain: cybercactus.local
        User:   janesmith
        Hash:   NTLMv2 capturado pelo atacante
    ↓
[FASE 5 — COMPROMETIMENTO]
    Rogue entity (192.168.232.215) possui o hash NTLMv2 de janesmith
    Crack offline possível (Hashcat, John the Ripper)
    Acesso à conta cybercactus.local\janesmith comprometido
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|--------------------|----------|
| Consulta incorreta da vítima | Wireshark → filtro `ip.src == 192.168.232.162 && (llmnr \|\| nbns)` (pacote 70) | `fileshaare` (Query Name) |
| IP da rogue entity | Wireshark → Statistics → Conversations IPv4 + pacote 171 (LLMNR Response Unsolicited) | `192.168.232.215` |
| Segunda vítima envenenada | Wireshark → Conversations IPv4 + detalhe pacote 171 (Dst) | `192.168.232.176` |
| Conta comprometida | Wireshark → filtro `ip.src == 192.168.232.215` → pacote 242 (NTLMSSP AUTH) | `janesmith` (`cybercactus.local\janesmith`) |
| Hostname alvo (SMB) | Wireshark → filtro `smb2` → pacote 241 (NTLMSSP CHALLENGE, Target Info) | `AccountingPC` (`AccountingPC.cybercactus.local`) |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Rogue entity (atacante) | `192.168.232.215` | Responde consultas LLMNR de forma não solicitada (`Unsolicited: True`) |
| Vítima 1 | `192.168.232.162` | Originou consulta LLMNR com o nome incorreto `fileshaare` |
| Vítima 2 | `192.168.232.176` | Recebeu resposta LLMNR envenenada para `fileshare` → enviou NTLMv2 |
| Consulta envenenada 1 | `fileshaare` | Nome mal digitado (double 'a') — vetor primário do envenenamento |
| Consulta envenenada 2 | `fileshare` | Recurso de rede falso respondido pela rogue entity a 192.168.232.176 |
| Conta comprometida | `cybercactus.local\janesmith` | Hash NTLMv2 capturado via NTLMSSP AUTH (pacote 242) |
| Hostname alvo | `AccountingPC` (`ACCOUNTINGPC`) | `AccountingPC.cybercactus.local` — atributo `NetBIOS computer name` no NTLMSSP CHALLENGE |
| Domínio AD | `cybercactus.local` | Domínio Active Directory do ambiente comprometido |
| Técnica (MITRE ATT&CK) | `T1557.001` | LLMNR/NBT-NS Poisoning and SMB Relay |
| Protocolo explorado | LLMNR (UDP 5355) + NBNS | Resolução de nomes local sem autenticação |
| Protocolo de captura | SMB2 + NTLMSSP | Canal de entrega do hash NTLMv2 ao atacante |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | Consulta incorreta da máquina 192.168.232.162 | `fileshaare` |
| Q2 | IP da rogue entity | `192.168.232.215` |
| Q3 | IP da segunda máquina envenenada | `192.168.232.176` |
| Q4 | Nome de usuário comprometido | `janesmith` |
| Q5 | Hostname da máquina acessada via SMB | `AccountingPC` |

---

## 🛡 Recomendações

- **Desabilitar LLMNR** via Group Policy: `Computer Configuration → Administrative Templates → Network → DNS Client → Turn off multicast name resolution: Enabled`
- **Desabilitar NetBIOS Name Service (NBNS)** em todas as interfaces de rede (via DHCP Options ou GPO)
- **Implementar SMB Signing obrigatório** para prevenir ataques de relay NTLM: GPO `Microsoft network server/client: Digitally sign communications always`
- **Adotar Kerberos em vez de NTLM** para autenticação em recursos internos, eliminando a superfície de ataque NTLMv2
- **Monitorar respostas LLMNR/NBNS não solicitadas** com IDS/IPS (Snort/Suricata com regras para detecção de Responder)
- **Revogar e redefinir** as credenciais da conta `janesmith` imediatamente; auditar toda atividade recente no domínio `cybercactus.local`
- **Isolar e investigar forensicamente** a máquina `192.168.232.215` para determinar o vetor de comprometimento inicial e a extensão do acesso obtido

---

## 📚 Referências

- [CyberDefenders — PoisonedCredentials CTF](https://cyberdefenders.org/blueteam-ctf-challenges/poisonedcredentials/)
- [MITRE ATT&CK — T1557.001: LLMNR/NBT-NS Poisoning and SMB Relay](https://attack.mitre.org/techniques/T1557/001/)
- [Wireshark — Display Filter Reference](https://www.wireshark.org/docs/dfref/)
- [Responder (Impacket) — LLMNR/NBT-NS/mDNS Poisoner](https://github.com/lgandx/Responder)
- [Microsoft — Disabling LLMNR via Group Policy](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2008-R2-and-2008/dd316044)

---