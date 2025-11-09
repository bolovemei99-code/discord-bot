# main.py - Discord 多功能机器人（Railway 专用版）
import discord
from discord.ext import commands
import sqlite3
import asyncio
import json
import os
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts 
                 (user_id INTEGER, amount REAL, desc TEXT, time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quick 
                 (trigger TEXT PRIMARY KEY, response TEXT)''')
    conn.commit()
    conn.close()

# 快捷回复系统
QUICK = {}
def load_quick():
    global QUICK
    if os.path.exists('quick.json'):
        with open('quick.json', 'r', encoding='utf-8') as f:
            QUICK = json.load(f)
def save_quick():
    with open('quick.json', 'w', encoding='utf-8') as f:
        json.dump(QUICK, f, ensure_ascii=False, indent=2)

# 启动事件
@bot.event
async def on_ready():
    init_db()
    load_quick()
    print(f'🚀 {bot.user} 已上线！Railway 部署成功！')

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    if channel: await channel.send(f'欢迎 {member.mention} 加入！')

# 记账
@bot.command()
async def add(ctx, amount: float, *, desc="无描述"):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("INSERT INTO accounts VALUES (?,?,?,?)",
              (ctx.author.id, amount, desc, datetime.now().strftime("%m-%d %H:%M")))
    conn.commit(); conn.close()
    await ctx.send(f"✅ +{amount} | {desc}")

@bot.command()
async def sub(ctx, amount: float, *, desc="无描述"):
    await add(ctx, -amount, desc)

@bot.command()
async def balance(ctx):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM accounts WHERE user_id=?", (ctx.author.id,))
    total = c.fetchone()[0] or 0
    conn.close()
    await ctx.send(f"💰 余额：**{total}**")

# 群发
@bot.command()
@commands.has_permissions(administrator=True)
async def mass(ctx, members: commands.Greedy[discord.Member], *, msg):
    ok = 0
    for m in members:
        try:
            await m.send(f"📩 群发：{msg}")
            ok += 1
            await asyncio.sleep(1)
        except: pass
    await ctx.send(f"✅ 成功发送 {ok}/{len(members)} 人")

# 快捷回复
@bot.command()
@commands.has_permissions(administrator=True)
async def quick(ctx, trigger, *, response):
    QUICK[trigger.lower()] = response
    save_quick()
    await ctx.send(f"✅ `{trigger}` → `{response}`")

@bot.command()
async def qr(ctx):
    if not QUICK: await ctx.send("无快捷回复"); return
    txt = "\n".join([f"`{k}` → `{v}`" for k,v in QUICK.items()])
    await ctx.send(f"**快捷回复：**\n{txt}")

# 自动回复
@bot.event
async def on_message(msg):
    if msg.author.bot: return
    txt = msg.content.lower()
    for t, r in QUICK.items():
        if t in txt:
            await msg.channel.send(r)
            break
    await bot.process_commands(msg)

# 启动（Token 从环境变量读取）
bot.run(os.getenv('DISCORD_TOKEN'))