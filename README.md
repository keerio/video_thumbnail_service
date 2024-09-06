# Video Thumbnail Service

This service monitors a specified folder for new MP4 or TS files, creates thumbnails for every 2 minutes of video, and provides a web interface to view and manage the videos and thumbnails.

## Installation

1. Install the required dependencies:

```
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-opencv
```

2. Clone this repository to `/opt/video_thumbnail_service`:

```
sudo git clone https://your-repository-url.git /opt/video_thumbnail_service
```

3. Install the Python requirements:

```
sudo pip3 install -r /opt/video_thumbnail_service/requirements.txt
```

4. Copy the service file to the systemd directory:

```
sudo cp /opt/video_thumbnail_service/video_thumbnail_service.service /etc/systemd/system/
```

5. Reload systemd, enable and start the service:

```
sudo systemctl daemon-reload
sudo systemctl enable video_thumbnail_service
sudo systemctl start video_thumbnail_service
```

## Usage

1. Access the web interface by opening a web browser and navigating to `http://your-server-ip:5050`.

2. Set the monitoring folder using the input field at the top of the page.

3. The service will automatically detect new MP4 or TS files in the specified folder and create thumbnails.

4. Use the web interface to view videos, their thumbnails, and remove videos and thumbnails as needed.

## Troubleshooting

Check the service status:

```
sudo systemctl status video_thumbnail_service
```

View the logs:

```
sudo journalctl -u video_thumbnail_service
```

If you encounter any issues, make sure the required dependencies are installed and the service has the necessary permissions to access the monitoring folder.