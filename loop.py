import discord
from discord import app_commands # coding: utf-8
from discord.ext import tasks
import configparser
import requests
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.message_content = True  # メッセージコンテントのintentはオンにする
intents.members = True
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')

MY_GUILDS = [discord.Object(id=config_ini.getint('GUILD', 'guild_id_ygm'))]

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self) 
    async def setup_hook(self):
        for id in MY_GUILDS:
            self.tree.copy_global_to(guild=id)
            await self.tree.sync(guild=id)
    
client = MyClient(intents=intents)

def get_product_name_state(product_url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.167 Safari/537.36",
            "Accept-Language": "ja,en-us;q=0.7,en;q=0.3",
            "Accept-Encoding": "HTTP::Message::decodable",
            "Accept": "text/html,application/xhtml_xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }
        try:
            res = requests.get(product_url, headers=headers)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Failed to http request:", e)
        else:
            soup = BeautifulSoup(res.text, "html.parser")
            product_name = soup.find(id="products_maintitle").getText()
            state = soup.find(id='js_buyBoxMain').getText()
            return [product_name, state]
        
@tasks.loop(minutes=2)#2分毎
async def send_message():
    data = [] #[[url, guild_id, user_id], [][]...]二次元配列
    #txtファイルの全ての行のurl文ループするfor文で、在庫があればそのguildのuserにDMを送る
    with open('product_and_user.txt', mode='r') as f:
    # ファイルの各行を1つずつ読み込んでリストに格納
        lines = f.readlines()
        # 各行を半角スペースで区切って、二次元配列に要素を追加
        for line in lines:
            # 改行文字を除去して、半角スペースで区切る
            items = line.rstrip().split(' ')
            # 二次元配列に要素を追加
            data.append(items)
    f.close()
    for i in range(len(data)):
        pro_data_list = get_product_name_state(data[i][0])
        #print(pro_data_list) #[商品名, 状態]
        if 'カート' in pro_data_list[1]:
            arrived_data = []
            with open('arrived.txt', mode='r') as f:
            # ファイルの各行を1つずつ読み込んでリストに格納
                lines = f.readlines()
                # 各行を半角スペースで区切って、二次元配列に要素を追加
                for line in lines:
                    # 改行文字を除去して、半角スペースで区切る
                    items = line.rstrip().split(' ')
                    # 二次元配列に要素を追加
                    arrived_data.append(items)
            f.close()
            if data[i] not in arrived_data:
                #print(data) #[[リンク, ギルドid, ユーザid], [], []...]
                # guildオブジェクトを取得
                guild = discord.utils.find(lambda g: g.id == int(data[i][1]), client.guilds)
                print(guild)
                member = guild.get_member(int(data[i][2]))
                embed = discord.Embed(title = "商品が入荷しました！", 
                        description = str(pro_data_list[0]) + 'が入荷しました！' , color = 0xf96fa6)
                
                f = open('arrived.txt', 'a', encoding='UTF-8', newline='\n')
                arribed_data = '\n' + str(data[i][0]) + ' ' + str(data[i][1]) + ' ' + str(data[i][2])
                f.writelines(arribed_data)
                f.close()    
                
                await member.send(embed=embed) 

@client.event
async def on_ready(): #botログイン完了時に実行
    print('on_ready') 
    send_message.start() # タスクの開始

client.run(config_ini.get('TOKEN', 'token_k'))  