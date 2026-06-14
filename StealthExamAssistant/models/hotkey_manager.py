import sys
from PySide6.QtCore import QObject, Signal, QThread
from config.settings import HOTKEY_TOGGLE, HOTKEY_QUIT, HOTKEY_PANIC, HOTKEY_RECOGNIZE

class HotkeyManager(QObject):
    """全局快捷键管理器"""
    
    # 信号
    toggle_monitoring = Signal()  # 切换监控状态
    toggle_visibility = Signal()  # 切换窗口可见性
    quit_app = Signal()  # 退出应用
    panic_triggered = Signal()  # 老板键触发
    recognize_triggered = Signal()  # 单次识别触发
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.listener = None
        # 保存当前快捷键配置
        self.hotkey_config = {
            'toggle': HOTKEY_TOGGLE,
            'quit': HOTKEY_QUIT,
            'panic': HOTKEY_PANIC,
            'recognize': HOTKEY_RECOGNIZE
        }
        self._start_listener()
        
    def _start_listener(self):
        """启动快捷键监听"""
        try:
            from pynput import keyboard
            
            # 解析快捷键配置
            def parse_hotkey(hotkey_str):
                """将快捷键字符串转换为frozenset"""
                return frozenset(hotkey_str.lower().split('+'))
            
            # 定义快捷键组合
            self.hotkeys = {
                parse_hotkey(self.hotkey_config['toggle']): self.toggle_visibility.emit,
                parse_hotkey(self.hotkey_config['quit']): self.quit_app.emit,
                parse_hotkey(self.hotkey_config['panic']): self.panic_triggered.emit,
                parse_hotkey(self.hotkey_config['recognize']): self.recognize_triggered.emit,
                frozenset({'ctrl', 'shift', 'm'}): self.toggle_monitoring.emit,  # 保留原有监控切换
            }
            
            # 当前按下的键
            self.current_keys = set()
            
            def on_press(key):
                try:
                    # 获取键名
                    if hasattr(key, 'char'):
                        key_name = key.char.lower() if key.char else None
                    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        key_name = 'ctrl'
                    elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                        key_name = 'shift'
                    elif key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                        key_name = 'cmd'
                    else:
                        key_name = None
                        
                    if key_name:
                        self.current_keys.add(key_name)
                        
                    # 检查是否匹配快捷键
                    for hotkey, callback in self.hotkeys.items():
                        if hotkey.issubset(self.current_keys):
                            callback()
                            self.current_keys.clear()
                            break
                            
                except Exception as e:
                    print(f"快捷键处理错误: {e}")
                    
            def on_release(key):
                try:
                    if hasattr(key, 'char'):
                        key_name = key.char.lower() if key.char else None
                    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        key_name = 'ctrl'
                    elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                        key_name = 'shift'
                    elif key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                        key_name = 'cmd'
                    else:
                        key_name = None
                        
                    if key_name and key_name in self.current_keys:
                        self.current_keys.remove(key_name)
                        
                except Exception as e:
                    pass
                    
            # 启动监听器
            self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.listener.daemon = True
            self.listener.start()
            
            print("[Hotkey] 全局快捷键已启用:")
            print(f"  {self.hotkey_config['toggle']} - 切换窗口")
            print(f"  {self.hotkey_config['quit']} - 退出程序")
            print(f"  {self.hotkey_config['panic']} - 老板键（紧急隐藏）")
            print(f"  {self.hotkey_config['recognize']} - 单次识别")
            print("  Ctrl+Shift+M - 切换监控")
            
        except ImportError:
            print("[Hotkey] pynput 未安装，全局快捷键不可用")
            print("[Hotkey] 请运行: pip install pynput")
        except Exception as e:
            print(f"[Hotkey] 快捷键监听启动失败: {e}")
            
    def update_hotkeys(self, toggle=None, quit_app=None, panic=None, recognize=None):
        """热更新快捷键配置"""
        # 更新配置
        if toggle is not None:
            self.hotkey_config['toggle'] = toggle
        if quit_app is not None:
            self.hotkey_config['quit'] = quit_app
        if panic is not None:
            self.hotkey_config['panic'] = panic
        if recognize is not None:
            self.hotkey_config['recognize'] = recognize
            
        # 停止旧的监听器
        if self.listener:
            self.listener.stop()
            self.listener = None
            
        # 重新启动监听器
        self._start_listener()
        print("[Hotkey] 快捷键配置已热更新")
            
    def stop(self):
        """停止监听"""
        if self.listener:
            self.listener.stop()