# Script para iniciar Servidor + Ngrok

# 1. Inicia o Servidor Python (Uvicorn) em uma NOVA janela
Write-Host "Iniciando servidor Marcinho Tur (Janela Separada)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"

# 2. Aguarda um pouco para o servidor subir
Start-Sleep -Seconds 3

# 3. Inicia o Ngrok na janela ATUAL (para você ver o link)
Write-Host "Iniciando Ngrok na porta 8000..." -ForegroundColor Cyan
Write-Host "⚠️ COPIE O LINK 'Forwarding' (https://....ngrok-free.app) QUE VAI APARECER ABAIXO!" -ForegroundColor Yellow
Write-Host "⚠️ Cole esse link no painel da Meta (Webhook)." -ForegroundColor Yellow
Write-Host ""

ngrok http 8000
