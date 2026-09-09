"""Build an offline article from the saved original; validate downloaded PDFs."""

import base64
import copy
import hashlib
import json
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

from lxml import html
from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
PAGE_URL = "https://www.metodolog.ru/node/975"
PDF_URLS = {
    "bushuev-2022-physical-effects.pdf": "https://books.ifmo.ru/file/pdf/3113.pdf",
    "triz-v-razvitii-2023-issue-12.pdf": (
        "https://r1.nubex.ru/s828-c8b/f3978_34/"
        "%D0%A2%D0%A0%D0%98%D0%97%20%D0%B2%20%D1%80%D0%B0%D0%B7%D0%B2%D0%B8%D1%82%D0%B8%D0%B8-20-09-2023.pdf"
    ),
}


def prepare():
    original = ROOT / "bushuev-2011-genetic-algorithms.original.html"
    source = html.fromstring(original.read_bytes())
    bodies = source.xpath("//div[contains(@class, 'field-name-body')]//div[@class='field-item even']")
    assert len(bodies) == 1, "Article body missing or ambiguous"
    body = bodies[0]
    expected_text = body.text_content()
    assert "Использование" in source.find(".//title").text
    assert "Литература" in expected_text, "Bibliography missing"
    article = copy.deepcopy(body)
    images = []
    for node in article.findall(".//img"):
        url = urljoin(PAGE_URL, node.get("src"))
        assert url.startswith("https://www.metodolog.ru/sites/"), url
        with urlopen(url, timeout=30) as response:
            raw = response.read()
            mime = response.headers.get_content_type()
        assert mime.startswith("image/"), mime
        with Image.open(BytesIO(raw)) as picture:
            picture.verify()
        node.set("src", "data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii"))
        images.append({"url": url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    assert len(images) == 6, "Unexpected article image count; inspect original"
    assert not article.xpath(".//script | .//iframe | .//object | .//embed"), "Unexpected active content"
    for node in article.iter():
        assert not any(key.lower().startswith("on") for key in node.attrib), "Active HTML attribute"
    assert article.text_content() == expected_text, "Article text changed"
    title = "Использование генетических алгоритмов для решения изобретательских задач"
    offline = ROOT / "bushuev-2011-genetic-algorithms.offline.html"
    offline.write_text(
        '<!doctype html><html lang="ru"><meta charset="utf-8"><title>' + title + '</title>'
        '<style>body{max-width:1100px;margin:2em auto;padding:0 1em;font:18px/1.5 serif}'
        'img{max-width:100%;height:auto}table{border-collapse:collapse}td,th{padding:4px}</style>'
        '<h1>' + title + '</h1><p>Локальная копия статьи А. Б. Бушуева. '
        'Дата публикации страницы: 29.04.2011. <a href="' + PAGE_URL + '">Источник</a>. '
        'Комментарии сайта не включены; текст, таблицы и 6 изображений статьи сохранены.</p>'
        + html.tostring(article, encoding="unicode") + '</html>', encoding="utf-8", newline="",
    )
    reread = html.fromstring(offline.read_bytes())
    assert reread.xpath("//div[@class='field-item even']")[0].text_content() == expected_text
    assert all(node.get("src").startswith("data:image/") for node in reread.findall(".//img"))
    assert len(reread.findall(".//table")) == len(body.findall(".//table"))
    records = []
    for filename, url in PDF_URLS.items():
        path = ROOT / filename
        assert path.read_bytes().startswith(b"%PDF-"), filename
        reader = PdfReader(path, strict=True)
        texts = [page.extract_text() or "" for page in reader.pages]
        assert all(text.strip() for text in texts), "Empty PDF text page; inspect visually"
        record = {"file": filename, "source_url": url, "pages": len(texts)}
        if "2023" in filename:
            record["article_title_pdf_pages"] = [i + 1 for i, text in enumerate(texts) if "тренды физических эффектов" in " ".join(text.lower().split())]
            record["article_doi_pdf_pages"] = [i + 1 for i, text in enumerate(texts) if "37095-2023-1-78-85" in text]
            assert len(texts) == 327 and record["article_doi_pdf_pages"] == [78]
            assert "ЛИТЕРАТУРА" in texts[84]
            record["article_pdf_pages"] = [78, 85]
        else:
            assert len(texts) == 48
        records.append(record)
    records.extend([
        {"file": original.name, "source_url": PAGE_URL, "kind": "unchanged HTML response"},
        {"file": offline.name, "source_url": PAGE_URL, "kind": "offline article derivative", "images": images},
    ])
    for record in records:
        raw = (ROOT / record["file"]).read_bytes()
        record.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    result = {"retrieved_date": "2026-09-08", "records": records}
    (ROOT / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    prepare()
