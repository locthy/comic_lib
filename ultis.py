import os
import json
import re
from colorama import Fore, Style
import time
from bs4 import BeautifulSoup
from datetime import datetime


def get_comics(BASE_DIR):
    """Returns a list of comic dictionaries: [{'name': 'Ngu_Linh_The_Gioi', 'cover': '...'}]"""
    comics = []
    if not os.path.exists(BASE_DIR):
        return comics

    # Mẫu Regex hỗ trợ số thập phân: Chap_1 hoặc Chap_26_1
    chap_pattern = re.compile(r"^Chap_(\d+)(?:_(\d+))?$", re.IGNORECASE)

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

            # --- LOGIC CHANGE START ---
            # Thay thế list comprehension bằng vòng lặp rõ ràng để xử lý số thập phân
            chap_nums = []
            for f in os.listdir(comic_path):
                if os.path.isdir(os.path.join(comic_path, f)):
                    match = chap_pattern.match(f)
                    if match:
                        main_part = match.group(1)
                        decimal_part = match.group(2)
                        # Chuyển đổi thành float
                        if decimal_part:
                            chap_nums.append(float(f"{main_part}.{decimal_part}"))
                        else:
                            chap_nums.append(float(main_part))

            # Tìm chương cao nhất dựa trên giá trị số thực (float)
            highest_chapter = max(chap_nums) if chap_nums else 0.0
            # --- LOGIC CHANGE END ---
            if not isinstance(highest_chapter, float):
                highest_chapter = int(highest_chapter)
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


def get_date_time():
    now = datetime.now()
    # Định dạng: Ngày/Tháng/Năm Giờ:Phút:Giây
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    return dt_string


def save_or_update_json(json_path, new_data):
    """
    new_data: Có thể là một phần (dict nhỏ) hoặc toàn bộ (dict lớn)
    """
    # Bước 1: Đọc dữ liệu cũ nếu file đã tồn tại
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


def get_data_from_response(res):
    """Return a list of comics chapter
        EG: []"26.2", "26", "25", ...]
        from a response of http request

    Args:
        res (list): _description_
    """

    soup = BeautifulSoup(res.text, "html.parser")
    scripts = soup.find_all("li", class_="item_chap")
    comic_chapters = []

    for script in scripts:
        try:
            # 2. Giải mã chuỗi JSON bên trong thẻ
            link_tag = script.find("a")

            # 3. Kiểm tra xem đây có phải là thẻ chứa danh sách kết quả (ItemList) không
            if link_tag and link_tag.text:
                # 4. Lặp qua các phần tử trong itemListElement để lấy URL
                chapter = link_tag.text
                comic_chapters.append(chapter)

        except Exception:
            continue
    comic_chapters = list(map(lambda x: x.split(" ")[-1], comic_chapters))
    return comic_chapters
