# Stealth Exam Assistant v1.0.0

**无痕答题辅助助手** — 基于 AI 的智能答题辅助工具

---

## 📋 功能特性

### 核心功能
- **智能识别**：OCR 识别屏幕题目，AI 分析并给出答案
- **三级检索**：FTS5 全文检索 → 向量语义检索 → 大模型推理
- **题库积累**：AI 回答的题目自动入库，下次直接命中
- **批量复盘**：支持一次性导入大量题目，AI 自动清洗入库
- **配置热更新**：修改配置后无需重启程序，立即生效

### 隐蔽特性
- **防录屏**：macOS/Windows 系统级防截图
- **终极置顶**：窗口始终在最上层，覆盖全屏应用
- **鼠标穿透**：监控时鼠标点击穿透，不影响操作
- **老板键**：一键隐藏，CPU 占用瞬间归零
- **快捷键驱动**：所有操作通过快捷键完成

---

## 🚀 快速开始

### 第一步：环境准备

**系统要求**：
- macOS 10.15+ 或 Windows 10+
- Python 3.8 或更高版本

**检查 Python 是否已安装**：
```bash
python3 --version   # macOS/Linux
python --version    # Windows
```

如果未安装 Python，请前往 [python.org](https://www.python.org/downloads/) 下载安装。

---

### 第二步：启动程序

#### macOS 用户

```bash
# 1. 打开终端，进入项目目录
cd /path/to/StealthExamAssistant

# 2. 给启动脚本添加执行权限
chmod +x start.sh

# 3. 运行启动脚本
./start.sh
```

#### Windows 用户

```cmd
# 1. 打开命令提示符或 PowerShell，进入项目目录
cd C:\path\to\StealthExamAssistant

# 2. 运行启动脚本
start.bat
```

> 💡 首次运行会自动创建虚拟环境并安装依赖，需要等待几分钟。

---

### 第三步：配置 API（必须）

程序需要连接云端大模型才能使用 AI 推理功能。

#### 3.1 创建配置文件

```bash
# macOS/Linux
cp .env.example .env

# Windows
copy .env.example .env
```

#### 3.2 编辑配置文件

```bash
# macOS
open -e .env

# Windows
notepad .env
```

#### 3.3 填入 API 配置

```env
# ==================== 云端 API（必填）====================
LLM_API_KEY=你的API密钥
LLM_API_BASE_URL=https://api.xiaomimimo.com/v1
LLM_MODEL_NAME=mimo-v2.5
```

**支持的 API 服务商**（任选其一）：

| 服务商 | API 地址 | 模型名称 | 获取 API Key |
|--------|----------|----------|-------------|
| 小米 MiMo | https://api.xiaomimimo.com/v1 | mimo-v2.5 | [官网申请](https://mimo.xiaomi.com) |
| OpenAI | https://api.openai.com/v1 | gpt-4 | [platform.openai.com](https://platform.openai.com) |
| 通义千问 | https://dashscope.aliyuncs.com/api/v1 | qwen-turbo | [阿里云控制台](https://dashscope.console.aliyun.com) |
| 智谱 AI | https://open.bigmodel.cn/api/paas/v4 | glm-4 | [open.bigmodel.cn](https://open.bigmodel.cn) |

> 💡 只要是 OpenAI 兼容格式的 API 都可以使用

---

### 第四步：安装本地 Embedding（可选，强烈推荐）

本地 Embedding 可以大幅提升题目命中率，且完全免费。

#### 4.1 安装 Ollama

**macOS**：
```bash
brew install ollama
```

**Windows**：
前往 [ollama.ai](https://ollama.ai) 下载安装包

#### 4.2 启动 Ollama 服务

```bash
ollama serve
```

> ⚠️ 保持此终端窗口打开，不要关闭

#### 4.3 拉取 Embedding 模型

打开**新的终端窗口**，执行：
```bash
ollama pull nomic-embed-text
```

模型大小约 274MB，下载完成后即可使用。

---

### 第五步：开始使用

#### 5.1 启动程序

```bash
# macOS
./start.sh

# Windows
start.bat
```

#### 5.2 基本操作流程

```
┌─────────────────────────────────────────────────────────┐
│  1. 主控台 → 创建/选择考试项目                          │
│     ↓                                                   │
│  2. 点击「启动辅助 HUD」按钮                            │
│     ↓                                                   │
│  3. HUD 出现 → 点击「□」按钮框选题目区域               │
│     ↓                                                   │
│  4. 按 Ctrl+Shift+M 开始监控                           │
│     ↓                                                   │
│  5. 切换到考试页面 → 按 Ctrl+Shift+A 识别题目          │
│     ↓                                                   │
│  6. HUD 显示题目和答案                                  │
└─────────────────────────────────────────────────────────┘
```

---

## ⌨️ 快捷键说明

| 快捷键 | 功能 | 使用场景 |
|--------|------|----------|
| `Ctrl+Shift+O` | 显示/隐藏 HUD | 需要查看答案时显示，不需要时隐藏 |
| `Ctrl+Shift+M` | 开始/停止监控 | 框选区域后开始监控 |
| `Ctrl+Shift+A` | 单次识别 | 每次需要识别题目时按一次 |
| `Ctrl+Shift+X` | 老板键 | 紧急情况一键隐藏，CPU 归零 |
| `Ctrl+Shift+Q` | 退出程序 | 完全退出 |

> 💡 **macOS 用户**：请使用 `Cmd` 键代替 `Ctrl` 键

> 💡 所有快捷键可在「设置」中自定义，修改后立即生效

---

## 🔧 详细配置说明

### .env 配置项完整说明

```env
# ==================== 云端 API（必填）====================
# 用于 AI 推理，必须配置
LLM_API_KEY=sk-xxx                    # 你的 API 密钥
LLM_API_BASE_URL=https://api.xxx.com/v1  # API 服务地址
LLM_MODEL_NAME=model-name             # 使用的模型名称

# ==================== 本地 Embedding（可选）====================
# 用于向量语义检索，大幅提升命中率
EMBEDDING_MODE=local                  # local=本地Ollama, cloud=云端API
EMBEDDING_API_KEY=ollama              # 本地模式固定为 ollama
EMBEDDING_API_BASE_URL=http://127.0.0.1:11434/v1  # Ollama 服务地址
EMBEDDING_MODEL_NAME=nomic-embed-text # Embedding 模型名称

# ==================== 快捷键（可选）====================
# 格式: ctrl+shift+字母 或 cmd+shift+字母（macOS）
HOTKEY_TOGGLE=ctrl+shift+o           # 显示/隐藏 HUD
HOTKEY_RECOGNIZE=ctrl+shift+a        # 单次识别
HOTKEY_PANIC=ctrl+shift+x            # 老板键（紧急隐藏）
HOTKEY_QUIT=ctrl+shift+q             # 退出程序

# ==================== UI 设置（可选）====================
HUD_OPACITY=0.9                       # HUD 透明度 (0.3-1.0)
```

### 配置热更新

修改 `.env` 文件后，无需重启程序：
1. 在主控台点击「⚙ 设置」按钮
2. 修改配置
3. 点击「保存配置」
4. 配置立即生效

---

## ⚠️ 权限设置（重要）

### macOS 权限设置

程序需要以下权限才能正常工作：

#### 1. 辅助功能权限（快捷键功能）

```
系统设置 → 隐私与安全性 → 辅助功能 → 添加「终端」或「Python」
```

**操作步骤**：
1. 打开「系统设置」
2. 点击「隐私与安全性」
3. 点击「辅助功能」
4. 点击左下角「+」按钮
5. 找到并添加「终端」应用（或 Python 应用）
6. 确保开关已打开

#### 2. 屏幕录制权限（截图功能）

```
系统设置 → 隐私与安全性 → 屏幕录制 → 添加「终端」或「Python」
```

**操作步骤**：
1. 打开「系统设置」
2. 点击「隐私与安全性」
3. 点击「屏幕录制」
4. 点击左下角「+」按钮
5. 找到并添加「终端」应用（或 Python 应用）
6. 确保开关已打开

> ⚠️ 如果不设置这些权限，快捷键和截图功能将无法使用

### Windows 权限设置

- 防录屏功能可能需要**管理员权限**运行
- 如遇杀毒软件拦截，请将程序添加到信任列表

---

## 📖 使用技巧

### 1. 如何提高识别准确率？

- 框选区域时，只框选**题目文字部分**，不要包含按钮、工具栏等
- 确保题目文字清晰可见，不要有遮挡
- 如果识别不准确，可以重新框选更精确的区域

### 2. 如何快速积累题库？

- 每次 AI 回答的题目会自动保存到题库
- 使用「批量复盘」功能可以一次性导入大量题目
- 安装 Ollama 后，语义检索会更准确

### 3. 老板键使用场景

- 有人靠近时，按 `Ctrl+Shift+X` 立即隐藏
- HUD 消失，CPU 占用瞬间归零
- 再按一次 `Ctrl+Shift+X` 恢复显示

### 4. 批量复盘功能

适用于：
- 导入往年真题
- 导入练习题库
- 导入错题本

操作步骤：
1. 复制题目文本（任意格式）
2. 切换到「批量复盘」选项卡
3. 粘贴文本
4. 点击「开始清洗入库」
5. AI 自动提取题目并保存

---

## 🐛 常见问题解答

### Q1: 启动时报错 "ModuleNotFoundError"

**原因**：依赖未安装完整

**解决**：
```bash
# 删除虚拟环境，重新安装
rm -rf venv
./start.sh  # macOS
start.bat   # Windows
```

### Q2: OCR 识别不到文字

**可能原因**：
1. 框选区域不正确
2. 屏幕分辨率问题
3. 权限未设置

**解决**：
1. 重新框选，确保只包含题目文字
2. 检查 `debug/latest_capture.png` 截图是否正常
3. 确认 macOS 已授予屏幕录制权限

### Q3: 快捷键无反应

**可能原因**：
1. macOS 辅助功能权限未设置
2. 与其他软件快捷键冲突

**解决**：
1. 按照「权限设置」章节设置辅助功能权限
2. 在「设置」中自定义快捷键，避免冲突

### Q4: 答案显示"未命中"

**原因**：题库为空或题目不在题库中

**解决**：
1. 首次使用会调用 AI 实时推理
2. 积累足够题目后会自动命中
3. 安装 Ollama 可启用语义检索，提高命中率

### Q5: 程序崩溃或闪退

**解决**：
1. 确认 Python 版本 ≥ 3.8
2. 删除 venv 目录，重新安装依赖
3. 查看终端/命令提示符中的错误信息
4. 检查 `.env` 配置是否正确

### Q6: macOS 提示"无法验证开发者"

**解决**：
```bash
# 打开终端，执行以下命令
xattr -cr /path/to/StealthExamAssistant
```

### Q7: Ollama 连接失败

**检查步骤**：
1. 确认 Ollama 已安装：`ollama --version`
2. 确认 Ollama 服务已启动：`ollama serve`
3. 确认模型已下载：`ollama list`
4. 测试连接：`curl http://127.0.0.1:11434`

---

## 📁 项目结构说明

```
StealthExamAssistant/
├── main.py                 # 程序入口
├── start.sh               # macOS 启动脚本
├── start.bat              # Windows 启动脚本
├── requirements.txt       # Python 依赖列表
├── .env.example           # 配置文件模板
├── README.md              # 本说明文档
│
├── config/                # 配置管理
│   └── settings.py        # 配置加载逻辑
│
├── models/                # 核心服务层
│   ├── vision_service.py  # 视觉服务（截屏）
│   ├── ocr_service.py     # OCR 文字识别
│   ├── llm_service.py     # LLM 大模型推理
│   ├── embedding_service.py # 向量检索服务
│   ├── database_service.py # 数据库服务
│   ├── hotkey_manager.py  # 全局快捷键管理
│   └── ...
│
├── views/                 # 界面层
│   ├── main_window.py     # 主控台窗口
│   ├── stealth_hud.py     # 悬浮窗 HUD
│   ├── settings_dialog.py # 设置对话框
│   └── ...
│
├── controllers/           # 控制器层
│   └── search_controller.py # 三级检索控制器
│
├── assets/                # 资源文件
│   └── icons/             # 图标
│
├── data/                  # 数据目录（自动创建）
│   └── exam_data.db       # SQLite 数据库
│
├── logs/                  # 日志目录（自动创建）
└── debug/                 # 调试目录（自动创建）
    └── latest_capture.png # 最新截图
```

---

## 📝 更新日志

### v1.0.0 (2026-06-14)

**核心功能**：
- ✅ OCR 题目识别
- ✅ AI 答案推理
- ✅ 三级检索引擎（FTS5 → 向量 → LLM）
- ✅ 批量复盘功能
- ✅ 题库自动积累

**隐蔽特性**：
- ✅ macOS/Windows 防录屏
- ✅ 终极置顶（Level 2000）
- ✅ 鼠标穿透
- ✅ 老板键紧急隐藏
- ✅ 全快捷键驱动

**用户体验**：
- ✅ 配置热更新（无需重启）
- ✅ 自定义快捷键
- ✅ Material Design 界面
- ✅ 跨平台支持

---

## 📄 许可证

本项目仅供学习研究使用，请勿用于商业用途。

---

## 🤝 反馈与支持

如有问题或建议：
1. 查看本 README 的「常见问题」章节
2. 检查 `logs/` 目录下的日志文件
3. 提交 Issue 描述问题

---

## 🙏 致谢

- [RapidOCR](https://github.com/RapidAI/RapidOCR) - OCR 文字识别
- [Ollama](https://ollama.ai) - 本地大模型运行
- [PySide6](https://doc.qt.io/qtforpython-6/) - GUI 框架
- [mss](https://github.com/BoboTiG/python-mss) - 屏幕截图
