# Helper functions
import logging
import os
from typing import Dict
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import bs4
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

from settings import (
    leagues,
    LEAGUE_URL,
)

# Create a logger object
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()

console_formatter = logging.Formatter(
    "\033[92m%(name)s - %(levelname)s - %(message)s\033[0m"
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


def get_squad_as_index(df: pd.DataFrame) -> pd.DataFrame:
    try:
        index = np.array(df["Unnamed: 0_level_0", "Squad"])
    except KeyError:
        try:
            index = np.array(df["Unnamed: 1_level_0", "Squad"])
        except KeyError:
            raise KeyError("NO SQUAD INFO")
    df.index = index

    return df


def get_season_years(year: int) -> str:

    if not isinstance(year, int):
        try:
            year = int(year)
        except TypeError:
            raise TypeError(
                f"Year value should be an int, or str you entered {year} which is {type(year)}."
            )
    if len(str(year)) != 4:
        raise KeyError("The value of year should be a 4 digit number")

    current_year = datetime.now().year
    first_data_year = 1888
    if year < first_data_year or year > current_year:
        raise KeyError(f"No football data for {year}")

    n_year = year + 1
    return f"{year}-{n_year}"


def edit_regular_season_table(regular_season_table: pd.DataFrame) -> pd.DataFrame:

    regular_season_table = regular_season_table.copy()
    # Top Team Scorer --> Most Goals (scored by a player)
    regular_season_table["M_G_Indv"] = regular_season_table["Top Team Scorer"].apply(
        lambda val: val.split("-")[-1]
    )

    cols_to_drop = ["Top Team Scorer", "Goalkeeper", "Notes"]
    regular_season_table = regular_season_table.drop(cols_to_drop, axis=1)

    return regular_season_table


def edit_home_away_table(home_away_table: pd.DataFrame) -> Dict:

    home_away_table = home_away_table.copy()
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


def remove_unnamed_cols(df: pd.DataFrame) -> pd.DataFrame:  # TODO: rename the function

    to_be_removed = [
        "Unnamed: 0_level_0",
        "Unnamed: 1_level_0",
        "Unnamed: 2_level_0",
        "Unnamed: 3_level_0",
    ]
    cols_to_rename = [col for col in df.columns.get_level_values(1) if " " in col]
    cols_to_rename.extend([col for col in df.columns.get_level_values(0) if " " in col])
    # Removing first Unnamed cols
    cols = [
        col
        for col in df.columns.get_level_values(0).unique()
        if col not in to_be_removed
    ]
    df = df[cols]

    unnamed_to_rename = [
        col
        for col in df.columns.get_level_values(0).unique()
        if col.startswith("Unnamed:")
    ]

    # Rename the columns
    df = df.rename(columns={col: "Details" for col in unnamed_to_rename})
    df = df.rename(columns={col: col.replace(" ", "_") for col in cols_to_rename})

    return df


def clean_opp_df(df_opp: pd.DataFrame) -> pd.DataFrame:

    # Removing the "vs " from the Opposition squad col
    df_opp["Unnamed: 0_level_0", "Squad"] = df_opp["Unnamed: 0_level_0", "Squad"].apply(
        lambda x: x.strip("vs ")
    )
    # Changing the col names of the opp df to have the "_Opp" suffix
    column_dict = {
        col_name: f"{col_name}_Opp" for col_name in df_opp.columns.get_level_values(1)
    }
    del column_dict["Squad"]
    del column_dict["# Pl"]
    df_opp = df_opp.rename(columns=column_dict)

    df_opp = get_squad_as_index(df_opp)
    df_opp = remove_unnamed_cols(df_opp)

    return df_opp


def clean_main_df(df: pd.DataFrame) -> pd.DataFrame:

    df = get_squad_as_index(df)
    df = remove_unnamed_cols(df)

    return df


def merge_dfs(df: pd.DataFrame, df_opp: pd.DataFrame) -> pd.DataFrame:

    return clean_main_df(df.copy()).join(clean_opp_df(df_opp.copy()))


def edit_squad_stats(
    squad_std_stats: pd.DataFrame, squad_opp_std_stats: pd.DataFrame
) -> pd.DataFrame:
    """Getting two dfs one with the teams std stats and one with their opposition.
    Editing and merging the two dfs into one.
    """

    squad_opp_std_stats = clean_opp_df(squad_opp_std_stats)

    # Dropping the first level of the cols in both dfs
    squad_std_stats = squad_std_stats.droplevel(level=0, axis=1)
    squad_opp_std_stats = squad_opp_std_stats.droplevel(level=0, axis=1)
    squad_df = pd.merge(squad_std_stats, squad_opp_std_stats, on="Squad")

    return squad_df


def edit_standard_stats_table(
    squad_std_stats: pd.DataFrame, squad_opp_std_stats: pd.DataFrame
) -> pd.DataFrame:
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
    squad_std_stats = squad_std_stats.copy()
    squad_opp_std_stats = squad_opp_std_stats.copy()
    squad_seasonal_stats = {}
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

    squad_opp_std_stats = get_squad_as_index(squad_opp_std_stats)

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

    squad_seasonal_stats = merge_dfs(squad_std_stats, squad_opp_std_stats)
    squad_seasonal_stats = squad_seasonal_stats.drop(
        columns="Playing_Time", axis=1, level=0
    )

    return squad_seasonal_stats


def edit_gk_tables(gk_df: pd.DataFrame, gk_opp_df: pd.DataFrame) -> pd.DataFrame:
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

    gk_df = get_squad_as_index(gk_df.copy())
    gk_opp_df = get_squad_as_index(gk_opp_df.copy())
    gk_df = gk_df.drop(["W", "D", "L"], axis=1, level=1)
    gk_opp_df = gk_opp_df.drop(["W", "D", "L"], axis=1, level=1)

    gk_overall = merge_dfs(gk_df, gk_opp_df)
    gk_overall = gk_overall.drop("Playing_Time", axis=1, level=0)

    return gk_overall


def get_year_at_season_st_of_tables(country: str, tier: int, year: int) -> list:
    league_id = leagues[country][tier]["id"]
    league_name = leagues[country][tier]["name"]
    season = get_season_years(year)

    leagues_list = pd.read_html(LEAGUE_URL.format(league_id, season))

    return leagues_list


class SetScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(chrome_options=options)
        self.tables_ids_prefixes = ["results", "stats"]
        self.failed_urls = []

    def scrap_url(self, url: str) -> bs4.BeautifulSoup:
        """Scraps the HTML document from the given URL and returns a BeautifulSoup object."""
        try:
            self.driver.get(url)
            html_document = self.driver.page_source
            soup = bs4.BeautifulSoup(html_document, "html.parser")
        except WebDriverException as e:
            logger.error(f"Failed to scrap URL {url}: {e}")
            self.failed_urls.append(url)
            return None

        return soup

    def get_league_url(self, country: str, tier: int, year: int) -> str:
        """Returns the URL for a given league based on the country, tier and year."""
        league_id = leagues[country][tier]["id"]
        season = get_season_years(year)

        url = LEAGUE_URL.format(league_id, season)

        return url

    def get_tables(self, soup: bs4.BeautifulSoup) -> Dict:
        # Creating pairs of table ids and DF names
        all_tables = soup.find_all("table")
        tables_ids = []
        for table in all_tables:
            id = table.get("id")
            if not id:
                continue
            for id_prefix in self.tables_ids_prefixes:
                if id.startswith(id_prefix):
                    tables_ids.append(id)

        tables_ids_df_names = {}
        for table_id in tables_ids:
            ids_chunks = table_id.split("_")
            if table_id.startswith("results"):
                suffix = "_".join(ids_chunks[1:])
                table_df_name = f"results_{suffix}"
            else:
                table_df_name = table_id

            tables_ids_df_names[table_id] = table_df_name

        tables = {}
        for table_id, table_df_name in tables_ids_df_names.items():
            table = soup.find("table", id=table_id)
            df = pd.read_html(str(table))[0]
            tables[table_df_name] = df

        return tables

    def create_single_season_dfs(self, tables: Dict) -> Dict:
        # breakpoint()
        seasons_data = {}
        # Edit original standing table
        results_overall = tables.get("results_overall")
        if results_overall is not None:
            """
            Regular Season Standing table
                :RK: Ranking
                :Squad: Team's Name
                :MP: Matched Played
                :W: Wins
                :D: Draws
                :L: Losses
                :GF: Goal For
                :GA: Goal Against
                :GD: Goal Difference
                :Pts: Points won
                :Pts/Mp: Points per Game
                :xG: Expected Goals
                :XGA: Expected Assists
                :XGD: Expected Goals Difference
                :Attendance: Average Home attendance
                :M_G_Indv: Most Goals Scored by one player.
            """
            regular_season = edit_regular_season_table(results_overall)
            seasons_data["standings_table"] = regular_season
        # Dictionary of 4 dfs. Home, Away, Home - Away, Home / Away stats
        home_away = tables.get("results_home_away")
        if home_away is not None:
            """
            Home Away data are 4 different dfs with the same columns
            - Home, Away, H-A, H/A -->
                :MP: Matched Played
                :W: Wins
                :D: Draws
                :L: Losses
                :GF: Goal For
                :GA: Goal Against
                :GD: Goal Difference
                :Pts: Points won
                :Pts/Mp: Points per Game
                :xG: Expected Goals
                :XGA: Expected Assists
                :XGD: Expected Goals Difference
            """
            # The first two dfs can be configured easily be calling clean_df on them
            home_away_data = edit_home_away_table(home_away)
            seasons_data["home"] = home_away_data["home"]
            seasons_data["away"] = home_away_data["away"]
            seasons_data["h-a"] = home_away_data["h-a"]
            seasons_data["h_div_a"] = home_away_data["h/a"]
        # Df for Standard, Performance, Per 90' and Expected stats
        squad_std_stats_for = tables.get("stats_squads_standard_for")
        squad_std_stats_against = tables.get("stats_squads_standard_against")
        if squad_std_stats_for is not None and squad_std_stats_against is not None:
            """
            - Standard  ->
                Df standard stats
                :#Pl: Number of Players used in games
                :Age: Age is weighted by minutes played
                :Poss: Possession, calculated as the % of passes attempted
            - Performance  ->
                DF Performance
                :Gls: Goals scored
                :Ast: Assists
                :G-PK: Non Penalty Goals (Total Goals - Pk)
                :PK: Penalty Goals
                :PKatt: Penalty kicks attempted
                :CrdY: Yellow Cards
                :CrdR: Red Cards
            - Per 90 Minutes'  ->
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
            - Expected  ->
                :xG: Expected Goals
                :npxG: Expected Non Penalty Goals
                :xAG: Expected Assists
                :npxG+xAG: Expected Non Penalty Goals and Expected Assists"""
            std_squads_stats = edit_standard_stats_table(
                squad_std_stats_for, squad_std_stats_against
            )
            seasons_data["standard_data"] = std_squads_stats
        # GoalKeeping General Stats
        gk_overall_for = tables.get("stats_squads_keeper_for")
        gk_overall_against = tables.get("stats_squads_keeper_against")
        if gk_overall_for is not None and gk_overall_against is not None:
            """
            GK Overall
            - Performance -->
                :GA: Goal Conceded
                :GA: Goals Conceded per 90'
                :SoTA: Shots on Target Against
                :Saves: Saves
                :Save%: Save percentage
                :CS: Clean Sheets
                :CS%: Clean Sheets percentage
            - Penalty Kicks -->
                :PKatt: Penalty Kicks Attempted
                :PKA: Penalty Kicks Allowed
                :PKsv: Penalty Kicks Saved
                :Save%: Penalty Kicks Saved Percentage
            """
            gk_overall = edit_gk_tables(gk_overall_for, gk_overall_against)
            seasons_data["gk_overall"] = gk_overall
        # Advanced Gk
        advanced_gk_for = tables.get("stats_squads_keeper_adv_for")
        advanced_gk_against = tables.get("stats_squads_keeper_adv_against")
        if advanced_gk_for is not None and advanced_gk_against is not None:
            """
            Advanced Goalkeeping
            - Goals -->
                :GA: Goal Against
                :PKA: Penalty Kicks Allowed
                :FK: FK Goals Conceded
                :CK: Goals Conceded by CornerKicks
                :OG: Own Goals
            - Expected -->
                :PSxG: Post-Shot Expected Goals: How likely is the goalkeeper to save the shot
                :PSxG/SoT: Post-Shot Expected Goal per Shot on Target
                :PSxG+/-: Post-Shot Expected Goals Minus Goals Allowed: numbers suggest better
                        luck or an above average ability to stop shots PSxG is expected goals based
                        on how likely the goalkeeper is to save the shot
                        Note: Does not include own goals xG totals include penalty kicks,
                :/90: Post-Shot Expected Goals Minus Goals Allowed per 90'
            - Launched (passes longer than 40 yrds) -->
                :Cmp: Launches Completed
                :Att: Launches Attempted
                :Cmp%: Percentage of Successful Launches attempted
            - Passes -->
                :Att: Passes Attempted
                :Thr: Throws Attempted
                :Launch%: Percentage of Launches out of the total attempted passes
                :AvgLen: Average length of Passes in yards
            - Goal Kicks -->
                :Att: Goal Kicks Attempted
                :Launch%: Percentage of Launches out of the total attempted Goal Kick
                :AvgLen: Average length of Goal Kick in yards
            - Crosses -->
                :Opp: Opponent's Attempted Crosses into penalty area
                :Stp: Number of crosses that were successfully stopped by a GoalKeeper
                :Stp%: Percentage of crosses that were successfully stopped by a GoalKeeper
            - Sweeper -->
                :#OPA: Number of defensive action outside the penalty area
                :#OPA/90: Number of defensive action outside the penalty area per 90'
                :AvgDist: Average distance from goal in yards of all defensive actions
            """
            advanced_gk = merge_dfs(advanced_gk_for, advanced_gk_against)
            seasons_data["gk_advanced"] = advanced_gk
        # Squad Shooting
        squad_shooting_for = tables.get("stats_squads_shooting_for")
        squad_shooting_against = tables.get("stats_squads_shooting_against")
        if squad_shooting_for is not None and squad_shooting_against is not None:
            """
            Squad Shooting
            - Standard shooting ->
                :Gls: Goals
                :Sht: Total Number of Shots
                :SoT: Total Number of Shots on Target
                :SoT%: Percentage of Shots on Target
                :Sh/90: Shots per 90'
                :G/Sh: Goal per Shot
                :G/SoT: Goal per Shot on Target
                :Dist: Average distance in yards, from goal of all shots taken
                :FK: Shots from Free Kicks
                :PK: Goals from Penalty Kicks  (TBR!)
                :PKatt: PKs Attempted          (TBR!)
            - Expected shooting stats ->
                :xG: Expected Goals
                :npxG: Non penalty xG
                :npxG/Sh: Non Penalty xG per shot
                :G-xG: Goals minus xG
                :np:G-xG:Non Penalty Goals minus Non Penalty xG

            """
            shooting_dfs = merge_dfs(squad_shooting_for, squad_shooting_against)
            seasons_data["shooting"] = shooting_dfs
        # Squad Passing
        squad_passing_for = tables.get("stats_squads_passing_for")
        squad_passing_against = tables.get("stats_squads_passing_against")
        if squad_passing_against is not None and squad_passing_against is not None:
            """
            Squad Passing
            - Total ->
                :Cmp: Passes Completed
                :Att: Passes Attempted
                :Cmp%: Completion Percentage
                :TotDist: Total distance in Yards that completed passes have traveled in any direction
                :PrgDist: Progressive distance: Total distance, in yards, that completed passes have
                        traveled towards the opponent's goal.
                        Note: Passes away from opponent's goal are counted as zero progressive yards.
            - Short Passes between 5-15 yards ->
                :Cmp: Short Passes Completed
                :Att: Passes Attempted
                :Cmp%: Completion Percentage
            - Medium  Passes between 15 - 30 yards ->
                :Cmp: Short Passes Completed
                :Att: Passes Attempted
                :Cmp%: Completion Percentage
            - Long Passes > 30 yards ->
                :Cmp: Short Passes Completed
                :Att: Passes Attempted
                :Cmp%: Completion Percentage
            - Advanced_Passing ->
                :Ast: Assists
                :xAG: Expected Assisted Goals
                :xA: The likelihood each completed pass becomes a goal assists given
                    the pass type, phase of play, location and distance.
                :A-xAG: Assists - Expected Assisted Goals
                :KP: Key Passes: Passes that directly lead to a shot (assisted shots)
                :1/3: Completed passes that enter the 1/3 of the pitch closest to the goal
                :PPA: Completed passes into the 18-yard box (not including set pieces)
                :CrsPA: Completed crosses into the 18-yard box (not including set pieces)
                :Prog: Progressive Passes: Completed passes that move the ball towards the
                    opponent's goal at least 10 yards from its furthest point in the last
                    six passes, or any completed pass into the penalty area.
                    Excludes passes from the defending 40% of the pitch
            """
            squad_passing_df = merge_dfs(squad_passing_for, squad_passing_against)
            squad_passing_df = squad_passing_df.rename(
                columns={"Details": "Advanced_Passing"}
            )
            seasons_data["passing"] = squad_passing_df
        # Squad Passing Type
        squad_pass_type_for = tables.get("stats_squads_passing_types_for")
        squad_pass_type_against = tables.get("stats_squads_passing_types_against")
        if squad_pass_type_for is not None and squad_pass_type_against is not None:
            """
            Pass Types
            - Total ->
                :Live: Live-Ball Passes (In play)
                :Dead: Dead-Ball Passes (From Fk, Ck, Kick Offs, Throw ins, and Goal Kicks)
                :FK: Passes from Free kicks
                :TB: Passes sent between the back defenders into open space.
                :Sw: Passes that traveled more than 40 yards of the width of the pitch
                :Crs: Crosses
                :TI:Throw-ins Taken
                :CK: Corner Kicks
            -   Corner Kicks ->
                :In: In-swinging Corner Kicks
                :Out: Out-swinging Corner Kicks
                :Str: Straight Corner Kicks
            - Outcomes ->
                :Cmp:  Passes Completed
                :Off: Offsides
                :Blocks: Blocked by the opponent who was standing in the path of the pass
            """
            squad_pass_type_df = merge_dfs(squad_pass_type_for, squad_pass_type_for)
            seasons_data["pass_type"] = squad_pass_type_for
        # Squad Goal and Shot Creation
        squad_gca_for = tables.get("stats_squads_gca_for")
        squad_gca_against = tables.get("stats_squads_gca_against")
        if squad_gca_for is not None and squad_gca_against is not None:
            """
            Goal And Shot Creation
            - SCA -->
            (Shot-Creation Actions)
                :SCA: Shot-Creating Actions: The two offensive actions directly leading
                    to a shot, such as passes, dribbles and drawing fouls.
                    Note: A single player can receive credit for multiple actions
                    and the shot-taker can also receive credit.
                :SCA90: Shot Creating Action per 90'
            - SCA Types -->
                :PassLive: Completed live-ball passes that lead to a shot attempt
                :PassDead: Completed dead-ball passes that lead to a shot attempt
                :Drib: Successful dribbles that lead to a shot attempt
                :Sh: Shots that lead to another shot attempt
                :Fld: Fouls Drawn that lead to a shot attempt
                :Def: Defensive actions that lead to a shot attempt
            - GCA -->
            (Goal-Creating Actions)
                :GCA: Goal-Creating Actions: The two offensive actions directly leading
                    to a goal, such as passes, dribbles and drawing fouls.
                    Note: A single player can receive credit for multiple actions
                    and the shot-taker can also receive credit.
                :GCA90: Goal-Creating Actions per 90'
            - GCA Types -->
                :PassLive: Completed live-ball passes that lead to a goal
                :PassDead: Completed dead-ball passes that lead to a goal
                :Drib: Successful dribbles that lead to a goal
                :Sh: Shots that lead to another shot attempt
                :Fld: Fouls Drawn that lead to a goal
                :Def: Defensive actions that lead to a goal
            """
            squad_goal_shot_creation_df = merge_dfs(squad_gca_for, squad_gca_against)
            seasons_data["gca"] = squad_goal_shot_creation_df
        # Squad Defending
        squad_defending_for = tables.get("stats_squads_defense_for")
        squad_defending_against = tables.get("stats_squads_defense_against")
        if squad_defending_for is not None and squad_defending_against is not None:
            """
            Defensive Actions
            - Tackles -->
                :Tkl: Number of players tackles
                :Tkl": Tackles that led to possession
                :Def_3rd: Tackles in defensive third
                :Mid_3rd: Tackles in middle third
                :Att_3rd: Tackles in attacking third
            - Vs_Dribbles -->
                :Tkl: Number of Dribbles tackled
                :Att: Number of time dribbled past plus number of tackles
                :Tkl%: Percentage of successfully tackled dribbles
                :Past: Number of times dribbled past by an opposing player
            - Blocks -->
                :Blocks: Number of times the ball was block by standing in its path
                :Sh: Number of blocked shots
                :Pass: Number of blocked passes
            - Advanced_Defending -->
                :Int: Interceptions
                :Tkl+Int: Number of Tackles and Interceptions
                :Clr: Clearances
                :Err: Mistakes leading to an opponent's shot
            """
            squad_defensive_actions_df = merge_dfs(
                squad_defending_for, squad_defending_against
            )
            squad_defensive_actions_df.rename(
                columns={"Details": "Advanced_Defending"}, inplace=True
            )
            seasons_data["defensive_actions"] = squad_defensive_actions_df
        # Squad Possession
        squad_possession_for = tables.get("stats_squads_possession_for")
        squad_possession_against = tables.get("stats_squads_possession_against")
        if squad_possession_for is not None and squad_possession_against is not None:
            """
            Squad Possession
            - Touches -->
                :Touches: Number of touches on the ball
                :Def_Pen: Touches in Defending Penalty Area
                :Def_3rd: Touches in defensive 3rd
                :Mid_3rd: Touches in middle 3rd
                :Att_3rd: Touches in attacking 3rd
                :Att_Pen: Touches in Attacking penalty area
                :Live: Live Ball Touches
            - Dribbles -->
                :Succ: Number of successful dribbles
                :Att: Number of attempted dribbles
                :Succ%: Percentage of successful dribbles
                :Mis: Number of times a player failed to gain control of the ball
                :Dis: Number of times a player lost control of the ball after been
                    tackled
            - Receiving -->
                :Rec: Number of times a player successfully received a pass
                :Prog: Progressive Passes Received: Completed passes that move the
                    ball towards the opponent's goal at least 10 yards from its
                    furthest point in the last six passes, or any completed pass
                    into the penalty area.
                    Excludes passes from the defending 40% of the pitch
            """
            squad_possession_stats = merge_dfs(
                squad_possession_for, squad_possession_against
            )
            seasons_data["possession"] = squad_possession_stats
        # Squad Other Stats
        squad_other_for = tables.get("stats_squads_misc_for")
        squad_other_against = tables.get("stats_squads_misc_against")
        if squad_other_for is not None and squad_other_against is not None:
            """
            Squad Other (Miscellaneous) Stats
            - Performance -->
                :CrdY: Number of Yellow Cards
                :CrdR: Number of Red Cards
                :2CrdY: Number of 2nd Yellow Cards
                :Fls: Fouls Committed
                :Fld: Fouls Won
                :Off: Number Offsides
                :Crs: Number of Crosses
                :Int: Number of Interceptions
                :Tkl: Number of Tackles Won
                :PKwon: Penalty Kicks won
                :PKcon: Penalty Kicks conceded
                :OG: Own Goals
                :Recov: Number of loose balls recovered
            - Aerial_Duels
                :Won: Number of Aerial Duels Won
                :Lost: Number of Aerial Duels Lost
                :Won%: Percentage of Aerial Duels Won
            """
            other_stats = merge_dfs(squad_other_for, squad_other_against)
            seasons_data["other"] = other_stats

        return seasons_data

    def get_single_season_league_dfs(self, country: str, tier: int, year: int) -> Dict:
        """Scraps the HTML document for a single season league and returns a dictionary."""
        url = self.get_league_url(country=country, tier=tier, year=year)
        soup = self.scrap_url(url=url)
        tables = self.get_tables(soup=soup)

        # return tables
        seasons_data = self.create_single_season_dfs(tables=tables)

        return seasons_data


def create_xlsx_from_dict(
    country: str, tier: int, season: str, data_dict: dict[str, pd.DataFrame]
) -> None:

    for data, df in data_dict.items():
        filename = f"{data}.xlsx"
        directory = Path(f"/home/grgkaralis/Documents/FootballData/footballdata/frames/{country}/{tier}/{season}/")
        path = Path(directory, f"{filename}")
        if not directory.exists():
            os.makedirs(directory)
        elif path.exists():
            logger.warning(f"{filename} exists")
            continue
        logger.info(f"Creating {path}")
        header = df.columns
        df.to_excel(path, header=header)


def year_at_season_st_list(year_range: str) -> list:
    """Create list of years to feed the get_single_season_league_data."""
    if not isinstance(year_range, str):
        raise TypeError(f"{year_range} is not a string.")

    years = year_range.split("-")
    if len(years) <= 1:
        raise KeyError("Year range input should look like this: '2010-2020'")
    start_year = int(years[0])
    end_year = int(years[1])
    if start_year >= end_year:
        raise KeyError(
            "First year of a year range can't be greater or equal to the last year"
        )
    year_at_season_st_list = [year for year in range(start_year, end_year)]

    return year_at_season_st_list


def create_multiple_season_dfs(country: str, tier: int, year_range: str) -> None:

    league_name = leagues[country][tier].get("name")
    files_to_check = [
        "standings_table.xlsx",
        "home_away.xlsx",
        "standard_data.xlsx",
        "gk_overall.xlsx",
        "gk_advanced.xlsx",
        "shooting.xlsx",
        "passing.xlsx",
        "pass_types.xlsx",
        "gca.xlsx",
        "defensive_actions.xlsx",
        "possession.xlsx",
        "other.xlsx",
    ]

    years = year_at_season_st_list(year_range)

    for year in years:
        season = get_season_years(year)
        path_of_data = Path(f"./frames/{country}/{tier}/{season}/")
        all_files_exist = all(
            [
                os.path.exists(os.path.join(path_of_data, file))
                for file in files_to_check
            ]
        )
        if all_files_exist:
            logger.warning(
                f"All the {league_name}'s data from the {season} season exist."
            )
            continue
        data_dict = get_single_season_league_data(country=country, tier=tier, year=year)
        create_xlsx_from_dict(
            country=country, tier=tier, season=season, data_dict=data_dict
        )
