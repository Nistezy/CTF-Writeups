# TryHackMe — Hackers Holiday CTF
## Level 0 — The Brochure

**Categoria:** OSINT / Estenografia (esteganografia via texto embutido em imagem)
**Dificuldade:** Fácil

---

### 🛎️ Concierge Briefing

> Before you ever set foot on the property, you decide to do a little homework on the Byte Lotus Hotel. The brochure's hero photo carries an unmistakable AI fingerprint, and the account behind it leads somewhere the hotel never intended you to look.
> Follow the trail, uncover the hidden connection, and find what was left behind.

---

## 🎯 Objetivo

Investigar o folheto (brochure) do **Byte Lotus Resort**, seguir as pistas de OSINT deixadas no Instagram do hotel e encontrar a flag escondida.

---

## 🔍 Passo 1 — Analisando o Brochure

O ponto de partida é o folheto de divulgação do hotel, entregue como parte do desafio.

![Brochure do Byte Lotus Resort](/Hacker%20Holiday%202026%20-%20THM/0º%20Level%20-%20The%20Brochure/images/thebrochure.png)

Alguns detalhes chamam atenção no material:

- A frase de efeito: *"A polished first impression can still leave a trail."* — um trocadilho, sugerindo que a imagem (gerada por IA) carrega um "rastro" (metadado ou informação oculta).
- A dica de busca: *"Some things aren't posted. Some clues are. Find us on Instagram... or not."* — aponta diretamente para uma investigação nas redes sociais.
- A menção à concierge **VERA**, que "pode te ajudar com mais informações" — sugerindo que existe um perfil dedicado a ela.

Essas informações indicam que o próximo passo é procurar o hotel no Instagram.

---

## 🔍 Passo 2 — Encontrando o Instagram do hotel

Pesquisando pelo nome do hotel, encontramos o perfil oficial:

```
instagram.com/thebytelotusresort
```

Ao abrir a aba **Following (Seguindo)** do perfil do hotel, percebemos que ele segue apenas **1 conta**:

![Perfil e lista de "Following" do The Byte Lotus Resort](/Hacker%20Holiday%202026%20-%20THM/0º%20Level%20-%20The%20Brochure/images/TheByteLotus_Instagram_Perfil_and_Following.png)

A conta seguida é:

```
@veratheconcierge
```

Isso confirma a pista do brochure sobre a "Vera" — a concierge citada no material promocional tem, de fato, um perfil próprio no Instagram, que não é divulgado publicamente pelo hotel.

---

## 🔍 Passo 3 — Explorando o perfil da Vera

Acessando o perfil:

```
instagram.com/veratheconcierge
```

A bio confirma a ligação com o hotel: *"Currently working for Byte Lotus Hotel."*

Ao observar as fotos publicadas no feed (o mesmo cenário de "pôr do sol" usado no brochure), uma das imagens contém um **texto embutido diretamente na imagem**, parecendo ruído/marca d'água — na verdade, é uma **string em Base64** escondida à vista de todos:

![String Base64 escondida na foto do perfil de Vera](/Hacker%20Holiday%202026%20-%20THM/0º%20Level%20-%20The%20Brochure/images/Base64_Flag.png)

String extraída da imagem:

```
VEhNe1YzckBzX2FDQzB1bnRfaDRzX2IzM25fZjB1bmQhfQ==
```

---

## 🔍 Passo 4 — Decodificando a string em Base64

Usando o **CyberChef** (`From Base64`) para decodificar a string encontrada na imagem:

![Decodificação da string via CyberChef](/Hacker%20Holiday%202026%20-%20THM/0º%20Level%20-%20The%20Brochure/images/Base64_Decode.png)

**Input:**
```
VEhNe1YzckBzX2FDQzB1bnRfaDRzX2IzM25fZjB1bmQhfQ==
```

**Output (flag):**
```
THM{V3r@s_aCC0unt_h4s_b33n_f0und!}
```

---

## 🚩 Flag

```
THM{V3r@s_aCC0unt_h4s_b33n_f0und!}
```

---

## 📝 Resumo da cadeia de investigação

1. **Brochure** → dica textual sobre "rastro" na imagem e sobre a concierge Vera.
2. **Instagram do hotel** (`@thebytelotusresort`) → verificar quem o hotel segue.
3. **Following list** → revela a conta oculta `@veratheconcierge`.
4. **Perfil da Vera** → uma das fotos contém uma string Base64 embutida.
5. **CyberChef (From Base64)** → decodificação revela a flag.

---