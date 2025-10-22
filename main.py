import base64
import os
import re
import configparser
import sys
from pathlib import Path
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
)
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.base import ImageRefMode
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI


def convert_pdf_to_markdown(input_doc_path, output_md_path):
    """Converts a PDF document to Markdown format."""
    accelerator_options = AcceleratorOptions(
        num_threads=8, device=AcceleratorDevice.CUDA
    )

    pipeline_options = PdfPipelineOptions()
    pipeline_options.accelerator_options = accelerator_options
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        }
    )

    # Enable the profiling to measure the time spent
    settings.debug.profile_pipeline_timings = True

    # Convert the document
    print(f"Converting {input_doc_path} to Markdown...")
    conversion_result = converter.convert(input_doc_path)
    doc = conversion_result.document

    # List with total time per document
    doc_conversion_secs = conversion_result.timings["pipeline_total"].times

    doc.save_as_markdown(
        filename=Path(output_md_path),
        artifacts_dir=Path(os.path.join(os.path.splitext(os.path.basename(output_md_path))[0], "image")),
        image_mode=ImageRefMode.REFERENCED,
    )
    print(f"Conversion took: {doc_conversion_secs} seconds")
    print(f"Markdown file saved to: {output_md_path}")


def simplify_image_references_in_markdown(markdown_path):
    """Simplifies image names in the markdown file and renames the image files."""
    print(f"Simplifying image references in {markdown_path}...")
    with open(markdown_path, "r+", encoding="utf-8") as f:
        content = f.read()

        # Find all unique image paths
        image_paths = set(re.findall(r"\((\S*?image_\d{6}_[a-f0-9]+\.png)\)", content))

        for old_path in image_paths:
            old_path_prefix = os.path.join("output", old_path)
            if not os.path.exists(path=old_path_prefix):
                continue

            directory = os.path.dirname(old_path_prefix)
            old_filename = os.path.basename(old_path_prefix)

            # Create new filename, e.g., image_000000.png
            parts = old_filename.split("_")
            new_filename = f"{parts[0]}_{parts[1]}.png"
            new_path = os.path.join(directory, new_filename)

            # Rename the physical file
            if not os.path.exists(new_path):
                os.rename(old_path_prefix, new_path)

            # Replace the path in the markdown content
            new_path_in_markdown = new_path.replace(f"output{os.sep}", "")
            content = content.replace(old_path, new_path_in_markdown)

        # Go back to the beginning of the file and write the modified content
        f.seek(0)
        f.write(content)
        f.truncate()
    print("Image references simplified.")


def refine_and_translate_content(markdown_path, pdf_path):
    """Refines and translates the Markdown content using an LLM."""
    print("Starting content refinement and translation...")

    config = configparser.ConfigParser()
    config.read('config.ini')
    google_api_key = config.get('api_keys', 'GOOGLE_API_KEY', fallback=None)

    if not google_api_key:
        print("Error: GOOGLE_API_KEY not found in config.ini")
        return

    os.environ["GOOGLE_API_KEY"] = google_api_key
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    except Exception as e:
        print(
            f"Error initializing LLM. Make sure your Google API key is set correctly. Error: {e}"
        )
        return

    try:
        with open(markdown_path, "rb") as f:
            markdown_content = f.read()

        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

    except FileNotFoundError as e:
        print(f"Error reading files: {e}")
        return

    prompt = """
    您是一名专业的科技文档编辑和翻译。您的任务是润色一份从随附 PDF 文档自动转换而来的 Markdown 文本。请以原始 PDF 作为布局、图像和上下文的真实依据。

    请根据提供的 Markdown 和 PDF 执行以下四项操作：

    1.  **清理多余字符**：查看 Markdown 文本，删除原始 PDF 中不存在的任何转换伪影或奇怪格式。
    2.  **解释图像内容**：参考 PDF 中的图表、示意图和图像，在图像引用后添加清晰简洁的解释。
    3.  **更正列表格式**：转换可能使嵌套列表扁平化。分析 PDF 中的列表结构，并在 Markdown 中恢复正确的多级缩进。
    4.  **翻译成中文**：将整个清理和更正后的文档翻译成简体中文。当您遇到专业或技术术语时，您必须在其译文旁边保留原始英文术语并用括号括起来。
    
    只需要输出调整翻译后的 markdown 文本，不需要任何其他的文字内容。
    """

    message_content = [
        SystemMessage(prompt),
        HumanMessage(
            [
                {
                    "type": "media",
                    "mime_type": "text/markdown",
                    "data": base64.b64encode(markdown_content).decode("utf-8"),
                },
                {
                    "type": "text",
                    "text": "这是原始的PDF文件:\n",
                },
                {
                    "type": "media",
                    "mime_type": "application/pdf",
                    "data": base64.b64encode(pdf_bytes).decode("utf-8"),
                },
            ]
        ),
    ]

    print(
        "Sending request to Gemini with the PDF and Markdown... This may take a moment."
    )
    try:
        response = llm.invoke(message_content)
        refined_content = response.content
    except Exception as e:
        print(f"An error occurred while invoking the LLM: {e}")
        return

    refined_output_path = os.path.splitext(markdown_path)[0] + "_refined_zh.md"
    with open(refined_output_path, "w", encoding="utf-8") as f:
        f.write(str(refined_content))

    print(f"Task complete! Refined and translated file saved to: {refined_output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <pdf_file_name>")
        print("Example: python main.py material.pdf")
        print("Make sure you put pdf file into input directory")
        sys.exit(1)

    fileName = sys.argv[1]
    if not fileName.endswith(".pdf"):
        print("Error: The provided file must be a PDF file (e.g., 08.pdf)")
        sys.exit(1)

    input_doc_path = os.path.join("input", fileName)
    output_md_path = os.path.join("output", fileName.replace(".pdf", ".md"))

    # Step 1: Convert PDF to Markdown
    convert_pdf_to_markdown(input_doc_path, output_md_path)

    # Step 2: Simplify image references
    simplify_image_references_in_markdown(output_md_path)

    # # Step 3: Refine and translate the content
    refine_and_translate_content(output_md_path, input_doc_path)


if __name__ == "__main__":
    main()
