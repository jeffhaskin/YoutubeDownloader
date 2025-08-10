import os
import threading
import subprocess
import time
import yt_dlp

class YtDlpDownloader:
    def __init__(self, callback_functions=None):
        """Initialize the downloader with callback functions from GUI."""
        self.callbacks = callback_functions or {}
    
    def log_message(self, message):
        """Send log message to GUI"""
        if 'log_message' in self.callbacks:
            self.callbacks['log_message'](message)
    
    def update_progress(self, status, data=None):
        """Update progress information in GUI"""
        if 'update_progress' in self.callbacks:
            self.callbacks['update_progress'](status, data)
    
    def on_complete(self):
        """Notify GUI when download is complete"""
        if 'on_complete' in self.callbacks:
            self.callbacks['on_complete']()
    
    def on_error(self, error_msg):
        """Notify GUI when an error occurs"""
        if 'on_error' in self.callbacks:
            self.callbacks['on_error'](error_msg)
    
    def download_video(self, url, output_dir, selected_format, with_subtitles=False, with_thumbnail=False, convert_to_mp4=False):
        """Download video using yt-dlp"""
        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'logger': CustomLogger(self),
            'progress_hooks': [self.progress_hook],
            'quiet': True,
        }
        
        # Set format-specific options
        if selected_format == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif selected_format == "mp4":
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            })
        elif selected_format == "webm":
            ydl_opts.update({
                'format': 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best',
            })
        
        # Add subtitle options if selected
        if with_subtitles:
            ydl_opts.update({
                'writesubtitles': True,
                'writeautomaticsub': True,
            })
        
        # Add thumbnail option if selected
        if with_thumbnail:
            postprocessors = ydl_opts.get('postprocessors', [])
            postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
            ydl_opts.update({
                'writethumbnail': True,
                'postprocessors': postprocessors,
            })
        
        try:
            self.log_message(f"Starting download of {url}")
            self.downloaded_file = None
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if selected_format == 'best' and convert_to_mp4 and self.downloaded_file:

                time.sleep(2)

                base, ext = os.path.splitext(self.downloaded_file)
                if ext.lower() != '.mp4':
                    mp4_file = base + '.mp4'
                    try:

                        # Detect whether the file has a video stream
                        probe = subprocess.run(
                            [
                                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                '-show_entries', 'stream=codec_type', '-of', 'csv=p=0',
                                self.downloaded_file
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        has_video = probe.stdout.strip() != b''

                        # Build ffmpeg command based on presence of video stream
                        if has_video:
                            cmd = [
                                'ffmpeg', '-y', '-i', self.downloaded_file,
                                '-c:v', 'libx264', '-preset', 'ultrafast',
                                '-c:a', 'copy', mp4_file
                            ]
                        else:
                            cmd = [
                                'ffmpeg', '-y', '-i', self.downloaded_file,
                                '-vn', '-c:a', 'copy', mp4_file
                            ]

                        subprocess.run(
                            cmd,

                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        os.remove(self.downloaded_file)
                        self.log_message(f"Converted to mp4: {os.path.basename(mp4_file)}")
                    except subprocess.SubprocessError as e:
                        self.on_error(f"ffmpeg conversion failed: {e}")
                        return

            self.on_complete()
        except Exception as e:
            error_msg = str(e)
            self.on_error(error_msg)
    
    def start_download(self, url, output_dir, selected_format, with_subtitles=False, with_thumbnail=False, convert_to_mp4=False):
        """Start the download process in a separate thread"""
        download_thread = threading.Thread(
            target=self.download_video,
            args=(url, output_dir, selected_format, with_subtitles, with_thumbnail, convert_to_mp4)
        )
        download_thread.daemon = True
        download_thread.start()
    
    def progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            # Extract download progress information
            try:
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                
                progress_data = {
                    'percent': percent,
                    'speed': speed,
                    'eta': eta
                }
                self.update_progress('downloading', progress_data)
            except:
                pass
        
        elif d['status'] == 'finished':
            filename = d.get('filename', 'Unknown')
            self.downloaded_file = filename
            self.log_message(f"Download finished: {os.path.basename(filename)}")
            self.update_progress('processing', None)

class CustomLogger:
    """Custom logger for yt-dlp that forwards messages to the downloader"""
    def __init__(self, downloader):
        self.downloader = downloader
    
    def debug(self, msg):
        if not msg.startswith('[debug] '):
            self.info(msg)
    
    def info(self, msg):
        self.downloader.log_message(msg)
    
    def warning(self, msg):
        self.downloader.log_message(f"Warning: {msg}")
    
    def error(self, msg):
        self.downloader.log_message(f"Error: {msg}")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import yt_dlp
    except ImportError:
        return False, "yt-dlp is not installed. Please install it with 'pip install yt-dlp'"
    
    # Check if ffmpeg is installed
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.SubprocessError, FileNotFoundError):
        return False, "FFmpeg is not installed. Please install it with 'brew install ffmpeg'"
    
    return True

if __name__ == "__main__":
    # This will only run if main.py is run directly
    from gui import main as gui_main
    gui_main()
