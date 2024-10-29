import json
import dotenv
import os
dotenv.load_dotenv()       
import textwrap
JSON_RESPONSE_PROMPT_TEMPLATE = """\
{system_prompt}
Output in the following json template:
{output_format}
DO NOT output anything else except the json.
"""
from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_openai_response(system_prompt: str, user_prompt: str, output_format: dict):
    from langfuse.openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url=os.getenv('OPENAI_API_BASE'))
    return client.chat.completions.create(
        model='gpt-4o',
        temperature = 0,
        messages=[
            {"role": "system", "content": JSON_RESPONSE_PROMPT_TEMPLATE.format(system_prompt=system_prompt,output_format=output_format)},
            {"role": "user", "content": user_prompt}
        ]
    )

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def get_json_response(system_prompt: str, user_prompt: str, output_format: dict) -> dict:
    try:
        response = get_openai_response(system_prompt, user_prompt, output_format)
        return json.loads(response.choices[0].message.content.strip().strip('```json').strip('````').strip())
    except Exception as e:
        print(f"[jsonify_chat_model]error parsing json from openai response: {str(e)}. retry...")
        raise

if __name__ == "__main__":
    output_format = textwrap.dedent("""
    {
        "steps": [ 
            {
            "explanation": string  // step description,
            "output": number  // result of the step
            },
            (More steps here...)
        ],
        "final_answer": number  // Final answer
    }""")
    while(True):
        res = get_json_response(system_prompt = 'You are a math problem solver.You break down the problem into steps and solve it step by step.',
                        user_prompt = 'solve (10 + 20 * 3) / 4 + 5?',
                        output_format = output_format)     
        res = json.dumps(res, indent=4)
        print(res)
