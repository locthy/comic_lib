import threading
import concurrent.futures
import time

# ---------------------------------------------------------
# 1. THE TASKS (Công việc thực tế)
# ---------------------------------------------------------

def handle_general_io():
    """This runs continuously in Thread 1"""
    for i in range(3):
        print(f"[Thread 1] Đang xử lý I/O chung... ({i+1}/3)")
        time.sleep(1.5)
    print("[Thread 1] Hoàn thành I/O chung!")

def download_single_image(image_id):
    """This is the task for the 4 workers inside Thread 2"""
    print(f"   -> [Worker] Đang tải ảnh {image_id}...")
    time.sleep(2) # Giả lập thời gian tải (Simulate download time)
    return f"Ảnh {image_id} đã xong!"

# ---------------------------------------------------------
# 2. THE MANAGER (Người quản lý - Chạy trong Thread 2)
# ---------------------------------------------------------

def image_download_manager():
    """This runs in Thread 2 and manages the 4 workers"""
    print("[Thread 2] Bắt đầu Quản lý Tải ảnh. Khởi tạo 4 workers...")
    image_list = [1, 2, 3, 4, 5, 6, 7, 8] # 8 images to download
    
    # NESTED WORKERS: Creating a pool inside this thread
    # CÔNG NHÂN LỒNG NHAU: Tạo hồ chứa bên trong luồng này
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(download_single_image, image_list)
        
        for res in results:
            print(f"   -> [Manager Nhận Kết Quả] {res}")
            
    print("[Thread 2] Hoàn thành toàn bộ việc tải ảnh!")

# ---------------------------------------------------------
# 3. MAIN PROGRAM (Chương trình chính)
# ---------------------------------------------------------

if __name__ == "__main__":
    print("[Main] Chương trình bắt đầu.\n")

    # Create the two top-level threads
    # Tạo 2 luồng quản lý cấp cao nhất
    thread_io = threading.Thread(target=handle_general_io)
    thread_images = threading.Thread(target=image_download_manager)

    # Start them both
    # Chạy cả 2 luồng
    thread_io.start()
    thread_images.start()

    print("[Main] Cả 2 hệ thống đã chạy ngầm. Main vẫn có thể làm việc khác.\n")

    # Wait for both systems to finish before closing the app
    # Chờ cả 2 hệ thống xong việc mới tắt app
    thread_io.join()
    thread_images.join()

    print("\n[Main] Tất cả hoàn tất. Tắt chương trình.")