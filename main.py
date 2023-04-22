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

@client.event
async def on_ready(): #botログイン完了時に実行
    print('on_ready') 

@client.tree.command(
    name='ヨドバシurl登録',
    description='ヨドバシ.comで入荷したら通知が来る商品URLを登録します。')
@app_commands.describe(yodobashi_url='ヨドバシ.comの商品URLを入力',)
async def ydbs_pro_reg(interaction: discord.Interaction, yodobashi_url: str):

    user_id = interaction.user.id
    guild_id = interaction.guild.id
    #txtファイルに商品URLとuserを書き込む
    f = open('product_and_user.txt', 'a', encoding='UTF-8', newline='\n')
    data = '\n' + str(yodobashi_url) + ' ' + str(guild_id) + ' ' + str(user_id)
    f.writelines(data)
    f.close()    
    embed = discord.Embed(title = "商品を登録しました", 
                    description =  "入荷するとDMにメッセージが来ます", color = 0xf96fa6)
    await interaction.response.send_message(embed=embed, ephemeral=False)
    pro_name = get_product_name_state(yodobashi_url)
    embed = discord.Embed(title = "商品を登録しました", 
                    description = pro_name[0], color = 0xf96fa6)
    await interaction.user.send(embed=embed)

client.run(config_ini.get('TOKEN', 'token'))  