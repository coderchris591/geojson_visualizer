import sys
import json
import os
from PyQt5.QtWidgets import (QMainWindow, QApplication, QStyle, QTabWidget, QVBoxLayout, QWidget, QGraphicsScene, QAction, QFileDialog,
                            QGraphicsView, QStatusBar, QToolBar, QGraphicsEllipseItem, QLabel, QGraphicsItem)
from PyQt5.QtCore import Qt,QPointF,QMarginsF, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QPen, QPainterPath, QPolygonF, QMouseEvent, QTextLayout



class MainWindow(QMainWindow):


    def __init__(self):
        super().__init__()

        # Window Settings
        self.setWindowTitle("GeoJSON Viewer")
        self.setGeometry(QStyle.alignedRect(Qt.LeftToRight, Qt.AlignCenter, self.size() * 1.3, QApplication.desktop().availableGeometry()))

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
    
        # Tab
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.setTabsClosable(True) 
        self.add_tab("Home")
        self.tab_widget.tabCloseRequested.connect(self.close_tab)  # Connect tabCloseRequested signal to close_tab method

        # Status Bar
        self.status_bar = QStatusBar()
        self.coordinate_label = QLabel("Coordinates: None")
        self.geometry_label = QLabel("Geometry: None")
        self.create_statusbar()

        # User Interface
        self.create_menu()
        self.create_toolbar()
    

     # Functions for User Interface

    def create_statusbar(self):
        # Set the status bar
        self.setStatusBar(self.status_bar)  
        # Coordinates
        # self.coordinate_label.setWindowFlags(Qt.ToolTip)
        self.coordinate_label.setStyleSheet("margin-left: 5px; margin-bottom: 5px; background-color: white; padding: 3px; border: 1px solid black")
        self.status_bar.addWidget(self.coordinate_label)
        # geometry
        # self.geometry_label.setStyleSheet("margin-left: 5px; margin-bottom: 5px; background-color: white; padding: 3px; border: 1px solid black")
        # self.status_bar.addWidget(self.geometry_label)

    def on_mouse_moved(self, x, y):
        self.coordinate_label.setText(f"Coordinates: X: {x:.2f}, Y: {y:.2f}")
        
    
    def add_tab(self,title):
        if title == "Home":
            label = QLabel()
            label.setText("Welcome to GeoJSON Visualizer!")
            label.setAlignment(Qt.AlignCenter)
            tab_content = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(label)
            tab_content.setLayout(layout)
            # Add the QWidget to the QTabWidget
            tab_index = self.tab_widget.addTab(tab_content, title)
            self.tab_widget.setCurrentIndex(tab_index)
        else:
            # Container for 2D Graphics
            scene = QGraphicsScene()
            # The QGraphicsView class provides a widget for displaying the contents of a QGraphicsScene 
            view = MyGraphicsView(scene)
            tab_index = self.tab_widget.addTab(view, title)
            self.tab_widget.setCurrentIndex(tab_index)
            view.mouse_moved.connect(self.on_mouse_moved)
            view.setMouseTracking(True)
            return scene,view
 
    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def create_toolbar(self):

        # Create Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Zoom in
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        # Zoom out
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        # Rotate
        rotate_action = QAction("Rotate 90 degrees", self)
        rotate_action.triggered.connect(self.rotate_view)
        toolbar.addAction(rotate_action)

    def zoom_in(self):
        view = self.tab_widget.currentWidget()
        try:
            view.scale(1.1, 1.1)
        except AttributeError as e:
            print("An error occurred:", str(e))
            pass

    def zoom_out(self):
        view = self.tab_widget.currentWidget()
        try:
            view.scale(0.9, 0.9)
        except AttributeError as e:
            print("An error occurred:", str(e))
            pass
    
    def rotate_view(self):
        view = self.tab_widget.currentWidget()
        try:
            view.rotate(90)
        except AttributeError as e:
            print("An error occurred:", str(e))
            pass

    def create_menu(self):

        # Open GeoJSON Files
        open_action = QAction("&Open GeoJSON File", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_geojson)

        # Close Application
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Create Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(open_action)
        file_menu.addAction(exit_action) 
    
    # Functions for dealing with geojsonMe
    def open_geojson(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open GeoJSON File", "", "GeoJSON Files (*.geojson)")
        if file_name:
            self.load_geojson(file_name)
    
    def load_geojson(self, geojson_file):

        scene, view = self.add_tab(os.path.basename(geojson_file))

        print("Loading GeoJSON file:", geojson_file)
        view = self.tab_widget.currentWidget()
    
        with open(geojson_file, 'r') as f:
            # load data into dictionary
            geojson_data = json.load(f)

        # Loop though each feature in GeoJSON
        for feature in geojson_data['features']:
            geometry = feature['geometry']
            # check if geometry has properties
            try:
                properties = feature['properties']
            except KeyError:
                properties = None

            # Geomertry Type and Coordinates
            geometry_type = geometry['type']
            coordinates = geometry['coordinates']

            # Point
            if geometry_type == 'Point':
                if type(coordinates[0]) == list:
                    coordinates = coordinates[0]
                node = self.render_point(coordinates, properties)
                scene.addItem(node)
                margins = QMarginsF(1,1,1,1)
                rect = scene.sceneRect().marginsAdded(margins)
                view.fitInView(rect, Qt.KeepAspectRatio)

            # Multipoint
            elif geometry_type == 'MultiPoint':
                for point in coordinates:
                    self.render_point(point, properties)

            # Linestring
            elif geometry_type == 'LineString':
                path, pen = self.render_line_string(coordinates)
                scene.addPath(path, pen)
                margins = QMarginsF(1,1,1,1)
                rect = scene.sceneRect().marginsAdded(margins)
                view.fitInView(rect, Qt.KeepAspectRatio)

            # Polygon
            elif geometry_type == 'Polygon':
                polygon = self.render_polygon(coordinates)
                scene.addPolygon(polygon, QPen(Qt.green, 0.2))
                margins = QMarginsF(1,1,1,1)
                rect = scene.sceneRect().marginsAdded(margins)
                view.fitInView(rect, Qt.KeepAspectRatio)
                for ring in coordinates:
                    if isinstance(ring[0], (float, int)):
                        ring = [ring]
            else:
                print("Geometry Type is not recognized.")
            
    def render_point(self, coordinates, properties=None ):
        point = QPointF(coordinates[0], coordinates[1])
        radius = properties.get("radius", 1)
        brush_color = QColor(properties.get("color", "red"))
        node = QGraphicsEllipseItem(point.x() - radius, point.y() - radius, 2 * radius, 2 * radius)
        node.setBrush(QBrush(brush_color))
        node.setPen(QPen(Qt.NoPen))
        # node.setAcceptHoverEvents(True)
        return node

    def render_line_string(self, coordinates):
        path = QPainterPath()
        path.moveTo(coordinates[0][0], coordinates[0][1])
        for coord in coordinates[1:]:
            path.lineTo(coord[0], coord[1])
        pen = QPen(Qt.blue)
        pen.setWidth(3)
        return path, pen

    def render_polygon(self, coordinates):
        for ring in coordinates:
            polygon = QPolygonF([QPointF(lon, lat) for lon, lat in ring])
            return polygon
    

class MyGraphicsView(QGraphicsView):
    mouse_moved = pyqtSignal(float, float)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        # items = self.scene().items(scene_pos)
        # i = 0
        # for item in items:
        #     if isinstance(item, QGraphicsItem):
        #         print("geometry ", i)
        #         i += 1

        self.mouse_moved.emit(scene_pos.x(), scene_pos.y())
        super().mouseMoveEvent(event)

    # def mouseClickEvent(self, event):




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

