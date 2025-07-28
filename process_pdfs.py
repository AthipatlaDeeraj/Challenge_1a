import os
import json
import fitz
import re
from collections import defaultdict
from langdetect import detect, LangDetectException
from langdetect import DetectorFactory

DetectorFactory.seed = 0

def is_likely_heading(text, font_size, main_text_size, font_flags, position_y, page_height):
    if not text or len(text.strip()) < 2:
        return False
    clean_text = text.strip()
    if len(clean_text) > 200:
        return False
    words = clean_text.split()
    if len(words) > 10:
        return False
    skip_patterns = [
        r'^\d+\s*$',
        r'^page\s+\d+',
        r'^figure\s+\d+',
        r'^table\s+\d+',
        r'^\d+\.\d+\.\d+\.\d+',
        r'^https?://',
        r'^\w+@\w+\.'
    ]
    for pattern in skip_patterns:
        if re.match(pattern, clean_text.lower()):
            return False
    score = 0
    if font_size > main_text_size * 1.15:
        score += 3
    elif font_size > main_text_size * 1.05:
        score += 1
    if font_flags & 16:
        score += 2
    relative_position = position_y / page_height if page_height > 0 else 0.5
    if relative_position < 0.2 or relative_position > 0.8:
        score += 1
    if clean_text.isupper() and len(words) <= 8:
        score += 2
    elif len([w for w in words if w[0].isupper()]) / len(words) > 0.7:
        score += 1
    if re.match(r'^\d+\.?\s+[A-Z]', clean_text):
        score += 2
    elif re.match(r'^\d+\.\d+\.?\s+[A-Z]', clean_text):
        score += 2
    elif re.match(r'^[A-Z]\.\s+[A-Z]', clean_text):
        score += 1
    indicators = ['chapter', 'section', 'introduction', 'conclusion', 'abstract', 'summary', 'overview', 'methodology', 'results', 'discussion']
    if any(ind in clean_text.lower() for ind in indicators):
        score += 1
    return score >= 3

def analyze_document_structure(doc):
    font_stats = defaultdict(lambda: {'count': 0, 'positions': [], 'texts': []})
    page_heights = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_heights.append(page.rect.height)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if 'lines' not in block:
                continue
            for line in block['lines']:
                for span in line['spans']:
                    size = round(span['size'], 1)
                    flags = span['flags']
                    text = span['text'].strip()
                    y_pos = span['bbox'][1] if 'bbox' in span else 0
                    if text and len(text) > 10:
                        font_stats[size]['count'] += len(text)
                        font_stats[size]['positions'].append(y_pos)
                        font_stats[size]['texts'].append(text)
    main_size = max(font_stats.keys(), key=lambda x: font_stats[x]['count']) if font_stats else 12.0
    avg_height = sum(page_heights) / len(page_heights) if page_heights else 792
    return main_size, avg_height, font_stats

def get_h(p, i_path, o_path):
    try:
        doc = fitz.open(i_path)
        j_data = {
            "title": doc.metadata.get('title', '').strip() or os.path.splitext(p)[0],
            "outline": []
        }
        toc = doc.get_toc(simple=False)
        if toc:
            valid = 0
            for lvl, txt, pg, dest in toc:
                if txt.strip() and dest and dest.get('kind') == fitz.LINK_GOTO:
                    clean_txt = txt.strip()
                    if len(clean_txt) > 1 and not re.match(r'^\d+\s*$', clean_txt):
                        j_data['outline'].append({
                            'level': f'H{min(lvl, 6)}',
                            'text': clean_txt,
                            'page': max(0, pg - 1)
                        })
                        valid += 1
            if valid >= 3:
                j_data['outline'].sort(key=lambda x: (x['page'], int(x['level'][1:])))
                with open(o_path, 'w', encoding='utf-8') as f:
                    json.dump(j_data, f, indent=4, ensure_ascii=False)
                return
        main_text_size, avg_height, font_stats = analyze_document_structure(doc)
        potential = []
        processed = set()
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if 'lines' not in block:
                    continue
                for line in block['lines']:
                    for span in line['spans']:
                        text = span['text'].strip()
                        size = round(span['size'], 1)
                        flags = span['flags']
                        y_pos = span['bbox'][1] if 'bbox' in span else 0
                        if not text or len(text) < 2:
                            continue
                        clean_text = ' '.join(text.split())
                        key = (clean_text.lower(), page_num)
                        if key in processed:
                            continue
                        if is_likely_heading(clean_text, size, main_text_size, flags, y_pos, avg_height):
                            processed.add(key)
                            level = 1
                            ratio = size / main_text_size if main_text_size > 0 else 1
                            if ratio >= 1.8:
                                level = 1
                            elif ratio >= 1.5:
                                level = 2
                            elif ratio >= 1.3:
                                level = 3
                            elif ratio >= 1.15 or (flags & 16):
                                level = 4
                            else:
                                level = 5
                            if re.match(r'^\d+\.\d+\.\d+', clean_text):
                                level = min(level + 2, 6)
                            elif re.match(r'^\d+\.\d+', clean_text):
                                level = min(level + 1, 6)
                            potential.append({
                                'level': f'H{level}',
                                'text': clean_text,
                                'page': page_num,
                                'size': size,
                                'flags': flags
                            })
        potential.sort(key=lambda x: (x['page'], -x['size'], x['text']))
        seen = set()
        final = []
        for h in potential:
            txt = h['text'].lower()
            if txt not in seen:
                seen.add(txt)
                try:
                    detect(h['text'])
                    final.append({
                        'level': h['level'],
                        'text': h['text'],
                        'page': h['page']
                    })
                except LangDetectException:
                    if len(h['text']) <= 100 and not re.match(r'^[^a-zA-Z]*$', h['text']):
                        final.append({
                            'level': h['level'],
                            'text': h['text'],
                            'page': h['page']
                        })
        j_data['outline'] = final if final else [{
            "level": "H1",
            "text": "No headings found.",
            "page": 0
        }]
        with open(o_path, 'w', encoding='utf-8') as f:
            json.dump(j_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        with open(o_path, 'w', encoding='utf-8') as f:
            json.dump({
                "title": os.path.splitext(p)[0],
                "outline": [{
                    "level": "H1",
                    "text": f"Processing error: {str(e)}",
                    "page": 0
                }]
            }, f, indent=4)

def run():
    i_dir = '/app/input'
    o_dir = '/app/output'
    if not os.path.exists(o_dir):
        os.makedirs(o_dir)
    pdfs = [f for f in os.listdir(i_dir) if f.lower().endswith('.pdf')]
    for p in pdfs:
        i_path = os.path.join(i_dir, p)
        o_path = os.path.join(o_dir, os.path.splitext(p)[0] + '.json')
        get_h(p, i_path, o_path)

if __name__ == "__main__":
    run()
