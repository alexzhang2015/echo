#!/usr/bin/env python3
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import openai
import os
import io
from pydantic import BaseModel, validator
import requests


# Load your API key from an environment variable or secret management service
openai.api_key = os.getenv("OPENAI_API_KEY")
prompt = '中文是普通话的句子'

app = FastAPI()


class OssUrl(BaseModel):
    url: str

    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL必须以http://或https://开头')
        return v


@app.get("/")
def hello_world():
    return {"message": "OK"}


@app.post("/api/transcribe/")
async def transcribe_url(ossurl: OssUrl):
    audio_file = requests.get(ossurl.url)
    file_name = os.path.basename(ossurl.url)
    with open(file_name, 'wb') as f:
        f.write(audio_file.content)

    with open(file_name, 'rb') as contents:
        transcript = openai.Audio.transcribe("whisper-1", contents)

    return {"transcribe": transcript.text}


@app.post("/api/audio")
async def upload_audio(file: UploadFile = File(...), language: str = Form("English")) -> dict:
    contents = io.BytesIO(await file.read())
    contents.name = 'testy.mp3'
    try:
        transcript = openai.Audio.transcribe(
            "whisper-1", contents, prompt=prompt, temperature=0.7)
        translate = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "user", "content": f'Translate the following text to "{language}": "{transcript.text}"'}]
        )
        response = {"transcribe": transcript.text,
                    "translate": translate['choices'][0]['message'].get("content")}
        return JSONResponse(status_code=200, content=response)
    except Exception as e:
        error_message = str(e)
        return JSONResponse(status_code=500, content={"error": error_message})


@app.post("/api/summarize")
async def summarize_audio(file: UploadFile = File(...)) -> dict:
    audio_file = await file.read()
    contents = io.BytesIO(audio_file)
    contents.name = 'testy.mp3'

    try:
        transcript = openai.Audio.transcribe("whisper-1", contents)
        content = f"请对以下文本进行总结，注意总结的凝炼性，将总结字数控制在100个字以内:\n{transcript.text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": content}],
            temperature=0.7,
            max_tokens=640,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        summarized_text = response.get(
            "choices")[0].get("message").get("content")
        return {"summarize": summarized_text}

    except Exception as e:
        return {"error": str(e)}
