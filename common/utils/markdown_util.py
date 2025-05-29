

def read(md_url: str) -> str:
    with open(md_url, 'r', encoding='utf-8') as file:
        content = file.read()
    return content