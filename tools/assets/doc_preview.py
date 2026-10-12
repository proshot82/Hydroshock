#!/usr/bin/env python3
"""Проба читалки: настоящий текст документа поверх носителя (ASSET_SPEC §7.1–§7.3, §8).

  python tools/assets/doc_preview.py ПОЛЯ.json ПАПКА_НОСИТЕЛЕЙ ВЫХОД_ПАПКА [--only DOC.a,DOC.b] [--sheet ЛИСТ.png]

ПОЛЯ.json — для каждого носителя поле под текст {"box": [x0, y0, x1, y1], "ink": [r, g, b]}
(в пикселях носителя 1400×980), по желанию "gap": [y0, y1] — полоса, которую текст обходит
(окно регламента: строка «[вырезано]» попадает в неё и не печатается), или "boxes" — по полю на
строку (таблички у кнопок поста, строки против пиктограмм); "center": true — строки по центру. Текст документа берётся из
итоговых текстов texts/act*/ACT*_TEXTS_FINAL.md (блок ```text), шрифт и носитель — по таблице §7.2.
Кегль подбирается наибольший, при котором текст с переносами по словам влезает в поле.
[оттиск] → assets/gfx/docs/stamp_kuh.png, [печать отеля] → stamp_hotel.png,
[отпечатокъ пальца] → mark_thumb.png. Это только проба для приёмки носителей: движок верстает сам,
но по тем же полям.
"""
import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / 'assets' / 'fonts'
DOCS = ROOT / 'assets' / 'gfx' / 'docs'
SANS, SANSB = 'PTSans-Regular.ttf', 'PTSans-Bold.ttf'
OLD, OLDB = 'OldStandard-Regular.ttf', 'OldStandard-Bold.ttf'
MONO, HAND = 'PTMono-Regular.ttf', 'Caveat.ttf'

# документ → (носитель, шрифт строк, шрифт первой строки или None — как остальные)
DOC = {
    'DOC.voucher': ('paper_union', SANS, SANSB), 'DOC.menu': ('paper_laminated', SANS, SANSB),
    'DOC.pictograms': ('panel_pictograms', SANS, None), 'DOC.bathday': ('paper_hotel', SANS, SANSB),
    'DOC.plate': ('plate_brass', OLD, OLDB), 'DOC.notice_counter': ('paper_kuh', OLD, OLDB),
    'DOC.notice_door': ('paper_kuh', OLD, OLDB), 'DOC.exhibit': ('plaque_museum', SANS, SANSB),
    'DOC.tag': ('tag_exhibit', SANS, SANSB), 'DOC.journal': ('page_ledger', HAND, OLDB),
    'DOC.paint_act': ('paper_office', SANS, SANSB), 'DOC.layoff': ('paper_hotel', SANS, SANSB),
    'DOC.plate_k': ('plate_enamel', SANSB, None), 'DOC.regulation': ('paper_regulation', SANS, SANSB),
    'DOC.memo': ('paper_soviet', MONO, None), 'DOC.instr1908': ('paper_1908', OLD, OLDB),
    'DOC.photo': ('photo_thursday', HAND, None), 'DOC.postcard': ('card_postcard', HAND, SANSB),
    'DOC.token': ('token_big', OLD, None), 'DOC.stencil': ('panel_steel', SANSB, None),
    'DOC.sticker': ('label_sticker', SANS, None), 'DOC.chalk': ('box_switch', HAND, None),
    'DOC.post': ('panel_post', OLDB, None), 'DOC.paint_can': ('label_can', SANS, SANSB),
    'DOC.water_stand': ('card_tent', SANS, SANSB), 'DOC.note': ('paper_note', HAND, None),
    'DOC.bill': ('paper_kuh', OLD, OLDB), 'DOC.tray_stamp': ('tray_porcelain', OLD, None),
    'DOC.complaint': ('paper_office', SANS, SANSB), 'DOC.invoice': ('paper_office', SANS, SANSB),
    'DOC.partial_mark': ('paper_kuh', OLD, None), 'DOC.reception_sign': ('plate_enamel', OLD, OLDB),
    'DOC.note_fixed': ('paper_note', HAND, None), 'DOC.plate_mark': ('plate_brass', OLD, None),
    'DOC.ledger': ('page_ledger', HAND, OLDB), 'DOC.seal_tag': ('tag_seal', OLD, None),
    'DOC.photo_family': ('photo_family', HAND, None), 'DOC.menu_new': ('paper_laminated', SANS, SANSB),
}
MARKS = {'[оттиск]': 'stamp_kuh.png', '[печать отеля]': 'stamp_hotel.png',
         '[отпечатокъ пальца]': 'mark_thumb.png'}


def texts():
    out = {}
    for f in sorted(ROOT.glob('texts/act*/ACT*_TEXTS_FINAL.md')):
        for part in re.split(r'^### ', f.read_text(encoding='utf-8'), flags=re.M):
            name = part.split('\n', 1)[0].strip()
            m = re.search(r'```text\n(.*?)```', part, re.S)
            if name.startswith('DOC.') and m:
                out[name] = m.group(1).rstrip('\n').split('\n')
    return out


def wrap(line, font, width):
    words, rows, cur = line.split(' '), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if font.getlength(t) <= width or not cur:
            cur = t
        else:
            rows.append(cur)
            cur = w
    rows.append(cur)
    return rows


def layout(lines, body, head, width, height, size):
    fb = ImageFont.truetype(str(FONTS / body), size)
    fh = ImageFont.truetype(str(FONTS / (head or body)), round(size * (1.08 if head else 1)))
    rows = []
    for i, ln in enumerate(lines):
        f = fh if (i == 0 and head) else fb
        if ln.strip() in MARKS:
            rows.append(('mark', ln.strip(), f, size * 2.2))
            continue
        if not ln.strip():
            rows.append(('gap', '', f, size * 0.5))
            continue
        for r in wrap(ln, f, width):
            rows.append(('text', r, f, size * 1.28))
    total = sum(r[3] for r in rows)
    return rows, total


def render(carrier_png, field, lines, body, head):
    im = Image.open(carrier_png).convert('RGB')
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = field.get('box', (0, 0, 0, 0))
    ink = tuple(field.get('ink', (40, 34, 28)))
    gap = field.get('gap')
    if field.get('boxes'):
        # по строке в каждое поле (таблички поста, строки пиктограмм): общий кегль
        parts = [(tuple(b), [ln]) for b, ln in zip(field['boxes'], lines)]
    elif gap:
        top_lines = []
        bottom_lines = []
        cut = next((i for i, ln in enumerate(lines) if ln.strip() == '[вырезано]'), None)
        top_lines, bottom_lines = (lines[:cut], lines[cut + 1:]) if cut is not None else (lines, [])
        parts = [((x0, y0, x1, gap[0]), top_lines), ((x0, gap[1], x1, y1), bottom_lines)]
    else:
        parts = [((x0, y0, x1, y1), lines)]
    # один кегль на весь документ: наибольший, при котором влезают все части
    size = int(field.get('max', 84))
    while size > 10:
        if all(layout(ls, body, head, b[2] - b[0], b[3] - b[1], size)[1] <= b[3] - b[1] for b, ls in parts if ls):
            break
        size -= 2
    for (bx0, by0, bx1, by1), ls in parts:
        if not ls:
            continue
        rows, total = layout(ls, body, head, bx1 - bx0, by1 - by0, size)
        y = by0 + (by1 - by0 - total) / 2 if field.get('center_v', True) else by0
        for kind, t, f, h in rows:
            if kind == 'text':
                w = f.getlength(t)
                x = bx0 + ((bx1 - bx0 - w) / 2 if field.get('center', False) else 0)
                d.text((x, y), t, font=f, fill=ink)
            elif kind == 'mark':
                m = Image.open(DOCS / MARKS[t]).convert('RGBA')
                s = h / m.height
                m = m.resize((max(1, round(m.width * s)), round(h)))
                im.paste(m, (round(bx1 - m.width - 10), round(y)), m)
            y += h
    return im, size


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('fields')
    ap.add_argument('carriers')
    ap.add_argument('out')
    ap.add_argument('--only', default='')
    ap.add_argument('--sheet', default='')
    a = ap.parse_args(argv)
    fields = json.loads(Path(a.fields).read_text(encoding='utf-8'))
    T = texts()
    only = set(filter(None, a.only.split(',')))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for doc, (carrier, body, head) in DOC.items():
        if only and doc not in only:
            continue
        src = Path(a.carriers) / f'{carrier}.png'
        if carrier not in fields or not src.exists() or doc not in T:
            print(f'{doc}: пропуск (нет поля, носителя или текста)')
            continue
        im, size = render(src, fields[carrier], T[doc], body, head)
        p = out / f'{doc[4:]}.png'
        im.save(p)
        made.append((doc, p, size))
        print(f'{doc}: {carrier}, кегль {size}')
    if a.sheet and made:
        tw, th, cols = 700, 490, 3
        sheet = Image.new('RGB', (tw * cols, (th + 26) * ((len(made) + cols - 1) // cols)), 'white')
        ds = ImageDraw.Draw(sheet)
        lab = ImageFont.truetype(str(FONTS / SANSB), 18)
        for i, (doc, p, size) in enumerate(made):
            x, y = (i % cols) * tw, (i // cols) * (th + 26)
            sheet.paste(Image.open(p).resize((tw, th), Image.LANCZOS), (x, y + 26))
            ds.text((x + 6, y + 3), f'{doc} — {DOC[doc][0]}, кегль {size}', font=lab, fill='black')
        sheet.save(a.sheet)


if __name__ == '__main__':
    main()
