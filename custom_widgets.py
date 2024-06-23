import typing
import utils

from PyQt6.QtWidgets import QWidget, QDialog, QMainWindow, QPlainTextEdit, QSizePolicy, QTextEdit, QGraphicsDropShadowEffect
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QEvent, QSize
from PyQt6.QtCore import QThread, pyqtSignal, QMimeData
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPixmap
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QWidget, \
    QGraphicsDropShadowEffect, QPushButton, QGridLayout, QSpacerItem, \
    QSizePolicy, QApplication, QHBoxLayout, QLabel, QScrollArea

import re, os
os.environ['QTWEBENGINE_DISABLE_SANDBOX']='1'

from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.admonition import AdmonitionExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.abbr import AbbrExtension
from markdown.extensions.smarty import SmartyExtension


def calculate_height_for_lines(font, num_lines):
    font_metrics = QFontMetrics(font)
    line_height = font_metrics.lineSpacing()
    return line_height * num_lines


class CustomTextEdit(QTextEdit):
    returnPressed = pyqtSignal(int)

    def __init__(self, 
                 parent: typing.Optional[QWidget] = None, 
                 font_size=10, 
                 min_lines=8,
                 max_lines=20) -> None:
        super().__init__(parent)
        self.index = 0
        css = utils.read_file('css/scrollbar_styles.css')
        self.verticalScrollBar().setStyleSheet(css)
        self.horizontalScrollBar().setStyleSheet(css)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        css = utils.read_file('css/text_edit_styles.css')
        self.setStyleSheet(css)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        font = QFont("Arial", font_size)  # 设置字体和大小
        self.setFont(font)
        self.min_height = int(calculate_height_for_lines(font, min_lines))
        self.max_height = int(calculate_height_for_lines(font, max_lines))
        self.setFixedHeight(self.min_height)

        # 自适应高度
        self.textChanged.connect(self.adjust_height)
        self.adjust_height()
    
    def resizeEvent(self, event):
        super(CustomTextEdit, self).resizeEvent(event)
        self.adjust_height()

    def adjust_height(self):
        height = int(self.document().size().height()) + 4 # Add some padding for better appearance

        height = max(self.min_height, height)
        height = min(self.max_height, height)

        self.setFixedHeight(height)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                self.insertPlainText('\n')
            else:
                self.returnPressed.emit(self.index)
        else:
            super().keyPressEvent(event)

    def insertFromMimeData(self, source: QMimeData):
        if source.hasText():
            self.insertPlainText(source.text())


class MarkdownView(QWebEngineView):
    height_changed = pyqtSignal()

    def __init__(self, ):
        super(MarkdownView, self).__init__()
        
        self.html_template = utils.read_file('css/webview.html')
        css = utils.read_file('css/web_engine_styles.css')
        self.setStyleSheet(css)
        
        self.slots = re.findall(r'{([a-zA-Z_]+)\}', self.html_template)
        self.loadFinished.connect(self.calculate_height)
        self.setMarkdown('<font color=grey> Output... </font>')
        self.is_hidden = True

    def setMarkdown(self, text):
        # print(f'setMarkdown: {text}')
        import time

        # start = time.time()
        self.text = text
        try:
            markdown_content = markdown(text, extensions=[
                # CodeHiliteExtension(linenums=False),
                # TocExtension(permalink=True),
                # FencedCodeExtension(),
                TableExtension(),
                FootnoteExtension(),
                AdmonitionExtension(),
                AttrListExtension(),
                DefListExtension(),
                AbbrExtension(),
                SmartyExtension()
            ])
            
            html = self.html_template.replace('{html_content}', markdown_content)
            self.setHtml(html)
        except:
            pass
        
        # print(f'markdown load time: {time.time()-start}')
        self.loadFinished.connect(self.add_flash_effect)
        
    def add_flash_effect(self):
        self.page().runJavaScript("""
            var element = document.querySelector('body');
            element.style.transition = 'box-shadow 0.2s ease-in-out, border-radius 0.2s ease-in-out';
            element.style.borderRadius = '10px'; // 调整圆角半径大小
            element.style.boxShadow = 'inset 0 0 10px rgba(0, 0, 0, 0.5)';
            setTimeout(function() {
                element.style.boxShadow = 'inset 0 0 0 rgba(0, 0, 0, 0)';
            }, 200);
            element.style.boxShadow = 'inset 0 0 0 rgba(0, 0, 0, 0)';
        """)
        
    def calculate_height(self):
        javascript_code = """
        function getPageHeight() {
            var body = document.body;
            var html = document.documentElement;
            
            // Calculate the total height of the page
            return [body.scrollHeight, body.offsetHeight, 
							  html.clientHeight, html.scrollHeight, html.offsetHeight];
        }
        getPageHeight();
        """
        self.page().runJavaScript(javascript_code, self.adjust_display_height)
    
    def adjust_display_height(self, heights):
        if heights:
            self.setFixedHeight(heights[-1] + 2)
            self.height_changed.emit()


class Color(QWidget):

    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)



class CustomMainWindow(QMainWindow):
    def __init__(self, ) -> None:
        super().__init__()
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        css = utils.read_file('css/main_window_styles.css')
        self.setStyleSheet(css)

        self.initUi()
        # 添加阴影
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(12)
        effect.setOffset(0, 0)
        effect.setColor(Qt.GlobalColor.gray)
        self.setGraphicsEffect(effect)

        # Initialize variables for dragging
        self._is_dragging = False
        self._drag_start_position = None
    
    def initUi(self):
        self.main_widget = QWidget()
        # self.main_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self.setCentralWidget(self.main_widget)
        
        self.main_widget.setObjectName('Main_Widget')

        self.out_layout = QVBoxLayout(self.main_widget)
        self.out_layout.setContentsMargins(5, 5, 5, 5)
        # self.out_layout.setSpacing(10)
        self.out_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.title_widget = QWidget()
        self.title_widget.setFixedHeight(20)
        self.out_layout.addWidget(self.title_widget)
        self.title_layout = QHBoxLayout(self.title_widget)
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        
        # setup title bar
        self.image_label = QLabel()
        self.image_label.setFixedSize(20, 20)
        self.image_label.setScaledContents(True)
        icon = QPixmap('icon.png')
        self.image_label.setPixmap(icon)
        
        self.title_layout.addWidget(self.image_label)

        self.title_label = QLabel()
        self.title_label.setText('Lancer Demo')
        self.title_layout.addWidget(self.title_label)

        self.close_button = QPushButton(objectName='closeButton')
        self.close_button.setFixedSize(20, 20)
        self.close_button.setIcon(QIcon('close.png'))  # 设置置顶图标
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet('''
        #closeButton {
            border: 0px solid #ccc;
            border-radius: 5px;
        }
        #closeButton:hover {
            background: red;
        }
        ''')
        self.title_layout.addWidget(self.close_button)

        self.input_text_edit = CustomTextEdit()
        self.input_text_edit.setPlaceholderText("Enter text here and press Enter...")
        # self.input_text_edit.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self.output_text_edit = MarkdownView()
        # self.output_text_edit.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)


        self.input_text_edit.returnPressed.connect(
            lambda : self.output_text_edit.setMarkdown(self.input_text_edit.toPlainText()))
        # self.input_text_edit.returnPressed.connect(self.add_output_widget)
        
        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.content_widget.setStyleSheet('border: 0px solid #ccc; background-color: #fff;')
        
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 0, 5, 0)
        self.content_layout.setSpacing(10)

        self.content_layout.addWidget(self.input_text_edit)
        self.content_layout.addWidget(self.output_text_edit)
        
        self.scroll_area = QScrollArea()
        # self.scroll_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.scroll_area.setStyleSheet('QScrollArea { border: none; }')
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content_widget)
        # self.scroll_area.setFixedHeight(300)
        import utils
        css = utils.read_file('css/scrollbar_styles.css')
        self.scroll_area.verticalScrollBar().setStyleSheet(css)

        self.out_layout.addWidget(self.scroll_area)
        
        # self.add_to_content_layout(self.input_text_edit)
        # self.add_to_content_layout(self.output_text_edit)
        self.set_position_and_gem_on_screen()
        # self.scroll_area.setFixedHeight(self.max_height)

    # def add_output_widget(self, ):
    #     if not utils.widget_in_layout(self.content_layout, self.output_text_edit):
    #         self.add_to_content_layout(self.output_text_edit)

    # def add_to_content_layout(self, widget):
    #     if not widget: return

    #     self.content_layout.addWidget(widget)

    #     # if isinstance(widget, QTextEdit):
    #     #     widget.textChanged.connect(self.adjust_window_height)
    #     # elif isinstance(widget, QWebEngineView):
    #     #     widget.loadFinished.connect(self.adjust_window_height)

    def set_position_and_gem_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        self.main_widget.setFixedWidth(int(screen_geometry.width() * 0.33))
        
        self.title_widget.height()
        # self.main_widget.setMaximumHeight()
        self.max_height = int(screen_geometry.height() * 0.6)

        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = int(screen_geometry.height() * 0.3)
        self.move(x, y)
    
    def adjust_window_height(self, ):
        print(f'content{self.content_layout.sizeHint().height()}; main_window: {self.main_widget.height()}')
        print(f'input edit{self.input_text_edit.height()}; output edit: {self.output_text_edit.height()}')

        # import time

        # start = time.time()
        height = min(self.content_layout.sizeHint().height(), self.max_height)

        self.scroll_area.setFixedHeight(height)
        # print(f'time: {time.time() - start};')

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_widget.geometry().contains(event.pos()):
            self._is_dragging = True
            self._drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            self._is_dragging = False

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            self.move(event.globalPosition().toPoint() - self._drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            event.accept()


if __name__ == '__main__':
    import sys
    from PyQt6.QtGui import QPalette, QColor, QIcon
    from PyQt6.QtWidgets import QSizePolicy, QApplication
    app = QApplication(sys.argv)
    w = CustomMainWindow()
    w.setWindowIcon(QIcon('icon.png'))
    w.show()
    sys.exit(app.exec())
