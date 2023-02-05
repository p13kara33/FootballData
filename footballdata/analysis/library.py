# Helper functions for creating specific data frames
# that will be used in plots
import logging
import pandas as pd

from footballdata.library import (
    year_at_season_st_list,
    get_season_years,
    create_xlsx_from_dict,
    SetScraper,
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


frames_dir = "/home/grgkaralis/Documents/FootballData/footballdata/frames/{}/{}/{}/{}"


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
    for year in year_at_season_st_list(year_range=year_range):
        season = get_season_years(year)
        seasons[season] = f"{df_name}.xlsx"

    return seasons


def n_season_standings(
    country: str, tier: int, year_range: str, save_df: bool = False
) -> dict:
    """Returns a dictionary with the each season's standings table."""

    seasons = season_df_pairs(year_range=year_range, df_name="standings_table")
    dfs = {}
    for season, file_name in seasons.items():
        full_path = frames_dir.format(country, tier, season, file_name)
        try:
            dfs[season] = pd.read_excel(full_path)
        except FileNotFoundError:
            logger.warning(f"Data for {country}'s {tier} tier doesn't exist for season {season}.")
            logger.info(f"Creating those data.")
            year = year_at_season_st_list(season)[0]
            data_dict = SetScraper().get_single_season_league_dfs(
                country=country, tier=tier, year=year
            )
            create_xlsx_from_dict(
                country=country, tier=tier, season=season, data_dict=data_dict
            )
            dfs[season] = pd.read_excel(full_path)
        dfs[season] = dfs[season].drop(columns="Unnamed: 0")
        dfs[season]["Season"] = season

    return dfs
