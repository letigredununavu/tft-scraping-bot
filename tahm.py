from bs4 import BeautifulSoup
import requests
from discord.ext import commands
import discord
from PIL import Image
from io import BytesIO
import urllib


token = "your token"


client = commands.Bot(command_prefix = '#', help_command=None)

region = 'na'

@client.command()
async def player(ctx, *, name):
    summoner_name = name
    
    page = requests.get(f'https://lolchess.gg/profile/{region}/{summoner_name}')

    soup = BeautifulSoup(page.content, "html.parser")

    profile_name = soup.find("span",class_ = "profile__summoner__name")

    if profile_name == None:
        await ctx.send("Mauvais nom")
    else:
        profile_region = soup.find("em", class_ = "profile__summoner__region")
        profile_region = profile_region.get_text()
        
        profile_name = profile_name.get_text(strip = True).replace(f'{profile_region}', "")
        
        await ctx.send(f'{profile_name} from {profile_region}')

        profile_icon_div = soup.find("div", class_ = "profile__icon")
        profile_icon_img = profile_icon_div.find("img")

        profile_tier_div = soup.find("div", class_ = "profile__tier__icon")
        profile_tier_icon = profile_tier_div.find("img")

        profile_tier_summary_div = soup.find("div", class_ = "profile__tier__summary")
        profile_tier_infos = profile_tier_summary_div.find_all("span")

        tier_info = []

        for tier_span in profile_tier_infos:
            # Pas sur du strip
            tier_info.append(tier_span.get_text(strip = True))
        
        profile_tier = tier_info[0]
        profile_tier_lp = ''
        if profile_tier != 'Unranked':
            profile_tier_lp = tier_info[1]

        matches = soup.find("div", class_ = "profile__match-history-v2__items")
        
        games_placements_div = matches.find_all("div", class_ = "placement", limit = 5)
        games_comps_div = matches.find_all("div", class_ = "units", limit = 5)
        games_traits_div = matches.find_all("div", class_ = "traits", limit = 5)

        # Tableau pour les placements
        games_placements = []

        # Le nombre de game que le joueur à joué, 5 au maximum
        nbr_games = len(games_placements_div)
        
        # Tableau des sources des images des traits
        games_traits = [[] for i in range(5)]
        
        # Tableau pour les sources des images des champions
        games_units = [[] for i in range(5)]

        games_units_stars = [[] for i in range(5)]

        for i in range(5):

            # Peut-etre tu vas devoir enlever le strip
            games_placements.append(games_placements_div[i].get_text(strip = True))
            
            # On va chercher les src des imgs
            games_traits_imgs = games_traits_div[i].find_all("img")
            
            for img in games_traits_imgs:
                games_traits[i].append(img['src'])

            # Les imgs des champions
            games_unit_div = games_comps_div[i].find_all("div", class_ = "unit")
            for unit in games_unit_div:
                imgs = unit.find_all("img")
                games_units_stars[i].append(imgs[0])
                games_units[i].append(imgs[1])

        #print(games_placements)
        #print(games_units)
        #print(games_traits)
        


        embed_title = f'{profile_tier} - {profile_tier_lp}'

        message = discord.Embed(
            title = embed_title,
            description = '5 dernières parties:',
            colour = discord.Colour.orange()
        )

        message.set_author(name=profile_name, icon_url='https:{}'.format(profile_icon_img['src']))
        message.set_thumbnail(url='https:{}'.format(profile_tier_icon['src']))

        for i in range(nbr_games):
            message.add_field(name=f'Match #{i+1}', value=f'Placement: {games_placements[i]}')


        image = create_match_image(games_units, games_traits, games_units_stars)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        file  = discord.File(buffer, 'game.png')

        message.set_image(url = "attachment://game.png")

        await ctx.send(file=file, embed=message)


def create_match_image(all_comps, all_traits, all_stars):
    background = Image.new('RGB', (1550, 1300), 0)

    width = 100
    height = 0

    for i in range(5):
        width = 100
        height = 15 + (i*240)
        traits = all_traits[i]
        stars = all_stars[i]
        comp = all_comps[i]

        # traits

        for trait in traits:
            TRAIT_WIDTH = 34
            TRAIT_HEIGHT = 34
            print(trait)

            if not '.svg' in trait:
                synergy = Image.open(urllib.request.urlopen('https:{}'.format(trait.replace("black", "white"))))
                size_ = (TRAIT_WIDTH, TRAIT_HEIGHT)

                synergy = synergy.resize(size_)

                
                
                background.paste(synergy, (width, height))
                width += synergy.width + 10

                
        # Stars
        start_width = 132
        for star in stars:
            STAR_WIDTH = 64
            STAR_HEIGHT = 20
            
            star = Image.open(urllib.request.urlopen('https:{}'.format(star['src'])))
            size_ = (STAR_WIDTH, STAR_HEIGHT)

            star = star.resize(size_)

            background.paste(star, (start_width, 45 + height))
            start_width += 138

            
        
        start_width = 100

        # Champs

        for champ in comp:
            CHAMP_WIDTH = 128
            CHAMP_HEIGHT = 128

            champ = Image.open(urllib.request.urlopen('https:{}'.format(champ['src'])))
            size_ = (CHAMP_WIDTH, CHAMP_HEIGHT)
            champ = champ.resize(size_)
            
            background.paste(champ, (start_width, 85 + height))
            start_width += champ.width + 10

    


    
    '''
    print(comp[0])
    champ = Image.open(urllib.request.urlopen('https:{}'.format(comp[0]['src'])))
    background.paste(champ, (1000, 100))
    '''

    return background







@client.command()
async def comps(ctx):

    page = requests.get(f'https://lolchess.gg/meta')
    soup = BeautifulSoup(page.content, 'html.parser')
    titles = soup.find_all("div", class_='guide-meta__deck__column name mr-3', limit=5)
    print(titles)
    message = "the bests comps in the current meta are:\n"
    for title in titles:
        message += f'{[l for l in title.stripped_strings][0]}\n'

    await ctx.send(message)


@client.command()
async def items(ctx, *, champion):
    
    page = requests.get(f'https://lolchess.gg/statistics/items')
    soup = BeautifulSoup(page.content, 'html.parser')
    champions = []
    all_items = []
    champs_pics = []
    balises = soup.find_all("tr")
    for balise in balises:
        chp = balise.find("span")
        if chp != None:
            champions.append(chp.get_text())
            champs_pics.append(balise.find("img", class_ = "mr-1")['src'])
            items = []
            items_div = balise.find_all("td", class_ = "items")
            if items_div != None:
                for item in items_div:
                    name = item.find("span", class_ = 'name')
                    items.append(name.get_text())
                all_items.append(items)
        else:
            print("nothing to see here")

    # print(all_items)
    if champion in champions:
        
        index = champions.index(champion)
        chp_pic = champs_pics[index]
        emb = discord.Embed(
            title = f'Items for {champion}'

        )
        
        emb.set_thumbnail(url="https:{}".format(chp_pic))
        
        for i in range(len(all_items[index])):
            emb.add_field(name = f'Item #{i+1}', value = all_items[index][i], inline=True)

        
        
        await ctx.send(embed=emb)
    else:
        await ctx.send('Incorrect champion')
        


@client.event
async def on_ready():
    print("We have logged in as {}".format(client))

@client.command()
async def ping(ctx):
    await ctx.send("pong!")

client.run(token)

