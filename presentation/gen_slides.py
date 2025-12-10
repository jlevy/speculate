#!/usr/bin/env -S uv run --quiet
# /// script
# dependencies = ["rich"]
# requires-python = ">=3.10"
# ///
"""
Generate a standalone static HTML slide presentation from a Markdown file.

Uses Remark.js (loaded from CDN) for rendering. The output is a single
self-contained HTML file that works locally via file:// URL or can be
hosted anywhere as a static page.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

from rich import print as rprint

APP_NAME = "gen_slides"
DESCRIPTION = "Generate HTML slides from Markdown using Remark.js"

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    :root {{
      --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
                   Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-size-base: 30px;
      --font-size-h1: 1.5em;
      --font-size-h2: 1.15em;
      --font-size-code: 0.9em;
      --font-size-slide-number: 14px;
      --line-height: 1.2;
      --spacing-slide: 1em 4em 1em 3em;
      --spacing-heading: 0.5em;
      --spacing-list-item: 0.5em;
      --color-code-bg: #f4f4f4;
      --border-radius: 3px;
    }}
    body {{
      font-family: var(--font-sans);
    }}
    .remark-slide-content {{
      font-size: var(--font-size-base);
      padding: var(--spacing-slide);
    }}
    .remark-slide-content h1 {{
      font-size: var(--font-size-h1);
      margin-bottom: var(--spacing-heading);
    }}
    .remark-slide-content h2 {{
      font-size: var(--font-size-h2);
      margin-bottom: var(--spacing-heading);
    }}
    .remark-slide-content ul {{
      line-height: var(--line-height);
      margin-top: 0.3em;
      margin-bottom: 0.3em;
    }}
    .remark-slide-content li {{
      margin-bottom: var(--spacing-list-item);
    }}
    .remark-slide-content li p {{
      margin: 0.1em 0;
    }}
    .remark-slide-content ol {{
      line-height: var(--line-height);
      margin-top: 0.3em;
      margin-bottom: 0.3em;
    }}
    .remark-slide-content p {{
      line-height: var(--line-height);
      margin-bottom: var(--spacing-list-item);
    }}
    .remark-slide-content code {{
      background: var(--color-code-bg);
      padding: 0.2em 0.4em;
      border-radius: var(--border-radius);
      font-size: var(--font-size-code);
    }}
    .remark-slide-content pre code {{
      display: block;
      padding: 1em;
    }}
    .remark-slide-number {{
      font-size: var(--font-size-slide-number);
      opacity: 0.5;
    }}
    /* Utility classes for slides */
    .remark-slide-content.small {{
      font-size: 22px;
    }}
    .remark-slide-content.smaller {{
      font-size: 18px;
    }}
    .remark-slide-content.two-column ul {{
      columns: 2;
      column-gap: 2em;
    }}
    .remark-slide-content.two-column li {{
      break-inside: avoid;
    }}
    /* Super-header for "Category: Title" format */
    .remark-slide-content h2 .super-header {{
      display: block;
      font-size: 0.5em;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #666;
      margin-bottom: 0.2em;
    }}
  </style>
</head>
<body>
  <textarea id="source" style="display: none;">
{markdown_content}
  </textarea>
  <script src="https://remarkjs.com/downloads/remark-latest.min.js"></script>
  <script>
    var slideshow = remark.create({{
      ratio: '16:9',
      highlightStyle: 'github',
      highlightLines: true,
      countIncrementalSlides: false,
      navigation: {{
        scroll: false,
        touch: true,
        click: false
      }}
    }});

    // Space advances, Backspace goes back (in addition to default arrow keys)
    document.addEventListener('keydown', function(e) {{
      if (e.code === 'Space' && !e.shiftKey) {{
        e.preventDefault();
        slideshow.gotoNextSlide();
      }} else if (e.code === 'Backspace') {{
        e.preventDefault();
        slideshow.gotoPreviousSlide();
      }}
    }});

    // Transform "Category: Title" h2 headings into super-header format
    document.querySelectorAll('.remark-slide-content h2').forEach(function(h2) {{
      var text = h2.textContent;
      var colonIndex = text.indexOf(':');
      if (colonIndex > 0 && colonIndex < 20) {{
        var prefix = text.substring(0, colonIndex);
        var rest = text.substring(colonIndex + 1).trim();
        h2.innerHTML = '<span class="super-header">' + prefix + '</span>' + rest;
      }}
    }});
  </script>
</body>
</html>
"""


def escape_html_textarea(content: str) -> str:
    """Escape content for embedding in HTML textarea."""
    # Only need to escape </textarea> if it appears in content
    return content.replace("</textarea>", "&lt;/textarea&gt;")


def convert_separators(content: str) -> str:
    """Convert '* * *' horizontal rules to Remark's '---' slide separators."""
    lines = content.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped == "* * *":
            result.append("---")
        else:
            result.append(line)
    return "\n".join(result)


def generate_slides(
    input_path: Path,
    output_path: Path | None = None,
    title: str | None = None,
) -> Path:
    """
    Generate HTML slides from a Markdown file.

    Args:
        input_path: Path to the input Markdown file
        output_path: Path for output HTML (default: same name with .html extension)
        title: Title for the HTML page (default: first heading or filename)

    Returns:
        Path to the generated HTML file
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    markdown_content = input_path.read_text(encoding="utf-8")

    # Convert * * * separators to --- for Remark
    markdown_content = convert_separators(markdown_content)

    # Determine title from first heading if not provided
    if title is None:
        for line in markdown_content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                break
        if title is None:
            title = input_path.stem

    # Determine output path
    if output_path is None:
        output_path = input_path.with_suffix(".html")

    # Escape content and generate HTML
    escaped_content = escape_html_textarea(markdown_content)
    html_content = HTML_TEMPLATE.format(
        title=title,
        markdown_content=escaped_content,
    )

    output_path.write_text(html_content, encoding="utf-8")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=dedent(__doc__ or ""),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="input Markdown file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output HTML file (default: same name with .html extension)",
    )
    parser.add_argument(
        "-t",
        "--title",
        default=None,
        help="HTML page title (default: first heading or filename)",
    )
    return parser


def print_success(message: str) -> None:
    """Print a success message with green checkmark."""
    rprint(f"[green]✔︎[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message with red label."""
    rprint(f"[red]Error:[/red] {message}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        output_path = generate_slides(
            input_path=args.input,
            output_path=args.output,
            title=args.title,
        )
        print_success(f"Generated: {output_path}")
        rprint(f"  Open in browser: file://{output_path.resolve()}")
    except KeyboardInterrupt:
        rprint()
        rprint("[yellow]Cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        rprint()
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
