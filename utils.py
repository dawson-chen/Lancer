import enum
import sys, os
import platform
from pynput.keyboard import Key, Controller
import pyperclip


class OperatingSystem(enum.Enum):
    WINDOWS = 'Windows'
    MACOS = 'macOS'
    LINUX = 'Linux'
    UNIX = 'Unix'
    OTHER = 'Other'


def get_activeApplication_mac():
    try:
        from AppKit import NSWorkspace
    except ImportError:
        print("can't import AppKit -- maybe you're running python from homebrew?")
        print("try running with /usr/bin/python instead")
        return None
    active_app = NSWorkspace.sharedWorkspace().activeApplication()
    return f'{active_app.get("NSApplicationBundleIdentifier")}:{active_app.get("NSApplicationName")}'


def get_activeApplication_win():
    # A simple, cross-platform module for obtaining GUI information on and controlling application's windows.
    # https://github.com/asweigart/PyGetWindow/tree/master
    import pygetwindow as gw

    foreground_window = gw.getActiveWindow()
    if not foreground_window:
        return None
    
    window_title = foreground_window.title
    if not window_title.strip():
        return None
    
    if '\u200b' in window_title:
        window_title = window_title.replace('\u200b', '')
    parts = window_title.split(' - ')
    return {'application_name': parts[-1], 'subTitle': ' - '.join(parts[:-1])}

def get_activeApplication():
    system = platform.system()
    if system == 'Windows':
        return get_activeApplication_win()
    elif system == 'macOS':
        return get_activeApplication_mac()
    return {}


def hotkey():
    from pynput import keyboard

    # The key combination to check
    COMBINATION = {keyboard.Key.alt, keyboard.KeyCode.from_char('d')}

    # The currently active modifiers
    current = set()


    def on_press(key):
        if key == keyboard.KeyCode.from_char('∂'):
            key = keyboard.KeyCode.from_char('d')
        # breakpoint()
        print(f'press: [{key}], buffer: [{current}]')
        if key in COMBINATION:
            current.add(key)
            if all(k in current for k in COMBINATION):
                print('hotkey active!')
        if key == keyboard.Key.esc:
            listener.stop()

    def on_release(key):
        if key == keyboard.Key.esc:
            return False
        current.remove(key)
        print(f'release: [{key}], buffer: [{current}]')

    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()


from pynput import keyboard
from pynput.keyboard import Key, Controller
import pyperclip

def get_selected_text():
    keyboard = Controller()
    pyperclip.copy('')
    # 模拟按下 Command + C
    with keyboard.pressed(Key.ctrl):
        keyboard.press('c')
        keyboard.release('c')
    time.sleep(0.2)
    # 使用 pyperclip 读取剪贴板内容
    copied_text = pyperclip.paste()
    return copied_text


import time
import pyperclip

def get_selected_text_from_foreground_app():
    
    from pywinauto import Desktop
    from pywinauto.keyboard import send_keys
    try:
        # 获取当前前台窗口
        foreground_window = Desktop(backend="uia").windows()[0]

        # 将焦点设置到前台窗口
        foreground_window.set_focus()

        # 清空剪贴板
        pyperclip.copy('')

        # 发送 Ctrl+C 复制选中文本
        send_keys('^c')
        time.sleep(0.5)  # 等待剪贴板内容更新

        # 获取剪贴板内容
        selected_text = pyperclip.paste()

        # 检查是否有选中文本
        if selected_text:
            return selected_text
        else:
            return None
    except Exception as e:
        print(f"获取选中文本时出错: {e}")
        return None
    
def read_file(relative_path):
    # 获取文件的绝对路径
    abs_path = os.path.abspath(relative_path)
    
    # 读取文件内容
    with open(abs_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    return content

def widget_in_layout(layout, widget):
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item.widget() == widget:
            return True
    return False

if __name__ == '__main__':
    import time
    while True:
        print(get_activeApplication())
        # print(get_selected_text_from_foreground_app())
        time.sleep(1)