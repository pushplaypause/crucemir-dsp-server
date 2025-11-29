from openai import OpenAI
client = OpenAI()

def songwriting_helper(style: str):
    prompt = f"""
    Create a professional songwriting blueprint in a {style} style:
    - Song structure (Intro, Verse, Chorus, Bridge)
    - Hook lines
    - Verse ideas
    - Emotional direction
    """

    res = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "structure": res.choices[0].message["content"]
    }
