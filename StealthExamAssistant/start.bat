@echo off
chcp 65001 >nul

echo ==========================================
echo   Stealth Exam Assistant v1.0.0
echo   无痕答题辅助助手
echo ==========================================
echo.

REM 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Python，请先安装 Python 3.8+
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 🐍 Python 版本:
python --version
echo.

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 首次运行，正在创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖是否安装
if not exist "venv\.deps_installed" (
    echo.
    echo 📦 正在安装依赖（首次安装需要几分钟）...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo ❌ 安装依赖失败
        pause
        exit /b 1
    )
    echo. > venv\.deps_installed
    echo ✅ 依赖安装完成
)

REM 检查配置文件
if not exist ".env" (
    echo.
    echo ⚠️  未找到 .env 配置文件
    echo    请复制 .env.example 为 .env 并填入配置
    echo.
    echo    命令: copy .env.example .env
    echo.
    echo    必填配置:
    echo    - LLM_API_KEY: 云端 API Key
    echo    - LLM_API_BASE_URL: API 地址
    echo    - LLM_MODEL_NAME: 模型名称
    echo.
    echo    可选配置（首次使用需安装 Ollama）:
    echo    - ollama serve
    echo    - ollama pull nomic-embed-text
    echo.
    pause
)

REM 创建必要目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "debug" mkdir debug

echo.
echo 🚀 启动程序...
echo.
echo 快捷键说明:
echo   Ctrl+Shift+O - 显示/隐藏 HUD
echo   Ctrl+Shift+M - 开始/停止监控
echo   Ctrl+Shift+A - 单次识别题目
echo   Ctrl+Shift+X - 老板键（紧急隐藏）
echo   Ctrl+Shift+Q - 退出程序
echo.
echo ==========================================

REM 启动程序
python main.py

pause
