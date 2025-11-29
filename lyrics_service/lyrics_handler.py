from openai import OpenAI
client = OpenAI()

def generate_lyrics(style: str, emotion: str):
    prompt = f"Write complete song lyrics in a {style} style. Emotion: {emotion}."

    res = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}]
    )

    lyrics = res.choices[0].message["content"]

    return {
        "lyrics": lyrics
    }
