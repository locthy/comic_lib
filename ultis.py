import os
import json
import re
from colorama import Fore, Style
import time
import sys


def get_comics(BASE_DIR):
    """Returns a list of comic dictionaries: [{'name': 'Ngu_Linh_The_Gioi', 'cover': '...'}]"""
    comics = []
    if not os.path.exists(BASE_DIR):
        return comics

    for item in os.listdir(BASE_DIR):
        comic_path = os.path.join(BASE_DIR, item)
        if os.path.isdir(comic_path):
            json_path = os.path.join(comic_path, "info.json")
            display_name = item.replace("_", " ")  # Tên mặc định nếu ko có JSON
            latest_chapter = ""
            url = ""
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Lấy tên từ JSON (giả sử key là 'name')
                        display_name = data.get("name", display_name)
                        latest_chapter = data.get("latest_chapter", latest_chapter)
                        url = data.get("url", url)
                except Exception as e:
                    print(f"Lỗi đọc JSON tại {item}: {e}")

            # Find highest chapter number from Chap_X folders
            chap_pattern = re.compile(r"^Chap_(\d+)$")
            chap_nums = [
                int(m.group(1))
                for f in os.listdir(comic_path)
                if os.path.isdir(os.path.join(comic_path, f))
                for m in [chap_pattern.match(f)]
                if m
            ]
            highest_chapter = max(chap_nums) if chap_nums else 0

            comics.append(
                {
                    "name": item,
                    "display_name": display_name,
                    "latest_chapter": latest_chapter,
                    "highest_chapter": highest_chapter,
                    "url": url,
                }
            )

    return comics


def countdown_timer(seconds):
    while seconds > 0:
        # Chuyển đổi giây thành Phút:Giây (Convert to Min:Sec)
        mins, secs = divmod(seconds, 60)
        timer = f"{mins:02d}:{secs:02d}"

        # In đè lên dòng cũ bằng \r (Overwrite line using \r)
        print(
            f"{Fore.LIGHTGREEN_EX}Next check in: {Fore.WHITE}{timer} {Fore.LIGHTGREEN_EX}remaining...{Style.RESET_ALL}",
            end="\r",
        )

        time.sleep(1)
        seconds -= 1

    # Xóa dòng đếm ngược khi kết thúc (Clear the line when done)
    print(" " * 50, end="\r")


def save_or_update_json(json_path, new_data):
    """
    new_data: Có thể là một phần (dict nhỏ) hoặc toàn bộ (dict lớn)
    """
    # Bước 1: Đọc dữ liệu cũ nếu file đã tồn tại
    print(json_path)
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                current_data = json.load(f)
            except json.JSONDecodeError:
                current_data = {}
    else:
        # Nếu file chưa tồn tại, bắt đầu bằng một dict trống
        current_data = {}

    # Bước 2: Hợp nhất dữ liệu (Đây là phần quan trọng nhất)
    # Nếu key đã có -> nó sẽ cập nhật giá trị mới
    # Nếu key chưa có -> nó sẽ thêm key mới vào
    current_data.update(new_data)

    # Bước 3: Ghi lại vào file
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(current_data, f, ensure_ascii=False, indent=4)
