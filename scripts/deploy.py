import os
import subprocess
import sys

def load_env(env_path=".env"):
    env_vars = {}
    if not os.path.exists(env_path):
        print(f"❌ Arquivo {env_path} não encontrado!")
        sys.exit(1)
        
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def deploy():
    print("🚀 Iniciando deploy para Google Cloud Run via Python...")
    
    env_vars = load_env()
    env_string = ",".join([f"{k}={v}" for k, v in env_vars.items()])
    
    cmd = [
        "gcloud", "run", "deploy", "marcinho-tur-api",
        "--project", "marcinho-tur-ai",
        "--source", ".",
        "--platform", "managed",
        "--region", "us-central1",
        "--allow-unauthenticated",
        "--quiet",
        "--no-cpu-throttling",
        "--set-env-vars", env_string
    ]
    
    try:
        # Run deploy
        subprocess.check_call(cmd, shell=True)
        print("\n✅ Deploy concluído com sucesso!")
        
        # Get URL
        url_cmd = [
            "gcloud", "run", "services", "describe", "marcinho-tur-api",
            "--platform", "managed",
            "--region", "us-central1",
            "--format", "value(status.url)"
        ]
        url = subprocess.check_output(url_cmd, shell=True).decode("utf-8").strip()
        
        print("\n" + "-"*50)
        print("📍 ACESSO RÁPIDO:")
        print(f"🔗 Painel Admin: {url}/admin")
        print(f"🔗 Webhook URL:  {url}/webhook")
        print("-"*50 + "\n")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro no deploy: {e}")
        sys.exit(1)

if __name__ == "__main__":
    deploy()
