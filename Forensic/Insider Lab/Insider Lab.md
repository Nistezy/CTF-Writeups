# 🕵️ Insider (Karen) — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense de Disco & Análise de Artefatos

---

| **Analista**          | Mauricio Robert                                                          |
|-----------------------|--------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                        |
| **Data do Relatório** | 13/06/2026                                                               |
| **Data do Incidente** | 20–23/03/2019                                                            |
| **Classificação**     | CONFIDENCIAL                                                             |
| **Ferramentas**       | Autopsy 4.23.1 · Exterro FTK Imager                                     |
| **Arquivo**           | `Horcrux.E01` (imagem de disco EXT4 — 14.304 MB)                        |

---

## 🔍 Resumo Executivo

A análise forense da imagem `Horcrux.E01` revelou uma máquina **Kali Linux** (hostname `KarenHacker`) utilizada por um insider — usuário **Karen** — para atividades de hacking ofensivo. Os artefatos descobertos incluem o download de **`mimikatz_trunk.zip`** (ferramenta de dump de credenciais), análise esteganográfica de uma imagem com **binwalk**, criação de um **"Super Secret File"** na área de trabalho, um **Checklist** com objetivos pessoais ("Gain Bob's Trust / Learn how to hack / Profit") e evidências de um ataque lançado contra a máquina de **Bob** via **AlphaSOC flightsim**. O histórico de comandos (`.bash_history`) e os logs de autenticação (`auth.log`) documentam toda a cadeia de atividades. O especialista **Castro** foi provocado dentro de um script bash por tentativas falhas de execução de comandos.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta              | Finalidade                                                                              |
|-------------------------|-----------------------------------------------------------------------------------------|
| **Autopsy 4.23.1**      | Análise do sistema de arquivos EXT4 — navegação de diretórios, keyword search, extração de texto, metadados (MD5/SHA-256) e análise de artefatos |
| **Exterro FTK Imager**  | Inspeção complementar de logs (`auth.log`, `kern.log`), visualização de capturas de tela e evidências de execução de ferramentas |

---

## 📋 Perguntas e Respostas

### Q1 — Qual distribuição Linux foi utilizada na máquina?

> **Resposta: `Kali Linux`**

**Solução:** A análise do arquivo `kern.log` no Autopsy, localizado em `/var/log/kern.log`, revelou a linha de inicialização do kernel registrada em `Mar 21 18:53:38 KarenHacker kernel`:

```
[0.000000] Linux version 4.13.0-kali1-amd64 (devel@kali.org)
            (gcc version 6.4.0 20171026 (Debian 6.4.0-9))
            #1 SMP Debian 4.13.10-1kali2 (2017-11-08)
```

A string `4.13.0-kali1-amd64`, compilada por `devel@kali.org`, confirma que a distribuição é **Kali Linux** — amplamente utilizada para testes de penetração e segurança ofensiva, coerente com as ferramentas encontradas no sistema (mimikatz, msfconsole).

![OS da Maquina](/Forensic/Insider%20Lab/images/OS_Used_kali(1).png)

---

### Q2 — Qual é o hash MD5 do arquivo Apache access.log?

> **Resposta: `d41d8cd98f00b204e9800998ecf8427e`**

**Solução:** Na seção "Suspicious Items" do Autopsy, o arquivo `access.log` foi localizado em `/var/log/apache2/access.log`. A aba **File Metadata** exibe:

```
Name:   access.log
Size:   0
MD5:    d41d8cd98f00b204e9800998ecf8427e
SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934c...
```

Este hash MD5 corresponde ao **hash universal de arquivo vazio** (0 bytes), indicando que o Apache foi instalado mas nunca recebeu requisições — ou os logs foram limpos.

![MD5](/Forensic/Insider%20Lab/images/MD5_Hash_Access.log(2).png)

---

### Q3 — Qual é o nome do arquivo da ferramenta de dump de credenciais baixada?

> **Resposta: `mimikatz_trunk.zip`**

**Solução:** A navegação pelo Autopsy em `/root/Downloads/` revelou o arquivo:

```
Nome:      mimikatz_trunk.zip
Tamanho:   845.749 bytes
MIME:      application/zip
MD5:       52070297d4596e64efeffe24fd58ee92
SHA-256:   3b9ef90fd4b695da0ed208a5be3099551295f3cb2d34f5b...
```

A análise hexadecimal do ZIP revela a string `wifi_passwords.yar`, confirmando que se trata do **Mimikatz** — ferramenta conhecida para dump de hashes NTLM, senhas em texto claro e tickets Kerberos de sistemas Windows.

![Ferramenta Dump](/Forensic/Insider%20Lab/images/Suspicious_Downloaded_Dumping_Tool(3).png)

---

### Q4 — Qual é o caminho absoluto do arquivo "super secreto"?

> **Resposta: `/root/Desktop/SuperSecretFile.txt`**

**Solução:** A análise do `.bash_history` no diretório `/root` no Autopsy revelou os seguintes comandos destacados:

```bash
touch snky snky > /root/Desktop/SuperSecretFile.txt
cat snky snky > /root/Desktop/SuperSecretFile.txt
```

O primeiro comando cria os arquivos `snky` e redireciona a saída para criar `/root/Desktop/SuperSecretFile.txt`. O segundo concatena o conteúdo dos arquivos `snky` para dentro do mesmo destino. O caminho completo **`/root/Desktop/SuperSecretFile.txt`** é confirmado pelo histórico de bash.

![Super Secret](/Forensic/Insider%20Lab/images/Super_Secret_File_Created(4).png)

---

### Q5 — Qual programa utilizou o arquivo `didyouthinkwedmakeiteasy.jpg`?

> **Resposta: `binwalk`**

**Solução:** A análise do `.bash_history` revela a sequência de comandos, incluindo:

```bash
history > history.txt
binwalk didyouthinkwedmakeiteasy.jpg
```

O **`binwalk`** é uma ferramenta de análise forense de firmware/arquivos que identifica arquivos e código embutidos dentro de outros arquivos (esteganografia). O arquivo `didyouthinkwedmakeiteasy.jpg` (1.865 bytes, localizado em `/root/Documents/myfirsthack/`, MD5: `de664b5130a1dcf156564c22e507b76c`) foi analisado por esta ferramenta — prática comum para extrair dados ocultos dentro de imagens JPEG.

![Binwalk](/Forensic/Insider%20Lab/images/Program_Used_didyouthinkwedmakeiteasy.jpg(5).png)

---

### Q6 — Qual é o terceiro objetivo do checklist criado por Karen?

> **Resposta: `Profit`**

**Solução:** A pesquisa por palavra-chave `secret` no Autopsy localizou o arquivo `Checklist` em `/root/Desktop/` (60 bytes, MD5: `050c06331d83aab64efad77ab7107dda`, MIME: `text/plain`). O conteúdo extraído exibe:

```
Check List:

- Gain Bob's Trust
- Learn how to hack
- Profit
```

O terceiro item — **`Profit`** — é o objetivo final de Karen, em referência ao famoso formato de meme de "planos em três etapas".

![Profit](/Forensic/Insider%20Lab/images/Third_Goal_of_Cheklist_by_Karen(6).png)

---

### Q7 — Quantas vezes o Apache foi executado?

> **Resposta: `0`**

**Solução:** A análise do diretório `/var/log/apache2/` no Autopsy revelou três arquivos: `access.log`, `error.log` e `other_vhosts_access.log` — **todos com `Size: 0 bytes`** e timestamps `0000-00-00 00:00:00`. O diretório foi criado pela instalação do pacote Apache, mas nenhum serviço foi efetivamente inicializado. Os arquivos de log vazios sem timestamps válidos confirmam **0 execuções** do Apache.

![Quantas Vezes o Apache foi Executado](/Forensic/Insider%20Lab/images/Apaches_Runs_0(7).png)

---

### Q8 — Qual arquivo contém evidência de ataque lançado contra outra máquina?

> **Resposta: `history.txt`**

**Solução:** A aba Application do Autopsy exibe uma captura de tela do desktop da máquina de Bob, com um terminal ativo executando:

```
C:\Users\Bob\AppData\Local\Temp>aylmao.exe
AlphaDOC Network Flight Simulator (https://github.com/alphasoc/flightsim)
[...] generates malicious network traffic for security teams to evaluate
security controls
```

No host de Karen, o comando `history > history.txt` (visível no `.bash_history`) gravou o histórico completo de comandos — incluindo a preparação e execução deste ataque — no arquivo **`history.txt`**, criado em `/root/Documents/myfirsthack/`.

![Evidencia do Ataque](/Forensic/Insider%20Lab/images/Evidence_of_This_Machine_is_Attacker(8).png)

---

### Q9 — Qual especialista em computação Karen estava provocando?

> **Resposta: `Young`**

**Solução:** A análise do arquivo `firstscript_fixed` em `/root/Documents/myfirsthack/` no Autopsy revela os comentários do script bash:

```bash
echo "Showing you your current path"
pwd
echo "Show my default route"
ip route | grep --color default
echo "Show network connections w/ port 80"
netstat | grep --color 80
echo "Heck yeah! I can write bash too Young"
```

A linha **`"echo "Heck yeah! I can write bash too Young""`** é um comentário sarcástico de Karen provocando **Young**.

![Young](/Forensic/Insider%20Lab/images/Karen_Provoke_Young(9).png)

---

### Q10 — Qual usuário executou `su` para obter acesso root às 11:26?

> **Resposta: `postgres`**

**Solução:** A análise do `auth.log` no Exterro FTK Imager (`/var/log/auth.log`) exibe múltiplas entradas com timestamp `Mar 20 11:26:22 KarenHacker`:

```
Mar 20 11:26:22 KarenHacker su[4060]: Successful su for postgres by root
Mar 20 11:26:22 KarenHacker su[4060]: + ??? root:postgres
Mar 20 11:26:22 KarenHacker su[4060]: pam_unix(su:session): session opened
                                       for user postgres by (uid=0)
```

As entradas `Successful su for postgres by root` repetem-se múltiplas vezes (PIDs 4060, 4074, 4081) no mesmo timestamp, indicando que o comando `su` foi utilizado para alternar para o usuário **`postgres`** — necessário para inicializar o banco de dados do Metasploit (`msfdb init`, visto no `.bash_history`).

![Postgre](/Forensic/Insider%20Lab/images/postgre_User_Used_SU(10).png)

---

### Q11 — Qual é o diretório de trabalho atual com base no histórico de bash?

> **Resposta: `/root/Documents/myfirsthack/`**

**Solução:** A análise do `.bash_history` no Autopsy revela a sequência completa de navegação:

```bash
cd ..
ls
cd home/
ls
cd /root
ls
cd ../root
cd /root/Documents/myfirsthack/../../Desktop/
sl
ls
cd ../Documents/myfirsthack/    ← retorno ao diretório
netstat
echo bob.txt
touch bob.txt
```

A navegação `cd /root/Documents/myfirsthack/../../Desktop/` é seguida por `cd ../Documents/myfirsthack/`, retornando o usuário ao diretório `/root/Documents/myfirsthack/`. Todos os comandos subsequentes (criação de scripts, `netstat`, `echo`, `touch`) ocorrem dentro deste diretório, confirmando que **`/root/Documents/myfirsthack/`** é o diretório de trabalho atual.

![Novo Desktop](/Forensic/Insider%20Lab/images/New_Desktop_of_Karen(11).png)

---

## ⛓ Linha do Tempo de Atividades (Timeline)

```
[20/03 ~09h] INSTALAÇÃO
    apt-get install moo (easter egg) — tentativas falhas de Castro
    Instalação de pacotes: Apache, PostgreSQL, Metasploit
    ↓
[20/03 11:23] SESSÃO ROOT
    gdm-password / systemd-logind — sessão aberta para root
    ↓
[20/03 11:26:22] PREPARAÇÃO METASPLOIT
    su postgres (múltiplas vezes — PIDs 4060, 4074, 4081)
    systemctl start postgresql → msfdb init → msfconsole
    ↓
[20-23/03] ATIVIDADES OFENSIVAS
    Download de mimikatz_trunk.zip → /root/Downloads/
    Criação de /root/Desktop/Checklist (objetivos de Karen)
    touch snky snky → /root/Desktop/SuperSecretFile.txt
    ↓
[21/03 18:53:38] BOOT DO KERNEL
    Linux 4.13.0-kali1-amd64 — Kali Linux confirmado no kern.log
    ↓
[~] ANÁLISE E ATAQUE
    binwalk didyouthinkwedmakeiteasy.jpg (esteganografia)
    history > history.txt (exportação do histórico)
    aylmao.exe run (AlphaSOC flightsim) na máquina Bob
    ↓
[~] ENCERRAMENTO
    shutdown now — finalização da sessão
```

---

## 🗺 Mapeamento MITRE ATT&CK

| ID | Técnica | Tática | Artefato |
|----|---------|--------|----------|
| T1592 | Gather Victim Host Information — reconhecimento da rede alvo | Reconnaissance | `firstscript`, `netstat` |
| T1003 | OS Credential Dumping — Mimikatz para dump de hashes NTLM | Credential Access | `mimikatz_trunk.zip` |
| T1027 | Obfuscated Files or Information — binwalk em imagem JPEG suspeita | Defense Evasion | `didyouthinkwedmakeiteasy.jpg` |
| T1059.004 | Unix Shell — scripts bash de hacking (`firstscript`, `hellworld.sh`) | Execution | `/root/Documents/myfirsthack/` |
| T1078 | Valid Accounts — uso de su para conta `postgres` (serviço crítico) | Privilege Escalation | `auth.log` |
| T1105 | Ingress Tool Transfer — download de mimikatz e ferramentas de pentest | Command & Control | `/root/Downloads/` |
| T1499 | Endpoint Denial of Service / Adversarial Traffic — AlphaSOC flightsim | Impact | `aylmao.exe` / `history.txt` |

---

## 🚨 Indicadores e Artefatos Identificados (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Sistema Operacional | Kali Linux 4.13.0-kali1-amd64 | Confirmado via `kern.log` — `devel@kali.org` |
| Usuário | `KarenHacker` / `root` | Hostname e usuário principal da máquina |
| Ferramenta | `mimikatz_trunk.zip` (845.749 bytes) | `/root/Downloads/` — dump de credenciais |
| MD5 Mimikatz | `52070297d4596e64efeffe24fd58ee92` | Hash MD5 do `mimikatz_trunk.zip` |
| MD5 access.log | `d41d8cd98f00b204e9800998ecf8427e` | Hash de arquivo vazio — Apache nunca executado |
| Arquivo Secreto | `/root/Desktop/SuperSecretFile.txt` | Criado via `touch snky snky > ...` |
| Checklist | `/root/Desktop/Checklist` (60 bytes) | Objetivos: Gain Bob's Trust / Learn how to hack / **Profit** |
| Ferramenta Análise | `binwalk` | Usado em `didyouthinkwedmakeiteasy.jpg` — possível esteganografia |
| Imagem Suspeita | `didyouthinkwedmakeiteasy.jpg` (1.865 bytes) | `/root/Documents/myfirsthack/` — MD5: `de664b5130a1dcf156564c22e507b76c` |
| Evidência de Ataque | `history.txt` | Histórico bash exportado — contém preparação e execução do ataque |
| Ferramenta Ataque | `aylmao.exe` (AlphaSOC flightsim) | Executado na máquina de Bob — gerador de tráfego malicioso |
| Scripts | `firstscript`, `firstscript_fixed`, `hellworld.sh` | `/root/Documents/myfirsthack/` — provocações a Castro |
| Usuário Alvo SU | `postgres` | Alvo de múltiplos `su` às `11:26:22` — preparação PostgreSQL/Metasploit |
| Apache | `access.log`, `error.log`, `other_vhosts_access.log` (0 bytes) | `/var/log/apache2/` — **Apache nunca executado** |
| Diretório de Trabalho | `/root/Documents/myfirsthack/` | CWD confirmado pelo `.bash_history` |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|-----------------|
| Q1 | Distribuição Linux utilizada | `Kali Linux` |
| Q2 | Hash MD5 do Apache access.log | `d41d8cd98f00b204e9800998ecf8427e` |
| Q3 | Ferramenta de dump de credenciais baixada | `mimikatz_trunk.zip` |
| Q4 | Caminho absoluto do arquivo "super secreto" | `/root/Desktop/SuperSecretFile.txt` |
| Q5 | Programa que usou `didyouthinkwedmakeiteasy.jpg` | `binwalk` |
| Q6 | Terceiro objetivo do checklist de Karen | `Profit` |
| Q7 | Número de execuções do Apache | `0` |
| Q8 | Arquivo com evidência de ataque a outra máquina | `history.txt` |
| Q9 | Especialista em computação provocado por Karen | `Castro` |
| Q10 | Usuário que executou `su` às 11:26 | `postgres` |
| Q11 | Diretório de trabalho atual (bash history) | `/root/Documents/myfirsthack/` |

---

## 📚 Referências

- [CyberDefenders — Insider CTF](https://cyberdefenders.org/)
- [Autopsy Digital Forensics Platform](https://www.autopsy.com/)
- [Exterro FTK Imager](https://www.exterro.com/ftk-imager)
- [Mimikatz — gentilkiwi](https://github.com/gentilkiwi/mimikatz)
- [AlphaSOC flightsim](https://github.com/alphasoc/flightsim)
- [Binwalk — Firmware Analysis Tool](https://github.com/ReFirmLabs/binwalk)
- [MITRE ATT&CK — T1003 OS Credential Dumping](https://attack.mitre.org/techniques/T1003/)

---