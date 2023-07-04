from gtts import gTTS

# 要转换为语音的中文文本
text = '你好，我是机器人助手。'

# 使用 gTTS 将文本转换为语音
tts = gTTS(text, lang='zh-cn')

# 将语音保存为 mp3 文件
tts.save('sample.mp3')