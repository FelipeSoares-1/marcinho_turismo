from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.brain import MEMORY
import os

router = APIRouter(prefix="/admin", tags=["admin"])

# Simple in-memory pause state (in production, use Redis/Database)
PAUSED_USERS = set()

# Setup templates (we'll create a simple HTML string for now to avoid complexity)
def get_admin_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Marcinho Tur - Painel de Controle</title>
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .user-card { border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
            .paused { background-color: #fff3cd; border-color: #ffeeba; }
            button { padding: 5px 10px; cursor: pointer; }
            .btn-pause { background-color: #dc3545; color: white; border: none; }
            .btn-resume { background-color: #28a745; color: white; border: none; }
        </style>
    </head>
    <body>
        <h1>🤖 Painel de Intervenção Humana</h1>
        <div id="users-list">Carregando...</div>

        <script>
            async function loadUsers() {
                const response = await fetch('/admin/api/users');
                const users = await response.json();
                const container = document.getElementById('users-list');
                container.innerHTML = '';

                if (users.length === 0) {
                    container.innerHTML = '<p>Nenhuma conversa ativa.</p>';
                    return;
                }

                users.forEach(user => {
                    const div = document.createElement('div');
                    div.className = 'user-card ' + (user.is_paused ? 'paused' : '');
                    div.innerHTML = `
                        <h3>${user.user_id} <small>(${user.channel})</small></h3>
                        <p>Status: <strong>${user.is_paused ? '🔴 PAUSADO (Humano no comando)' : '🟢 ATIVO (IA respondendo)'}</strong></p>
                        <button class="${user.is_paused ? 'btn-resume' : 'btn-pause'}" onclick="togglePause('${user.user_id}', ${!user.is_paused})">
                            ${user.is_paused ? 'RETOMAR IA' : 'PAUSAR IA'}
                        </button>
                    `;
                    container.appendChild(div);
                });
            }

            async function togglePause(userId, pause) {
                await fetch(`/admin/api/pause?user_id=${userId}&pause=${pause}`, { method: 'POST' });
                loadUsers();
            }

            loadUsers();
            setInterval(loadUsers, 5000); // Auto-refresh every 5s
        </script>
    </body>
    </html>
    """

@router.get("/", response_class=HTMLResponse)
async def admin_panel():
    return get_admin_html()

@router.get("/api/users")
async def list_users():
    users_list = []
    # MEMORY keys are like "whatsapp:551199999999"
    for key in MEMORY.keys():
        parts = key.split(":")
        if len(parts) == 2:
            channel, user_id = parts
            is_paused = user_id in PAUSED_USERS
            users_list.append({
                "user_id": user_id,
                "channel": channel,
                "is_paused": is_paused
            })
    return users_list

@router.post("/api/pause")
async def toggle_pause(user_id: str, pause: bool):
    if pause:
        PAUSED_USERS.add(user_id)
    else:
        if user_id in PAUSED_USERS:
            PAUSED_USERS.remove(user_id)
    return {"status": "ok", "user_id": user_id, "paused": pause}

def is_user_paused(user_id: str) -> bool:
    return user_id in PAUSED_USERS
