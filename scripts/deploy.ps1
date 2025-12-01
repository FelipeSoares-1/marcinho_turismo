# Script de Deploy para Google Cloud Run
# Lê o arquivo .env e faz o deploy

$envFile = ".env"
if (-not (Test-Path $envFile)) {
    Write-Error "Arquivo .env não encontrado!"
    exit 1
}

# Lê as variáveis do .env
$envVars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        if (-not [string]::IsNullOrWhiteSpace($key)) {
            $envVars[$key] = $value
        }
    }
}

# Constrói a string de variáveis de ambiente para o gcloud
$envString = $envVars.Keys | ForEach-Object { "$_=$($envVars[$_])" }
$envString = $envString -join ","

Write-Host "Iniciando deploy para o Google Cloud Run..." -ForegroundColor Green

# Executa o deploy
gcloud run deploy marcinho-tur-api `
    --project marcinho-tur-ai `
    --source . `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --quiet `
    --no-cpu-throttling `
    --set-env-vars $envString

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deploy concluído com sucesso!" -ForegroundColor Green
    
    # Obtém a URL do serviço
    $serviceUrl = gcloud run services describe marcinho-tur-api --platform managed --region us-central1 --format 'value(status.url)'
    
    Write-Host ""
    Write-Host "--------------------------------------------------" -ForegroundColor Cyan
    Write-Host "📍 ACESSO RÁPIDO:" -ForegroundColor Cyan
    Write-Host "🔗 Painel Admin: $serviceUrl/admin" -ForegroundColor Yellow
    Write-Host "🔗 Webhook URL:  $serviceUrl/webhook" -ForegroundColor Yellow
    Write-Host "--------------------------------------------------" -ForegroundColor Cyan
    Write-Host ""
}
else {
    Write-Host "Erro no deploy." -ForegroundColor Red
}
