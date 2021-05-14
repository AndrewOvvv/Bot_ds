# -*- coding: utf-8 -*- 

import discord
import datetime
from discord.ext import commands
from config import settings

import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials


intents = discord.Intents.default()
intents.members = True
intents.reactions = True


FILE_DATA = "DATA.txt"
FILE_LOGINS = "LOGINS.txt"

DATA = dict()
STATES = dict()
LOGINS = dict()
ALL_LOGINS = []
LOGGED_IN = set()

ADMIN_ROLE_ID = 784900321242906704


STR_NO = '🅾️'
STR_YES = '✅'
CONFIRMATIONS = ['!delete', '!lock', '!unlock']
EXCEPTION = 'Incorect input'


CREDENTIALS_FILE = 'mypython-297819-82d9beab3a5c.json'

credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',
                                                                                  'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)

spreadsheetId = '1ioH-xvJDvTS2KHG46cW4nXY0uEwfXUXXtVidatsxIIg'


def ReadAll():
    global DATA, STATES, LOGINS
    fin = open(FILE_DATA, "r", encoding='utf-8')
    DATA = dict()
    STATES = dict()
    GroupName = ""
    for line in fin: 
        if line[0] == "!":
            GroupName = line[1:-1]
            DATA[GroupName] = []
        else:
            Value, State = line[:-1].split()
            DATA[GroupName].append(Value)
            STATES[(GroupName, len(DATA[GroupName]))] = int(State)
    fin.close()
    fin = open(FILE_LOGINS, "r", encoding='utf-8')
    LOGINS = dict()
    for line in fin:
        UserId, UserLogin = line[:-1].split()
        LOGINS[int(UserId)] = UserLogin
        LOGGED_IN.add(UserLogin)
    fin.close()
    
    
def ReadLogins():
    global ALL_LOGINS
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()
    sheets = sheet_metadata.get('sheets')
    title = sheets[0].get("properties").get("title")
    ranges = [title + "!B2:B999"]
    results = service.spreadsheets().values().batchGet(spreadsheetId = spreadsheetId, 
                                         ranges = ranges, 
                                         valueRenderOption = 'FORMATTED_VALUE',  
                                         dateTimeRenderOption = 'FORMATTED_STRING').execute() 
    sheet_values = results['valueRanges'][0]['values']
    ALL_LOGINS = []
    for elem in sheet_values:
        ALL_LOGINS.append(elem[0])


def ReadResults(SheetName, RowNumber):
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()
    sheets = sheet_metadata.get('sheets')
    ranges = [SheetName + "!G" + RowNumber + ":" + chr(ord('G') + len(DATA[SheetName]) - 1) + RowNumber]
    results = service.spreadsheets().values().batchGet(spreadsheetId = spreadsheetId, 
                                         ranges = ranges, 
                                         valueRenderOption = 'FORMATTED_VALUE',  
                                         dateTimeRenderOption = 'FORMATTED_STRING').execute()
    if 'values' in results['valueRanges'][0]:
        return results['valueRanges'][0]['values'][0] + [''] * (len(DATA[SheetName]) - len(results['valueRanges'][0]['values'][0]))
    else:
        return [''] * len(DATA[SheetName])


def WriteAll():
    fout = open(FILE_DATA, "w", encoding='utf-8')
    for GroupName in DATA:
        print("!" + GroupName, file=fout) 
        for i in range(len(DATA[GroupName])):
            print(DATA[GroupName][i], str(STATES[(GroupName, i + 1)]), file=fout)
    fout.close()
    fout = open(FILE_LOGINS, "w", encoding='utf-8')
    for UserId in LOGINS:
        print(UserId, LOGINS[UserId], file=fout)
    fout.close()


bot = commands.Bot(command_prefix = settings['prefix'], intents = intents)
bot.remove_command('help')

@bot.event
async def on_reaction_add(reaction, user):
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(user.id).roles
    if user == bot.user or not is_admin:
        return
    if user != reaction.message.author:
        return    
    emoji = reaction.emoji
    if emoji == STR_YES and reaction.message.content in CONFIRMATIONS:
        ReadAll()
        if reaction.message.content == '!delete':
            Groups = []
            for GroupName in DATA:
                for i in range(len(DATA[GroupName])):
                    del STATES[(GroupName, i + 1)]
                Groups.append(GroupName)
            for GroupName in Groups:
                del DATA[GroupName]
        elif reaction.message.content == '!lock':
            for GroupName in DATA:
                for i in range(len(DATA[GroupName])):
                    STATES[(GroupName, i + 1)] = 1         
        elif reaction.message.content == '!unlock':
            for GroupName in DATA:
                for i in range(len(DATA[GroupName])):
                    STATES[(GroupName, i + 1)] = 0    
        WriteAll()
        await reaction.message.delete()
        
@bot.command()
async def login(ctx, *args):
    ReadAll()
    if len(args) == 1:
        if ctx.message.author.id not in LOGINS:
            ReadLogins()
            if args[0] in ALL_LOGINS and args[0] not in LOGGED_IN:
                LOGINS[ctx.message.author.id] = args[0]
                await ctx.send('Successfully logged in ' + ctx.message.author.mention)
            else:
                await ctx.send(EXCEPTION)    
        else:
            await ctx.send(EXCEPTION)            
    else:
        await ctx.send(EXCEPTION)
    WriteAll()
            
@bot.command()
async def add(ctx, *args):
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(ctx.message.author.id).roles
    if (not is_admin):
        return    
    ReadAll()
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(ctx.message.author.id).roles
    if (not is_admin):
        return    
    if len(args) == 1:
        GroupName = args[0]
        if GroupName not in DATA:
            DATA[GroupName] = []
        else:
            await ctx.send(EXCEPTION)
    elif len(args) > 1:
        GroupName = args[0]
        if GroupName in DATA:
            for i in range(1, len(args)):
                DATA[GroupName].append(args[i])
                STATES[(GroupName, len(DATA[GroupName]))] = 0
        else:
            await ctx.send(EXCEPTION)
    else:
        await ctx.send(EXCEPTION)
    WriteAll()
    
@bot.command()
async def delete(ctx, *args):
    ReadAll()
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(ctx.message.author.id).roles
    if (not is_admin):
        return
    if (len(args) == 0):
        await ctx.message.add_reaction(STR_YES)
        await ctx.message.add_reaction(STR_NO)
    elif len(args) == 1:
        GroupName = args[0]
        if GroupName in DATA:
            for i in range(len(DATA[GroupName])):
                del STATES[(GroupName, i + 1)]
            del DATA[GroupName]
        else:
            await ctx.send(EXCEPTION)
    elif len(args) > 1:
        GroupName = args[0]
        FLAG = True
        for i in range(1, len(args)):
            if not args[i].isdigit() or not(1 <= int(args[i]) <= len(DATA[GroupName])):
                FLAG = False
        if FLAG:
            items = sorted(list(map(int, args[1:])))[::-1]
            if GroupName in DATA:
                GroupStates = []
                for i in range(len(DATA[GroupName])):
                    GroupStates.append(STATES[(GroupName, i + 1)]) 
                    del STATES[(GroupName, i + 1)]
                for i in range(len(items)):
                    DATA[GroupName].pop(items[i] - 1)
                    GroupStates.pop(items[i] - 1)
                for i in range(len(DATA[GroupName])):
                    STATES[(GroupName, i + 1)] = GroupStates[i]       
            else:
                await ctx.send(EXCEPTION)
        else:
            await ctx.send(EXCEPTION)
    else:
        await ctx.send(EXCEPTION)
    WriteAll()     
    
@bot.command()
async def edit(ctx, *args):
    ReadAll()
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(ctx.message.author.id).roles
    if (not is_admin):
        return    
    if len(args) == 2:
        GroupName = args[0]
        NewGroupName = args[1]
        if GroupName in DATA:
            if NewGroupName not in DATA:
                DATA[NewGroupName] = []
                for i in range(len(DATA[GroupName])):
                    DATA[NewGroupName].append(DATA[GroupName][i])
                    STATES[(NewGroupName, i + 1)] = STATES[(GroupName, i + 1)]
                    del STATES[(GroupName, i + 1)]
                del DATA[GroupName]
            else:
                await ctx.send(EXCEPTION)
        else:
            await ctx.send(EXCEPTION)
    elif len(args) == 3:
        GroupName = args[0]
        Index = args[1]
        Value = args[2]
        if GroupName in DATA:
            if Index.isdigit() and (1 <= int(Index) <= len(DATA[GroupName])):
                DATA[GroupName][int(Index) - 1] = Value
            else:
                await ctx.send(EXCEPTION)
        else:
            await ctx.send(EXCEPTION)
    else:
        await ctx.send(EXCEPTION)
    WriteAll()
    
@bot.command()
async def lock(ctx, *args):
    ReadAll()
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(ctx.message.author.id).roles
    if (not is_admin):
        return
    if (len(args) == 0):
        await ctx.message.add_reaction(STR_YES)
        await ctx.message.add_reaction(STR_NO)    
    elif len(args) == 1:
        GroupName = args[0]
        if GroupName in DATA:
            for i in range(len(DATA[GroupName])):
                STATES[(GroupName, i + 1)] = 1
        else:
            await ctx.send(EXCEPTION)
    elif len(args) == 2:
        GroupName = args[0]
        Index = args[1]
        if GroupName in DATA:
            if Index.isdigit() and (1 <= int(Index) <= len(DATA[GroupName])):
                STATES[(GroupName, int(Index))] = 1
            else:
                await ctx.send(EXCEPTION)
        else:
            await ctx.send(EXCEPTION)
    else:
        await ctx.send(EXCEPTION)
    WriteAll()
    
@bot.command()
async def unlock(ctx, *args):
    ReadAll()
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(ctx.message.author.id).roles
    if (not is_admin):
        return
    if (len(args) == 0):
        await ctx.message.add_reaction(STR_YES)
        await ctx.message.add_reaction(STR_NO)
    elif len(args) == 1:
        GroupName = args[0]
        if GroupName in DATA:
            for i in range(len(DATA[GroupName])):
                STATES[(GroupName, i + 1)] = 0
        else:
            await ctx.send(EXCEPTION)
    elif len(args) == 2:
        GroupName = args[0]
        Index = args[1]
        if GroupName in DATA:
            if Index.isdigit() and (1 <= int(Index) <= len(DATA[GroupName])):
                STATES[(GroupName, int(Index))] = 0
            else:
                await ctx.send(EXCEPTION)
        else:
            await ctx.send(EXCEPTION)
    else:
        await ctx.send(EXCEPTION)
    WriteAll()

@bot.command()
async def check(ctx, *args):
    ReadAll()
    is_login = ctx.message.author.id in LOGINS
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(ctx.message.author.id).roles
    if is_login or is_admin:
        if len(args) > 0:
            GroupName = args[0]
            if GroupName in DATA:
                if len(args) == len(DATA[GroupName]) + 1:
                    Answers = []
                    for i in range(1, len(args)):
                        if (DATA[GroupName][i - 1] == args[i]):
                            Answers.append(1)
                        else:
                            Answers.append(0)
                    Result = ''
                    if is_admin:
                        for elem in Answers:
                            if elem:
                                Result += STR_YES
                            else:
                                Result += STR_NO     
                    else:
                        ReadLogins()
                        RowNumber = ''
                        for i in range(len(ALL_LOGINS)):
                            if ALL_LOGINS[i] == LOGINS[ctx.message.author.id]:
                                RowNumber = str(i + 2)                        
                        Results = ReadResults(GroupName, RowNumber)
                        sum_answers, blocked = 0, 0
                        for i in range(len(Answers)):
                            if not STATES[(GroupName, i + 1)] and Answers[i]:
                                sum_answers += 1
                            elif STATES[(GroupName, i + 1)]:
                                Answers[i] = Results[i]
                                blocked += 1
                            Answers[i] = str(Answers[i])
                        Result = str(sum_answers) + '/' + str(len(Answers) - blocked) + ' ' + STR_YES
                        results = service.spreadsheets().values().batchUpdate(spreadsheetId = spreadsheetId, body = {
                            "valueInputOption": "USER_ENTERED",
                            "data": [
                                {"range": GroupName + "!G" + RowNumber + ":" + chr(ord('G') + len(DATA[GroupName]) - 1) + RowNumber,
                                 "majorDimension": "ROWS",     
                                 "values": [Answers]}
                            ]
                        }).execute()                        
                    await ctx.send(Result)
                else:
                    await ctx.send(EXCEPTION)
            else:
                await ctx.send(EXCEPTION)
        else:
            await ctx.send(EXCEPTION)
    else:
        await ctx.send('Please, log in ' + ctx.message.author.mention)    
    WriteAll()

@bot.command()
async def get(ctx, *args):
    ReadAll()
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(ctx.message.author.id).roles
    if len(args) == 0:
        if len(DATA) > 0:
            emb = discord.Embed(colour = discord.Color.magenta())
            emb.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
            for GroupName in DATA:
                Answers = ''
                if len(DATA[GroupName]) == 0:
                    Answers = 'No data'
                for i in range(len(DATA[GroupName])):
                    Answers += str(i + 1) + '. '
                    if is_admin:
                        Answers += DATA[GroupName][i] + ' '
                    if STATES[(GroupName, i + 1)]:
                        Answers += STR_NO
                    else:
                        Answers += STR_YES
                    Answers += '\n'
                emb.add_field(name = GroupName, value = Answers, inline = False)
            await ctx.send(embed = emb)
        else:
            emb = discord.Embed(title = 'No data', colour = discord.Color.dark_purple())
            emb.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
            emb.set_image(url = 'https://c4.wallpaperflare.com/wallpaper/500/442/354/outrun-vaporwave-hd-wallpaper-thumb.jpg')
            await ctx.send(embed = emb)            
    elif len(args) == 1:
        GroupName = args[0]
        if GroupName in DATA:
            Answers = ''
            if len(DATA[GroupName]) == 0:
                Answers = 'No data'            
            for i in range(len(DATA[GroupName])):
                    Answers += str(i + 1) + '. '
                    if is_admin:
                        Answers += DATA[GroupName][i] + ' '
                    if (STATES[(GroupName, i + 1)]):
                        Answers += STR_NO
                    else:
                        Answers += STR_YES
                    Answers += '\n'
            emb = discord.Embed(title = GroupName, description = Answers, colour = discord.Color.magenta())
            emb.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)    
            await ctx.send(embed = emb)
        else:
            await ctx.send(EXCEPTION)        
    elif len(args) == 2:
        GroupName = args[0]
        Index = args[1]
        if GroupName in DATA:
            if Index.isdigit() and (1 <= int(Index) <= len(DATA[GroupName])):
                Answer = Index + '. '
                if is_admin:
                    Answer += DATA[GroupName][int(Index) - 1] + ' '                
                if (STATES[(GroupName, int(Index))]):
                    Answer += STR_NO
                else:
                    Answer += STR_YES                
                emb = discord.Embed(title = GroupName, description = Answer, colour = discord.Color.magenta())
                emb.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
                await ctx.send(embed = emb)
            else:
                await ctx.send(EXCEPTION)            
        else:
            await ctx.send(EXCEPTION)
    else:
        await ctx.send(EXCEPTION)
        
@bot.command()
async def help(ctx, *args):
    ReadAll()
    is_admin = bot.guilds[0].get_role(ADMIN_ROLE_ID) in bot.guilds[0].get_member(ctx.message.author.id).roles
    if is_admin:
        emb = discord.Embed(title = 'Все доступные команды бота для принимающих', colour = discord.Color.magenta())
        emb.add_field(name = ':small_blue_diamond: !add <Название группы заданий>', value = 'Добавляет новую группу заданий', inline = False)
        emb.add_field(name = ':small_blue_diamond: !add <Название группы заданий> <Ответ_1> ... <Ответ_n>', value = 'Добавляет ответы к группе', inline = False)
        emb.add_field(name = ':small_blue_diamond: !delete', value = 'Удаляет все группы заданий (требует подтверждения)', inline = False)
        emb.add_field(name = ':small_blue_diamond: !delete <Название группы заданий>', value = 'Удаляет группу заданий', inline = False)
        emb.add_field(name = ':small_blue_diamond: !delete <Название группы заданий> <Номер задания>', value = 'Удаляет задание из группы', inline = False)
        emb.add_field(name = ':small_blue_diamond: !edit <Название группы заданий> <Новое название>', value = 'Изменяет название группы', inline = False)
        emb.add_field(name = ':small_blue_diamond: !edit <Название группы заданий> <Номер задания> <Новый ответ>', value = 'Изменяет ответ на задание', inline = False)
        emb.add_field(name = ':small_blue_diamond: !lock', value = 'Блокирует все задания для сдачи (требует подтверждения)', inline = False)
        emb.add_field(name = ':small_blue_diamond: !lock <Название группы заданий>', value = 'Блокирует все задания в группе', inline = False)
        emb.add_field(name = ':small_blue_diamond: !lock <Название группы заданий> <Номер задания>', value = 'Блокирует задание', inline = False)
        emb.add_field(name = ':small_blue_diamond: !unlock', value = 'Разблокирует все задания для сдачи (требует подтверждения)', inline = False)
        emb.add_field(name = ':small_blue_diamond: !unlock <Название группы заданий>', value = 'Разблокирует все задания в группе', inline = False)
        emb.add_field(name = ':small_blue_diamond: !unlock <Название группы заданий> <Номер задания>', value = 'Разблокирует задание', inline = False)
        emb.add_field(name = ':small_blue_diamond: !get', value = 'Выводит список всех групп и заданий в них с ответами и статусом блокировки', inline = False)
        emb.add_field(name = ':small_blue_diamond: !get <Название группы>', value = 'Выводит список всех заданий группы с ответами и статусом блокировки', inline = False)
        emb.add_field(name = ':small_blue_diamond: !get <Название группы> <Номер задания>', value = 'Выводит ответ и статус блокировки задания', inline = False)
        emb.add_field(name = ':small_blue_diamond: !check <Название группы> <Ответ_1> ... <Ответ_n>', value = 'Выводит результат проверки (отдельно для каждого задания)', inline = False)
    else:
        emb = discord.Embed(title = 'Все доступные команды бота для учеников', colour = discord.Color.magenta())
        emb.add_field(name = ':small_blue_diamond: !login <Ваш пароль>', value = 'Связывает ваш дискорд-аккаунт с гугл-таблицами и позволяет сдавать задания', inline = False)
        emb.add_field(name = ':small_blue_diamond: !get', value = 'Выводит список всех групп и заданий в них со статусом блокировки', inline = False)
        emb.add_field(name = ':small_blue_diamond: !get <Название группы>', value = 'Выводит список всех заданий группы со статусом блокировки', inline = False)
        emb.add_field(name = ':small_blue_diamond: !get <Название группы> <Номер задания>', value = 'Выводит статус блокировки задания', inline = False)
        emb.add_field(name = ':small_blue_diamond: !check <Название группы> <Ответ_1> ... <Ответ_n>', value = 'Выводит результат проверки (количество верных ответов)', inline = False)
    emb.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)
    emb.set_thumbnail(url = 'https://csfrager.ru/files/forums_imgs/1577119190.png')
    await ctx.send(embed = emb)    

bot.run(settings['token'])
