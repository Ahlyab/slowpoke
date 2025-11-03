from openai import OpenAI
# access the api key from the environment variable
api_key = os.getenv("GEMINI_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def query(prompt: str, context: list[dict[str, str]], model: str = "gemini-2.5-flash", system_prompt: str = "You are a helpful assistant.", reasoning_effort: str = "low") -> str:
    return client.chat.completions.create(
        model=model,
        messages=context + [{"role": "user", "content": prompt}],
        system=system_prompt,
        reasoning_effort=reasoning_effort
    )
