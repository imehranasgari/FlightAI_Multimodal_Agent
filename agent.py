import os
import json
import random
import requests
from io import BytesIO
from PIL import Image
from gtts import gTTS
from openai import OpenAI
from dotenv import load_dotenv
from database import get_ticket_price

os.environ["NO_PROXY"] = "localhost,127.0.0.1"
load_dotenv(override=True)

# تنظیمات کلاینت‌ها
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"

def get_client_and_model(model_choice: str):
    """بر اساس انتخاب کاربر، کلاینت و مدل مرتبط را برمی‌گرداند"""
    if model_choice == "Gemini (Cloud)":
        client = OpenAI(api_key=GOOGLE_API_KEY, base_url=GEMINI_BASE_URL)
        return client, "gemini-2.5-flash"
    else:  # حالت پیش‌فرض Ollama
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        return client, "llama3.2"

SYSTEM_PROMPT = """You are a helpful customer support assistant for FlightAI.
Always use the get_ticket_price tool to check flight prices. Never invent prices.
Give concise, courteous answers (maximum 2 sentences).
"""

price_function_spec = {
    "name": "get_ticket_price",
    "description": "Get the return ticket price for a destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The destination city name in English (e.g. london, paris, tokyo)."
            }
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}
TOOLS = [{"type": "function", "function": price_function_spec}]

def generate_voice(text: str) -> bytes:
    try:
        tts = gTTS(text=text, lang="en", tld="co.uk")
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        print(f"[TTS Error] {e}")
        return None

def generate_image(city: str) -> Image.Image:
    if not city or city.lower() in ["unknown", "destination city"]:
        return None
    prompt = f"Vibrant pop-art travel poster of {city}, iconic landmarks, beautiful typography, 4k"
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=768&nologo=true&seed={seed}&model=flux"
    try:
        resp = requests.get(url, timeout=25)
        if resp.status_code == 200:
            return Image.open(BytesIO(resp.content))
    except Exception as e:
        print(f"[Image Error] {e}")
    return None

def handle_tool_calls(tool_calls):
    responses = []
    cities_queried = []
    for tool_call in tool_calls:
        if tool_call.function.name == "get_ticket_price":
            try:
                args = json.loads(tool_call.function.arguments)
                city = args.get("destination_city", "")
                if city:
                    cities_queried.append(city)
                content = get_ticket_price(city)
            except Exception as e:
                content = f"Error executing tool: {e}"
            responses.append({
                "role": "tool",
                "content": content,
                "tool_call_id": tool_call.id
            })
    return responses, cities_queried

def run_agent_chat(history, model_choice: str = "Gemini (Cloud)"):
    """اجرای درخواست به همراه انتخاب پویا مدل"""
    client, model_name = get_client_and_model(model_choice)
    
    formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        formatted_messages.append({"role": msg["role"], "content": msg["content"]})

    cities_queried = []
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=formatted_messages,
            tools=TOOLS
        )

        while response.choices[0].finish_reason == "tool_calls":
            tool_msg = response.choices[0].message
            tool_responses, detected_cities = handle_tool_calls(tool_msg.tool_calls)
            cities_queried.extend(detected_cities)

            # تبدیل استاندارد پیام کستی مدل به دیکشنری
            formatted_messages.append(tool_msg.model_dump())
            formatted_messages.extend(tool_responses)

            response = client.chat.completions.create(
                model=model_name,
                messages=formatted_messages,
                tools=TOOLS
            )

        reply = response.choices[0].message.content or "How may I help you with your flight booking today?"
    except Exception as e:
        reply = f"Error contacting AI service ({model_name}): {e}"

    history.append({"role": "assistant", "content": reply})
    audio = generate_voice(reply)
    image = generate_image(cities_queried[-1]) if cities_queried else None

    return history, audio, image