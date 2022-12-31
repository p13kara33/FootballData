#### URLS ####

LEAGUE_URL = "https://fbref.com/en/comps/{}/{}/"

fc_ids = {
    "Manchester Utd": {
        "Manchester-United-Stats" : 19538871,
    }
}


#### League Dictionary Format ####
# "country": {
#         tier_no: {
#             "id": int
#             "name": str
#             "abbrv": None
#         }
#     }

leagues = {
    "England": {
        1: {"id": 9, "name": "Premier League", "abbrv": "EPL", "gender": "M"},
        2: {"id": 10, "name": "Championship", "abbrv": None, "gender": "M"},
        3: {"id": 15, "name": "League One", "abbrv": None, "gender": "M"},
        4: {"id": 16, "name": "League Two", "abbrv": None, "gender": "M"},
    },
    "Italy": {
        1: {"id": 11, "name": "Seria A", "abbrv": None, "gender": "M"},
        2: {"id": 18, "name": "Seria B", "abbrv": None, "gender": "M"},
    },
    "Germany": {
        1: {"id": 20, "name": "Bundesliga", "abbrv": None, "gender": "M"},
        2: {"id": 2, "name": "2 Bundesliga", "abbrv": None, "gender": "M"},
        3: {"id": 59, "name": "3 Liga", "abbrv": None, "gender": "M"},
    },
    "Spain": {
        1: {"id": 12, "name": "La Liga", "abbrv": None, "gender": "M"},
        2: {"id": 17, "name": "Segunda Division", "abbrv": None, "gender": "M"},
    },
    "France": {
        1: {"id": 13, "name": "Ligue 1", "abbrv": None, "gender": "M"},
        2: {"id": 60, "name": "Ligue 2", "abbrv": None, "gender": "M"},
    },
    "USA": {
        1: {"id": 22, "name": "Major League Soccer", "abbrv": "MLS", "gender": "M"}
    },
    "Norway": {1: {"id": 28, "name": "Eliteserien", "abbrv": None, "gender": "M"}},
    "Scotland": {
        1: {"id": 40, "name": "Scottish Premiership", "abbrv": "SPL", "gender": "M"}
    },
    "Portugal": {1: {"id": 32, "name": "Primeira Liga", "abbrv": None, "gender": "M"}},
    "Netherlands": {1: {"id": 23, "name": "Eredevisie", "abbrv": None, "gender": "M"}},
    "Greece": {
        1: {"id": 27, "name": "Super-League-Greece", "abbrv": None, "gender": "M"}
    },
    "Sweden": {1: {"id": 29, "name": "Allsvenskan", "abbrv": None, "gender": "M"}},
    "Russia": {
        1: {"id": 30, "name": "Russian Premier League", "abbrv": None, "gender": "M"}
    },
    "Turkey": {1: {"id": 26, "name": "Super Lig", "abbrv": None, "gender": "M"}},
    "Poland": {1: {"id": 36, "name": "Ekstraklasa", "abbrv": None, "gender": "M"}},
    "Finland": {1: {"id": 43, "name": "Veikkausliiga", "abbrv": None, "gender": "M"}},
    "Ukraine": {
        1: {"id": 39, "name": "Ukrainian Premier League", "abbrv": None, "gender": "M"}
    },
    "Switzerland": {
        1: {"id": 57, "name": "Swiss Super League", "abbrv": None, "gender": "M"}
    },
    "Mexico": {1: {"id": 31, "name": "Liga MX", "abbrv": None, "gender": "M"}},
    "Denmark": {1: {"id": 50, "name": "Superliga", "abbrv": None, "gender": "M"}},
    "Belgium": {
        1: {"id": 37, "name": "Belgian First Division A", "abbrv": None, "gender": "M"}
    },
    "Austria": {
        1: {"id": 56, "name": "Austrian Bundesliga", "abbrv": None, "gender": "M"}
    },
    "Hungary": {1: {"id": 46, "name": "NB I", "abbrv": None, "gender": "M"}},
    "Romania": {1: {"id": 47, "name": "Liga I", "abbrv": None, "gender": "M"}},
    "Croatia": {1: {"id": 63, "name": "1 HNL", "abbrv": None, "gender": "M"}},
    "Serbia": {
        1: {"id": 54, "name": "Serbian SuperLiga", "abbrv": None, "gender": "M"}
    },
    "Czech Republic": {
        1: {"id": 66, "name": "Czech First League", "abbrv": None, "gender": "M"}
    },
    "Bulgaria": {
        1: {"id": 67, "name": "Bulgarian First League", "abbrv": None, "gender": "M"}
    },
    "Peru": {1: {"id": 44, "name": "Liga 1", "abbrv": None, "gender": "M"}},
    "Paraguay": {
        1: {"id": 61, "name": "Primera Division", "abbrv": None, "gender": "M"}
    },
}
