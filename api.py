import os
from openai import OpenAI


CLIENT = None
MODEL_NAME = None


def setup_client(base_url, api_key, model_name):
    global CLIENT, MODEL_NAME
    try:
        CLIENT = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    except:
        pass
    MODEL_NAME = model_name

def test_api(base_url, api_key, model_name):
    try:
        CLIENT = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        response = CLIENT.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "hello？"},
            ],
            temperature=0.3,
            stream=True,
        )
        for idx, chunk in enumerate(response):
            return True, 'Pass!'
    except Exception as e:
        return False, f'{e}'
    
def request(messages):
    try:
        response = CLIENT.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.3,
            stream=True,
        )
        # return response
        for idx, chunk in enumerate(response):
            chunk_message = chunk.choices[0].delta
            if chunk_message.content:
                yield chunk_message.content
    except Exception as e:
        yield f'# API Error occur\n\n<font color=red>{e} </font>'
        

if __name__ == '__main__':
    prompt = '写一下勾股定理的公式'
    for content in request(prompt):
        # content = chunk.choices[0].delta.content

        print(content, flush=True, end='')
        import time
        time.sleep(0.1)
