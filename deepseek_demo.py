from openai import OpenAI

client = OpenAI(
    api_key="sk-558d92bbe0af4f319dbc75c56a52cefe",
    base_url="https://api.deepseek.com",   # 也可以写 https://api.deepseek.com/v1
)

resp = client.chat.completions.create(
    model="deepseek-chat",   # 非思考模式；推理用 deepseek-reasoner
    messages=[
        {"role": "system", "content": "你是接口自动化测试专家，只输出代码。"},
        {"role": "user", "content": "用 pytest+requests 写一个 GET /health 的冒烟测试"}
    ],
    temperature=0.1,
)

print(resp.choices[0].message.content)