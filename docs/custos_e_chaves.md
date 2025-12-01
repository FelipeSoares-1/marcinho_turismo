# Guia de Custos e Configuração de APIs

Este documento detalha como obter as chaves necessárias para o projeto e uma estimativa de custos mensais para manter o **Marcinho Tur AI** no ar.

---

## 1. Google Gemini (Inteligência e Áudio)

Responsável pelo "cérebro" do bot (respostas de texto) e pela "audição" (transcrição de áudio).

### Como conseguir a chave (API Key):

1. Acesse o **[Google AI Studio](https://aistudio.google.com/)**.
2. Faça login com sua conta Google.
3. Clique em **"Get API key"** no menu lateral esquerdo.
4. Clique em **"Create API key"**.
5. Copie a chave gerada (começa com `AIza...`).
6. Coloque no seu arquivo `.env` como `GOOGLE_API_KEY`.

### Custos (Estimativa):

O modelo que estamos usando é o **Gemini 2.0 Flash** (ou 1.5 Flash).

- **Plano Gratuito:** O Google oferece um plano gratuito generoso (atualmente até 15 requisições por minuto, 1 milhão de tokens por minuto).
  - _Para uma agência pequena/média, o plano gratuito costuma ser suficiente._
- **Plano Pago (Pay-as-you-go):** Se exceder o gratuito.
  - Entrada (Texto/Áudio): ~$0.075 (aprox. R$ 0,45) por 1 milhão de tokens.
  - Saída (Resposta): ~$0.30 (aprox. R$ 1,80) por 1 milhão de tokens.
  - **Custo Realista:** Provavelmente **R$ 0,00** nos primeiros meses.

---

## 2. Meta / WhatsApp Business API

Responsável por enviar e receber mensagens no WhatsApp.

### Como conseguir o Token e ID:

1. Acesse o **[Meta for Developers](https://developers.facebook.com/)**.
2. Crie um aplicativo do tipo **"Empresa" (Business)**.
3. Adicione o produto **"WhatsApp"** ao app.
4. No menu lateral "WhatsApp" > "Configuração da API":
   - Copie o **Identificador do número de telefone** (`WHATSAPP_PHONE_NUMBER_ID`).
   - Gere um **Token de Acesso Permanente** (em "Usuários do Sistema" no Business Manager) ou use o temporário para testes.
5. Coloque no `.env` como `WHATSAPP_API_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`.

### Custos (Estimativa):

A Meta cobra por **conversa** (janela de 24h), não por mensagem.

- **Conversas de Serviço (iniciadas pelo usuário):**
  - As primeiras **1.000 conversas por mês são GRATUITAS**.
  - Após 1.000: Aprox. $0.03 (R$ 0,15 a R$ 0,20) por conversa de 24h.
- **Conversas de Marketing (iniciadas pela empresa):**
  - Não tem franquia gratuita. Custa aprox. $0.06 (R$ 0,35) por conversa.
- **Custo Realista:** Se você tiver menos de 1.000 clientes ativos chamando por mês, o custo será **R$ 0,00**.

---

## 3. Google Cloud Run (Hospedagem)

Onde o código do robô fica rodando 24h por dia.

### Configuração:

Já configuramos o deploy via script. Você precisa ter uma conta no **Google Cloud Platform (GCP)** com faturamento ativado (cartão de crédito).

### Custos (Estimativa):

O Cloud Run cobra apenas quando o código está processando uma requisição.

- **Plano Gratuito:** 2 milhões de requisições mensais gratuitas.
- **Custo Realista:** Para um bot de WhatsApp, é muito difícil estourar o plano gratuito do Cloud Run.
- **Atenção:** Pode haver custos residuais de "Artifact Registry" (armazenar a imagem do container), geralmente centavos ou poucos reais (R$ 1,00 - R$ 5,00/mês).

---

## Resumo Final (Custo Mensal Estimado)

| Item                       | Pequena Escala (< 1.000 clientes/mês) | Média Escala (> 1.000 clientes/mês) |
| :------------------------- | :------------------------------------ | :---------------------------------- |
| **Inteligência (Gemini)**  | R$ 0,00 (Free Tier)                   | R$ 10,00 - R$ 50,00                 |
| **WhatsApp (Meta)**        | R$ 0,00 (1.000 grátis)                | R$ 0,20 por cliente extra           |
| **Hospedagem (Cloud Run)** | R$ 0,00 - R$ 5,00                     | R$ 5,00 - R$ 20,00                  |
| **TOTAL ESTIMADO**         | **R$ 0,00 a R$ 5,00**                 | **Variável**                        |

**Conclusão:** Para começar, o custo é praticamente zero. Você só começará a pagar valores significativos se o volume de atendimentos explodir (o que seria um ótimo problema!).
