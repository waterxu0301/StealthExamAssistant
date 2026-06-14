#!/bin/bash

# ==================================================
# Stealth Exam Assistant 启动脚本
# ==================================================

echo "=========================================="
echo "  Stealth Exam Assistant v1.0.0"
echo "  无痕答题辅助助手"
echo "=========================================="
echo ""

# 检查 Python 版本
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "🐍 Python 版本: $PYTHON_VERSION"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 首次运行，正在创建虚拟环境..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 创建虚拟环境失败"
        exit 1
    fi
    echo "✅ 虚拟环境创建成功"
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖是否安装
if [ ! -f "venv/.deps_installed" ]; then
    echo ""
    echo "📦 正在安装依赖..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if [ $? -ne 0 ]; then
        echo "❌ 安装依赖失败"
        exit 1
    fi
    touch venv/.deps_installed
    echo "✅ 依赖安装完成"
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  未找到 .env 配置文件"
    echo "   请复制 .env.example 为 .env 并填入配置"
    echo ""
    echo "   cp .env.example .env"
    echo ""
    echo "   必填配置："
    echo "   - LLM_API_KEY: 云端 API Key"
    echo ""
    echo "   可选配置（首次使用需安装 Ollama）："
    echo "   - ollama serve"
    echo "   - ollama pull nomic-embed-text"
    echo ""
    read -p "按 Enter 继续（使用默认配置）..."
fi

# 创建必要目录
mkdir -p data logs debug

echo ""
echo "🚀 启动程序..."
echo ""
echo "快捷键说明："
echo "  Ctrl+Shift+O - 显示/隐藏 HUD"
echo "  Ctrl+Shift+M - 开始/停止监控"
echo "  Ctrl+Shift+A - 单次识别题目"
echo "  Ctrl+Shift+X - 老板键（紧急隐藏）"
echo "  Ctrl+Shift+Q - 退出程序"
echo ""
echo "=========================================="

# 启动程序
$PYTHON_CMD main.py
