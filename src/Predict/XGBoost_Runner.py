import copy

import numpy as np
import pandas as pd
import xgboost as xgb
from colorama import Fore, Style, init, deinit
from src.Utils import Expected_Value
from src.Utils import Kelly_Criterion as kc

from datetime import date
from src.Utils.ses import send_email_with_attachment
import json


# from src.Utils.Dictionaries import team_index_current
# from src.Utils.tools import get_json_data, to_data_frame, get_todays_games_json, create_todays_games
init()
xgb_ml = xgb.Booster()
# xgb_ml.load_model('Models/XGBoost_Models/XGBoost_68.7%_ML-4.json')
xgb_ml.load_model('Models/XGBoost_Models/XGBoost_68.7%_ML-4.json')
xgb_uo = xgb.Booster()
# xgb_uo.load_model('Models/XGBoost_Models/XGBoost_53.7%_UO-9.json')
xgb_uo.load_model('Models/XGBoost_Models/XGBoost_54.4%_UO-9.json')


def xgb_runner(data, todays_games_uo, frame_ml, games, home_team_odds, away_team_odds, kelly_criterion):
    ml_predictions_array = []

    for row in data:
        ml_predictions_array.append(xgb_ml.predict(xgb.DMatrix(np.array([row]))))

    frame_uo = copy.deepcopy(frame_ml)
    frame_uo['OU'] = np.asarray(todays_games_uo)
    data = frame_uo.values
    data = data.astype(float)

    ou_predictions_array = []

    for row in data:
        ou_predictions_array.append(xgb_uo.predict(xgb.DMatrix(np.array([row]))))

    count = 0
    jars_bets = []
    for game in games:
        home_team = game[0]
        away_team = game[1]
        winner = int(np.argmax(ml_predictions_array[count]))
        under_over = int(np.argmax(ou_predictions_array[count]))
        winner_confidence = ml_predictions_array[count]
        un_confidence = ou_predictions_array[count]
        if winner == 1:
            winner_confidence = round(winner_confidence[0][1] * 100, 1)
            if under_over == 0:
                un_confidence = round(ou_predictions_array[count][0][0] * 100, 1)
                if un_confidence > 63:
                    if not todays_games_uo[count] == None:
                        jars_bets.append({'type': 'OU', 'home_team': home_team, 'away_team': away_team, 'confidence': un_confidence, 'line': 'U' + str(todays_games_uo[count])})
                print(
                    Fore.GREEN + home_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ' vs ' + Fore.RED + away_team + Style.RESET_ALL + ': ' +
                     Fore.MAGENTA + 'UNDER ' + Style.RESET_ALL + str(
                         todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL)
            else:
                un_confidence = round(ou_predictions_array[count][0][1] * 100, 1)
                if un_confidence > 63:
                    if not todays_games_uo[count] == None:
                        jars_bets.append({'type': 'OU', 'home_team': home_team, 'away_team': away_team, 'confidence': un_confidence, 'line': 'O' + str(todays_games_uo[count])})
                print(
                    Fore.GREEN + home_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ' vs ' + Fore.RED + away_team + Style.RESET_ALL + ': ' +
                    Fore.BLUE + 'OVER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL)
        else:
            winner_confidence = round(winner_confidence[0][0] * 100, 1)
            if under_over == 0:
                un_confidence = round(ou_predictions_array[count][0][0] * 100, 1)
                if un_confidence > 63:
                    if not todays_games_uo[count] == None:
                        jars_bets.append({'type': 'OU', 'home_team': home_team, 'away_team': away_team, 'confidence': un_confidence, 'line': 'U' + str(todays_games_uo[count])})
                print(
                    Fore.RED + home_team + Style.RESET_ALL + ' vs ' + Fore.GREEN + away_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ': ' +
                    Fore.MAGENTA + 'UNDER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL)
            else:
                un_confidence = round(ou_predictions_array[count][0][1] * 100, 1)
                if un_confidence > 63:
                    if not todays_games_uo[count] == None:
                        jars_bets.append({'type': 'OU', 'home_team': home_team, 'away_team': away_team, 'confidence': un_confidence, 'line': 'O' + str(todays_games_uo[count])})
                print(
                    Fore.RED + home_team + Style.RESET_ALL + ' vs ' + Fore.GREEN + away_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ': ' +
                    Fore.BLUE + 'OVER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL)
        count += 1

    if kelly_criterion:
        print("------------Expected Value & Kelly Criterion-----------")
    else:
        print("---------------------Expected Value--------------------")
    count = 0
    for game in games:
        home_team = game[0]
        away_team = game[1]
        ev_home = ev_away = 0
        if home_team_odds[count] and away_team_odds[count]:
            ev_home = float(Expected_Value.expected_value(ml_predictions_array[count][0][1], int(home_team_odds[count])))
            ev_away = float(Expected_Value.expected_value(ml_predictions_array[count][0][0], int(away_team_odds[count])))
        expected_value_colors = {'home_color': Fore.GREEN if ev_home > 0 else Fore.RED,
                        'away_color': Fore.GREEN if ev_away > 0 else Fore.RED}

        if home_team_odds[count]:
            bankroll_descriptor = ' Fraction of Bankroll: '
            bankroll_fraction_home = bankroll_descriptor + str(kc.calculate_kelly_criterion(home_team_odds[count], ml_predictions_array[count][0][1])) + '%'
            jars_kc_home = kc.calculate_kelly_criterion(home_team_odds[count], ml_predictions_array[count][0][1])
            print
            if jars_kc_home > 50:
                jars_bets.append({'type': 'ML', 'team': home_team, 'units': str(jars_kc_home / 100)})
            print(home_team + ' EV: ' + expected_value_colors['home_color'] + str(ev_home) + Style.RESET_ALL + (bankroll_fraction_home if kelly_criterion else ''))

        
        if away_team_odds[count]:
            bankroll_descriptor = ' Fraction of Bankroll: '
            bankroll_fraction_away = bankroll_descriptor + str(kc.calculate_kelly_criterion(away_team_odds[count], ml_predictions_array[count][0][0])) + '%'     
            jars_kc_away = kc.calculate_kelly_criterion(away_team_odds[count], ml_predictions_array[count][0][0])
            if jars_kc_away > 50:
                jars_bets.append({'type': 'ML', 'team': away_team, 'units': str(jars_kc_away / 100)})
            print(away_team + ' EV: ' + expected_value_colors['away_color'] + str(ev_away) + Style.RESET_ALL + (bankroll_fraction_away if kelly_criterion else ''))

        count += 1

    if jars_bets:
        formatted_jars_bets = []

        for data in jars_bets:
            if data['type'] == 'ML':
                result_string = f"{data['away_team']} at {data['team']} {data['units']}"
            elif data['type'] == 'OU':
                result_string = f"{data['away_team']} at {data['home_team']} {data['line']}"
            else:
                result_string = "Invalid data type"  # Handle other types if needed
            formatted_jars_bets.append(result_string)

        send_email_with_attachment("Jar's Picks", json.dumps(jars_bets, indent=4))
        send_email_with_attachment("Jar's Formatted Picks", json.dumps(formatted_jars_bets, indent=4))
    else: 
        send_email_with_attachment("No Picks For Todays Games", f"No picks for {date.today()} games.")

    deinit()
