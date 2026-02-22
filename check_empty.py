import os
import re


# Configuration
# This should match the path in truyen.py
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static","kho_truyen", "ngu_linh_the_gioi")

def check_empty_chapters():
    if not os.path.exists(BASE_DIR):
        print(f"Directory not found: {BASE_DIR}")
        return

    print(f"Scanning {BASE_DIR} for empty chapters...")
    
    empty_chapters = []
    pattern = re.compile(r"Chap_(\d+)$")
    
    # Get all chapter folders
    items = os.listdir(BASE_DIR)
    
    # Sort them to make output cleaner
    # We want to sort by chapter number, not string
    sorted_items = []
    for item in items:
        match = pattern.match(item)
        if match:
             sorted_items.append((int(match.group(1)), item))
    
    sorted_items.sort()
    
    for chapter_num, folder_name in sorted_items:
        folder_path = os.path.join(BASE_DIR, folder_name)
        
        if os.path.isdir(folder_path):
            # Check for files
            files = os.listdir(folder_path)
            # Filter for images to be sure, or just check if empty
            images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            
            if not images:
                print(f"EMPTY: {folder_name}")
                empty_chapters.append(chapter_num)
            else:
                # Optional: Check if it has very few images? 
                # For now, user said "is empty"
                pass

    if empty_chapters:
        print("\nSummary of empty chapters:")
        print(f"{len(empty_chapters)} empty chapters found.")
        print(f"Chapter numbers: {empty_chapters}")
        
        print("\nTo redownload these, you can modify truyen.py loop:")
        print(f"for i in {empty_chapters}:")
        print("    download_chapter(i)")
        return empty_chapters
    else:
        print("\nNo empty chapter folders found!")
        return []

if __name__ == "__main__":
    empty = check_empty_chapters()
