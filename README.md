## 留子课程幻灯片整理翻译工具

本工具旨在为海外留学生提供一个高效、智能的课程资料处理解决方案，以应对他们在学习过程中遇到的语言障碍和复杂的幻灯片整理挑战。

许多留学生在面对英文或其他语言的课程幻灯片时，不仅需要理解专业内容，还要克服语言隔阂，并且手动整理和翻译耗时费力，容易遗漏关键信息，尤其是在处理含有大量图表的幻灯片时。

### 程序功能

1.  **自动化内容提取与转换：** 将 PDF 格式的课程幻灯片**自动转换为结构化的 Markdown 格式**，便于后续编辑和阅读。
2.  **智能格式优化与增强：** 利用**大型语言模型 (LLM) 进行深度处理，对转换后的 Markdown 内容进行微调，优化版面格式，并智能地为图片增加注解**，提升理解效率。
3.  **精准专业翻译：** 将内容**翻译成简体中文，同时智能识别并保留专业名词的英文原文注解**，确保专业术语的准确性，避免翻译歧义，让学生在中文语境下理解内容的同时，也能熟悉和掌握专业英文表达。

### 前置要求

- Nvidia GPU
- Gemini API Key （目前使用 gemini-2.5-flash，也可以修改代码使用其他 LLM）

### 安装

1.  **安装 uv：** 如果您尚未安装 `uv`，请按照官方文档进行安装。通常可以使用 pip 安装：
    ```bash
    pip install uv
    ```
2.  **安装依赖：** 在项目根目录下，使用 `uv` 安装所有必要的依赖：
    ```bash
    uv pip install .
    ```

### 配置

本项目使用 `config.ini` 文件来管理 API 密钥。请确保在运行程序之前，在项目根目录下创建 `config.ini` 文件，并按照以下格式配置您的 `GOOGLE_API_KEY`：

```ini
[api_keys]
GOOGLE_API_KEY = 您的Google API密钥
```

请将 `您的Google API密钥` 替换为您的实际 Google API 密钥。

### 使用方法

1.  将需要处理的 PDF 文件放入 `input` 目录下。
2.  运行 `main.py` 脚本。程序将自动处理 `input` 目录下的所有 PDF 文件。请使用 `uv run` 命令来执行脚本，以确保在正确的虚拟环境中运行：
    ```bash
    uv run python main.py
    ```

## 引用

- [docling](https://github.com/docling-project/docling)
- [langchain](https://github.com/langchain-ai/langchain)
