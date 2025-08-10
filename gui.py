import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QComboBox, QCheckBox, QProgressBar, 
                           QPushButton, QTextEdit, QFileDialog, QMessageBox, 
                           QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

# Import the downloader class from main.py
from main import YtDlpDownloader, check_dependencies

class DownloaderSignals(QObject):
    """Signal class for communication between threads"""
    log_message = pyqtSignal(str)
    update_progress = pyqtSignal(str, object)
    download_complete = pyqtSignal()
    download_error = pyqtSignal(str)

class YtDlpGui(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Create signals for thread communication
        self.signals = DownloaderSignals()
        
        # Connect signals to slots
        self.signals.log_message.connect(self.log_message)
        self.signals.update_progress.connect(self.update_progress)
        self.signals.download_complete.connect(self.download_complete)
        self.signals.download_error.connect(self.download_error)
        
        # Create the downloader with callbacks
        self.downloader = YtDlpDownloader({
            'log_message': self.signals.log_message.emit,
            'update_progress': self.signals.update_progress.emit,
            'on_complete': self.signals.download_complete.emit,
            'on_error': self.signals.download_error.emit,
        })
        
        # Setup GUI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("yt-dlp GUI for macOS")
        self.setMinimumSize(750, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # URL input section
        url_layout = QHBoxLayout()
        url_label = QLabel("Video URL:")
        self.url_entry = QLineEdit()
        paste_button = QPushButton("Paste")
        paste_button.clicked.connect(self.paste_url)
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_entry)
        url_layout.addWidget(paste_button)
        main_layout.addLayout(url_layout)
        
        # Format selection section
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mp3", "webm", "best"])
        self.format_combo.setCurrentIndex(3)  # Selects "best" (index 3)
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch(1)
        main_layout.addLayout(format_layout)
        
        # Output directory section
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Save to:")
        self.output_dir_entry = QLineEdit()
        self.output_dir_entry.setText("/Users/jeffhaskin/youtube")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_directory)
        
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.output_dir_entry)
        dir_layout.addWidget(browse_button)
        main_layout.addLayout(dir_layout)
        
        # Options section
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.subtitles_check = QCheckBox("Download subtitles")
        self.thumbnail_check = QCheckBox("Download thumbnail")
        
        options_layout.addWidget(self.subtitles_check)
        options_layout.addWidget(self.thumbnail_check)
        main_layout.addWidget(options_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.hide()
        
        self.status_label = QLabel("Ready")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        main_layout.addWidget(progress_group)
        
        # Log section
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)
        
        # Buttons section
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_fields)
        
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_download)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.download_button)
        main_layout.addLayout(button_layout)
    
    def paste_url(self):
        """Paste clipboard content to URL entry"""
        clipboard = QApplication.clipboard()
        self.url_entry.setText(clipboard.text())
    
    def browse_directory(self):
        """Open directory browser dialog"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory",
            self.output_dir_entry.text()
        )
        if directory:
            self.output_dir_entry.setText(directory)
    
    def log_message(self, message):
        """Add message to log display"""
        self.log_text.append(message)
        # Scroll to the bottom
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())
    
    def update_progress(self, status, data):
        """Update progress information"""
        if status == 'downloading' and data:
            self.progress_bar.show()
            self.status_label.setText(f"Downloading: {data['percent']} at {data['speed']}, ETA: {data['eta']}")
        elif status == 'processing':
            self.progress_bar.show()
            self.status_label.setText("Post-processing...")
    
    def download_complete(self):
        """Called when download is complete"""
        self.progress_bar.hide()
        self.status_label.setText("Download complete!")
        QMessageBox.information(self, "Success", "Download completed successfully!")
    
    def download_error(self, error_msg):
        """Called when an error occurs during download"""
        self.progress_bar.hide()
        self.status_label.setText("Error occurred")
        self.log_message(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", f"Download failed: {error_msg}")
    
    def clear_fields(self):
        """Clear input fields and reset status"""
        self.url_entry.clear()
        self.status_label.setText("Ready")
        self.log_text.clear()
        self.progress_bar.hide()
    
    def start_download(self):
        """Start the download process"""
        url = self.url_entry.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return
        
        # Show progress bar
        self.progress_bar.show()
        self.status_label.setText("Downloading...")
        
        # Get options from GUI
        output_dir = self.output_dir_entry.text()
        selected_format = self.format_combo.currentText()
        with_subtitles = self.subtitles_check.isChecked()
        with_thumbnail = self.thumbnail_check.isChecked()
        
        # Start the download
        self.downloader.start_download(
            url, 
            output_dir, 
            selected_format,
            with_subtitles,
            with_thumbnail
        )

def show_dependency_error(message):
    """Show error message about missing dependencies"""
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "Missing Dependency", message)
    sys.exit(1)

def main():
    """Main function to start the application"""
    # Check dependencies first
    deps_check = check_dependencies()
    if deps_check is not True:  # This means deps_check contains (False, error_message)
        _, error_message = deps_check
        show_dependency_error(error_message)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    
    window = YtDlpGui()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
