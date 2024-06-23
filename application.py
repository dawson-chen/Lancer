from typing import List
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from windows import Window, SettingsWindow
import threading
import keyboard
from config import Config
import sys
import selection, utils
import shutil
import os


class TrayApplication(QApplication):
    show_window = pyqtSignal()
    
    def __init__(self, argv: List[str]) -> None:
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        self.tray_icon = QSystemTrayIcon(QIcon("icons/icon.png"), self)
        
        self.create_tray_menu()
        
        self.pop_window = None
        
        if not os.path.exists('configs/config.yaml'):
            shutil.copy('configs/default_config.yaml', 'configs/config.yaml')
        self.settings_window = SettingsWindow('configs/config.yaml', 'configs/default_config.yaml')
        
        self.hotkey_listen_t = threading.Thread(target=self.keyboard_listener, daemon=True)
        self.hotkey_listen_t.start()
        
        self.settings_window.hotkeys_changed.connect(self.change_hotkey)
        
        self.show_window.connect(self.open_window)
        
    def create_tray_menu(self,):
        tray_menu = QMenu()
        open_settings_action = QAction("Open Settings", self)
        open_settings_action.triggered.connect(self.open_settings_window)
        tray_menu.addAction(open_settings_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def change_hotkey(self, old_hotkeys):
        keyboard.remove_hotkey(old_hotkeys)
        keyboard.add_hotkey(self.config_window.config['hotkeys'], self.trigger_business_window)
        
    def keyboard_listener(self):
        keyboard.add_hotkey('alt+d', self.trigger_business_window)
        keyboard.wait()
    
    def trigger_business_window(self):
        self.show_window.emit()
        
    def open_window(self, ):
        selected_text = selection.get_selected()
        active_app = utils.get_activeApplication()
        args={
            "select_text": selected_text,
            "context_info": active_app
        }
        self.pop_window = Window(args)
        self.pop_window.show()
    
    def open_settings_window(self):
        self.settings_window.show()
    
    def quit(self):
        keyboard.unhook_all_hotkeys()  # 解除所有快捷键绑定
        self.tray_icon.hide()
        sys.exit()


if __name__ == "__main__":
    app = TrayApplication(sys.argv)
    sys.exit(app.exec())