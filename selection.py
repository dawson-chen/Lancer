import ctypes 
import comtypes.client
import pyperclip
from pynput.keyboard import Controller, Key
import time
import ctypes
import PIL.ImageGrab

import comtypes.client
# Generate the UIAutomationClient module
comtypes.client.GetModule('UIAutomationCore.dll')
from comtypes.gen import UIAutomationClient


def get_selected():
    try:
        text = get_text_by_automation()
        if text: 
            return text
    except:
        pass
    try:
        text = get_text_by_clipboard()
        if text:
            return text
    except:
        pass
    return None


def get_text_by_automation():
    # UIA(Microsoft UI Automation API)
    comtypes.CoInitialize()
    automation = comtypes.client.CreateObject(UIAutomationClient.CUIAutomation)
    focused_element = automation.GetFocusedElement()
    # 检查获取的元素
    if focused_element:
        # 获取 TextPattern
        text_pattern_id = UIAutomationClient.UIA_TextPatternId
        text_pattern = focused_element.GetCurrentPattern(text_pattern_id)

        if text_pattern:
            text_pattern = text_pattern.QueryInterface(UIAutomationClient.IUIAutomationTextPattern)
            # 获取 TextRange 数组
            text_ranges = text_pattern.GetSelection()
            # 检查并输出 TextRange 数组
            if text_ranges:
                target = ""
                # 获取 TextRange 数组长度
                length = text_ranges.Length
                # 迭代 TextRange 数组
                for i in range(length):
                    text_range = text_ranges.GetElement(i)
                    text = text_range.GetText(-1)
                    target += text
                return target
    return ''


# Function to get clipboard sequence number on Windows
def get_clipboard_sequence_number():
    user32 = ctypes.windll.user32
    return user32.GetClipboardSequenceNumber()

# Function to simulate Ctrl+C copy operation
def copy():
    keyboard = Controller()
    
    num_before = get_clipboard_sequence_number()

    # Release all potential pressed keys
    keyboard.release(Key.ctrl)
    keyboard.release(Key.alt)
    keyboard.release(Key.shift)
    keyboard.release(Key.space)
    keyboard.release(Key.cmd)
    keyboard.release(Key.tab)
    keyboard.release(Key.esc)
    keyboard.release(Key.caps_lock)
    keyboard.release('c')

    # Simulate Ctrl+C
    keyboard.press(Key.ctrl)
    keyboard.press('c')
    keyboard.release('c')
    keyboard.release(Key.ctrl)

    # Wait for the clipboard to update
    time.sleep(0.1)
    num_after = get_clipboard_sequence_number()
    return num_after != num_before

# Function to get text from clipboard, simulating the copy operation
def get_text_by_clipboard():

    # Read old clipboard content
    old_text = pyperclip.paste()
    old_image = None
    try:
        old_image = PIL.ImageGrab.grabclipboard()
    except:
        pass

    if copy():
        # Read new clipboard content
        new_text = pyperclip.paste()

        # Restore old clipboard content
        if old_text:
            pyperclip.copy(old_text)
        elif old_image:
            # Pyperclip does not support image pasting, using PIL for image restoration
            PIL.ImageGrab.ImageGrab.clipboard_set_image(old_image)
        else:
            pyperclip.copy('')  # Clear clipboard

        if new_text:
            return new_text.strip()
        else:
            raise ValueError("New clipboard content is not text")

    else:
        raise ValueError("Copy operation failed")
        

if __name__ == '__main__':
    while True:

        text = get_selected()
        print(text)
        import time
        time.sleep(4)