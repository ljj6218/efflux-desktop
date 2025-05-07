import base64

def open_and_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        file_content = f.read()
        base64_encoded = base64.b64encode(file_content).decode("utf-8")
        return base64_encoded


from pdfminer.high_level import extract_text

def extract_pdf_text(file_path):
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        print(f"读取 PDF 时出错: {e}")
        return None

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextBox, LTTextLine, LTAnno

def extract_table_like_text(file_path):
    rows = []
    for page_layout in extract_pages(file_path):
        items = []
        for element in page_layout:
            if isinstance(element, (LTTextBox, LTTextLine)):
                print(f"找到的文本: {element.get_text()}")
                if hasattr(element, 'bbox'):
                    print(f"文本的边界框: {element.bbox}")
                    for text_line in element:
                        if hasattr(text_line, 'bbox'):
                            x0, y0, x1, y1 = text_line.bbox
                            text = text_line.get_text().strip()
                            if text:
                                # 记录 (y 坐标, x 坐标, 文本)
                                items.append((y1, x0, text))
            elif isinstance(element, LTAnno):
                print("找到注释，跳过...")

            # if isinstance(element, LTTextContainer):
            #     for text_line in element:
            #         x0, y0, x1, y1 = text_line.bbox
            #         text = text_line.get_text().strip()
            #         if text:
            #             # 记录 (y 坐标, x 坐标, 文本)
            #             items.append((y1, x0, text))

        # 按 y 从高到底排序（上到下）
        items.sort(key=lambda i: -i[0])

        current_row_y = None
        current_row = []

        for y, x, text in items:
            if current_row_y is None or abs(current_row_y - y) > 5:
                # 保存上一行
                if current_row:
                    # 按 x 从大到小排序（右到左）
                    # current_row.sort(key=lambda i: -i[0])
                    rows.append([t for _, t in current_row])
                current_row = [(x, text)]
                current_row_y = y
            else:
                current_row.append((x, text))

        # 最后一行
        if current_row:
            current_row.sort(key=lambda i: -i[0])
            rows.append([t for _, t in current_row])

    return rows

