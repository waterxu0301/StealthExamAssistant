#!/usr/bin/env python3
"""
Stealth Exam Assistant - Main Entry Point
Dual-window architecture: Main Console + Stealth HUD
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from views.main_window import MainWindow
from views.stealth_hud import StealthHUD
from models.hotkey_manager import HotkeyManager

def main():
    """Main application entry point."""
    # High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Stealth Exam Assistant")
    app.setApplicationVersion("2.0.0")
    
    # Set application icon
    icon_path = Path(__file__).parent / "assets" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create main window (console)
    main_window = MainWindow()
    
    # Create stealth HUD (hidden initially)
    hud = StealthHUD()
    
    # Create hotkey manager
    hotkey_manager = HotkeyManager()
    
    # 设置热键管理器到主窗口（用于配置热更新）
    main_window.set_hotkey_manager(hotkey_manager)
    
    # 老板键状态跟踪
    is_panic_mode = False
    
    # Connect signals
    def launch_hud():
        main_window.hide()
        hud.show()
        
    def return_to_main():
        hud.hide()
        main_window.show()
        
    def toggle_monitoring():
        if hud.isVisible():
            hud.toggle_monitoring()
            
    def toggle_visibility():
        if hud.isVisible():
            hud.hide()
        elif main_window.isVisible():
            main_window.hide()
            hud.show()
        else:
            hud.show()
            
    def trigger_recognize():
        """触发单次识别"""
        if hud.isVisible() and hud.is_monitoring:
            print("[Main] 快捷键触发识别")
            hud.vision_service.capture_and_recognize()
            
    def panic_toggle():
        """老板键切换：立即隐藏/恢复HUD"""
        nonlocal is_panic_mode
        if is_panic_mode:
            # 恢复模式
            hud.show()
            is_panic_mode = False
            print("[Panic] 已恢复正常模式")
        else:
            # 紧急隐藏模式
            hud.hide()
            is_panic_mode = True
            print("[Panic] 已进入紧急隐藏模式")
            
    def quit_app():
        """退出应用"""
        print("[App] 正在退出...")
        # 停止监控
        if hud.is_monitoring:
            hud.stop_monitoring()
        # 停止热键监听
        hotkey_manager.stop()
        print("[App] 退出完成")
        app.quit()
        
    # Connect signals
    main_window.launch_hud.connect(launch_hud)
    hud.return_to_main.connect(return_to_main)
    hotkey_manager.toggle_monitoring.connect(toggle_monitoring)
    hotkey_manager.toggle_visibility.connect(toggle_visibility)
    hotkey_manager.recognize_triggered.connect(trigger_recognize)
    hotkey_manager.panic_triggered.connect(panic_toggle)
    hotkey_manager.quit_app.connect(quit_app)
    
    # Show main window
    main_window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
