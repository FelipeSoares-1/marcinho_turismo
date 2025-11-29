from fastapi import FastAPI
from app.routes import webhook

app = FastAPI(title="Marcinho Tur AI Agent Backend")

# Incluir rotas
app.include_router(webhook.router)
from app.routes import admin
app.include_router(admin.router)

@app.get("/")
async def root():
    return {"message": "Marcinho Tur AI Backend is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Reload trigger 2
