from common.utils.file_util import get_resource_path, check_file_and_create

def read(md_url: str) -> str:
    with open(get_resource_path(md_url), 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def write(md_url: str, content: str) -> None:
    check_file_and_create(get_resource_path(md_url))
    with open(get_resource_path(md_url), 'w', encoding='utf-8') as file:
        file.write(content)