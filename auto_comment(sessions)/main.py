import asyncio
import openai
from pyrogram import Client, filters
import random
import os
import tiktoken
from pyrogram import errors

filepath = os.path.abspath(__file__)
proxy_dir = filepath.replace("\\main.py", "\\proxy")
cur_dir = filepath.replace('\\main.py', '')
sessions_dir = os.path.join(os.path.dirname(filepath), 'sessions')

with open(f'{cur_dir}/' + 'hello_mssg.txt', 'r', encoding='utf-8') as fl:
    hello = fl.read()
    print('Hello message:', hello)

with open(f'{cur_dir}/' + 'delay.txt', 'r') as fl:
    delay_min, delay_max = map(int, fl.read().split(','))
    print(f'Minimum delay:{delay_min}''\n'
          f'Maximum delay:{delay_max}')

with open(f'{cur_dir}/' + 'prompt.txt', 'r', encoding='utf-8') as fl:
    prompt = fl.read()
    print('Prompt:', prompt)

with open(f'{cur_dir}/' + 'chance.txt', 'r') as fl:
    probability = float(fl.read())
    print('Probability of starting working:', probability)

with open(f'{proxy_dir}/' + 'proxy.txt', 'r') as fl:
    proxy_list = fl.read().split('\n')

with open(f'{cur_dir}/' + 'admins.txt', 'r') as fl:
    admins = fl.read()

with open(f'{cur_dir}/' + 'api_openai.txt', 'r') as fl:
    API_KEY = fl.read()

with open(f'{cur_dir}/' + 'keywords.txt', 'r', encoding='utf-8') as fl:
    keywords = fl.read().split('\n')
    regex = '|'.join(keywords)

sessions = []

for files in os.listdir(sessions_dir):
    if files.endswith(".session"):
        files = files.split('.')
        sessions.append(files[0])

cur_proxy = random.choice(proxy_list)

proxy = {
    "scheme": "socks5",
    "hostname": cur_proxy.split(':')[0],
    "port": int(cur_proxy.split(':')[1]),
    "username": cur_proxy.split(':')[2],
    "password": cur_proxy.split(':')[3],
}

app = Client(sessions[0], workdir=sessions_dir)

encoding = tiktoken.get_encoding(encoding_name="cl100k_base")

sent_messages = []


@app.on_message(filters.private)
async def recieve_msggs(client, message):
    chat_id = message.chat.id
    if chat_id not in sent_messages:
        await app.send_message(chat_id=chat_id, text=hello)
        sent_messages.append(chat_id)


@app.on_message(filters.regex(regex) & filters.channel)
async def send_comment(client, message):
    try:
        openai.api_key = API_KEY

        if message.text or message.caption:

            text = message.text or message.caption

            channel_message_tokens = len(encoding.encode(text))
            max_history_tokens = 4096 - 2300

            link = f"https://t.me/{message.chat.username}/{message.id}"

            messages = [
                {"role": "system", "content": prompt},
                {"role": "assistant", "content": 'You are a social media user,write comment as a real human' +
                                                 text
                 }
            ]

            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=messages,
                max_tokens=1800,
                temperature=0.6
            )

            assistant_response = response['choices'][0]['message']['content']
            assistant_response = assistant_response.strip('\n').strip()

            print('ChatGPT:', assistant_response)
            delay_minutes = random.randint(delay_min, delay_max)
            await asyncio.sleep(delay_minutes * 60)

            if channel_message_tokens < max_history_tokens:

                try:
                    await app.get_chat(message.chat.id)

                    chance = random.random()

                    if chance <= probability:

                        print('by the will of random ... the script will be executed')

                        m = await app.get_discussion_message(message.chat.id, message.id)
                        await m.reply(assistant_response)

                        await app.send_message(chat_id=admins,
                                               text=f'New comment!\n'
                                                    f'\n'
                                                    f'Link to the post:{link}'
                                                    f'\n'
                                                    f'Comment:{assistant_response}')

                    else:
                        print('by the will of random ... the script will not be executed')

                except errors.UserBannedInChannel:
                    print('Your account is banned on the channel!')

            else:
                print('The comment uses to many tokens to write the comment!')
        else:
            print('Channel has not got the comment section!')
    except Exception as e:
        print(f'There is an error: {e}')


if __name__ == "__main__":
    app.run()
