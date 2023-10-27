# Helper functions for creating specific data frames
# that will be used in plots

import pandas as pd

from footballdata.library import get_season_years, year_at_season_start_list

frames_dir = "../frames/{}/{}/{}/{}"


def season_df_pairs(year_range: str, df_name: str) -> dict:
    """Gets a range of years and a df name and returns
    the dictionary of season and it's pairs

        :country: Name of the country in Initial Case (the first letter Capital)
        :tier: The level of the league
        :year_range: The first year of the first season the last year of the last season
                        splitted by a "_"
        :df_name: Name of the table in the DB select one of those:
                "standings_table",
                "home_away",
                "standard_data",
                "gk_overall",
                "gk_advanced",
                "shooting",
                "passing",
                "pass_types",
                "gca",
                "defensive_actions",
                "possession",
                "other"

        Returns a dict: dict {"year_0-year_1": "df_name.xlsx", "year_1-year_2": "df_name.xlsx"}
    """
    # Creating the seasons' years one by one
    seasons = {}
    for year in year_at_season_start_list(year_range=year_range):
        season = get_season_years(year)
        seasons[season] = f"{df_name}.xlsx"

    return seasons


def n_season_standings(
    country: str, tier: int, year_range: str, save_df: bool = False
) -> dict:
    """Returns a dictionary with the each season's standings table."""

    seasons = season_df_pairs(year_range=year_range, df_name="standings_table")
    dfs = {}

    # TODO: if file is not found create it !
    for season, file_name in seasons.items():
        full_path = frames_dir.format(country, tier, season, file_name)
        dfs[season] = pd.read_excel(full_path)
        dfs[season].drop(columns="Unnamed: 0", inplace=True)
        dfs[season]["Season"] = season

    return dfs
