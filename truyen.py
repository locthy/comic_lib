import os
import requests
import time
import json
import re
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from datetime import datetime
import threading
import concurrent.futures
import bisect
from ultis import save_or_update_json, get_date_time, get_data_from_response

# Khởi tạo (Cần thiết để chạy trên Windows)
init(autoreset=True)
# --- CONFIGURATION ---
# Base directory for all downloads
# KHO_TRUYEN_DIR = os.path.join("static", "kho_truyen")
KHO_TRUYEN_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static", "kho_truyen_local"
)
# Log file for failed downloads
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log_fail.json")
TIME_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "time.json")
AVG_TIME = 0

# Headers derived from your logs (Essential for bypassing bot detection)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://foxtruyen2.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}
BASE_URL = "https://foxtruyen2.com/"
MAX_RETRIES = 3


def log_failure(comic_name, chapter_num):
    """
    Logs a failed chapter to log_fail.json in the format:
    {
        "comic_name": "1, 2, 5"
    }
    """
    try:
        data = {}
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                try:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                except json.JSONDecodeError:
                    print(
                        Fore.YELLOW
                        + "Warning: log_fail.json is corrupted. Starting fresh."
                    )
                    data = {}

        # Get existing failures
        current_fails = data.get(comic_name, "")
        if current_fails:
            fail_list = [int(x.strip()) for x in current_fails.split(",") if x.strip()]
        else:
            fail_list = []

        # Add new failure if not exists
        if chapter_num not in fail_list:
            fail_list.append(chapter_num)
            fail_list.sort()

            # Update data
            data[comic_name] = ", ".join(map(str, fail_list))

            # Save back to file
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            print(Fore.RED + f"Logged failure for {comic_name} Chapter {chapter_num}")

    except Exception as e:
        print(Fore.RED + f"Failed to log failure: {e}")


def get_cookie():
    """
    Get cookies (session)
    return cookie
    """
    session = requests.Session()
    try:
        # 1. Truy cập trang chủ để server thiết lập Cookie ban đầu (GSession)
        print(
            f"{Fore.YELLOW}[SYSTEM]{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}Đang kết nối tới {BASE_URL} để lấy Cookie..."
        )
        response = session.get(BASE_URL, headers=HEADERS, timeout=15)

        # 2. Kiểm tra mã trạng thái
        if response.status_code == 200:
            # Trích xuất Cookie dưới dạng Dictionary để kiểm tra
            cookies = session.cookies.get_dict()
            if not "GSession" in cookies:
                print(
                    f"{Fore.LIGHTCYAN_EX}[INFO]{Style.RESET_ALL} Không tìm thấy GSession, nhưng đã có {len(cookies)} cookies khác."
                )

            return session
        else:
            print(
                f"{Fore.RED}[ERROR]{Style.RESET_ALL} Server trả về mã: {response.status_code}"
            )
            return None

    except Exception as e:
        print(f"{Fore.RED}[FATAL]{Style.RESET_ALL} Lỗi khởi tạo: {e}")
        return None


def get_comic_parse_data(soup):
    """
    Get a list of dictionary contains: name, url, cover, latest_chapter
    @param: soup - the DOM HTML after parsing using bs4
    Return list of dictionary : comics_data:[{
            "name": name,
            "url": url,
            "cover": cover,
            "latest_chapter": latest_chap
            }, ...]
    """
    items = soup.select(".list_item_home .item_home")

    comics_data = []

    for item in items:
        # 1. Lấy thẻ chứa tên và link truyện
        book_tag = item.select_one(".book_name")
        name = book_tag.text.strip()
        url = book_tag["href"]

        # 2. Lấy link ảnh bìa (Lưu ý: FoxTruyen dùng lazy-load nên phải lấy data-src)
        img_tag = item.select_one(".image-cover img")
        cover = img_tag.get("data-src") or img_tag.get("src")

        # 3. Lấy chương mới nhất
        latest_chap_tag = item.select_one(".cl99")
        latest_chap = latest_chap_tag.text.strip() if latest_chap_tag else "N/A"

        comics_data.append(
            {"name": name, "url": url, "cover": cover, "latest_chapter": latest_chap}
        )
    return comics_data


def get_comic():
    """
    Request BASE_URL + "tim-kiem.html?q=" + comic_code
    Retrive Comics
    Return comics_data:[{
            "name": name,
            "url": url,
            "cover": cover,
            "latest_chapter": latest_chap
            }, ...]
    """
    comic_name = input("Enter comic name: ").strip()
    comic_code = comic_name.replace(" ", "%20")
    url = BASE_URL + "tim-kiem.html?q=" + comic_code

    result = get_cookie()
    cookie_dict = result.cookies.get_dict()
    session = requests.Session()
    new_headers = HEADERS.copy()

    # Chuyển dictionary cookies thành chuỗi định dạng "key1=value1; key2=value2"
    cookie_string = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

    # Thêm vào header dưới key "Cookie"
    new_headers.update({"Cookie": cookie_string})
    if result:
        try:
            # 3. Truy cập trang chủ để server thiết lập Cookie ban đầu (GSession)
            # print(f"{Fore.LIGHTGREEN_EX}[SYSTEM]{Style.RESET_ALL} Đang kết nối tới {url} để lấy truyện ...")
            response = session.get(url, headers=new_headers, timeout=15)

            # 4. Kiểm tra mã trạng thái
            if response.status_code == 200:
                # Trích xuất Cookie dưới dạng Dictionary để kiểm tra
                soup = BeautifulSoup(response.text, "html.parser")
                comics_data = get_comic_parse_data(soup)
                return comics_data

            else:
                print(
                    f"{Fore.RED}[ERROR]{Style.RESET_ALL} Server trả về mã: {response.status_code}"
                )
                return None

        except Exception as e:
            print(f"{Fore.RED}[FATAL]{Style.RESET_ALL} Lỗi khởi tạo: {e}")
            return None


def show_comics(comics_data):
    """
    #Show the list of reference comics that user search
    #@param comics_data:[{
            "name": name,
            "url": url,
            "cover": cover,
            "latest_chapter": latest_chap
            }, ....]
    @Return a dictionary of the chosen comic_data
        {
            "name": name,
            "url": url,
            "cover": cover,
            "latest_chapter": latest_chap
        }
    """

    print(
        f"{Fore.LIGHTCYAN_EX}----------- {Fore.LIGHTYELLOW_EX}{f'Tìm thấy {len(comics_data)} truyện'} {Fore.LIGHTCYAN_EX}-----------{Style.RESET_ALL}"
    )
    for i, comic in enumerate(comics_data, 1):
        print(
            f"{i}. Truyện {Fore.LIGHTGREEN_EX}{comic['name']}{Style.RESET_ALL} {Fore.LIGHTCYAN_EX}| {comic['latest_chapter']}"
        )

    comic_index = int(
        input(
            Fore.LIGHTYELLOW_EX + "Please choose a comic to install (Example: 1) : "
        ).strip()
    )
    print(Fore.LIGHTGREEN_EX + f"[Successful] {comics_data[comic_index - 1]['name']}!")
    return comics_data[comic_index - 1]


def extract_comic_info(url):
    """
    Extracts comic name and ID from URL.
    @param url: A link to a chapter
    Example: https://foxtruyen2.com/truyen-tranh/ta-la-ta-de-36199.html
    Returns: comic_name, comic_id
    Example: ('ta-la-ta-de', '36199')
    """
    try:
        # Remove base url part
        path = url.split("/truyen-tranh/")[-1]
        # path : ta-la-ta-de-36199-chap-96.html

        # Remove .html
        if path.endswith(".html"):
            path = path[:-5]
            # ta-la-ta-de-36199

        last_dash_index = path.rfind("-")
        comic_id = path[last_dash_index + 1 :]
        comic_name = path[:last_dash_index]

        return comic_name, comic_id
    except Exception as e:
        print(Fore.RED + f"Error parsing URL: {e}")
        return None, None


def download_chapter(comic_name, comic_id, chapter_num, comic_data):

    global AVG_TIME
    # 1. Chuẩn hóa tên để làm folder (lowercase, underscores)
    comic_folder = comic_name.lower().replace("-", "_")
    # Tên slug dùng cho URL (dashes)
    slug = comic_name.lower().replace("_", "-")
    url_chap = str(chapter_num).replace(".", "-")
    folder_chap = str(chapter_num).replace(".", "_")
    chapter_url = (
        f"https://foxtruyen2.com/truyen-tranh/{slug}-{comic_id}-chap-{url_chap}.html"
    )

    # Định nghĩa các đường dẫn
    comic_root = os.path.join(KHO_TRUYEN_DIR, comic_folder)
    output_folder = os.path.join(comic_root, f"Chap_{folder_chap}")
    json_path = os.path.join(comic_root, "info.json")

    # Tạo thư mục gốc và lưu info.json (Chỉ làm nếu chưa có hoặc cập nhật)
    os.makedirs(comic_root, exist_ok=True)

    save_or_update_json(json_path, comic_data)

    # Kiểm tra xem chương này đã tải chưa (Skip nếu > 5 ảnh)

    os.makedirs(output_folder, exist_ok=True)
    # print(Fore.LIGHTCYAN_EX + f"\n=== Starting Chapter {chapter_num} ===")

    session = requests.Session()
    try:
        # CHỈ GỌI GET 1 LẦN DUY NHẤT
        response = session.get(chapter_url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(
                Fore.RED
                + f"Failed to fetch comic: {comic_name} | chapter: {chapter_num} {response.status_code}"
            )
            print(chapter_url)
            return

        soup = BeautifulSoup(response.text, "html.parser")

        # 2. Xử lý Thumbnail (Chỉ tải nếu chưa có)
        thumb_path = os.path.join(comic_root, "thumbnail.jpg")
        if not os.path.exists(thumb_path):
            meta_image = soup.find("meta", property="og:image")
            if meta_image:
                thumb_url = meta_image["content"]
                try:
                    img_data = session.get(thumb_url, headers=HEADERS, timeout=10)
                    if img_data.status_code == 200:
                        with open(thumb_path, "wb") as f:
                            f.write(img_data.content)
                        print(Fore.LIGHTGREEN_EX + "Downloaded thumbnail.jpg")
                except:
                    pass

        # 3. Lấy danh sách ảnh
        image_tags = soup.find_all("img")
        image_urls = []
        for img in image_tags:
            src = img.get("data-original") or img.get("data-src") or img.get("src")
            if src and "hinhgg.com" in src and "avatar.hinhgg.com" not in src:
                image_urls.append(src)

        # Fallback pattern
        if not image_urls:
            print(Fore.YELLOW + "Attempting pattern generation...")
            base_cdn = f"https://hinhgg.com/{comic_id}/{chapter_num}/"
            image_urls = [f"{base_cdn}{i}.jpg" for i in range(1, 150)]

        # 4. Tải ảnh hàng loạt
        start_time = time.time()
        success_count = 0
        # print(Fore.YELLOW + f"Found {len(image_urls)}images | Downloading ... ")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            # Giao việc cho workers (Submit tasks)
            for i, img_url in enumerate(image_urls):
                filename = os.path.join(output_folder, f"page_{i:04}.jpg")

                # GIAO VIỆC: executor.submit(tên_hàm, tham_số_1, tham_số_2, ...)
                task = executor.submit(
                    download_single_image, img_url, filename, session
                )
                futures.append(task)

            # Thu thập kết quả khi workers làm xong (Collect results)
            for future in concurrent.futures.as_completed(futures):
                result = future.result()

                if result == True:
                    success_count += 1
                elif result == "404":
                    # Lưu ý: Vì đã giao việc (submit) hết 150 tasks rồi,
                    # nên ta không thể 'break' dễ dàng như chạy tuần tự được.
                    # Nhưng kệ nó, worker gặp 404 sẽ tự dừng rất nhanh.
                    pass

        # 5. Thống kê
        total_seconds = time.time() - start_time
        if success_count > 0:
            AVG_TIME = (AVG_TIME + float(total_seconds) / int(success_count)) / 2

    except Exception as e:
        print(Fore.RED + f"Error: {e} {chapter_num}")


def download_single_image(img_url, filename, session):
    """Một worker sẽ chạy hàm này để tải 1 bức ảnh với cơ chế thử lại (retry)"""
    if os.path.exists(filename):
        return True  # Đã tồn tại (Already exists)
    MAX_RETRIES = 3
    # Lặp đúng 3 lần (Loop exactly 3 times)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # timeout=10 đảm bảo nó không bị treo vĩnh viễn
            img_res = session.get(img_url, headers=HEADERS, timeout=10)

            if img_res.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(img_res.content)
                # print(f"{Fore.LIGHTGREEN_EX}Downloaded{Style.RESET_ALL} -> {filename}")
                return True  # Thành công, thoát hàm ngay! (Success, exit function!)

            elif img_res.status_code == 404:
                return "404"  # Báo hiệu hết chương (End of chapter)

            else:
                # Bắt lỗi HTTP khác (vd: 502 Bad Gateway)
                print(
                    f"{Fore.YELLOW}Lần thử {attempt} thất bại (Mã lỗi {img_res.status_code}) cho {img_url}{Style.RESET_ALL}"
                )

        except Exception as e:
            # Bắt lỗi mất kết nối mạng (Network timeout)
            print(
                f"{Fore.YELLOW}Lần thử {attempt} rớt mạng cho {img_url}: {e}{Style.RESET_ALL}"
            )

        # Nếu code chạy đến đây, nghĩa là đã thất bại.
        # Chờ 2 giây trước khi thử lại (trừ khi đây là lần thử cuối cùng)
        if attempt < MAX_RETRIES:
            time.sleep(2)

    # Nếu vòng lặp chạy xong mà vẫn chưa return, nghĩa là cả 3 lần đều hỏng.
    print(
        f"{Fore.RED}Bỏ cuộc! Không thể tải {img_url} sau {MAX_RETRIES} lần thử.{Style.RESET_ALL}"
    )
    return False


def get_chapters(url):
    """
    return a list of downloadable chapter of the comic EG: ["26.2", "26", "25", ...]
    @param url: (EG) "https://foxtruyen2.com/truyen-tranh/ta-la-ta-de-36199.html"
    """
    session = requests.Session()
    response = session.get(url, headers=HEADERS, timeout=10)
    comic_name, comic_id = extract_comic_info(url)
    if response.status_code != 200:
        print(Fore.RED + f"Failed to fetch comic {comic_name}: {response.status_code}")
        return

    result = get_data_from_response(response)
    return result


def get_highest_chapter(comic_name):
    """
    Find the highest available chapter of comic in storage (Count the highest num of the folder name)
    @param comic_name: comic name format (ta-la-ta-de)
    return int | chap_num ? exist : 0
    """
    comic_path = os.path.join(KHO_TRUYEN_DIR, comic_name.replace("-", "_"))
    # 1. Create the folder if it doesn't exist
    if not os.path.exists(comic_path):
        return 0
    else:
        folders = [
            f
            for f in os.listdir(comic_path)
            if os.path.isdir(os.path.join(comic_path, f))
        ]
        chapter_numbers = []
        for f in folders:
            # Tìm các con số trong tên folder (ví dụ: 'Chap_505' -> '505')
            match = re.search(r"\d+", f)
            if match:
                chapter_numbers.append(int(match.group()))

    # Trả về số lớn nhất, nếu danh sách rỗng thì trả về 0
    return max(chapter_numbers) if chapter_numbers else 0

def getListOfDownloadChapter (startChap, endChapter, listComicChapter):
    listComicChapter = [float(x) for x in listComicChapter]

    startChapIndex = bisect.bisect_right(listComicChapter, startChap)
    endChapIndex = bisect.bisect_right(listComicChapter, endChapter)
    return listComicChapter[startChapIndex:endChapIndex]

def download_multi():
    # .map() automatically applies the function to every item in the list
    # .map() tự động áp dụng hàm cho từng phần tử trong danh sách
    start_chap, end_chap, comic_name, comic_id, comic_data, comic_url = handle_io()
    # get the list of downloadable chapters
    chapter_list = getListOfDownloadChapter(start_chap, end_chap, get_chapters(comic_url)[::-1]) #reverse to [1, 2, 3] instead of [3, 2, 1]
    highest_chap = get_highest_chapter(comic_name)
    if highest_chap > 0 and not end_chap < highest_chap:
        target_index = -1

        # 1. Search for the index of the latest chapter
        # 1. Tìm kiếm chỉ mục của chương mới nhất
        for index, chap_string in enumerate(chapter_list):
            # We convert latest_chap to a string to check if it's inside the URL/title
            # Chúng ta chuyển đổi latest_chap thành chuỗi để kiểm tra xem nó có nằm trong URL/tiêu đề không
            if str(highest_chap) in chap_string:
                target_index = index
                break  # Found it! Stop searching. / Tìm thấy rồi! Dừng tìm kiếm.

        # 2. Slice the list if we successfully found the index
        # 2. Cắt danh sách nếu chúng ta tìm thấy chỉ mục thành công
        if target_index != -1:
            # We use target_index + 1 to grab everything AFTER the latest chapter
            # Chúng ta dùng target_index + 1 để lấy mọi thứ SAU chương mới nhất
            chapter_list = chapter_list[target_index + 1 :]

    for chapter in (chapter_list):
        download_chapter(comic_name, comic_id, chapter, comic_data)

    date_time = get_date_time()
    if len(chapter_list) == 0:
        print(
            Fore.LIGHTCYAN_EX
            + f"[{date_time}] {Fore.LIGHTYELLOW_EX} There is no new chapter!!"
        )
    elif(len(chapter_list) == 1):
        print(
            Fore.LIGHTCYAN_EX
            + f"[{date_time}] Download{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{comic_name} {Fore.LIGHTYELLOW_EX} Chapter {chapter_list[0]}"
        )
    else:
        print(
            Fore.LIGHTCYAN_EX
            + f"[{date_time}] Download{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{comic_name} {Fore.LIGHTYELLOW_EX}| From chapter {chapter_list[-1]} to {chapter_list[0]}"
        )


def handle_io():
    global AVG_TIME
    comics_data = None
    while True:
        # Get the list of dictionaries of comics data that user search
        comics_data = get_comic()
        if comics_data:
            break
    # get a comic data in dictionary that user want
    comic_data = show_comics(comics_data)
    comic_url = comic_data["url"]
    # set the latest_chapter: "chuong 67.2" -> "67.2"
    comic_max_chapter = int(float(comic_data["latest_chapter"].strip().split(" ")[-1]))
    comic_name, comic_id = extract_comic_info(comic_url)

    highest_chapter_in_library = get_highest_chapter(comic_name)

    if comic_name and comic_id:
        print(
            Fore.LIGHTYELLOW_EX
            + f"Detected Comic: {comic_name} (ID: {comic_id}) | Chapter: {comic_max_chapter}"
        )
        if highest_chapter_in_library > 0:
            print(
                Fore.LIGHTGREEN_EX
                + f"Library is up to {highest_chapter_in_library} chapters of {comic_data['name']}"
            )
        # Ask for range
        start_chap = None
        end_chap = None
        while True:
            start_chap = input(
                Fore.LIGHTBLUE_EX
                + f"Start Chapter [Default {highest_chapter_in_library}]: "
            ).strip()
            if not start_chap:
                start_chap = highest_chapter_in_library
                break
            else:
                start_chap = int(start_chap)
                if start_chap < 0 or start_chap > comic_max_chapter:
                    print(Fore.YELLOW + "Please Enter a valid chapter: ")
                else:
                    break

        while True:
            end_chap = input(
                Fore.LIGHTCYAN_EX + f"End Chapter [Default {comic_max_chapter}]: "
            ).strip()
            if not end_chap:
                end_chap = comic_max_chapter
                break
            else:
                end_chap = int(end_chap)
                if end_chap < start_chap or end_chap > comic_max_chapter:
                    print(Fore.YELLOW + "Please Enter a valid chapter: ")
                else:
                    break

        print(
            Fore.LIGHTGREEN_EX
            + f"Downloading {comic_name} | from chapters {start_chap} to {end_chap}..."
        )
        return start_chap, end_chap, comic_name, comic_id, comic_data, comic_url

    return


def run_main():
    # thread_download =  threading.Thread(target=download_multi)
    # thread_download.start()
    download_multi()


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
        run_main()
