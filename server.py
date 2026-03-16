import os
import re
import argparse
from flask import Flask, render_template, send_from_directory, abort, jsonify, request
from ultis import get_comics

app = Flask(__name__)

# Configuration
# BASE_DIR points to "kho_truyen" which contains comic folders
# BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"static", "kho_truyen")
BASE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static", "kho_truyen_local"
)
PORT = 5000

# Ensure base dir exists
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)


def get_chapters(comic_name):
    """
    Scans the comic directory for folders matching 'Chap_X'
    Returns a sorted list of dictionaries: [{'id': 1, 'name': 'Chapter 1', 'folder': 'Chap_1'}, ...]
    """
    chapters = []
    comic_path = os.path.join(BASE_DIR, comic_name)

    if not os.path.exists(comic_path):
        return []

    pattern = re.compile(r"^Chap_(\d+)(?:[_\.-](\d+))?$", re.IGNORECASE)

    for item in os.listdir(comic_path):
        if os.path.isdir(os.path.join(comic_path, item)):
            match = pattern.match(item)

            if match and len(os.listdir(os.path.join(comic_path, item))) > 2:
                main_part = match.group(1)
                decimal_part = match.group(2)

                if decimal_part:
                    chapter_num = float(f"{main_part}.{decimal_part}")
                else:
                    chapter_num = float(main_part)
                chapters.append(
                    {
                        "id": chapter_num,
                        "folder": item,
                        "name": f"Chapter {chapter_num}",
                    }
                )

    # Sort by chapter number
    chapters.sort(key=lambda x: x["id"])
    return chapters


def get_comic_name(comic_name):
    comics = get_comics(BASE_DIR)
    current_comic_info = next((c for c in comics if c["name"] == comic_name), None)

    # Nếu tìm thấy thì lấy display_name, không thì lấy tên folder
    display_name = (
        current_comic_info["display_name"]
        if current_comic_info
        else comic_name.replace("_", " ")
    )
    return display_name


@app.route("/")
def index():
    # Only return the template. JS will handle the data later.
    # Chỉ trả về template. JS sẽ xử lý dữ liệu sau.
    return render_template("index.html")


@app.route("/api/comics")
def api_get_comics():
    comic_data = get_comics(BASE_DIR)
    sort_method = request.args.get("sort", "latest")

    if sort_method == "chapter":
        sorted_data = sorted(
            comic_data, key=lambda c: float(c.get("highest_chapter") or 0), reverse=True
        )
    else:
        sorted_data = sorted(
            comic_data, key=lambda c: float(c.get("time_update") or 0), reverse=True
        )

    return jsonify(sorted_data)


@app.route("/wtf/")
def view_wtf():
    comics = get_comics(BASE_DIR)
    return render_template("wtf.html", comics=comics)


@app.route("/comic/<comic_name>")
def view_comic(comic_name):
    chapters = get_chapters(comic_name)

    display_name = get_comic_name(comic_name)
    return render_template(
        "chapter_list.html",
        comic_name=comic_name,
        chapters=chapters,
        display_name=display_name,
    )


# Đổi <float:chapter_id> thành <string:chapter_id>
@app.route("/read/<comic_name>/<string:chapter_id>")
def view_chapter(comic_name, chapter_id):

    # 1. Ép kiểu an toàn từ chuỗi URL sang số thực (Float)
    try:
        target_id = float(chapter_id)
    except ValueError:
        return abort(404, description="Invalid chapter ID")

    chapters = get_chapters(comic_name)

    # 2. Ép kiểu c["id"] sang float khi so sánh để tránh lỗi "26.2" == 26.2 (String vs Float)
    current_chapter = next((c for c in chapters if float(c["id"]) == target_id), None)

    display_name = get_comic_name(comic_name)
    if not current_chapter:
        return abort(404, description="Chapter not found")

    # Find prev/next chapters
    current_index = chapters.index(current_chapter)
    prev_chapter = chapters[current_index - 1] if current_index > 0 else None
    next_chapter = (
        chapters[current_index + 1] if current_index < len(chapters) - 1 else None
    )

    # Get images in the chapter folder (Folder path will now be exactly what get_chapters found)
    chapter_path = os.path.join(BASE_DIR, comic_name, current_chapter["folder"])
    images = []
    if os.path.exists(chapter_path):
        for f in os.listdir(chapter_path):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                images.append(f)

        # Sort images naturally/numerically (page_001.jpg, page_002.jpg)
        images.sort()

    return render_template(
        "chapter.html",
        comic_name=comic_name,
        chapters=chapters,
        current_chapter=current_chapter,
        prev_chapter=prev_chapter,
        next_chapter=next_chapter,
        images=images,
        display_name=display_name,
    )


@app.route("/images/<comic_name>/<chapter_folder>/<path:filename>")
def serve_image(comic_name, chapter_folder, filename):
    return send_from_directory(
        os.path.join(BASE_DIR, comic_name, chapter_folder), filename
    )


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
        prog="Backend",
        description="Start the backend process",
        epilog="Backend daemon for http_deamon application",
    )
    parser.add_argument(
        "--server-ip",
        type=str,
        default="0.0.0.0",
        help="IP address to bind the server. Default is 0.0.0.0",
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=PORT,
        help="Port number to bind the server. Default is {}.".format(PORT),
    )

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    app.run(debug=True, port=port)
