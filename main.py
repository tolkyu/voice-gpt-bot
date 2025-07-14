import discord
from openai import OpenAI
import speech_recognition as sr
import datetime



DISCORD_TOKEN = 'YOUR TOKEN'
OPENAI_API_KEY = 'YOUR TOKEN'

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)

client_openai = OpenAI(api_key=OPENAI_API_KEY)

def save_audio(audio, filename="recorded.wav"):
    with open(filename, "wb") as f:
        f.write(audio.get_wav_data())

def log_event(text):
    with open("bot_log.log", "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {text}\n")
        
def record_and_transcribe():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙 Слухаю...")
        audio = r.listen(source)

    save_audio(audio)
    log_event("Аудіо записано у recorded.wav")

    try:
        text = r.recognize_google(audio, language='uk-UA')
        print("📄 Розпізнано:", text)

        with open("questions.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()} - {text}\n")

        log_event(f"Розпізнано текст: {text}")
        return text
    except Exception as e:
        log_event(f"Помилка розпізнавання: {e}")
        return "Не вдалося розпізнати"


def ask_gpt(prompt):
    try:
        response = client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        log_event(f"GPT відповів: {answer}")
        return answer
    except Exception as e:
        log_event(f"Помилка OpenAI API: {e}")
        if "RateLimit" in str(e) or "quota" in str(e).lower():
            return "Вибач, ліміт використання AI вичерпано. Спробуй пізніше."
        else:
            return "Сталася помилка. Спробуй пізніше."

@client.event
async def on_ready():
    print(f'🤖 Бот запущено як {client.user}')
    log_event("Бот успішно запущено")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!join'):
        if message.author.voice:
            channel = message.author.voice.channel
            if message.guild.voice_client is None:
                await channel.connect()
                await message.channel.send("✅ Підключено до голосового каналу")
                log_event("Підключено до голосового каналу")
            else:
                await message.channel.send("🟡 Я вже в голосовому каналі")
        else:
            await message.channel.send("❌ Ви не в голосовому каналі")

    if message.content.startswith('!ask'):
        await message.channel.send("🎤 Слухаю твоє питання з мікрофону комп’ютера...")
        question = record_and_transcribe()
        await message.channel.send(f"🧠 Ти сказав: `{question}`")

        answer = ask_gpt(question)
        await message.channel.send(f"🤖 GPT каже: `{answer}`")

    if message.content.startswith('!leave'):
        if message.guild.voice_client:
            await message.guild.voice_client.disconnect()
            await message.channel.send("👋 Відключено")
            log_event("Відключено від голосового каналу")
        else:
            await message.channel.send("❌ Я не в голосовому каналі")

client.run(DISCORD_TOKEN)
