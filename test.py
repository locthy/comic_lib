import os
import requests
import time
import json
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

init(autoreset=True)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://foxtruyen2.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}
BASE_URL = "https://foxtruyen2.com/"


def test():
    
    session = requests.Session()
    try:
        # 3. Truy cập trang chủ để server thiết lập Cookie ban đầu (GSession)
        print(f"{Fore.YELLOW}[SYSTEM]{Style.RESET_ALL} Đang kết nối tới {BASE_URL} để lấy Cookie...")
        response = session.get(BASE_URL, headers=HEADERS, timeout=15)
        
        # 4. Kiểm tra mã trạng thái
        if response.status_code == 200:
            # Trích xuất Cookie dưới dạng Dictionary để kiểm tra
            cookies = session.cookies.get_dict()
            if 'GSession' in cookies:
                print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Đã lấy được GSession: {cookies['GSession'][:10]}...")
            else:
                print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Không tìm thấy GSession, nhưng đã có {len(cookies)} cookies khác.")
                
            return session
        else:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Server trả về mã: {response.status_code}")
            return None, None

    except Exception as e:
        print(f"{Fore.RED}[FATAL]{Style.RESET_ALL} Lỗi khởi tạo: {e}")
        return None, None

def get_comic():
    comic_name = input("Enter comic name: ").strip()
    comic_code = comic_name.replace(" ", "%20")
    url = BASE_URL + "tim-kiem.html?q=" + comic_code
    print(url)

    result = test()
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
            print(f"{Fore.GREEN}[SYSTEM]{Style.RESET_ALL} Đang kết nối tới {url} để lấy truyện ...")
            response = session.get(url, headers=new_headers, timeout=15)
            
            # 4. Kiểm tra mã trạng thái
            if response.status_code == 200:
                # Trích xuất Cookie dưới dạng Dictionary để kiểm tra
                soup = BeautifulSoup(response.text, 'html.parser')
                scripts = soup.find_all('script', type='application/ld+json')
                comic_urls = []

                for script in scripts:
                    try:
                        # 2. Giải mã chuỗi JSON bên trong thẻ
                        data = json.loads(script.string)
                        
                        # 3. Kiểm tra xem đây có phải là thẻ chứa danh sách kết quả (ItemList) không
                        if data.get('@type') == 'ItemList':
                            # 4. Lặp qua các phần tử trong itemListElement để lấy URL
                            for item in data.get('itemListElement', []):
                                url = item.get('url')
                                if url:
                                    comic_urls.append(url)

                        print(f"{Fore.CYAN}--- Tìm thấy {len(comic_urls)} truyện ---{Style.RESET_ALL}")
                        for i, url in enumerate(comic_urls, 1):
                            print(f"{i}. {Fore.GREEN}{url}{Style.RESET_ALL}")
                    except (json.JSONDecodeError, TypeError):
                        continue
                
            else:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Server trả về mã: {response.status_code}")
                return None, None

        except Exception as e:
            print(f"{Fore.RED}[FATAL]{Style.RESET_ALL} Lỗi khởi tạo: {e}")
            return None, None
            
def test1(url):
    """
    Extracts comic name and ID from URL.
    Example: https://foxtruyen2.com/truyen-tranh/ta-la-ta-de-36199-chap-96.html
    Returns: ('ta-la-ta-de', '36199', '96')
    """
    # Pattern to match: .../slug-id-chap-num.html
    # We want to capture the slug (name), id, and current chapter num
    # Since extracting the name might be tricky due to variable dashes, we can split by common parts
    try:
        # Remove base url part
        path = url.split("/truyen-tranh/")[-1] 
        # path is like: ta-la-ta-de-36199-chap-96.html
        
        # Remove .html
        if path.endswith(".html"):
            path = path[:-5]
            #ta-la-ta-de-36199
            
        last_dash_index = path.rfind("-")
        comic_id = path[last_dash_index+1:]
        comic_name = path[:last_dash_index]

        return comic_name, comic_id
    except Exception as e:
        print(Fore.RED + f"Error parsing URL: {e}")
        return None, None, None

# In kết quả với màu sắc cho dễ nhìn
import os

import os

def force_lowercase_folders(parent_dir):
    for folder_name in os.listdir(parent_dir):
        old_path = os.path.join(parent_dir, folder_name)
        
        if os.path.isdir(old_path):
            new_name = folder_name.lower()
            
            # Chỉ xử lý nếu tên cũ có chứa chữ hoa
            if folder_name != new_name:
                temp_path = os.path.join(parent_dir, folder_name + "_temp")
                final_path = os.path.join(parent_dir, new_name)
                
                try:
                    # Bước 1: Đổi sang tên tạm
                    os.rename(old_path, temp_path)
                    # Bước 2: Đổi từ tên tạm sang tên chữ thường
                    os.rename(temp_path, final_path)
                    print(f"Done: {folder_name} -> {new_name}")
                except Exception as e:
                    print(f"Lỗi với {folder_name}: {e}")

# Chạy script
force_lowercase_folders("static/kho_truyen")

# Sử dụng script cho folder kho_truyen của bạn



