from truyen import download_chapter, get_highest_chapter, extract_comic_info
import os
import requests
import time
import json
import re
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from datetime import datetime
from ultis import get_comics, countdown_timer

init(autoreset=True)

BASE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static", "kho_truyen_local"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://foxtruyen2.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}
BASE_URL = "https://foxtruyen2.com/"
CHAPTER_DIFF = 5
RESET_TIME = 4 * 60 * 60


def get_data_from_response(res):
    """Return a list of comics url
        EG: "https://foxtruyen2.com/truyen-tranh/yuusha-izoku-57826-chap-4.html"
        from a response of http request

    Args:
        res (list): _description_
    """

    soup = BeautifulSoup(res.text, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")
    comic_urls = []

    for script in scripts:
        try:
            # 2. Giải mã chuỗi JSON bên trong thẻ
            data = json.loads(script.string)

            # 3. Kiểm tra xem đây có phải là thẻ chứa danh sách kết quả (ItemList) không
            if data.get("@type") == "ItemList":
                # 4. Lặp qua các phần tử trong itemListElement để lấy URL
                for item in data.get("itemListElement", []):
                    url = item.get("url")
                    if url:
                        comic_urls.append(url)

        except (json.JSONDecodeError, TypeError):
            continue
    return comic_urls


def extract_comic_infoss(url):
    """
    Extracts comic name and ID from URL.
    @param url: A link to a chapter
    Example: https://foxtruyen2.com/truyen-tranh/ta-la-ta-de-36199-chap-4.html
    Returns: comic_name, comic_id, chapter
    Example: ('ta-la-ta-de', '36199', 4)
    """
    try:
        # Remove base url part
        path = url.split("/truyen-tranh/")[-1]
        # path : ta-la-ta-de-36199-chap-4.html

        # Remove .html
        if path.endswith(".html"):
            path = path[:-5]
            # ta-la-ta-de-36199-chap-4

        # 2. Split by dash into a list
        # ['ta', 'la', 'ta', 'de', '36199', 'chap', '4']
        parts = path.split("-")

        # 3. Extract from the end (backward indexing)
        chapter = parts[-1]  # The very last part (4)
        # parts[-2] is "chap" (we can skip it)
        comic_id = parts[-3]  # The ID (36199)

        # 4. Join everything else back together for the name
        # Joins everything from index 0 up to -3
        comic_name = "-".join(parts[:-3])

        return comic_name, comic_id, chapter
    except Exception as e:
        print(Fore.RED + f"Error parsing URL: {e}")
        return None, None, None


def get_new_chapter():
    comics_data = get_comics(BASE_DIR)
    session = requests.Session()

    for comic_data in comics_data:
        url = comic_data["url"]
        highest_chapter = int(comic_data["highest_chapter"])

        response = session.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(Fore.RED + f"Failed to load page: {response.status_code}")
            return

        detail_data = get_data_from_response(response)
        latest_chapter = len(detail_data)
        comic_name, comic_id = extract_comic_info(url)
        comic_dic = {"latest_chapter": f"Chương {latest_chapter}"}
        diff = latest_chapter - highest_chapter

        if 0 < diff < 5:
            for chapter in range(highest_chapter + 1, latest_chapter + 1):
                print(
                    Fore.LIGHTCYAN_EX
                    + f"[Starting] download{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{comic_name} {Style.RESET_ALL}| Chapter{Fore.LIGHTYELLOW_EX} {chapter} "
                )
                download_chapter(comic_name, comic_id, chapter, comic_dic)


def run():
    get_new_chapter()
    print(Fore.LIGHTCYAN_EX + "Sleep ...............")
    countdown_timer(RESET_TIME)


if __name__ == "__main__":
    while True:
        print(
            Fore.LIGHTGREEN_EX
            + "--------------------------------------------------------"
        )
        print(
            Fore.LIGHTGREEN_EX
            + "------------------- COMIC DOWNLOADER -------------------"
        )
        print(
            Fore.LIGHTGREEN_EX
            + "--------------------------------------------------------"
        )
        run()
