
import utils


from PyQt6.QtWidgets import QWidget, QDialog, QMainWindow, QPlainTextEdit, QSizePolicy, QTextEdit, QGraphicsDropShadowEffect
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QEvent, QSize, QTimer
from PyQt6.QtCore import QThread, pyqtSignal, QMimeData
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPixmap
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QWidget, \
    QGraphicsDropShadowEffect, QPushButton, QGridLayout, QSpacerItem, \
    QSizePolicy, QApplication, QHBoxLayout, QLabel, QScrollArea
from PyQt6.QtGui import QPalette, QColor, QIcon
from PyQt6.QtWidgets import QSizePolicy, QApplication
import sys
import yaml
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QWidget, QTextEdit, QGroupBox, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt

import re, os
os.environ['QTWEBENGINE_DISABLE_SANDBOX']='1'

from custom_widgets import CustomTextEdit, MarkdownView
import api
import asyncio
import sys
from config import Config
import time


class OpenAIWorker(QThread):
    update_text = pyqtSignal(str)
    completed = pyqtSignal()

    def __init__(self, messages):
        super().__init__()
        self.messages = messages
        self.response = ""
        self._is_running = True
        self.last_emit_time = 0

    async def fetch_openai_response(self):
        for chunk in api.request(self.messages):
            if not self._is_running:
                break
            self.response += chunk
            self.update_text.emit(self.response)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.fetch_openai_response())
        self.completed.emit()

    def stop(self):
        self._is_running = False
        self.completed.emit()


class Window(QMainWindow):
    def __init__(self, args={}) -> None:
        super().__init__()
        
        # self.selected_text = args.get('select_text', '')
        # self.active_app = args.get('context_info', None)
        self.config = Config(args)

        self.messages = []
        self.worker = None

        self.init_layout()
        self.init_title_bar()
        self.init_scroll_area()
        self.init_content()

        # Initialize variables for dragging
        self._is_dragging = False
        self._drag_start_position = None

        if self.config.select_text:
            self.inputs_widgets[-1].setPlainText(self.config.select_text)
            
            QTimer.singleShot(200, lambda : self.inputs_widgets[-1].returnPressed.emit(0)) 
        

    def init_layout(self,):
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        css = utils.read_file('css/main_window_styles.css')
        self.setStyleSheet(css)
        self.main_widget = QWidget(objectName='Main_Widget')
        self.setCentralWidget(self.main_widget)

        self.out_layout = QVBoxLayout(self.main_widget)
        self.out_layout.setContentsMargins(5, 5, 5, 10)
        self.out_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def init_title_bar(self,):
        self.title_widget = QWidget()
        self.title_widget.setFixedHeight(20)
        self.title_layout = QHBoxLayout(self.title_widget)
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        
        # setup title bar
        self.image_label = QLabel()
        self.image_label.setFixedSize(20, 20)
        self.image_label.setScaledContents(True)
        icon = QPixmap('icons/icon.png')
        self.image_label.setPixmap(icon)
        
        self.title_layout.addWidget(self.image_label)

        self.title_label = QLabel()
        self.title_label.setText('Lancer')
        self.title_layout.addWidget(self.title_label)

        self.close_button = QPushButton(objectName='closeButton')
        self.close_button.setFixedSize(20, 20)
        self.close_button.setIcon(QIcon('icons/close.png'))  # 设置置顶图标
        self.close_button.clicked.connect(self.close)
        self.title_layout.addWidget(self.close_button)
        self.out_layout.addWidget(self.title_widget)

    def init_scroll_area(self,):
        self.scroll_area = QScrollArea(objectName='scrollArea')
        css = utils.read_file('css/scrollbar_styles.css')
        self.scroll_area.verticalScrollBar().setStyleSheet(css)
        self.scroll_area.setWidgetResizable(True)
        self.content_widget = QWidget(objectName='contentWidget')
        self.scroll_area.setWidget(self.content_widget)

        css = utils.read_file('css/scrollbar_styles.css')
        self.scroll_area.verticalScrollBar().setStyleSheet(css)

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 0, 5, 0)
        self.content_layout.setSpacing(10)
        self.content_widget.setLayout(self.content_layout)

        self.out_layout.addWidget(self.scroll_area)
        
    def init_content(self, ):
        self.inputs_widgets = []
        self.outputs_widgets = []

        self.set_position_and_gem_on_screen()

        self.new_round_widgets()
        # self.input_text_edit.returnPressed.connect(self.add_output_widget)
        # self.add_to_content_layout(self.input_text_edit)
        # self.add_to_content_layout(self.output_text_edit)

        # new_text_edit = CustomTextEdit(min_lines=3)
        # new_text_edit.setPlaceholderText("Enter text here and press Enter...")
        # new_text_edit.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # self.add_to_content_layout(new_text_edit)

    def new_round_widgets(self, ):
        is_first_round = not self.inputs_widgets

        min_lines = 8 if is_first_round else 3

        input_text_edit = CustomTextEdit(min_lines=min_lines)
        input_text_edit.index = len(self.inputs_widgets)
        input_text_edit.setPlaceholderText("Enter text here and press Enter...")
        input_text_edit.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        output_text_edit = MarkdownView()
        output_text_edit.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self.inputs_widgets.append(input_text_edit)
        self.outputs_widgets.append(output_text_edit)

        self.add_to_content_layout(input_text_edit)
        # input_text_edit.returnPressed.connect(self.add_output_widget_hook_wrapper(output_text_edit))

        # input_text_edit.returnPressed.connect(
        #     lambda : output_text_edit.setMarkdown(input_text_edit.toPlainText()))
        input_text_edit.returnPressed.connect(self.stream_openai)
        
    
    def stream_openai(self, index):
        input_text_edit = self.inputs_widgets[index]
        output_text_edit = self.outputs_widgets[index]

        if output_text_edit.is_hidden:
            if not utils.widget_in_layout(self.content_layout, output_text_edit):
                self.add_to_content_layout(output_text_edit)
                self.adjust_window_height()
                output_text_edit.is_hidden = False

        messages = self.generate_message(index)

        if self.worker and self.worker.isRunning():
            self.worker.quit()
            
        if input_text_edit.toPlainText():
            self.worker = OpenAIWorker(messages)
            self.worker.update_text.connect(output_text_edit.setMarkdown)
            if index == len(self.inputs_widgets)-1:
                self.worker.completed.connect(self.new_round_widgets)
            self.worker.start()
    
    def generate_message(self, index):
        system_prompt, user_prompt = self.config.get_prompts()
        messages = [{"role": "system", "content": system_prompt}]
        
        for i in range(index):
            messages.append({
                'role': 'user',
                'content': self.inputs_widgets[i].toPlainText()
            })
            messages.append({
                'role': 'assistant',
                'content': self.outputs_widgets[i].text
            })
        user_content = self.inputs_widgets[index].toPlainText()
        if index == 0 and user_prompt:
            user_content = user_prompt
            
        messages.append({
            'role': 'user',
            'content': user_content
        })
        return messages

    def add_output_widget_hook_wrapper(self, widget):
        def add_output_widget_hook():
            if not utils.widget_in_layout(self.content_layout, widget):
                self.add_to_content_layout(widget)
        return add_output_widget_hook

    def add_to_content_layout(self, widget):
        if not widget: return
        # self.content_widget.setUpdatesEnabled(False)
        widget.setVisible(False)
        self.content_layout.addWidget(widget)
        widget.setVisible(True)
        # self.content_widget.setUpdatesEnabled(True)

        if isinstance(widget, QTextEdit):
            widget.textChanged.connect(self.adjust_window_height)
        elif isinstance(widget, QWebEngineView):
            widget.height_changed.connect(self.adjust_window_height)

    def set_position_and_gem_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        self.main_widget.setFixedWidth(int(screen_geometry.width() * 0.30))
        
        self.max_height = int(screen_geometry.height() * 0.6)

        window_geometry = self.geometry()
        x = (screen_geometry.width() - self.main_widget.width()) // 2
        y = int(screen_geometry.height() * 0.3)
        self.move(x, y)

    def adjust_window_height(self, ):
        # print(f'content{self.content_layout.sizeHint().height()}; main_window: {self.main_widget.height()}')
        # print(f'input edit{self.input_text_edit.height()}; output edit: {self.output_text_edit.height()}')

        height = min(self.content_layout.sizeHint().height(), self.max_height)
        self.scroll_area.setFixedHeight(height)

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

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        super().closeEvent(event)

class SettingsWindow(QMainWindow):
    hotkeys_changed = pyqtSignal(str)
    def __init__(self, config_path, default_config_path):
        super().__init__()
        self.config_path = config_path
        self.default_config_path = default_config_path
        self.setWindowTitle('Lancer Settings')
        self.resize(800, 600)
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.load_config()
        self.init_ui()

    def load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)

    def save_config(self):
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.safe_dump(self.config, file, allow_unicode=True)

    def init_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)

        main_widget = QWidget()
        scroll_area.setWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        api_out_layout = QVBoxLayout()
        api_group = QGroupBox('Openai API')
        api_layout = QFormLayout()
        
        self.base_url = QLineEdit()
        self.base_url.setText(self.config['API']['base_url'])
        api_layout.addRow(QLabel('base url'), self.base_url)

        self.API_key = QLineEdit()
        self.API_key.setText(self.config['API']['api_key'])
        api_layout.addRow(QLabel('API key'), self.API_key)
        
        self.model_name = QLineEdit()
        self.model_name.setText(self.config['API']['model_name'])
        api_layout.addRow(QLabel('Model Name'), self.model_name)
        
        api_out_layout.addLayout(api_layout)
        test_api_button = QPushButton('Test API')
        test_api_button.clicked.connect(self.test_api)
        api_out_layout.addWidget(test_api_button)
        
        api_group.setLayout(api_out_layout)
        layout.addWidget(api_group)
        
        # General Settings Group
        general_group = QGroupBox('General Settings')
        general_layout = QFormLayout()

        self.hotkeys = QLineEdit()
        self.hotkeys.setText(self.config['hotkeys'])
        general_layout.addRow(QLabel('Hotkeys'), self.hotkeys)
        
        self.always_on_top = QCheckBox()
        self.always_on_top.setChecked(self.config['default']['window']['always_on_top'])
        general_layout.addRow(QLabel('Always on Top'), self.always_on_top)

        self.close_when_focus_out = QCheckBox()
        self.close_when_focus_out.setChecked(self.config['default']['window']['close_when_focus_out'])
        general_layout.addRow(QLabel('Close When Focus Out'), self.close_when_focus_out)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # Prompts Group
        prompts_group = QGroupBox('Prompts')
        prompts_layout = QFormLayout()

        self.system_prompt_wo_context = QTextEdit()
        self.system_prompt_wo_context.setMinimumHeight(100)
        self.system_prompt_wo_context.setText(self.config['default']['system_prompt_wo_context'])
        prompts_layout.addRow(QLabel('System Prompt Without Context'), self.system_prompt_wo_context)

        self.system_prompt = QTextEdit()
        self.system_prompt.setMinimumHeight(100)
        self.system_prompt.setText(self.config['default']['system_prompt'])
        prompts_layout.addRow(QLabel('System Prompt'), self.system_prompt)

        self.user_prompt = QTextEdit()
        self.user_prompt.setText(self.config['default']['user_prompt'])
        prompts_layout.addRow(QLabel('User Prompt'), self.user_prompt)

        self.user_prompt_custom = QTextEdit()
        self.user_prompt_custom.setText(self.config['default']['user_prompt_custom'])
        prompts_layout.addRow(QLabel('User Prompt Custom'), self.user_prompt_custom)

        prompts_group.setLayout(prompts_layout)
        layout.addWidget(prompts_group)

        # Custom Tasks Group
        custom_group = QGroupBox('Custom Tasks')
        custom_layout = QVBoxLayout()

        custom_description = QLabel('How you want lancer to perform when you launch Lancer in specific application.')
        custom_layout.addWidget(custom_description)
    
        add_button = QPushButton('Add Custom Task')
        add_button.clicked.connect(lambda: self.add_custom_task(custom_layout))
        custom_layout.addWidget(add_button)

        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)

        self.custom_tasks_widgets = []
        self.add_custom_tasks(custom_layout)

        # Save button
        save_button = QPushButton('Save')
        save_button.setStyleSheet('background-color: green; color: white;')
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        reset_button = QPushButton('Reset All')
        reset_button.setStyleSheet('background-color: red; color: white;')
        reset_button.clicked.connect(self.reset_settings)
        layout.addWidget(reset_button)
    
    # 修改 reset_settings 方法
    def reset_settings(self):
        reply = QMessageBox.question(self, 'Confirm Reset', 'Are you sure you want to reset all settings?', 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self._reset_settings()
    
    def _reset_settings(self):
        import shutil
        shutil.copy(self.default_config_path, self.config_path)
        self.load_config()
        central_widget = self.centralWidget().widget()
        for i in reversed(range(central_widget.layout().count())):
            widget_to_remove = central_widget.layout().itemAt(i).widget()
            central_widget.layout().removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        # 重新初始化 UI
        self.init_ui()

    def add_custom_tasks(self, custom_layout):
        for app_config in self.config['custom']:
            self.add_custom_task(custom_layout, app_config['app'], app_config['tasks'])

    def add_custom_task(self, custom_layout, app='', tasks=None):
        if tasks is None:
            tasks = []

        task_widget = QWidget()
        task_layout = QVBoxLayout()
        task_widget.setLayout(task_layout)

        app_layout = QHBoxLayout()
        app_label = QLabel('App:')
        app_line_edit = QLineEdit()
        app_line_edit.setText(app)
        app_layout.addWidget(app_label)
        app_layout.addWidget(app_line_edit)
        task_layout.addLayout(app_layout)

        tasks_label = QLabel('Tasks:')
        tasks_edit = QTextEdit()
        tasks_edit.setText("\n".join(tasks))
        task_layout.addWidget(tasks_label)
        task_layout.addWidget(tasks_edit)

        remove_button = QPushButton('Remove')
        remove_button.clicked.connect(lambda: self.remove_custom_task(custom_layout, task_widget))
        task_layout.addWidget(remove_button)
        
        # custom_layout.addWidget(task_widget)
        
        custom_layout.insertWidget(custom_layout.count()-1, task_widget)
        self.custom_tasks_widgets.append((app_line_edit, tasks_edit, task_widget))

    def remove_custom_task(self, custom_layout, task_widget):
        custom_layout.removeWidget(task_widget)
        task_widget.deleteLater()
        self.custom_tasks_widgets = [(app, tasks, widget) for app, tasks, widget in self.custom_tasks_widgets if widget != task_widget]

    def save_settings(self):
        self.config['default']['window']['always_on_top'] = self.always_on_top.isChecked()
        self.config['default']['window']['close_when_focus_out'] = self.close_when_focus_out.isChecked()
        self.config['hotkeys'] = self.hotkeys.text()
        
        self.config['default']['system_prompt_wo_context'] = self.system_prompt_wo_context.toPlainText()
        self.config['default']['system_prompt'] = self.system_prompt.toPlainText()
        self.config['default']['user_prompt'] = self.user_prompt.toPlainText()
        self.config['default']['user_prompt_custom'] = self.user_prompt_custom.toPlainText()

        self.config['custom'] = []
        for app_line_edit, tasks_edit, _ in self.custom_tasks_widgets:
            app_config = {
                'app': app_line_edit.text(),
                'tasks': tasks_edit.toPlainText().split('\n')
            }
            self.config['custom'].append(app_config)

        self.config['API']['base_url'] = self.base_url.text()
        self.config['API']['api_key'] = self.API_key.text()
        self.save_config()
        print('Settings saved')
        
    def test_api(self):
        base_url = self.base_url.text()
        api_key = self.API_key.text()
        model_name = self.model_name.text()
        
        import api
        api.setup_client(base_url, api_key, model_name)
        
        ok, msg = api.test_api(base_url, api_key, model_name)
        ok
        if ok:
            QMessageBox.information(self, 'API Test', 'API is working correctly!')
            self.config['API']['base_url'] = self.base_url.text()
            self.config['API']['api_key'] = self.API_key.text()
            api.setup_client(base_url, api_key, model_name)
            self.save_config()
        else:
            QMessageBox.warning(self, 'API Test', f'API returned an error: {msg}')
    


def create_application(args):
    print(os.environ['QTWEBENGINE_DISABLE_SANDBOX'])
    # Create the application
    print(sys.argv)
    
    app = QApplication([os.path.abspath(__file__)])
    app.setWindowIcon(QIcon('icons/icon.png'))
    # Create and show the main window
    window = Window(args=args)
    window.setWindowTitle('Lancer')
    window.setWindowIcon(QIcon('icons/icon.png'))

    window.show()
    # Run the application's event loop
    print(111111)
    sys.exit(app.exec())


if __name__ == '__main__':
    args = {
        'context_info': {'application_name': 'Microsoft Office PowerPoint', 'subTitle': '晋升答辩'},
        "select_text": ''''''
    }
    create_application(args)