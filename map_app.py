# download google image
import io
import os
import sys
import subprocess
import folium
from folium.plugins.draw import Draw
from PyQt5.QtWidgets import QApplication, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QLabel, QProgressBar, QSpinBox, QDateEdit, QPushButton, QDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QDate
import json
from PyQt5.QtGui import QIcon, QPixmap
from coord_convert import gcj02_to_wgs84


class InfoDialog(QDialog):
    """更多信息对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("更多信息")
        self.setFixedSize(400, 300)
        self.setWindowModality(Qt.ApplicationModal)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("小白影像下载器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        
        # 开发作者信息
        author_label = QLabel("开发作者：ytkz")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setStyleSheet("font-size: 14px; margin: 10px;")
        
        # 图片显示
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        
        # 尝试加载图片
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "link.jpg")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # 缩放图片以适应对话框
            scaled_pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        else:
            image_label.setText("图片未找到: resources/link.jpg")
            image_label.setStyleSheet("color: gray; font-style: italic;")
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        close_button.setMaximumWidth(100)
        
        # 布局
        layout.addWidget(title_label)
        layout.addWidget(author_label)
        layout.addWidget(image_label)
        layout.addStretch()
        
        # 按钮居中布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.setContentsMargins(20, 20, 20, 20)

class Worker(QThread):
    progress = pyqtSignal(int)
    coordinates_ready = pyqtSignal(list)  # Signal to emit coordinates

    def __init__(self, jsonfile):
        super().__init__()
        self.jsonfile = jsonfile

    def readjson(self):
        try:
            with open(self.jsonfile, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            self.coordinates_ready.emit([])  # Emit empty list on error
            return []

        coordinates_info = []
        for feature in json_data.get("features", []):
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [])

            # Handle Polygon
            if geometry.get("type") == "Polygon":
                for polygon in coords:
                    coordinates_info.append(polygon)

            # Handle MultiPolygon
            elif geometry.get("type") == "MultiPolygon":
                for multi_polygon in coords:
                    for polygon in multi_polygon:
                        coordinates_info.append(polygon)

        return coordinates_info

    def run(self):
        coordinates = self.readjson()
        if coordinates:
            print("Coordinates loaded successfully.")
            self.coordinates_ready.emit(coordinates)
        else:
            print("No coordinates found or failed to read JSON.")


class DownloadWorker(QThread):
    progress_update = pyqtSignal(int)  # Signal to update download progress
    download_complete = pyqtSignal(str)  # Signal emitted when download is complete
    error_occurred = pyqtSignal(str)  # Signal emitted when an error occurs

    def __init__(self, coordinates, output_path, zoom_level=18, date="2010-01-01"):
        super().__init__()
        self.coordinates = coordinates
        self.output_path = output_path
        self.zoom_level = zoom_level
        self.date = date

    def reorganize_coords(self, coords):
        longitudes = []
        latitudes = []
        for point in coords:
            longitude, latitude = point
            longitudes.append(longitude)
            latitudes.append(latitude)
        return longitudes, latitudes

    def run(self):
        try:
            total = len(self.coordinates)
            j = 0
            # 获取GEHistoricalImagery.exe的路径
            exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GEHistoricalImagery.exe")
            
            for i, coords in enumerate(self.coordinates, start=1):
                longitudes, latitudes = self.reorganize_coords(coords)
                
                # 生成唯一的输出文件名
                output_filename = f"historical_img_{j}"
                while any(f.startswith(output_filename) for f in os.listdir(self.output_path) if os.path.isfile(os.path.join(self.output_path, f))):
                    j += 1
                    output_filename = f"historical_img_{j}"

                # 构建GEHistoricalImagery命令
                lower_left = f"{min(latitudes)},{min(longitudes)}"
                upper_right = f"{max(latitudes)},{max(longitudes)}"
                
                # 设置输出文件路径
                output_file = os.path.join(self.output_path, f"{output_filename}.tif")
                
                cmd = [
                    exe_path,
                    "download",
                    "--lower-left", lower_left,
                    "--upper-right", upper_right,
                    "--zoom", str(self.zoom_level),
                    "--date", self.date,
                    "--provider", "TM",
                    "--output", output_file
                ]
                
                # 执行下载命令
                try:
                    print(f"Executing: {' '.join(cmd)}")
                    print(f"Working directory: {self.output_path}")
                    
                    result = subprocess.run(
                        cmd,
                        cwd=self.output_path,
                        capture_output=True,
                        text=True,
                        encoding='gbk',  # 使用gbk编码处理中文输出
                        errors='ignore',  # 忽略编码错误
                        timeout=300  # 5分钟超时
                    )
                    
                    if result.returncode == 0:
                        print(f"Download completed successfully for region {i}")
                        if result.stdout:
                            print(f"Output: {result.stdout}")
                    else:
                        error_message = f"Download failed for region {i}: {result.stderr}"
                        print(error_message)
                        self.error_occurred.emit(error_message)
                        continue
                        
                except subprocess.TimeoutExpired:
                    error_message = f"Download timeout for region {i}"
                    print(error_message)
                    self.error_occurred.emit(error_message)
                    continue
                except Exception as e:
                    error_message = f"Failed to execute download for region {i}: {e}"
                    print(error_message)
                    self.error_occurred.emit(error_message)
                    continue

                # 更新进度
                progress_percent = int((i / total) * 100)
                self.progress_update.emit(progress_percent)
                j += 1

            self.download_complete.emit("All downloads completed successfully!")
        except Exception as e:
            error_message = f"An error occurred during downloads: {e}"
            print(error_message)
            self.error_occurred.emit(error_message)


class Mapy(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.download_worker = None
        self.output_path = None
        self.init_ui()

    def init_ui(self):
        vbox = QVBoxLayout(self)

        # 参数设置区域
        params_layout = QHBoxLayout()
        
        # 缩放比例设置
        zoom_label = QLabel("缩放比例:")
        self.zoom_spinbox = QSpinBox()
        self.zoom_spinbox.setRange(1, 20)
        self.zoom_spinbox.setValue(18)  # 默认值18
        
        # 日期设置
        date_label = QLabel("日期:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate(2024, 1, 1))  # 默认日期
        self.date_edit.setCalendarPopup(True)
        
        # 更多信息按钮
        self.info_button = QPushButton("更多信息")
        self.info_button.clicked.connect(self.show_info_dialog)
        self.info_button.setMaximumWidth(100)
        
        params_layout.addWidget(zoom_label)
        params_layout.addWidget(self.zoom_spinbox)
        params_layout.addWidget(date_label)
        params_layout.addWidget(self.date_edit)
        params_layout.addStretch()  # 添加弹性空间，使按钮靠右
        params_layout.addWidget(self.info_button)

        # WebEngineView to display the map
        self.webEngineView = QWebEngineView()
        self.webEngineView.page().profile().downloadRequested.connect(self.handle_downloadRequested)
        self.setWindowTitle('Icon')

        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print("Icon file not found: resources/icon.ico")

        # Progress bar to show download progress
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)  # Hidden initially

        # Status label to show messages
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)

        # Load the initial map
        self.loadPage()

        # Add widgets to layout
        vbox.addLayout(params_layout)
        vbox.addWidget(self.webEngineView)
        vbox.addWidget(self.progress_bar)
        vbox.addWidget(self.status_label)

        self.setLayout(vbox)
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("小白影像下载")
        self.show()

    def loadPage(self):
        location = [30.2899, 120.1568]
        folium_map = folium.Map(
            location=location,
            zoom_start=10,
            tiles='http://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}',
            attr='AutoNavi Map',
        )

        Draw(
            export=True,
            filename="data.geojson",
            position="topleft",
            draw_options={
                'polyline': False,
                'rectangle': {'shapeOptions': {'color': '#f06'}},
                'circle': False,
                'marker': False,
                'polygon': False,
                'circlemarker': False
            },
            edit_options={
                'edit': True,
                'remove': True
            }
        ).add_to(folium_map)

        data = io.BytesIO()
        folium_map.save(data, close_file=False)
        
        # 获取HTML内容并修改export按钮文字
        html_content = data.getvalue().decode()
        # 添加JavaScript来修改export按钮文字并隐藏Leaflet按钮
        custom_js = """
        <style>
        /* 隐藏Leaflet attribution控件 */
        .leaflet-control-attribution {
            display: none !important;
        }
        </style>
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // 等待页面完全加载后修改按钮文字
            setTimeout(function() {
                var exportButton = document.getElementById('export');
                if (exportButton) {
                    exportButton.innerHTML = 'download';
                    exportButton.title = 'download data';
                }
            }, 1000);
        });
        </script>
        """
        
        # 在</body>标签前插入自定义JavaScript
        html_content = html_content.replace('</body>', custom_js + '</body>')
        
        self.webEngineView.setHtml(html_content)

    def handle_downloadRequested(self, item: QWebEngineDownloadItem):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")

        if directory:
            # Generate a unique filename to prevent overwriting
            base_filename = 'data.geojson'
            jsonfile = os.path.join(directory, base_filename)
            i = 1
            while os.path.exists(jsonfile):
                jsonfile = os.path.join(directory, f'temp{i}.geojson')
                i += 1

            item.setPath(jsonfile)
            item.accept()

            # Connect to stateChanged signal to handle download completion
            item.stateChanged.connect(lambda state, path=jsonfile: self.onStateChanged(state, path))

    def onStateChanged(self, state, jsonfile):
        if state == QWebEngineDownloadItem.DownloadCompleted:
            print(f"Download completed: {jsonfile}")
            self.output_path = os.path.dirname(jsonfile)

            # Start Worker to read JSON and emit coordinates
            self.worker = Worker(jsonfile)
            self.worker.coordinates_ready.connect(self.start_download)
            self.worker.start()
            self.status_label.setText("Processing coordinates...")
        elif state == QWebEngineDownloadItem.DownloadFailed:
            QMessageBox.critical(self, "Download Failed", "The GeoJSON file failed to download.")

    def start_download(self, coordinates):
        if not coordinates:
            QMessageBox.warning(self, "No Coordinates", "No coordinates found in the GeoJSON file.")
            self.status_label.setText("No coordinates to download.")
            return

        # 将坐标转换为WGS84坐标系
        wgs84_coordinates = []
        for i in coordinates:
            wgs84_coordinates.append([])
            for j in i:
                wgs84_coordinates[-1].append(gcj02_to_wgs84(j[0], j[1]))

        # 获取用户设置的参数
        zoom_level = self.zoom_spinbox.value()
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        
        self.download_worker = DownloadWorker(wgs84_coordinates, self.output_path, zoom_level, selected_date)
        self.download_worker.progress_update.connect(self.update_progress)
        self.download_worker.download_complete.connect(self.on_download_complete)
        self.download_worker.error_occurred.connect(self.on_download_error)
        self.download_worker.start()

        # Show and reset the progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting downloads...")

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Download Progress: {progress}%")

    def on_download_complete(self, message):
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        QMessageBox.information(self, "Download Complete", message)

    def on_download_error(self, error_message):
        QMessageBox.critical(self, "Download Error", error_message)
        self.status_label.setText("Error occurred during downloads.")

    def show_info_dialog(self):
        """显示更多信息对话框"""
        dialog = InfoDialog(self)
        dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Mapy()
    sys.exit(app.exec_())
