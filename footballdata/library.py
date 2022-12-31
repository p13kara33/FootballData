# Helper functions
from calendar import c
import numpy as np
import pandas as pd

from settings import (
    leagues,
    LEAGUE_URL,
)


def get_season_years(year):
    n_year = year + 1
    return f"{year}-{n_year}"


def edit_regular_season_table(regular_season_table):

    # Top Team Scorer --> Most Goals (scored by a player)
    regular_season_table["M_G_Indv"] = regular_season_table["Top Team Scorer"].apply(
        lambda val: val.split("-")[-1]
    )

    cols_to_drop = ["Top Team Scorer", "Goalkeeper", "Notes"]
    regular_season_table.drop(cols_to_drop, axis=1, inplace=True)

    return regular_season_table


def edit_home_away_table(home_away_table):

    squads = home_away_table["Unnamed: 1_level_0", "Squad"]
    index = pd.MultiIndex.from_arrays(
        [np.arange(1, 21), np.array(squads)], names=["Rk", "Squads"]
    )

    home_stats = home_away_table["Home"]
    home_stats.index = index
    away_stats = home_away_table["Away"]
    away_stats.index = index
    h_a_diff_stats = home_stats - away_stats
    h_a_diff_stats.index = index
    h_a_prop_stats = home_stats / away_stats
    h_a_prop_stats.index = index

    home_away_stats = {
        "home": home_stats,
        "away": away_stats,
        "h-a": h_a_diff_stats,
        "h/a": h_a_prop_stats,
    }
    return home_away_stats


def _edit_opp_df(squad_opp_std_stats):

    # Removing the "vs " from the Opposition squad col
    squad_opp_std_stats["Unnamed: 0_level_0", "Squad"] = squad_opp_std_stats[
        "Unnamed: 0_level_0", "Squad"
    ].apply(lambda x: x.strip("vs "))
    # Changing the col names of the opp df to have the "_Opp" suffix
    column_dict = {
        col_name: f"{col_name}_Opp"
        for col_name in squad_opp_std_stats.columns.get_level_values(1)
    }
    del column_dict["Squad"]
    del column_dict["# Pl"]
    squad_opp_std_stats = squad_opp_std_stats.rename(columns=column_dict)

    return squad_opp_std_stats


def edit_squad_stats(squad_std_stats, squad_opp_std_stats):
    """Getting two dfs one with the teams std stats and one with their opposition.
    Editing and merging the two dfs into one.
    """

    squad_opp_std_stats = _edit_opp_df(squad_opp_std_stats)

    # Dropping the first level of the cols in both dfs
    squad_std_stats = squad_std_stats.droplevel(level=0, axis=1)
    squad_opp_std_stats = squad_opp_std_stats.droplevel(level=0, axis=1)
    squad_df = pd.merge(squad_std_stats, squad_opp_std_stats, on="Squad")

    return squad_df


def _create_squad_tables(column_name, squad_df, opp_squad_df):

    squad_df = squad_df[column_name]
    opp_squad_df = opp_squad_df[column_name]
    df_merged = pd.merge(squad_df, opp_squad_df, right_index=True, left_index=True)

    return df_merged


def edit_standard_stats_table(squad_std_stats, squad_opp_std_stats):
    """Taking as an input the Team's and their opposition team's stats and create
    5 tables.

    - Standard
        Df standard stats
        :#Pl: Number of Players used in games
        :Age: Age is weighted by minutes played
        :Age_Opp: Age of the opposition teams
        :Poss: Possession, calculated as the % of passes attempted
        :Poss_Opp: The % of passes attempted by the opposition teams
    - Performance
        DF Performance
        :Gls_Opp: Goals conceded
        :Ast_Opp: Assists allowed
        :G-PK_Opp: No penalty goals conceded
        :PK_Opp:  Goals from Penalty conceded
        :PKatt_Opp: Penalty Kicks attempted by opposition teams
        :CrdY_Opp: Yellow Cards the opposition received
        :CrdR_Opp: Red Cards the opposition received
        :Gls: Goals scored
        :Ast: Assists
        :G-PK: Non Penalty Goals (Total Goals - Pk)
        :PK: Penalty Goals
        :PKatt: Penalty kicks attempted
        :CrdY: Yellow Cards
        :CrdR: Red Cards
    - Per 90 Minutes'
        :Gls_Opp: Goals allowed per 90'
        :Ast_Opp: Assists allowed per 90'
        :G+A_Opp: Goals and Assists allowed per 90'
        :G-PK_Opp: Non Penalty Goals allowed per 90'
        :G+A-PK_Opp: Non Penalty Goals and assists allowed per 90'
        :xG_Opp: Expected Goals of opposition allowed per 90'
        :xAG_Opp: Expected Assists of opposition allowed per 90'
        :xG+xAG_Opp: Expected Goals and expected Assists of opposition allowed per 90'
        :npxG_Opp: Non penalty Expected Goals of opposition allowed per 90'
        :npxG+xAG_Opp: Non Penalty Expected Goals and Expected Assists of opposition allowed by 90'
        :Gls: Goals scored per 90'
        :Ast: Assists made per 90'
        :G+A: Goal and Assists per 90'
        :G-PK: Non Penalty Goals per 90'
        :G+A-PK: Non Penalty Goals and Assists per 90'
        :xG: Expected Goals per 90'
        :xAG: Expected Assists per 90'
        :xG+xAG: Expected Goals and Expected Assists per 90'
        :npxG: Expected Non Penalty Goals per 90'
        :npxG+xAG: Expected Non Penalty Goals and Expected Assists per 90'
    - Expected
        :xG_Opp: Expected Goals allowed
        :npxG_Opp: Expected Non Penalty Goals allowed
        :xAG_Opp: Expected Assists allowed
        :npxG+xAG_Opp: Expected Non Penalty Goals and Expected Assists allowed
        :xG: Expected Goals
        :npxG: Expected Non Penalty Goals
        :xAG: Expected Assists
        :npxG+xAG: Expected Non Penalty Goals and Expected Assists

    """
    squad_seasonal_stats = {}
    squad_opp_std_stats = _edit_opp_df(squad_opp_std_stats.copy())

    index = np.array(squad_std_stats["Unnamed: 0_level_0", "Squad"])
    unnamed_cols = [
        col
        for col in squad_std_stats.columns.get_level_values(0).unique()
        if col.startswith("Unnamed:")
    ]
    squad_opp_std_stats.index = index
    squad_std_stats.index = index

    df_std = squad_std_stats[unnamed_cols].droplevel(0, axis=1)
    df_std_opp = squad_opp_std_stats[unnamed_cols].droplevel(0, axis=1)
    df_std_squads = pd.merge(df_std, df_std_opp, on=["Squad", "# Pl"])

    squad_seasonal_stats["Standard"] = df_std_squads

    for column_name in ["Performance", "Per 90 Minutes", "Expected"]:
        df = _create_squad_tables(column_name, squad_opp_std_stats, squad_std_stats)
        squad_seasonal_stats[column_name] = df

    return squad_seasonal_stats


def edit_gk_talbes(gk_df, gk_opp_df):
    """
    Taking as an input the 2 gk tables and generating 1

    - Gk Overall:
        :SoTA: Shot on Target Against 
        :Saves: Saves 
        :Save%: Save percentage
        :CS: Clean Sheets
        :CS%: Clean Sheets percentage 
        :PKA:
        :PKsv: Penalty Kicks Saved
        ::
        :Save%: Penalty Save Percentage
        :SoTA_Opp: Shot on Target Against of Opposition Gks
        :Saves_Opp: Saves of Opposition Gks
        :Save%_Opp: Save Percentage of Opposition Gks
        :CS_Opp: Clean sheets of Opposition Gks
        :CS%_Opp: Clean sheets percentage of Opposition Gks
        :PKsv_Opp: Penalty Saved by Opposition Gks
        :Save%_Opp: Penalty Saved percentage by Opposition Gks
    """
    index = np.array(gk_df["Unnamed: 0_level_0", "Squad"])
    for df in [gk_df, gk_opp_df]:
        df.index = index

    del_cols = ["W", "D", "L", "GA", "GA90", "PKatt", "PKA", "PKm"]
    col_0 = [["Performance", "Penalty Kicks"], [ "Goals", "Expected", "Launched", "Passes", "Goal Kicks", "Crosses", "Sweeper"]]
    gk_df = gk_df[col_0[0]]
    gk_df = gk_df.droplevel(0, axis=1)
    gk_df.drop(columns=del_cols, inplace=True)

    gk_opp_df = _edit_opp_df(gk_opp_df)
    gk_opp_df = gk_opp_df[col_0[0]]
    gk_opp_df = gk_opp_df.droplevel(0, axis=1)
    gk_opp_df.drop(columns=[f"{col}_Opp" for col in del_cols], inplace=True)

    gk_overall = gk_df.join(gk_opp_df)

    return gk_overall


def get_single_season_league_data(country, tier, year):
    league_id = leagues[country][tier]["id"]
    league_name = leagues[country][tier]["name"]
    season = get_season_years(year)

    leagues_list = pd.read_html(LEAGUE_URL.format(id, season))

    # Edit original tables
    regular_season = edit_regular_season_table(leagues_list[0].copy())
    # Dictionary of 4 dfs. Home, Away, Home - Away, Home / Away stats
    home_away = edit_home_away_table(leagues_list[1].copy())
    # Dictionary of 4 dfs. Standard, Performance, Per 90' and Expected stats
    std_squads_stats = edit_standard_stats_table(leagues_list[2].copy(), leagues_list[3].copy())
    gk_overall = edit_gk_talbes(leagues_list[4].copy(), leagues_list[5].copy())
    # TODO: Advanced Gk

    
    return leagues_list
