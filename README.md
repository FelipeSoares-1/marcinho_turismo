# 🤖 Marcinho Tur - Agente de IA

Este repositório contém o código fonte do agente de atendimento da Marcinho Tur, integrado com WhatsApp e Instagram via Meta Graph API.

## 🚀 Como Rodar o Simulador (Recomendado para Demos)

Para testar a inteligência do bot sem depender do WhatsApp:

1.  Abra o terminal na pasta raiz do projeto.
2.  Execute o script de simulação:
    ```powershell
    .\.venv\Scripts\python.exe scripts/simulate_whatsapp.py
    ```
3.  Converse com o Marcinho diretamente no terminal!

## 📁 Estrutura do Projeto

- **`app/`**: Código principal da aplicação (Cérebro, Rotas, Serviços).
- **`scripts/`**: Scripts utilitários e de teste.
  - `simulate_whatsapp.py`: Chat local no terminal.
  - `test_whatsapp_send.py`: Teste de envio de mensagem real.
  - `start_tunnel.ps1`: Inicia servidor + Ngrok (para Webhook).
- **`.env`**: Credenciais e Tokens (Não compartilhe!).

## 🛠️ Comandos Úteis

**Iniciar Servidor + Ngrok (Para WhatsApp Real):**

```powershell
.\scripts\start_tunnel.ps1
```

**Testar Envio de Mensagem:**

```powershell
.\.venv\Scripts\python.exe scripts/test_whatsapp_send.py 5511999999999
```
