# TryHackMe — Hackers Holiday CTF
## Level 6 — Overheard at Breakfast

**Categoria:** OSINT / Reconhecimento Passivo
**Dificuldade:** Fácil/Média

---

### 🛎️ Concierge Briefing

> The breakfast terrace is loud this morning, clinking cutlery, espresso machines, the usual chatter. One guest couldn't help but linger at a nearby table, seeing more of a conversation than they were meant to.
> When the table's occupant stepped away for a refill, they seized the moment and grabbed a screenshot before it could disappear. Somewhere in that conversation is enough to track down an account nobody was supposed to find.

---

## 🎯 Objetivo

O desafio entrega um **print de uma conversa** flagrada "por acaso" durante o café da manhã. A missão é ler atentamente a conversa, extrair a informação que permite rastrear uma conta pessoal escondida do hóspede, e usar essa informação para chegar a um perfil online — de onde sai a flag.

---

## 🔍 Passo 1 — Lendo a conversa flagrada

A captura de tela mostra uma conversa entre **Ponzi** (influencer, com selo de verificado `L3AK`) e **Lambo!**, um dos hóspedes VIP do Byte Lotus já visto em levels anteriores:

![Conversa flagrada entre Ponzi e Lambo no café da manhã](/Hacker%20Holiday%202026%20-%20THM/6º%20Level%20-%20Overhead%20Breakfest/images/conversation.png)

Trechos-chave da conversa:

> **Ponzi:** *"love to hear it!!! so i've been posting so much on social media and helping customers around. i never ended up getting your handle, so that i could possibly tag you next time."*
>
> **Lambo!:** *"Great to hear, I've been seeing those awesome posts. Yeah nowadays I don't really use much social media... Though I'm still out there, I used to use this free tool that let me upload my profile and link other media accounts was neat, until I wiped everything. Started with a **G** if I remember correctly. But if anything this is my best way of communication: `lambobytelotushotel@gmail.com`"*

Duas informações essenciais são reveladas aqui:

1. Um **e-mail pessoal** de Lambo: `lambobytelotushotel@gmail.com`.
2. Uma pista sobre uma ferramenta gratuita de perfil/avatar, cujo nome **começa com "G"** e permite vincular contas de redes sociais a partir do e-mail.

---

## 🔍 Passo 2 — Identificando a ferramenta "G"

A descrição — *"free tool that let me upload my profile and link other media accounts"*, cujo nome começa com **G** — aponta diretamente para o **Gravatar** ("Globally Recognized Avatar"), serviço que associa um avatar e um perfil público a partir do **hash MD5 de um endereço de e-mail**.

![Página inicial do Gravatar: "Your Free Profile For The Web"](/Hacker%20Holiday%202026%20-%20THM/6º%20Level%20-%20Overhead%20Breakfest/images/Gravatar.png)

O próprio slogan do site confirma a ideia: *"Transform your email address into your digital passport — one avatar, one bio, social connections, and verified links."* — exatamente o que Lambo descreveu na conversa.

---

## 🔍 Passo 3 — Gerando o hash MD5 do e-mail e montando a URL do Gravatar

O Gravatar identifica perfis públicos através do **hash MD5** do e-mail (em minúsculas, sem espaços). A partir do e-mail extraído da conversa, o hash e as URLs do perfil foram gerados:

![Processo de extração do e-mail, geração do hash MD5 e construção das URLs do Gravatar](/Hacker%20Holiday%202026%20-%20THM/6º%20Level%20-%20Overhead%20Breakfest/images/Lambo_in_Gravatar.png)

```
E-mail:      lambobytelotushotel@gmail.com
Hash MD5:    d4a5fc5d3128890778667e24617d7cc0

URL do avatar:  https://www.gravatar.com/avatar/d4a5fc5d3128890778667e24617d7cc0
URL do perfil:  https://gravatar.com/d4a5fc5d3128890778667e24617d7cc0
```

Acessando a URL do perfil, foi possível confirmar que ela pertence de fato a **Lambo (@0xMia)**, o mesmo hóspede VIP já mapeado em desafios anteriores — reunindo, como o briefing sugeria, dados suficientes para *"track down an account nobody was supposed to find"*.

---

## 🔍 Passo 4 — Decodificando o dado encontrado no perfil

Dentro do perfil público do Gravatar (bio/campo de descrição), havia um trecho de texto em **Base64**, deixado propositalmente por trás da "conta que ninguém deveria encontrar". Usando o **CyberChef** (`From Base64`) para decodificá-lo:

![Decodificação Base64 no CyberChef revelando a flag](/Hacker%20Holiday%202026%20-%20THM/6º%20Level%20-%20Overhead%20Breakfest/images/Flag.png)

**Input:**
```
VEhNe1MzY3JlVF9QcjBmaWwzX0g0c19iMzNuX0lkZW50MWZpM2R9s
```

**Output (flag):**
```
THM{S3creT_Pr0fil3_H4s_b33n_Ident1fi3d}
```

---

## 🚩 Flag

```
THM{S3creT_Pr0fil3_H4s_b33n_Ident1fi3d}
```

---

## 📝 Resumo da cadeia de investigação

1. **Briefing + screenshot da conversa** → um hóspede é flagrado revelando, sem querer, seu e-mail pessoal e uma pista sobre uma ferramenta de perfil ("started with G").
2. **Identificação da ferramenta** → a pista aponta para o **Gravatar**, serviço que gera perfis públicos a partir do hash MD5 do e-mail.
3. **Hash MD5 do e-mail** (`lambobytelotushotel@gmail.com` → `d4a5fc5d3128890778667e24617d7cc0`) → geração da URL do perfil/avatar.
4. **Acesso ao perfil do Gravatar** → confirma a identidade de Lambo e expõe um dado codificado em Base64.
5. **CyberChef (From Base64)** → revela a flag escondida no perfil.

---