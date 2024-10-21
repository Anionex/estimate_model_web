from openai import OpenAI
#api_key = "sk-8Q6LhBRt1S3ykFHwC9997dDcA29f4f27A7F97bD24443Ec59"
#api_base="https://ssapi.onechat.shop/v1"
api_key = "sk-Vq0Rr2GKwXozgLGB5f156a75944b43719e6bD5EeD66e7784"
api_base = "https://chatapi.onechats.top/v1"
client = OpenAI(api_key=api_key, base_url=api_base)
completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "不是，哥们?"}
  ]
)

print(completion.choices[0].message)