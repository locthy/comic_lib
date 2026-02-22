import os
import re
import argparse
import json
from flask import Flask, render_template, send_from_directory, redirect, url_for, abort

app = Flask(__name__)

# Configuration
# BASE_DIR points to "kho_truyen" which contains comic folders
#BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"static", "kho_truyen")
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"static", "kho_truyen_local")
PORT = 5000

# Ensure base dir exists
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

def get_comics():
    """Returns a list of comic dictionaries: [{'name': 'Ngu_Linh_The_Gioi', 'cover': '...'}]"""
    comics = []
    if not os.path.exists(BASE_DIR):
        return comics

    for item in os.listdir(BASE_DIR):
        comic_path = os.path.join(BASE_DIR, item)
        if os.path.isdir(comic_path):
            json_path = os.path.join(comic_path, 'info.json')
            display_name = item.replace('_', ' ') # Tên mặc định nếu ko có JSON
            latest_chapter = "";
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Lấy tên từ JSON (giả sử key là 'name')
                        display_name = data.get('name', display_name)
                        latest_chapter = data.get('latest_chapter', latest_chapter)
                except Exception as e:
                    print(f"Lỗi đọc JSON tại {item}: {e}")
            
            comics.append({
                'name': item,
                'display_name': display_name,
                'latest_chapter': latest_chapter
            })
            
    return comics

def get_chapters(comic_name):
    """
    Scans the comic directory for folders matching 'Chap_X'
    Returns a sorted list of dictionaries: [{'id': 1, 'name': 'Chapter 1', 'folder': 'Chap_1'}, ...]
    """
    chapters = []
    comic_path = os.path.join(BASE_DIR, comic_name)
    
    if not os.path.exists(comic_path):
        return []

    pattern = re.compile(r"Chap_(\d+)$")
    
    for item in os.listdir(comic_path):
        if os.path.isdir(os.path.join(comic_path, item)):
            match = pattern.match(item)
            if match and len(os.listdir(os.path.join(comic_path, item))) > 2:
                chapter_num = int(match.group(1))
                chapters.append({
                    'id': chapter_num,
                    'folder': item,
                    'name': f"Chapter {chapter_num}"
                })
    
    # Sort by chapter number
    chapters.sort(key=lambda x: x['id'])
    return chapters

def get_comic_name(comic_name):
    comics = get_comics()
    current_comic_info = next((c for c in comics if c['name'] == comic_name), None)
    
    # Nếu tìm thấy thì lấy display_name, không thì lấy tên folder
    display_name = current_comic_info['display_name'] if current_comic_info else comic_name.replace('_', ' ')
    return display_name

@app.route('/')
def index():
    comics = get_comics()
    return render_template('index.html', comics=comics)

@app.route('/wtf/')
def view_wtf():
    comics = get_comics()
    return render_template('wtf.html', comics=comics)

@app.route('/comic/<comic_name>')
def view_comic(comic_name):
    chapters = get_chapters(comic_name)
    
    display_name = get_comic_name(comic_name)
    return render_template('chapter_list.html', comic_name=comic_name, chapters=chapters, display_name=display_name)

@app.route('/read/<comic_name>/<int:chapter_id>')
def view_chapter(comic_name, chapter_id):
    chapters = get_chapters(comic_name)
    current_chapter = next((c for c in chapters if c['id'] == chapter_id), None)
    
    display_name = get_comic_name(comic_name)
    if not current_chapter:
        return abort(404, description="Chapter not found")

    # Find prev/next chapters
    current_index = chapters.index(current_chapter)
    prev_chapter = chapters[current_index - 1] if current_index > 0 else None
    next_chapter = chapters[current_index + 1] if current_index < len(chapters) - 1 else None

    # Get images in the chapter folder
    chapter_path = os.path.join(BASE_DIR, comic_name, current_chapter['folder'])
    images = []
    if os.path.exists(chapter_path):
        for f in os.listdir(chapter_path):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                images.append(f)
        
        # Sort images naturally/numerically (page_001.jpg, page_002.jpg)
        images.sort()

    return render_template('chapter.html', 
                           comic_name=comic_name,
                           chapters=chapters,
                           current_chapter=current_chapter,
                           prev_chapter=prev_chapter,
                           next_chapter=next_chapter,
                           images=images,
                           display_name=display_name)

@app.route('/images/<comic_name>/<chapter_folder>/<path:filename>')
def serve_image(comic_name, chapter_folder, filename):
    return send_from_directory(os.path.join(BASE_DIR, comic_name, chapter_folder), filename)


if __name__ == "__main__":
    """
    Entry point for launching the backend server.

    This block parses command-line arguments to determine the server's IP address
    and port. It then calls `create_backend(ip, port)` to start the RESTful
    application server.

    :arg --server-ip (str): IP address to bind the server (default: 127.0.0.1).
    :arg --server-port (int): Port number to bind the server (default: 9000).
    """

    parser = argparse.ArgumentParser(
        prog='Backend',
        description='Start the backend process',
        epilog='Backend daemon for http_deamon application'
    )
    parser.add_argument('--server-ip',
        type=str,
        default='0.0.0.0',
        help='IP address to bind the server. Default is 0.0.0.0'
    )
    parser.add_argument(
        '--server-port',
        type=int,
        default=PORT,
        help='Port number to bind the server. Default is {}.'.format(PORT)
    )
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    app.run(debug=True, port=port)