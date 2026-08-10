
import os
import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")

chat_id = None
jogos_conhecidos = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "⚽ Gol Mento ativado!\n\n"
        "Vou acompanhar os jogos ao vivo e avisar quando sair gol.\n\n"
        "Comandos:\n"
        "/id - mostra seu ID\n"
        "/status - verifica se o bot está funcionando"
    )


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Seu Chat ID é: {update.effective_chat.id}"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 Gol Mento está funcionando!")


def buscar_jogos():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": API_KEY
    }
    params = {
        "live": "all"
    }

    resposta = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    if resposta.status_code != 200:
        return []

    return resposta.json().get("response", [])


async def verificar_gols(context: ContextTypes.DEFAULT_TYPE):
    global jogos_conhecidos

    if not chat_id or not API_KEY:
        return

    try:
        jogos = buscar_jogos()

        for jogo in jogos:
            fixture_id = jogo["fixture"]["id"]

            casa = jogo["teams"]["home"]["name"]
            visitante = jogo["teams"]["away"]["name"]

            gols_casa = jogo["goals"]["home"] or 0
            gols_visitante = jogo["goals"]["away"] or 0

            placar = f"{gols_casa}-{gols_visitante}"
            estado = jogo["fixture"]["status"]["short"]

            chave = f"{fixture_id}:{placar}"

            if chave not in jogos_conhecidos:
                jogos_conhecidos.add(chave)

                if gols_casa > 0 or gols_visitante > 0:
                    mensagem = (
                        "🚨⚽ GOL!\n\n"
                        f"🏠 {casa}\n"
                        f"✈️ {visitante}\n\n"
                        f"📊 Placar: {placar}\n"
                        f"⏱️ Status: {estado}\n"
                    )

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=mensagem
                    )

    except Exception as erro:
        print("Erro:", erro)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("status", status))

    app.job_queue.run_repeating(
        verificar_gols,
        interval=60,
        first=10
    )

    print("Gol Mento iniciado!")
    app.run_polling()


if __name__ == "__main__":
    main()
