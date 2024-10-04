import math
import sys
import logging
import json

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from tabulate import tabulate

from MiniLeagues import *
from variables import *

BASE_URL = 'https://fantasy.premierleague.com/api/'

#=====================================
# element options for an individual players:
# history - previous weeks in this season
# history_past - previous seasons data

def get_player_history(player_id, elements = 'history'):
    '''get all gameweek info for a given player_id'''
    req_json = requests.get(BASE_URL + 'element-summary/' + str(player_id) + '/').json()
    return pd.json_normalize(req_json[elements])

#=====================================

def get_fixture_data():
    '''get all gameweek info for a given player_id'''
    req_json = requests.get(BASE_URL + 'fixtures/').json()
    return pd.json_normalize(req_json)
#=====================================

def get_current_gw():
    # print('Fetching curr gameweek...')
    URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
    DATA = requests.get(URL).json()
    CURR_GW_OBJS = [x for x in DATA['events'] if x['is_current'] == True]
    if len(CURR_GW_OBJS) == 0:
        CURR_GW_OBJS = DATA['events']        
    CURR_GW = CURR_GW_OBJS[-1]['id']
    return CURR_GW
#=====================================

def get_team(team_id):
    gw = get_current_gw()
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gw}/picks/"

    # Send a GET request to fetch the data
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # # Save the new JSON response to the file
        # with open('team.json', "w") as json_file:
        #     json.dump(data, json_file, indent=2)
    # print(f"Data for team {team_id} in GW {gw} successfully saved")
    picks = data.get("picks", [])
    picks_df = pd.DataFrame(picks)
    picks_df = picks_df['element'].to_list()
    print (picks_df)
    return picks_df
    
#=====================================
# element options for global data:
# teams = individual team data
# elements = all player data

def get_global_info(elements = 'teams'):
    '''get all team data'''
    req_json = requests.get(BASE_URL + 'bootstrap-static/').json()
    return pd.json_normalize(req_json[elements])
#=====================================
def get_my_team(team_id):
    full_elements_df = get_global_info('elements')
    full_elements_df = full_elements_df.astype({"form": float, "total_points": int})
    full_elements_df.to_csv('full_elements_df.csv')
    my_team = get_team(team_id)
    df_filtered=full_elements_df[full_elements_df.id.isin(my_team)]
    df_filtered.reset_index(drop=True, inplace=True)
    df = df_filtered[['web_name','selected_by_percent','total_points','points_per_game','expected_goals_per_90','goals_scored','expected_assists_per_90','assists','expected_goal_involvements_per_90','clean_sheets']]
    table = tabulate(df,headers=["Name",'selected_by_percent','total points', "PPG",'xG/90','goals','xA/90','asists','xGi/90','clean sheets','bonus'],tablefmt='fancy_grid')
    text_file=open("team_id.csv","w")
    text_file.write(table)
    text_file.close()
#=====================================
def displayMyPlayers(team_id):
    full_elements_df = get_global_info('elements')
    full_elements_df = full_elements_df.astype({"form": float, "total_points": int})
    plt.figure(figsize=(10,8))
    fig, axs = plt.subplots(2,2,figsize=(10, 8))
    fig.suptitle('Your team form')

    # element_type: 0 = GKP, 1 = DEF, 2 = MID, 3 = FWD
    for idx, element_type in enumerate(range(1,5)):
        row = idx % 2
        col = math.floor(idx/2)
        my_team = get_team(team_id)
        elements_df = full_elements_df[full_elements_df.element_type == element_type]
        df_filtered=elements_df[elements_df.id.isin(my_team)]
        # print (df_filtered)

        for unused_idx, element in df_filtered.iterrows():
            name = element['web_name']
            scores = get_player_history(element['id'])['total_points'].to_list()
            gwk = get_player_history(element['id'])['round'].to_list()
            moving_avg = movingaverage(scores, min(3, len(scores)))
            x = []
            if len(scores) < 2:
                x = gwk[-1]
            else:
                x = gwk[1:-1]
            axs[row, col].plot(x, moving_avg, 'o-', label = name)

        axs[row, col].legend(loc="upper left")
        axs[row, col].set_xlabel('Gameweek')
        axs[row, col].set_ylabel('Running Ava. Points')
    plt.tight_layout()
    plt.savefig('team_id.png')

#=====================================
def displayTopPlayers():
    full_elements_df = get_global_info('elements')
    full_elements_df = full_elements_df.astype({"form": float, "total_points": int})
    plt.figure(figsize=(10,6))
    fig, axs = plt.subplots(2,2,figsize=(10, 8))
    fig.suptitle('Player Form')

    # element_type: 0 = GKP, 1 = DEF, 2 = MID, 3 = FWD
    for idx, element_type in enumerate(range(1,5)):
        row = idx % 2
        col = math.floor(idx/2)
        elements_df = full_elements_df[full_elements_df.element_type == element_type]
        elements_df = elements_df.sort_values(by='form', ascending=False).head(10)
        for unused_idx, element in elements_df.iterrows():
            name = element['web_name']
            scores = get_player_history(element['id'])['total_points'].to_list()
            gwk = get_player_history(element['id'])['round'].to_list()
            moving_avg = movingaverage(scores, min(3, len(scores)))
            x = []
            if len(scores) < 2:
                x = gwk[-1]
            else:
                x = gwk[1:-1]
            axs[row, col].plot(x, moving_avg, 'o-', label = name)

        axs[row, col].legend(loc="upper left")
        axs[row, col].set_xlabel('Gameweek')
        axs[row, col].set_ylabel('Running Ava. Points')
    plt.tight_layout()
    plt.savefig('public/Plot.png')

#=====================================

def movingaverage(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'valid')

#=====================================

def printTeamForm():
    all_fixtures_df = get_fixture_data()
    all_fixtures_df = all_fixtures_df[all_fixtures_df.finished == True]
    all_fixtures_df = all_fixtures_df.astype({"team_h_score": int, "team_a_score": int})

    team_df = get_global_info('teams')
    id_to_name = team_df.set_index('id')['name'].to_dict()

    x = PrettyTable()
    names = ["Team", "Points Per Game [5]", "Goals Per Game [5]", "Points Per Game Overall", "Clean Sheets", "Games Team Scored In"]
    x.field_names = names

    for id, name in id_to_name.items():
        fixtures_df = all_fixtures_df[((all_fixtures_df.team_h == id) |
            (all_fixtures_df.team_a == id))]
        fixtures_df['is_home_team'] = np.where(fixtures_df.team_h == id, True, False)
        fixtures_df['team_goals'] = np.where(fixtures_df.is_home_team == True,
                fixtures_df.team_h_score , fixtures_df.team_a_score)
        fixtures_df['opp_goals'] = np.where(fixtures_df.is_home_team == False,
                fixtures_df.team_h_score , fixtures_df.team_a_score)
        fixtures_df['clean_sheets'] = np.where(fixtures_df.opp_goals == 0, 1, 0)
        fixtures_df['did_team_score'] = np.where(fixtures_df.team_goals > 0, 1, 0)
        fixtures_df['points'] = np.where(fixtures_df.team_goals > fixtures_df.opp_goals, 3, np.where(fixtures_df.team_goals == fixtures_df.opp_goals, 1, 0))
        fixtures_df.sort_values(by=['event'])

        row = [name, round(fixtures_df.tail(5).points.mean(),2), round(fixtures_df.tail(5).team_goals.mean(), 2), round(fixtures_df.points.mean(), 2), fixtures_df.clean_sheets.sum(), fixtures_df.did_team_score.sum()]
        x.add_row(row)

    with open('table.html', 'r') as file :
        filedata = file.read()

    filedata = filedata.replace('TEAM_FORM', x.get_html_string(sortby='Goals Per Game [5]', reversesort=True))
    filedata = filedata.replace('<table>', '<table class="sortable-theme-finder" data-sortable> <caption><h2>Team form (last 5 gameweeks)</h2><sup>Click on any column to sort</sup></caption>')
    # filedata = filedata.replace('<table border="1" class="dataframe">', '<table class="sortable-theme-finder" data-sortable> <caption><h2>Team form (last 5 gameweeks)</h2></caption>')

    with open('public/team_form.html', 'w') as file:
        file.write(filedata)

#=====================================

def printDifficulties():
    all_fixtures_df = get_fixture_data()
    team_df = get_global_info('teams')
    id_to_name = team_df.set_index('id')['name'].to_dict()

    x = PrettyTable()
    names = ["Team"]

    lookahead = [3, 5, 10]
    for number in lookahead:
        names.append("Difficulty Next {}".format(number))
    names.append("Remaining Difficulty")

    x.field_names = names

    for id, name in id_to_name.items():
        fixtures_df = all_fixtures_df[((all_fixtures_df.team_h == id) | 
            (all_fixtures_df.team_a == id)) & (all_fixtures_df.finished == False)]
        fixtures_df['is_home_team'] = np.where(fixtures_df.team_h == id, True, False)
        fixtures_df['difficulty'] = np.where(fixtures_df.is_home_team == True,
                fixtures_df.team_h_difficulty, fixtures_df.team_a_difficulty)
        fixtures_df.sort_values(by=['event'])
        row = [name]
        for number in lookahead:
            row.append(round(fixtures_df.head(number).difficulty.mean(), 2))
        row.append(round(fixtures_df.difficulty.mean(), 2))
        x.add_row(row)

    with open('tpl_index.html', 'r') as file :
        filedata = file.read()

    filedata = filedata.replace('HTML_TABLE', x.get_html_string())
    filedata = filedata.replace('<table>', '<table class="styled-table">')

    with open('index.html', 'w') as file:
        file.write(filedata)
    # print(x.get_html_string())

#=====================================

def showMiniLeague(mini_league_code):
    mini_league_list, names, teams = getMiniLeague(mini_league_code)

    table = PrettyTable()
    table.field_names = ["Name", "Team name", "Total points","Benched Points", "Cost of Transfers", "Transfers"]

    for idx, row in enumerate(mini_league_list):
        if idx % 100 == 0:
            logging.info('Processing player count {}'.format(idx))
        points, bench_points, cost, transfers = getBenchedPoints(row)
        table.add_row([names[idx], teams[idx], points, bench_points, cost, transfers])

    print(table.get_string(sortby="Total points", reversesort=True))

#=====================================

def main():
    # displayMyPlayers(team_id)
    get_my_team(team_id)
    # printDifficulties()
    # displayTopPlayers()
    # printTeamForm()
    # showMiniLeague(mini_league_code)

#=====================================

if __name__ == "__main__":
    # execute only if run as a script
    main()
