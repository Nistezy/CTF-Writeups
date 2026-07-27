# 🕵️ OhSINT — CTF Writeup
### TryHackMe | OSINT / Reconhecimento Passivo | Metadados EXIF · Reutilização de Username · Vazamento de Wi-Fi e Credenciais

---

| **Analista**              | Mauricio Robert                                                                    |
|----------------------------|-------------------------------------------------------------------------------------|
| **Organização**            | Faculdade Impacta                                                                   |
| **Data do Relatório**      | 23/07/2026                                                                          |
| **Data da Investigação**   | 23/07/2026 · 00:24 (GMT-3)                                                          |
| **Alvo**                   | Imagem fornecida (`WindowsXP_1551719014755.jpg`) — TryHackMe · OhSINT               |
| **Classificação**          | CONFIDENCIAL                                                                        |
| **Ferramentas**            | ExifTool Online · Google Search · GitHub · WiGLE · Have I Been Pwned              |
| **Plataforma**             | TryHackMe — OSINT / Reconhecimento Passivo                                         |

---

## 🔍 Resumo Executivo

Este relatório documenta uma investigação de **OSINT (Open Source Intelligence)** conduzida a partir de uma **única imagem fornecida** como ponto de partida (TryHackMe — OhSINT), em aproximadamente **31 minutos**. A extração de metadados EXIF da imagem revelou o nome de usuário do autor e coordenadas GPS precisas. A pesquisa pelo username levou à descoberta de um repositório público no GitHub, um endereço de e-mail e um blog pessoal — cujo código-fonte escondia uma senha em texto branco. Uma postagem em rede social do mesmo usuário expôs o BSSID de sua rede Wi-Fi doméstica, permitindo geolocalizá-la publicamente. Por fim, o e-mail identificado foi confirmado em uma base de vazamentos de dados conhecida. **Nenhuma técnica ativa ou intrusiva foi utilizada** — toda a cadeia de descobertas dependeu exclusivamente de **fontes abertas e más práticas de higiene de informação** por parte do indivíduo investigado.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                  | Versão | Finalidade                                                                     |
|-------------------------------|--------|---------------------------------------------------------------------------------|
| **ExifTool Online**          | 11.27  | Extração de metadados EXIF/XMP da imagem fornecida (GPS, autor, hashes)         |
| **Google Search**            | -      | Pesquisa de nome de usuário, e-mail e BSSID                                     |
| **GitHub**                   | -      | Localização de repositório público e informações de perfil do autor            |
| **View-Source (navegador)**  | -      | Inspeção do código-fonte HTML do blog pessoal                                   |
| **WiGLE**                    | -      | Geolocalização do BSSID da rede Wi-Fi (SSID e cidade)                           |
| **Have I Been Pwned**        | -      | Verificação de vazamentos de dados associados ao e-mail identificado           |

---

## 📋 Fases de Investigação

### FASE 1 — Análise Forense de Metadados EXIF

> **00:24 GMT-3 · ExifTool Online**

A imagem fornecida como ponto de partida do desafio (`WindowsXP_1551719014755.jpg`) foi submetida a uma ferramenta de extração de metadados. A análise do bloco **XMP** revelou:

```
MD5:            49e91584068dd192c849496cba8e2883
SHA1:            0821d0cc219874ca0dcece0d280fdb6dc3f34856
SHA256:          288d646784d42d9c9d113472b4553d441ba91ce2446da5374a9fa8143678f38f

XMP (4 properties)
Copyright:       OWoodflint
GPSLatitude:     54 deg 17' 41.27" N
GPSLongitude:    2 deg 15' 1.33" W
XMPToolkit:      Image::ExifTool 11.27
```

O campo **Copyright** — normalmente preenchido automaticamente por softwares de edição ou pelo próprio autor — expôs diretamente o **nome de usuário**, enquanto as coordenadas GPS embutidas revelaram a **localização geográfica precisa** associada ao dispositivo que capturou a imagem.

> 🚩 **Username identificado (EXIF/Copyright): `OWoodflint`**
> 🚩 **Coordenadas GPS (EXIF): `54°17'41.27" N, 2°15'1.33" W`**

---

### FASE 2 — OSINT de Username: GitHub, E-mail e Localização

> **~00:30 GMT-3 · Google Search + GitHub**

Com o username `OWoodflint` em mãos, a pesquisa foi direcionada a plataformas públicas que costumam reutilizar o mesmo identificador. A busca no GitHub localizou o repositório público **`OWoodfl1nt/people_finder`**, cujo README continha:

```markdown
# people_finder

Hi all, I am from London, I like taking photos and open source projects.

Follow me on twitter: @OWoodflint

This project is a new social network for taking photos in your home town.

Project starting soon! Email me if you want to help out: OWoodflint@gmail.com

https://oliverwoodflint.wordpress.com/
```

O README revelou, em uma única página, a **cidade de origem** (Londres), o **e-mail de contato** e um link para o **blog pessoal** do autor — o próximo alvo da investigação.

> 🚩 **E-mail identificado: `OWoodflint@gmail.com`**

---

### FASE 3 — Blog Pessoal: Localização Declarada e Senha Oculta

> **~00:36 GMT-3 · Browser + View-Source**

O blog pessoal (**Oliver Woodflint Blog** — *"Photos you can relate to"*) continha uma única postagem, intitulada **"Hey"**:

```
Im in New York right now, so I will update this site right away with new photos!
```

Essa declaração de localização (Nova York) **contrasta** com a cidade real informada no GitHub (Londres) e com as coordenadas GPS extraídas do EXIF — funcionando como uma pista de desvio (*red herring*) dentro do desafio.

A inspeção do **código-fonte HTML** da página (`view-source:`), no entanto, revelou um elemento oculto: um parágrafo estilizado com **texto branco sobre fundo branco** (`color:#ffffff`), invisível na renderização normal, mas plenamente legível no código-fonte:

```html
<p style="color:#ffffff;" class="has-text-color wp-block-paragraph">pennYDr0pper!</p>
```

> 🚩 **Senha oculta encontrada (blog): `pennYDr0pper!`**

---

### FASE 4 — Rede Social (X/Twitter): Vazamento de BSSID Wi-Fi

> **~00:45 GMT-3 · Perfil @OWoodflint no X**

A pesquisa pelo mesmo identificador em redes sociais localizou um perfil no **X** (antigo Twitter), com nome de exibição `0x0000000000000000000000` e handle **@OWoodflint**. Entre as publicações do perfil, uma postagem de março de 2019 expôs, de forma displicente, o BSSID da rede Wi-Fi doméstica do usuário:

```
@OWoodflint · Mar 3, 2019
From my house I can get free wifi ;D

Bssid: B4:5D:50:AA:86:41 - Go nuts!
```

Essa informação, normalmente inofensiva à primeira vista, permite a **geolocalização física aproximada** de uma rede sem fio através de bancos de dados públicos de wardriving.

---

### FASE 5 — Geolocalização do BSSID (WiGLE / Google)

> **~00:50 GMT-3 · WiGLE.net**

**Consulta:**
```
B4:5D:50:AA:86:41
```

A pesquisa do BSSID em bancos de dados de geolocalização de redes sem fio confirmou que o endereço MAC pertence a uma rede identificada pelo SSID **`UnileverWiFi`**, localizada na região **central de Londres, Reino Unido** — corroborando a cidade real informada no GitHub e contrastando com a localização de viagem mencionada no blog (Nova York).

> 🚩 **SSID / Localização da rede Wi-Fi: `UnileverWiFi` — Central London, UK**

---

### FASE 6 — Verificação de Vazamento de Dados (Have I Been Pwned)

> **~00:55 GMT-3 · haveibeenpwned.com**

**Consulta:**
```
OWoodflint@gmail.com
```

A verificação do e-mail identificado confirmou **1 vazamento de dados** associado ao endereço:

```
1 Data Breach — Gravatar (Outubro/2020)

Em outubro de 2020, uma técnica de scraping em massa expôs 167 milhões de
nomes, usernames e hashes MD5 de e-mails associados a avatares do Gravatar.
114 milhões desses hashes foram posteriormente quebrados e distribuídos,
revelando os e-mails originais.

Compromised data: Email addresses · Names · Usernames
```

> 🚩 **Vazamento de dados confirmado: `Gravatar` — Outubro/2020**

---

## ⛓ Linha do Tempo da Investigação

```
[00:24 GMT-3] FASE 1 — METADADOS EXIF DA IMAGEM (ExifTool Online)
    Copyright → username "OWoodflint"
    GPS → 54°17'41.27" N, 2°15'1.33" W
    ↓
[00:30 GMT-3] FASE 2 — OSINT DE USERNAME (Google + GitHub)
    Repositório OWoodfl1nt/people_finder
    Cidade: London · E-mail: OWoodflint@gmail.com
    Blog pessoal localizado: oliverwoodflint.wordpress.com
    ↓
[00:36 GMT-3] FASE 3 — BLOG PESSOAL (Browser + View-Source)
    Postagem "Hey" → localização declarada: New York (red herring)
    Código-fonte HTML → senha oculta (texto branco): pennYDr0pper!
    ↓
[00:45 GMT-3] FASE 4 — REDE SOCIAL (X — @OWoodflint)
    Postagem expõe BSSID da rede Wi-Fi doméstica: B4:5D:50:AA:86:41
    ↓
[00:50 GMT-3] FASE 5 — GEOLOCALIZAÇÃO DO BSSID (WiGLE/Google)
    SSID: UnileverWiFi
    Localização: Central London, UK
    ↓
[00:55 GMT-3] FASE 6 — VERIFICAÇÃO DE VAZAMENTO (Have I Been Pwned)
    OWoodflint@gmail.com → 1 vazamento confirmado (Gravatar, 2020)
    ↓
[00:55 GMT-3] INVESTIGAÇÃO CONCLUÍDA — Identidade digital reconstruída
    Duração total: ~31 minutos
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Metadados EXIF | ExifTool Online | Username `OWoodflint`; GPS `54°17'41.27"N, 2°15'1.33"W` |
| OSINT de Username | Google + GitHub | E-mail `OWoodflint@gmail.com`; cidade `London`; blog pessoal |
| Blog Pessoal | Browser + View-Source | Localização declarada `New York` (red herring); senha oculta `pennYDr0pper!` |
| Rede Social | Perfil @OWoodflint (X) | BSSID Wi-Fi doméstico exposto: `B4:5D:50:AA:86:41` |
| Geolocalização | WiGLE / Google | SSID `UnileverWiFi` — Central London |
| Vazamento de Dados | Have I Been Pwned | Gravatar (2020) — e-mail, nome e username comprometidos |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Ponto de partida | `WindowsXP_1551719014755.jpg` | Imagem fornecida — metadados EXIF/XMP não higienizados |
| Username | `OWoodflint` | Campo Copyright dos metadados EXIF |
| Coordenadas GPS | `54°17'41.27" N, 2°15'1.33" W` | Embutidas na imagem original |
| E-mail | `OWoodflint@gmail.com` | README público do repositório GitHub `people_finder` |
| Repositório GitHub | `OWoodfl1nt/people_finder` | Biografia, e-mail e link do blog pessoal |
| Blog pessoal | `oliverwoodflint.wordpress.com` | Localização declarada (desvio) e senha oculta no HTML |
| Senha exposta | `pennYDr0pper!` | Texto branco oculto no código-fonte do blog |
| Perfil em rede social | `@OWoodflint` (X) | Postagem expõe BSSID da rede Wi-Fi doméstica |
| BSSID exposto | `B4:5D:50:AA:86:41` | Publicado publicamente pelo próprio usuário |
| SSID / Localização real | `UnileverWiFi` — Central London | Geolocalizado via WiGLE a partir do BSSID |
| Vazamento de dados | Gravatar (Out/2020) | E-mail, nome e username comprometidos e distribuídos publicamente |
| Técnica (MITRE ATT&CK) | `T1593` | Search Open Websites/Domains |
| Técnica (MITRE ATT&CK) | `T1589` | Gather Victim Identity Information |

---

## ✅ Resumo dos Achados

| # | Achado | Valor |
|---|--------|-------|
| 🚩 Username | EXIF (Copyright) | `OWoodflint` |
| 🚩 GPS (EXIF) | Coordenadas da imagem | `54°17'41.27" N, 2°15'1.33" W` |
| 🚩 E-mail | GitHub README | `OWoodflint@gmail.com` |
| 🚩 Senha oculta | Blog (view-source) | `pennYDr0pper!` |
| 🚩 SSID / Localização Wi-Fi | WiGLE (via BSSID `B4:5D:50:AA:86:41`) | `UnileverWiFi` — Central London |
| 🚩 Vazamento de dados | Have I Been Pwned | Gravatar — Outubro/2020 |

---

## 🛡 Recomendações

- **Remover metadados EXIF/XMP** (GPS, autor, dispositivo) de imagens antes de publicá-las em redes sociais, blogs ou repositórios públicos
- **Evitar reutilizar o mesmo nome de usuário** em múltiplas plataformas quando se deseja manter anonimato ou separação entre identidades pessoais e profissionais
- **Nunca ocultar senhas ou informações sensíveis no código-fonte** de páginas web (texto branco, comentários HTML, atributos ocultos) — o código-fonte é sempre publicamente acessível
- **Nunca publicar o BSSID, SSID ou qualquer identificador de redes Wi-Fi domésticas** em redes sociais ou plataformas públicas
- **Utilizar senhas únicas por serviço** e habilitar autenticação multifator, especialmente após a confirmação de vazamentos de dados associados ao e-mail
- **Monitorar periodicamente o e-mail pessoal** em serviços como Have I Been Pwned para identificar novos vazamentos de dados
- **Revisar a pegada digital pessoal (digital footprint)** periodicamente, buscando pelo próprio nome, username e e-mail em motores de busca

---

## 📚 Referências

- [TryHackMe — OhSINT](https://tryhackme.com/room/ohsint)
- [ExifTool by Phil Harvey](https://exiftool.org)
- [WiGLE: Wireless Network Mapping](https://wigle.net)
- [Have I Been Pwned](https://haveibeenpwned.com)
- [MITRE ATT&CK T1593 — Search Open Websites/Domains](https://attack.mitre.org/techniques/T1593/)
- [MITRE ATT&CK T1589 — Gather Victim Identity Information](https://attack.mitre.org/techniques/T1589/)

---

*Writeup elaborado por Mauricio Robert — Faculdade Impacta | Julho 2026*
