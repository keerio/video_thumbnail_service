import os
import time
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
import cv2
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'ts'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_thumbnails(video_path, output_folder):
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if fps <= 0 or total_frames <= 0:
        print(f"Error: Invalid video file: {video_path}")
        video.release()
        return

    duration = total_frames / fps
    interval = 120  # 2 minutes

    for i in range(0, int(duration), interval):
        video.set(cv2.CAP_PROP_POS_MSEC, i * 1000)
        success, image = video.read()
        if success:
            thumbnail_path = os.path.join(output_folder, f"thumbnail_{i}.jpg")
            cv2.imwrite(thumbnail_path, image)
        else:
            print(f"Error: Failed to read frame at {i} seconds for {video_path}")

    video.release()

def get_video_length(video_path):
    try:
        video = cv2.VideoCapture(video_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        video.release()
        
        if fps <= 0 or total_frames <= 0:
            return None
        
        duration_seconds = total_frames / fps
        return duration_seconds
    except Exception as e:
        print(f"Error reading video {video_path}: {str(e)}")
        return None

def should_remove_video(video_path):
    # Check if file size is less than 2 MB
    if os.path.getsize(video_path) < 2 * 1024 * 1024:
        return True
    
    # Check if video length is less than 5 minutes or not readable
    duration = get_video_length(video_path)
    if duration is None or duration < 300:  # 300 seconds = 5 minutes
        return True
    
    return False

def remove_video_and_thumbnails(video_path):
    thumbnail_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbs', os.path.splitext(os.path.basename(video_path))[0])
    
    if os.path.exists(video_path):
        os.remove(video_path)
    
    if os.path.exists(thumbnail_folder):
        for thumbnail in os.listdir(thumbnail_folder):
            os.remove(os.path.join(thumbnail_folder, thumbnail))
        os.rmdir(thumbnail_folder)

def process_video(video_path, thumbnail_folder):
    if should_remove_video(video_path):
        print(f"Removing video: {video_path}")
        remove_video_and_thumbnails(video_path)
    else:
        try:
            create_thumbnails(video_path, thumbnail_folder)
        except Exception as e:
            print(f"Error processing video {video_path}: {str(e)}")

def process_existing_videos(folder):
    thumbs_folder = os.path.join(folder, 'thumbs')
    os.makedirs(thumbs_folder, exist_ok=True)
    
    for video in os.listdir(folder):
        if allowed_file(video):
            video_path = os.path.join(folder, video)
            thumbnail_folder = os.path.join(thumbs_folder, os.path.splitext(video)[0])
            if not os.path.exists(thumbnail_folder):
                os.makedirs(thumbnail_folder, exist_ok=True)
            threading.Thread(target=process_video, args=(video_path, thumbnail_folder)).start()

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and allowed_file(event.src_path):
            video_name = os.path.basename(event.src_path)
            thumbs_folder = os.path.join(os.path.dirname(event.src_path), 'thumbs')
            thumbnail_folder = os.path.join(thumbs_folder, os.path.splitext(video_name)[0])
            os.makedirs(thumbnail_folder, exist_ok=True)
            threading.Thread(target=process_video, args=(event.src_path, thumbnail_folder)).start()

observer = Observer()
event_handler = VideoHandler()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_folder', methods=['POST'])
def set_folder():
    global observer
    folder = request.form['folder']
    app.config['UPLOAD_FOLDER'] = folder
    os.makedirs(folder, exist_ok=True)
    observer.unschedule_all()
    observer.schedule(event_handler, folder, recursive=False)
    observer.start()
    process_existing_videos(folder)
    return jsonify({"status": "success", "message": f"Monitoring folder: {folder}"})

@app.route('/get_videos_and_thumbnails')
def get_videos_and_thumbnails():
    videos = []
    thumbs_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbs')
    for video in os.listdir(app.config['UPLOAD_FOLDER']):
        if allowed_file(video):
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video)
            if not should_remove_video(video_path):
                thumbnail_folder = os.path.join(thumbs_folder, os.path.splitext(video)[0])
                thumbnails = [f for f in os.listdir(thumbnail_folder) if f.endswith('.jpg')] if os.path.exists(thumbnail_folder) else []
                duration = get_video_length(video_path)
                if duration:
                    hours, remainder = divmod(duration, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    length = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                else:
                    length = "Unknown"
                videos.append({
                    "name": video,
                    "thumbnails": thumbnails,
                    "length": length
                })
    return jsonify(videos)

@app.route('/remove_video/<video>')
def remove_video(video):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video)
    remove_video_and_thumbnails(video_path)
    return jsonify({"status": "success", "message": f"Removed video and thumbnails: {video}"})

@app.route('/uploads/<path:filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    video = os.path.splitext(os.path.dirname(filename))[0]
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbs', video), os.path.basename(filename))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)