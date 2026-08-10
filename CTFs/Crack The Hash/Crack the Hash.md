# Writeup — Crack the Hash

## Sala
**Crack the Hash**

## Objetivo
Identificar o tipo de cada hash fornecido e quebrá-lo, recuperando a senha em texto puro. Foram utilizadas duas abordagens complementares:

- **CrackStation** (`crackstation.net`) — serviço online com rainbow tables/lookup tables gigantes (190GB para MD5/SHA1, 19GB para os demais), ideal para hashes simples e não salgados.
- **Hashcat** (v7.1.2, rodando no Windows via PowerShell) — utilizado para hashes mais complexos, salgados ou com iterações (bcrypt, sha256, sha512crypt, HMAC-SHA1), usando a wordlist `rockyou.txt` como dicionário de ataque (`-a 0`, modo de ataque por dicionário).
- Como apoio para identificar o **hash mode** correto no Hashcat, foi consultada a página oficial *Example Hashes* do wiki do Hashcat (`hashcat.net/wiki/doku.php?id=example_hashes`), comparando o formato do hash capturado com os exemplos de cada modo.

Comando geral usado no Hashcat:
```
hashcat.exe -m <modo> .\hash.txt .\rockyou.txt --show
```
(o parâmetro `-w 3` foi usado em algumas execuções para aumentar o workload profile e acelerar o ataque).

---

## Hash 1 — MD5
**Hash:** `48bb6e862e54f2a795ffc4e541caed4d`

**Ferramenta:** CrackStation
**Tipo identificado:** MD5
**Senha:** `easy`

O hash bateu diretamente na lookup table do CrackStation (match "verde" = exato), sem necessidade de força bruta.

![Hash](/CTFs/Crack%20The%20Hash/images/1º%20Hash.png)

---

## Hash 2 — SHA1
**Hash:** `CBFDAC6008F9CAB4083784CBD1874F76618D2A97`

**Ferramenta:** CrackStation
**Tipo identificado:** SHA1
**Senha:** `password123`

![Hash](/CTFs/Crack%20The%20Hash/images/2º%20Hash.png)

---

## Hash 3 — SHA256
**Hash:** `1C8BFE8F801D79745C4631D09FFF36C82AA37FC4CCE4FC946683D7B336B63032`

**Ferramenta:** CrackStation
**Tipo identificado:** SHA256
**Senha:** `letmein`

![Hash](/CTFs/Crack%20The%20Hash/images/3º%20Hash.png)

---

## Hash 4 — bcrypt
**Hash:** `$2y$12$Dwt18Zj6pcyc3Dy1FWZ5ieeUznr71EeNkJkUlypTsgBX...8wsRom`

**Ferramenta:** Hashcat
**Modo Hashcat:** `-m 3200` (bcrypt $2*$, Blowfish (Unix))
**Wordlist:** `rockyou.txt`
**Senha:** `bleh`

Como bcrypt é um algoritmo lento e projetado para dificultar ataques de força bruta (custo configurável via fator de trabalho, aqui `$2y$12$`), o crack foi bem mais demorado que os hashes simples — o Hashcat precisou testar candidato a candidato contra o dicionário até encontrar o match, exibindo `Status: Cracked` ao final.

![Hash](/CTFs/Crack%20The%20Hash/images/4º%20Hash.jpeg)

---

## Hash 5 — MD4
**Hash:** `279412f945939ba78ce0758d3fd83daa`

**Ferramenta:** CrackStation
**Tipo identificado:** MD4
**Senha:** `Eternity22`

![Hash](/CTFs/Crack%20The%20Hash/images/5º%20Hash.jpeg)

---

## Hash 6 — SHA2-256
**Hash:** `f09edcb1fcefc6dfb23dc3505a882655ff77375ed8aa2d1c13f640fccc2d0c85`

**Ferramenta:** Hashcat
**Modo Hashcat:** `-m 1400` (SHA2-256)
**Wordlist:** `rockyou.txt`
**Senha:** `paule`

O modo `1400` foi confirmado comparando o formato do hash (64 caracteres hexadecimais) com o exemplo `SHA2-256` na página de referência do Hashcat.

![Hash](/CTFs/Crack%20The%20Hash/images/6º%20Hash.jpeg)

---

## Hash 7 — NTLM
**Hash:** `1DFECA0C002AE40B86l9ECF94819CC1B`

**Ferramenta:** CrackStation
**Tipo identificado:** NTLM
**Senha:** `n63uay81kcf41`

Hash típico de credenciais Windows (NTLM), quebrado diretamente pela lookup table do CrackStation.

![Hash](/CTFs/Crack%20The%20Hash/images/7º%20Hash.jpeg)

---

## Hash 8 — sha512crypt (Unix `$6$`)
**Hash:** `$6$aReallyHardSalt$6WKUtqzq.UQQmm0p/T7MPpNbGNnzXPMAXi4bJHl9be.cfi3/qxIf.h5qpS4l8qMhSrHVXgMpdj56xeKZAs02..waka99`

**Ferramenta:** Hashcat
**Modo Hashcat:** `-m 1800` (sha512crypt $6$, SHA512 (Unix))
**Wordlist:** `rockyou.txt`
**Senha:** `VALENCIA`

Hash salgado (`$6$aReallyHardSalt$...`) do formato usado no `/etc/shadow` de sistemas Linux. Levou aproximadamente 18 minutos de execução (Time.Estimated ~52 mins mostrado, mas encontrado antes), já que o `sha512crypt` também é propositalmente lento (múltiplas iterações internas).

![Hash](/CTFs/Crack%20The%20Hash/images/8°%20Hash.jpeg)

---

## Hash 9 — HMAC-SHA1 (key = $salt)
**Hash:** `e5d8870e5bdd2660cab8dbe07a942c8669e56d6:tryhackme`

**Ferramenta:** Hashcat
**Modo Hashcat:** `-m 160` (HMAC-SHA1 (key = $salt))
**Wordlist:** `rockyou.txt`
**Senha:** `481616481616`

Aqui o salt (`tryhackme`) vem concatenado ao hash após os dois pontos (`:`), formato característico dos modos HMAC do Hashcat, onde o salt é usado como chave (key) do HMAC.

![Hash](/CTFs/Crack%20The%20Hash/images/9°%20Hash.jpeg)

---

## Resumo Final

| # | Hash (tipo) | Ferramenta | Modo Hashcat | Senha |
|---|-------------|------------|--------------|-------|
| 1 | MD5 | CrackStation | — | `easy` |
| 2 | SHA1 | CrackStation | — | `password123` |
| 3 | SHA256 | CrackStation | — | `letmein` |
| 4 | bcrypt | Hashcat | `-m 3200` | `bleh` |
| 5 | MD4 | CrackStation | — | `Eternity22` |
| 6 | SHA2-256 | Hashcat | `-m 1400` | `paule` |
| 7 | NTLM | CrackStation | — | `n63uay81kcf41` |
| 8 | sha512crypt ($6$) | Hashcat | `-m 1800` | `VALENCIA` |
| 9 | HMAC-SHA1 (key=$salt) | Hashcat | `-m 160` | `481616481616` |

## Conclusões

- Hashes não salgados e amplamente conhecidos (MD5, SHA1, SHA256, MD4, NTLM) foram resolvidos quase instantaneamente por lookup tables online (CrackStation), sem gasto computacional local.
- Hashes salgados, com custo de iteração (bcrypt, sha512crypt) ou com estrutura de chave HMAC exigiram o uso do Hashcat com ataque de dicionário (`rockyou.txt`), e o tempo de cracking aumentou proporcionalmente à complexidade/custo do algoritmo.
- A identificação correta do **hash mode** foi essencial para o sucesso do ataque no Hashcat — o wiki oficial (*Example Hashes*) foi fundamental para comparar o formato do hash capturado com os exemplos documentados antes de escolher o modo (`-m`).
- Esta sala reforça a importância de **não usar algoritmos rápidos (MD5/SHA1/SHA256) sem salt** para armazenamento de senhas, e de preferir funções lentas e salgadas como bcrypt, scrypt ou sha512crypt para dificultar ataques de força bruta/dicionário.

---