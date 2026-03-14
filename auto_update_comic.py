from truyen import download_chapter, extract_comic_info, getListOfDownloadChapter
import os
import requests
import json
import bisect
from colorama import Fore, Style, init
from ultis import get_comics, countdown_timer, get_date_time, get_data_from_response

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
RESET_TIME = 12 * 60 * 60


def extract_comic_info_with_chapter(url):
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
        highest_chapter = float(comic_data["highest_chapter"])
        latest_chapter = float(str(comic_data["latest_chapter"].split(" ")[-1]))

        if highest_chapter != latest_chapter:
            continue

        comic_name, comic_id = extract_comic_info(url)

        response = session.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(
                Fore.RED + f"Failed to fetch comic {comic_name}: {response.status_code}"
            )
            return

        detail_data = get_data_from_response(response)
        new_latest_chapter = float(detail_data[0])

        comic_download_list = getListOfDownloadChapter(
            latest_chapter, new_latest_chapter, detail_data[::-1]
        )
        if new_latest_chapter % 1 == 0:
            new_latest_chapter = int(new_latest_chapter)

        if latest_chapter % 1 == 0:
            latest_chapter = int(latest_chapter)

        comic_dic = {"latest_chapter": f"Chương {new_latest_chapter}"}

        if len(comic_download_list) == 0:
            continue

        for chapter in comic_download_list:
            download_chapter(comic_name, comic_id, chapter, comic_dic)

        date_time = get_date_time()
        if new_latest_chapter - highest_chapter == 1:
            print(
                Fore.LIGHTCYAN_EX
                + f"[{date_time}] Download{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{comic_name} {Fore.LIGHTYELLOW_EX}| Chapter {new_latest_chapter} "
            )
        else:
            print(
                Fore.LIGHTCYAN_EX
                + f"[{date_time}] Download{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{comic_name} {Fore.LIGHTYELLOW_EX}| From chapter {latest_chapter + 1} to {new_latest_chapter}"
            )


def run():
    get_new_chapter()
    countdown_timer(RESET_TIME)


if __name__ == "__main__":
    print(
        Fore.LIGHTGREEN_EX + "--------------------------------------------------------"
    )
    print(
        Fore.LIGHTGREEN_EX + "------------------- COMIC DOWNLOADER -------------------"
    )
    print(
        Fore.LIGHTGREEN_EX + "--------------------------------------------------------"
    )
    while True:
        run()
