from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup as bs

app = Flask(__name__)

# Your existing code

# Define functions and scraping logic

def basic_info(rows, row_name):
    for row in rows:
        if row.th and row.th.text.strip() == row_name:
            return row.td.text.strip()
    return None

def find_table_by_header(soup, header_text):
    header = soup.find('h2', string=header_text)
    if header:
        return header.find_next('table', class_='vitals-table')
    return None

def get_type_defenses_stats(data):
    type_defenses_stats = data.get('type_defenses_stats', {})
    results = []

    for key, value in type_defenses_stats.items():
        if value == "":
            value = "*1"
        else:
            value = f"*{value}"
        results.append((key, value))

    return results

def get_pokedex_entry(soup, game_version):
    pokedex_section = soup.find('h2', string='Pokédex entries')
    if pokedex_section:
        tables = pokedex_section.find_all_next('table', class_='vitals-table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                version_cell = row.find('th')
                entry_cell = row.find('td')
                if version_cell and entry_cell:
                    version = version_cell.text.strip()
                    entry = entry_cell.text.strip()
                    if game_version in version:
                        return entry
    return None

def get_moves_by_level_up(soup):
    moves_section = soup.find('h3', string='Moves learnt by level up')
    if moves_section:
        table = moves_section.find_next('table', class_='data-table')
        if table:
            moves = []
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 4:
                    level = columns[0].text.strip()
                    move = columns[1].text.strip()
                    move_type = columns[2].find('a').text.strip()
                    category = columns[3].find('img')['alt'].strip()
                    power = columns[4].text.strip() if len(columns) > 4 else 'N/A'
                    accuracy = columns[5].text.strip() if len(columns) > 5 else 'N/A'
                    moves.append({
                        'level': level,
                        'move': move,
                        'type': move_type,
                        'category': category,
                        'power': power,
                        'accuracy': accuracy
                    })
            return moves
    return None

def get_moves_by_tms(soup):
    moves_section = soup.find('h3', string='Moves learnt by TM')
    if moves_section:
        table = moves_section.find_next('table', class_='data-table')
        if table:
            moves = []
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 4:
                    TM = columns[0].text.strip()
                    move = columns[1].text.strip()
                    move_type = columns[2].find('a').text.strip()
                    category = columns[3].find('img')['alt'].strip()
                    power = columns[4].text.strip() if len(columns) > 4 else 'N/A'
                    accuracy = columns[5].text.strip() if len(columns) > 5 else 'N/A'
                    moves.append({
                        'TM': TM,
                        'move': move,
                        'type': move_type,
                        'category': category,
                        'power': power,
                        'accuracy': accuracy
                    })
            return moves
    return None

def egg_moves(soup):
    moves_section = soup.find('h3', string='Egg moves')
    if moves_section:
        table = moves_section.find_next('table', class_='data-table')
        if table:
            moves = []
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 4:
                    Egg_move = columns[0].text.strip()
                    move = columns[1].text.strip()
                    move_type = columns[1].find('a').text.strip() if columns[1].find('a') else '-'
                    category = columns[2].find('img')['alt'].strip() if columns[2].find('img') else '-'
                    power = columns[3].text.strip() if len(columns) > 3 else '-'
                    accuracy = columns[4].text.strip() if len(columns) > 4 else '-'
                    moves.append({
                        'egg_move': Egg_move,
                        'move': move,
                        'type': move_type,
                        'category': category,
                        'power': power,
                        'accuracy': accuracy
                    })
            return moves
    return None

def get_evolution_details(pokemon_name):
    url = f"https://pokemondb.net/pokedex/{pokemon_name.lower()}"
    response = requests.get(url)
    response.raise_for_status()
    soup = bs(response.content, "html.parser")
    evolution_details = extract_evolution_details(soup)
    evo_from_list = []
    evo_to_list = []
    for detail in evolution_details:
        if detail['to'].lower() == pokemon_name.lower():
            evo_from_list.append({
                "from": detail['from'],
                "method": detail['method']
            })
        elif detail['from'].lower() == pokemon_name.lower():
            evo_to_list.append({
                "to": detail['to'],
                "method": detail['method']
            })
    return evo_from_list, evo_to_list

def extract_evolution_details(soup):
    evolution_section = soup.find('div', class_='infocard-list-evo')
    if not evolution_section:
        return []
    evolution_details = []
    def parse_infocard(infocard):
        name_tag = infocard.find('a', class_='ent-name')
        return name_tag.text.strip() if name_tag else 'Unknown'
    def parse_evolution_chain(evolution_section, current_pokemon=None, evolution_method=None):
        for tag in evolution_section.find_all(['div', 'span'], recursive=False):
            if 'infocard' in tag['class'] and 'infocard-arrow' not in tag['class']:
                if current_pokemon:
                    next_pokemon = parse_infocard(tag)
                    evolution_details.append({
                        'from': current_pokemon,
                        'method': evolution_method,
                        'to': next_pokemon
                    })
                    current_pokemon = next_pokemon
                    evolution_method = None
                else:
                    current_pokemon = parse_infocard(tag)
            elif 'infocard-arrow' in tag['class']:
                method_tag = tag.find('small')
                if method_tag:
                    evolution_method = method_tag.text.strip('()')
            elif 'infocard-evo-split' in tag['class']:
                split_sections = tag.find_all('div', class_='infocard-list-evo')
                for split_section in split_sections:
                    parse_evolution_chain(split_section, current_pokemon, evolution_method)
    parse_evolution_chain(evolution_section)
    return evolution_details

def pokemon_data(soup):
    name = soup.find('h1').text.strip()
    info_table = soup.find('table', class_='vitals-table')
    info_rows = info_table.find_all('tr')
    id = basic_info(info_rows, 'National №')
    type = basic_info(info_rows, 'Type')
    category = basic_info(info_rows, 'Species')
    height = basic_info(info_rows, 'Height')
    weight = basic_info(info_rows, 'Weight')
    abilities = basic_info(info_rows, 'Abilities')
    local_no = basic_info(info_rows, 'Local №')

    training_table = find_table_by_header(soup, 'Training')
    if training_table:
        training_rows = training_table.find_all('tr')
        ev_yield = basic_info(training_rows, 'EV yield')
        catchrate = basic_info(training_rows, 'Catch rate')
        basefriendship = basic_info(training_rows, 'Base Friendship')
        baseexp = basic_info(training_rows, 'Base Exp.')
        growthrate = basic_info(training_rows, 'Growth Rate')

    breeding_table = find_table_by_header(soup, 'Breeding')
    if breeding_table:
        breeding_rows = breeding_table.find_all('tr')
        egggroups = basic_info(breeding_rows, 'Egg Groups')
        gender = basic_info(breeding_rows, 'Gender')
        eggcycles = basic_info(breeding_rows, 'Egg cycles')

    base_stats = find_table_by_header(soup, 'Base stats')
    if base_stats:
        basestats_rows = base_stats.find_all('tr')
        hp = basic_info(basestats_rows, 'HP')
        atk = basic_info(basestats_rows, 'Attack')
        defense = basic_info(basestats_rows, 'Defense')
        spa = basic_info(basestats_rows, 'Sp. Atk')
        spd = basic_info(basestats_rows, 'Sp. Def')
        speed = basic_info(basestats_rows, 'Speed')

    url = f"https://nox-api.vercel.app/pokedex/{name}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    type_chart = get_type_defenses_stats(data)
    Nor = type_chart[0][1]
    Fir = type_chart[1][1]
    Wat = type_chart[2][1]
    Ele = type_chart[3][1]
    Gra = type_chart[4][1]
    Ice = type_chart[5][1]
    Fig = type_chart[6][1]
    Poi = type_chart[7][1]
    Gro = type_chart[8][1]
    Fly = type_chart[9][1]
    Psy = type_chart[10][1]
    Bug = type_chart[11][1]
    Roc = type_chart[12][1]
    Gho = type_chart[13][1]
    Dra = type_chart[14][1]
    Dar = type_chart[14][1]
    Ste = type_chart[15][1]
    Fai = type_chart[16][1]

    game_version = "Scarlet"
    entry = get_pokedex_entry(soup, game_version)

    moves_by_level_up = get_moves_by_level_up(soup)
    moves_by_tm = get_moves_by_tms(soup)
    moves_by_egg_move = egg_moves(soup)

    evolution_from_details, evolution_to_details = get_evolution_details(name.lower())

    pokemon_info = {
        "Basic_Info": {
            "Name": name,
            "National_Id": id,
            "Category": category,
            "Type": type,
            "Description": entry,
            "Ability": abilities,
            "Evolution": {
                "Pre_Evolution": evolution_from_details,
                "Post_Evolution": evolution_to_details
            },
            "Local_No": local_no,
        },
        "Base_Stats": {
            "Hp": hp,
            "Attack": atk,
            "Defence": defense,
            "Sp.Attack": spa,
            "Sp.Defence": spd,
            "Speed": speed
        },
        "Moves": {
            "Level_up_Moves": moves_by_level_up,
            "TM_Moves": moves_by_tm,
            "Egg_Moves": moves_by_egg_move
        },
        "Type_Defenses": {
            "Normal": Nor,
            "Fire": Fir,
            "Water": Wat,
            "Electric": Ele,
            "Grass": Gra,
            "Ice": Ice,
            "Fighting": Fig,
            "Poison": Poi,
            "Ground": Gro,
            "Flying": Fly,
            "Psychic": Psy,
            "Bug": Bug,
            "Rock": Roc,
            "Ghost": Gho,
            "Dragon": Dra,
            "Dark": Dar,
            "Steel": Ste,
            "Fairy": Fai
        },
        "Training_Data": {
            "Egg_Group": egggroups,
            "Gender": gender,
            "Egg_Cycles": eggcycles
        }
    }

    return pokemon_info

@app.route('/pokemon/<name>', methods=['GET'])
def get_pokemon(name):
    url = f"https://pokemondb.net/pokedex/{name.lower()}"
    request = requests.get(url)
    soup = bs(request.content, "html.parser")
    
    # Call your existing functions to scrape the data
    pokemon_info = pokemon_data(soup)
    
    return jsonify(pokemon_info)

if __name__ == '__main__':
    app.run(debug=True)
