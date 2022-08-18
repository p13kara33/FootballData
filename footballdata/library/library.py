from curses import window
import imp
import pandas as pd
import numpy as np
from .dataframe_format import secondary_games_cols


def unique_values_dict(games):
    """
    Gets a dataframe and returns dictionary
    with the unique values of each column
    """

    unique_values = {}
    for col in games:
        unique_values[col] = games[col].unique()

    return unique_values


def matches_to_team_conversion(games, team_name):
    """
    Receiving the league-matches dataframe and adjust it to the
    set format for each team individually."""
    primary_df = games.drop(secondary_games_cols, axis=1)
    team_df = primary_df[
        (primary_df["home_team_name"] == team_name)
        | (primary_df["away_team_name"] == team_name)
    ]

    # Creating the new columns
    team_df.loc[:, "Game_type"] = np.where(
        team_df.loc[:, "home_team_name"] == team_name, "home", "away"
    )
    team_df.loc[:, "Opponent"] = np.where(
        team_df.loc[:, "home_team_name"] != team_name,
        team_df.home_team_name,
        team_df.away_team_name,
    )
    team_df = team_df.drop(["home_team_name", "away_team_name"], axis=1)

    # When a team is playing at home their xG is derived from
    # the team_a_xg and when is not the team_b_xg represents its xG
    team_df.loc[:, "xG-F"] = np.where(
        team_df.loc[:, "Game_type"] == "home",
        team_df.loc[:, "team_a_xg"],
        team_df.loc[:, "team_b_xg"],
    )
    # When a team plays away the team_a_xg represents the Against xG
    # and when it plays at home the team_b_xg will be derived for its Against xG
    team_df.loc[:, "xG-A"] = np.where(
        team_df.loc[:, "Game_type"] == "away",
        team_df.loc[:, "team_a_xg"],
        team_df.loc[:, "team_b_xg"],
    )
    return team_df


def expected_goals_format(games, team_name):
    """
    Receiving the league-matches dataframe and creates df
    for one individual team with additional information regarding the
    eXpected Goals of the team in question.
    """
    team_df = matches_to_team_conversion(games, team_name)
    window_size = team_df.shape[0]
    # Creating the Xg columns
    team_df["xG_diff_pg"] = team_df.loc[:, "xG-F"] - team_df.loc[:, "xG-A"]
    team_df["xG-F_total"] = team_df.loc[:, "xG-F"].cumsum(axis=0)
    team_df["xG-A_total"] = team_df.loc[:, "xG-A"].cumsum(axis=0)
    team_df["xG_diff_total"] = team_df.loc[:, "xG_diff_pg"].cumsum(axis=0)

    return team_df


def matches_to_teams_conversion(games):
    all_teams = games["home_team_name"].unique().tolist()

    teams_performance = {}
    for team in all_teams:
        teams_performance[team] = expected_goals_format(games, team).reset_index(
            drop=True
        )

    return teams_performance


def moving_avg(games):
    """
    The first one should always be same as the total xG
    """

    teams_performance = matches_to_teams_conversion(games)
    game_weeks = np.array(games["Game Week"].unique())
    for team in teams_performance:
        team_df = teams_performance[team]
        xg_for = np.array(team_df["xG-F_total"])
        xg_against = np.array(team_df["xG-A_total"])
        xg_for_mavg = np.zeros_like(xg_for)
        xg_against_mavg = np.zeros_like(xg_against)

        for game_week in game_weeks:
            xg_for_mavg[game_week - 1] = xg_for[game_week - 1] / game_week
            xg_against_mavg[game_week - 1] = xg_against[game_week - 1] / game_week

        team_df["xG-F_Moving_average"] = xg_for_mavg
        team_df["xG-A_average"] = xg_against_mavg

        return teams_performance


def game_s_xg_distance(games):
    clubs = matches_to_team_conversion(games)

    # Use the moving average
    for club_name, club_df in clubs.items():
        for opponent in club_df[:, "Opponent"]:
            # club_df[:, "xG-distance"] = clubs["Opponent"]
            pass
