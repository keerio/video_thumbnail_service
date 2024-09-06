import os
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
import cv2
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
THUMBNAIL_FOLDER = 'thumbnails'
ALLOWED_EXTENSIONS = {'mp4', 'ts'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

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

def process_existing_videos(folder):
    for video in os.listdir(folder):
        if allowed_file(video):
            video_path = os.path.join(folder, video)
            thumbnail_folder = os.path.join(app.config['THUMBNAIL_FOLDER'], video)
            if not os.path.exists(thumbnail_folder):
                os.makedirs(thumbnail_folder, exist_ok=True)
                try:
                    create_thumbnails(video_path, thumbnail_folder)
                except Exception as e:
                    print(f"Error processing video {video}: {str(e)}")

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and allowed_file(event.src_path):
            video_name = os.path.basename(event.src_path)
            thumbnail_folder = os.path.join(app.config['THUMBNAIL_FOLDER'], video_name)
            os.makedirs(thumbnail_folder, exist_ok=True)
            try:
                create_thumbnails(event.src_path, thumbnail_folder)
            except Exception as e:
                print(f"Error processing new video {video_name}: {str(e)}")

observer = Observer()
event_handler = VideoHandler()
observer.schedule(event_handler, app.config['UPLOAD_FOLDER'], recursive=False)
observer.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_folder', methods=['POST'])
def set_folder():
    folder = request.form['folder']
    app.config['UPLOAD_FOLDER'] = folder
    os.makedirs(folder, exist_ok=True)
    observer.unschedule_all()
    observer.schedule(event_handler, folder, recursive=False)
    process_existing_videos(folder)
    return jsonify({"status": "success", "message": f"Monitoring folder: {folder}"})

@app.route('/get_videos_and_thumbnails')
def get_videos_and_thumbnails():
    videos = []
    for video in os.listdir(app.config['UPLOAD_FOLDER']):
        if allowed_file(video):
            thumbnail_folder = os.path.join(app.config['THUMBNAIL_FOLDER'], video)
            thumbnails = [f for f in os.listdir(thumbnail_folder) if f.endswith('.jpg')]
            videos.append({
                "name": video,
                "thumbnails": thumbnails
            })
    return jsonify(videos)

@app.route('/remove_video/<video>')
def remove_video(video):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video)
    thumbnail_folder = os.path.join(app.config['THUMBNAIL_FOLDER'], video)
    
    if os.path.exists(video_path):
        os.remove(video_path)
    
    if os.path.exists(thumbnail_folder):
        for thumbnail in os.listdir(thumbnail_folder):
            os.remove(os.path.join(thumbnail_folder, thumbnail))
        os.rmdir(thumbnail_folder)
    
    return jsonify({"status": "success", "message": f"Removed video and thumbnails: {video}"})

@app.route('/uploads/<path:filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    video = os.path.dirname(filename)
    return send_from_directory(os.path.join(app.config['THUMBNAIL_FOLDER'], video), os.path.basename(filename))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)