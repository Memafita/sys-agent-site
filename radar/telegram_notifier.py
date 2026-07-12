"""Notificador Telegram para o Radar de Mercado.

Envia um resumo legivel (markdown) para o seu chat do Telegram, de forma
que o seu iPhone funcione como "controle remoto" recebendo os alertas.

Como configurar (uma unica vez, pelo celular mesmo):
  1. Abra o @BotFather no Telegram e mande /newuser -> ele devolve um TOKEN.
  2. Mande qualquer mensagem para o seu bot novo.
  3. Acesse https://api.telegram.org/bot<TOKEN>/getUpdates e copie o "chat"."id".
  4. Preencha config.json com o token e o chat_id.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests


def carregar_config(caminho: str = "config.json") -> dict:
    p = Path(caminho)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def enviar(texto: str, config: dict | None = None, caminho_config: str = "config.json") -> bool:
    config = config or carregar_config(caminho_config)
    token = config.get("telegram_bot_token", "").strip()
    chat_id = str(config.get("telegram_chat_id", "")).strip()
    if not token or "COLE_AQUI" in token or not chat_id:
        print("[telegram] config.json sem token/chat_id valido -> pulando envio.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": texto,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        return r.status_code == 200
    except requests.RequestException as e:
        print(f"[telegram] erro: {e}")
        return False
