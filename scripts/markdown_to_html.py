#!/usr/bin/env python3
"""
Markdown → HTML converter
Transforms a Markdown file following the ECRI-template.md format
into HTML blocks following the template.html structure.

Usage:
    python markdown_to_html.py input.md [output.html]
    If output path is omitted, prints to stdout.
"""

import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Inline Markdown → HTML
# ---------------------------------------------------------------------------

def inline_md_to_html(text: str) -> str:
    """Convert inline Markdown (bold, italic, links) to HTML."""
    # Bold+italic: ***text*** or ___text___
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'___(.+?)___',        r'<strong><em>\1</em></strong>', text)
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__',     r'<strong>\1</strong>', text)
    # Italic: *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_',   r'<em>\1</em>', text)
    # Links: [label](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
    return text


# ---------------------------------------------------------------------------
# YouTube helpers
# ---------------------------------------------------------------------------

YOUTUBE_RE = re.compile(
    r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})'
)

def youtube_embed(video_id: str) -> str:
    """Return a responsive YouTube iframe block."""
    return (
        '<div class="video-wrapper" style="position:relative;padding-bottom:56.25%;'
        'height:0;overflow:hidden;">'
        f'<iframe src="https://www.youtube.com/embed/{video_id}" '
        'style="position:absolute;top:0;left:0;width:100%;height:100%;" '
        'frameborder="0" allowfullscreen loading="lazy"></iframe>'
        '</div>'
    )

def try_youtube_image_link(line: str):
    """
    Detect a Markdown image whose URL is a YouTube link:
        ![caption](https://www.youtube.com/watch?v=ID)
    Returns an embed string or None.
    """
    m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line.strip())
    if m:
        url = m.group(2)
        yt = YOUTUBE_RE.search(url)
        if yt:
            return youtube_embed(yt.group(1))
    return None

def try_bare_youtube(line: str):
    """Detect a bare YouTube URL on its own line."""
    stripped = line.strip()
    yt = YOUTUBE_RE.fullmatch(stripped)
    if not yt:
        yt = YOUTUBE_RE.match(stripped)
        if yt and yt.group(0) == stripped:
            pass
        else:
            yt = None
    if yt:
        return youtube_embed(yt.group(1))
    return None


# ---------------------------------------------------------------------------
# Image helper
# ---------------------------------------------------------------------------

def parse_img_tag(line: str):
    stripped = line.strip()
    if not stripped.lower().startswith('<img '):
        return None
    stripped = re.sub(
        r'src=["\']([^"\']+)["\']',
        lambda m: f'src="journal/media/{Path(m.group(1)).name}"',
        stripped
    )
    if 'max-width' not in stripped:
        stripped = stripped.rstrip('>').rstrip('/')
        stripped += ' style="max-width:100%;height:auto;">'
    return stripped

def parse_md_image(line: str):
    """
    Convert a Markdown image ![alt](src …) to a responsive <img> tag.
    Returns HTML string or None.
    """
    m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line.strip())
    if m:
        alt, src = m.group(1), m.group(2)
        # Extract existing style attribute if embedded in src (unlikely but safe)
        return f'<img src="journal/media/{Path(src).name}" alt="{alt}" style="max-width:100%;height:auto;">'
    return None


# ---------------------------------------------------------------------------
# Block rendering
# ---------------------------------------------------------------------------

def render_block(lines: list[str], css_class: str) -> str:
    """
    Convert a list of raw Markdown lines into a <div class="…"> block
    containing <p> elements.
    Handles:
      - blank-line paragraph separation
      - inline formatting
      - images (raw <img> and Markdown ![])
      - YouTube embeds (image-link syntax and bare URLs)
    """
    paragraphs = []   # list of rendered HTML strings
    current_lines = []

    def flush():
        if current_lines:
            inner = ' '.join(current_lines).strip()
            if inner:
                paragraphs.append(f'<p>{inline_md_to_html(inner)}</p>')
            current_lines.clear()

    for raw_line in lines:
        line = raw_line.rstrip('\n')

        # Blank line → paragraph break
        if not line.strip():
            flush()
            continue

        # Raw <img> tag
        img_tag = parse_img_tag(line)
        if img_tag:
            flush()
            paragraphs.append(img_tag)
            continue
        
        # Raw <iframe> tag
        if line.strip().lower().startswith('<iframe '):
            flush()
            paragraphs.append(line.strip())
            continue
        
        # YouTube via image-link syntax ![caption](youtube_url)
        yt_embed = try_youtube_image_link(line)
        if yt_embed:
            flush()
            paragraphs.append(yt_embed)
            continue

        # Bare YouTube URL
        yt_bare = try_bare_youtube(line)
        if yt_bare:
            flush()
            paragraphs.append(yt_bare)
            continue

        # Markdown image (non-YouTube)
        md_img = parse_md_image(line)
        if md_img:
            flush()
            paragraphs.append(md_img)
            continue

        # Regular text line → accumulate
        current_lines.append(line.strip())

    flush()

    if not paragraphs:
        return ''

    inner_html = '\n    '.join(paragraphs)
    return f'  <div class="{css_class}">\n    {inner_html}\n  </div>'


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

SECTION_RE = re.compile(r'^##\s+(Prompt|Response|Modèle pour les réponses)\s*:?\s*(.*)$', re.IGNORECASE)
DATE_RE    = re.compile(r'^\d{4}-\d{2}-\d{2}$')
TITLE_RE   = re.compile(r'^#\s+')  # H1 title

def parse_ecri(md_text: str):
    """
    Parse the ECRI markdown file.
    Returns:
        model_label : str | None   — content of "Modèle pour les réponses" or None
        sections    : list of (type, title, lines)
                      type  in {'Prompt', 'Response'}
                      title is a str (possibly empty) — only set for Prompt sections
    """
    lines = md_text.splitlines(keepends=True)
    model_label = None
    sections = []          # list of ('Prompt'|'Response', title, [lines])
    current_type = None
    current_title = ''
    current_lines = []
    skip_next_date = False

    def flush_section():
        if current_type and current_lines:
            # Strip leading/trailing blank lines
            stripped = current_lines.copy()
            while stripped and not stripped[0].strip():
                stripped.pop(0)
            while stripped and not stripped[-1].strip():
                stripped.pop()
            if stripped:
                sections.append((current_type, current_title, stripped))

    for line in lines:
        stripped = line.strip()

        # Skip H1 title
        if TITLE_RE.match(stripped):
            continue

        # Detect section headers
        m = SECTION_RE.match(stripped)
        if m:
            flush_section()
            current_type = None
            current_title = ''
            current_lines = []
            section_name = m.group(1)
            inline_title = m.group(2).strip()

            if section_name.lower() == 'modèle pour les réponses':
                current_type = '__model__'
                skip_next_date = True
            elif section_name.lower() == 'prompt':
                current_type = 'Prompt'
                current_title = inline_title  # may be empty string
                skip_next_date = True
            elif section_name.lower() == 'response':
                current_type = 'Response'
                skip_next_date = True
            continue

        # Skip date lines immediately after a section header
        if skip_next_date and DATE_RE.match(stripped):
            skip_next_date = False
            continue
        skip_next_date = False

        # Accumulate content
        if current_type == '__model__':
            if stripped:  # first non-blank content is the model label
                model_label = stripped
                current_type = None  # section consumed
        elif current_type in ('Prompt', 'Response'):
            current_lines.append(line)

    flush_section()
    return model_label, sections


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------

def convert(md_text: str) -> str:
    model_label, sections = parse_ecri(md_text)

    blocks = []

    for sec_type, sec_title, sec_lines in sections:
        css_class = 'author-voice' if sec_type == 'Prompt' else 'ai-voice'

        # Inter-title: only for Prompt sections with a non-empty title
        if sec_type == 'Prompt' and sec_title:
            blocks.append(f'  <h3 class="section-title">{sec_title}</h3>')

        # Prepend model label to the first block if present
        effective_lines = sec_lines
        if model_label:
            label_line = f'*{model_label}*\n'
            effective_lines = [label_line, '\n'] + list(sec_lines)
            model_label = None  # only prepend once (to very first block)

        rendered = render_block(effective_lines, css_class)
        if rendered:
            blocks.append(rendered)

    return '<main>\n' + '\n\n'.join(blocks) + '\n</main>'


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print('Usage: python ecri_md_to_html.py input.md [output.html]', file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f'Error: file not found: {input_path}', file=sys.stderr)
        sys.exit(1)

    md_text = input_path.read_text(encoding='utf-8')
    html = convert(md_text)

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
        output_path.write_text(html, encoding='utf-8')
        print(f'Written to {output_path}')
    else:
        print(html)


if __name__ == '__main__':
    main()
