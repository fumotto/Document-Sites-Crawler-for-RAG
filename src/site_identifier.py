import re

def generate_site_identifier(url):
    # スキーム除去
    url = re.sub(r'^https?://', '', url)
    # 小文字化
    url = url.lower()
    # 英数字以外の文字を_に置換
    url = re.sub(r'[^a-z0-9]', '_', url)
    # _の連続を1文字に圧縮
    url = re.sub(r'_+', '_', url)
    # 先頭・末尾の_を除去
    url = url.strip('_')
    return url