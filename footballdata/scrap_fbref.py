import requests
from bs4 import BeautifulSoup

from footballdata.settings import leagues


# function to extract html document from given url
def getHTMLdocument(url):
    # request for HTML document of given url
    response = requests.get(url)

    # response will be provided in JSON format
    return response.text


my_dict = {}

for country in leagues:
    national_divisions = leagues[country]
    for tier in national_divisions:
        year = 1980
        tier_id = national_divisions[tier]["id"]
        print(f"Getting player data for {national_divisions[tier]['name']}")

        while year < 2023:
            url = f"https://fbref.com/en/comps/{tier_id}/{year}-{year+1}/stats/"
            year += 1
            html_document = getHTMLdocument(url)
            soup = BeautifulSoup(html_document, "html.parser")
            print(f"Season {year}-{year+1}")
            for tr in soup.find_all("table"):
                tds = tr.find_all("td")
                for td in tds:
                    if td.get("data-append-csv"):
                        player_url = td.find("a").get("href")
                        pl_list = player_url.split("/")
                        player_id = pl_list[3]
                        player_name = pl_list[4]
                        if player_name in my_dict.keys():
                            continue
                        my_dict[player_name] = {"id": player_id, "url": player_url}
        print(f"{'='*80}")
