from common.utils.file_util import get_resource_path

def read(md_url: str) -> str:
    with open(get_resource_path(md_url), 'r', encoding='utf-8') as file:
        content = file.read()
    return content