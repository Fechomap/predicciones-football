"""Script para obtener el Chat ID de Telegram"""
import sys
import os
import requests

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.config import Config

def get_chat_id():
    """Obtiene el chat ID de Telegram"""

    if not Config.TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN no configurado en .env")
        return

    print("=" * 60)
    print("📱 OBTENER CHAT ID DE TELEGRAM")
    print("=" * 60)
    print()
    print("Pasos:")
    print("1. Abre Telegram")
    print("2. Busca tu bot y envíale un mensaje (cualquier texto)")
    print("3. Presiona ENTER aquí para obtener tu Chat ID")
    print()

    input("Presiona ENTER cuando hayas enviado un mensaje al bot...")

    # Hacer request a getUpdates
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getUpdates"

    try:
        response = requests.get(url)
        data = response.json()

        if not data.get("ok"):
            print(f"❌ Error de API: {data}")
            return

        updates = data.get("result", [])

        if not updates:
            print("❌ No se encontraron mensajes.")
            print("   Asegúrate de haber enviado un mensaje al bot primero.")
            return

        # Obtener el último mensaje
        last_update = updates[-1]
        message = last_update.get("message", {})
        chat = message.get("chat", {})
        chat_id = chat.get("id")

        if not chat_id:
            print("❌ No se pudo obtener el Chat ID")
            return

        print()
        print("=" * 60)
        print("✅ CHAT ID ENCONTRADO!")
        print("=" * 60)
        print()
        print(f"Tu Chat ID es: {chat_id}")
        print()
        print("Agrega esta línea a tu archivo .env:")
        print()
        print(f"TELEGRAM_CHAT_ID={chat_id}")
        print()
        print("=" * 60)

        # Mostrar info del chat
        print()
        print("Información del chat:")
        print(f"  - Tipo: {chat.get('type', 'N/A')}")
        print(f"  - Usuario: @{chat.get('username', 'N/A')}")
        print(f"  - Nombre: {chat.get('first_name', '')} {chat.get('last_name', '')}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    get_chat_id()
