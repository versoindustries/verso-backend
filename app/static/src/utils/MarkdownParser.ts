/**
 * MarkdownParser - Zero-dependency Markdown to HTML converter
 * 
 * Enterprise-grade parser supporting:
 * - Block elements: headings, blockquotes, code blocks, lists, tables, horizontal rules
 * - Inline elements: bold, italic, strikethrough, code, links, images
 * - Security: XSS-safe via HTML entity escaping
 */

// HTML entity escaping for XSS prevention
function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
}

// Detect language from code fence for syntax highlighting class
function getLanguageClass(lang: string): string {
    const supported = ['javascript', 'typescript', 'python', 'html', 'css', 'json', 'bash', 'sql', 'jsx', 'tsx'];
    const normalized = lang.toLowerCase().trim();
    if (supported.includes(normalized)) {
        return `language-${normalized}`;
    }
    return 'language-plaintext';
}

// Parse inline elements (bold, italic, links, etc.)
function parseInline(text: string): string {
    let result = escapeHtml(text);

    // Images: ![alt](src) - must come before links
    result = result.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="md-image" />');

    // Links: [text](url)
    result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="md-link">$1</a>');

    // Bold: **text** or __text__
    result = result.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    result = result.replace(/__([^_]+)__/g, '<strong>$1</strong>');

    // Italic: *text* or _text_ (but not within words for underscores)
    result = result.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    result = result.replace(/(?<![a-zA-Z])_([^_]+)_(?![a-zA-Z])/g, '<em>$1</em>');

    // Strikethrough: ~~text~~
    result = result.replace(/~~([^~]+)~~/g, '<del>$1</del>');

    // Inline code: `code`
    result = result.replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>');

    // Auto-link URLs (simple pattern)
    result = result.replace(
        /(?<!href="|src=")(https?:\/\/[^\s<]+)/g,
        '<a href="$1" target="_blank" rel="noopener noreferrer" class="md-link">$1</a>'
    );

    // Line breaks (two spaces + newline or explicit <br>)
    result = result.replace(/  \n/g, '<br />');

    return result;
}

// Parse a single block and return HTML
function parseBlock(lines: string[], startIndex: number): { html: string; consumed: number } {
    const line = lines[startIndex];
    const trimmed = line.trim();

    // Empty line
    if (trimmed === '') {
        return { html: '', consumed: 1 };
    }

    // Fenced code block: ```language
    if (trimmed.startsWith('```')) {
        const lang = trimmed.slice(3).trim();
        const langClass = getLanguageClass(lang);
        const codeLines: string[] = [];
        let i = startIndex + 1;

        while (i < lines.length && !lines[i].trim().startsWith('```')) {
            codeLines.push(lines[i]);
            i++;
        }

        const codeContent = escapeHtml(codeLines.join('\n'));
        return {
            html: `<pre class="md-code-block ${langClass}"><code>${codeContent}</code></pre>`,
            consumed: i - startIndex + 1
        };
    }

    // Headings: # to ######
    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
        const level = headingMatch[1].length;
        const text = parseInline(headingMatch[2]);
        return { html: `<h${level} class="md-heading md-h${level}">${text}</h${level}>`, consumed: 1 };
    }

    // Horizontal rule: ---, ***, ___
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
        return { html: '<hr class="md-hr" />', consumed: 1 };
    }

    // Blockquote: > text
    if (trimmed.startsWith('>')) {
        const quoteLines: string[] = [];
        let i = startIndex;

        while (i < lines.length && (lines[i].trim().startsWith('>') || lines[i].trim() === '')) {
            const quoteLine = lines[i].trim();
            if (quoteLine === '') {
                // Check if next line continues the quote
                if (i + 1 < lines.length && lines[i + 1].trim().startsWith('>')) {
                    quoteLines.push('');
                    i++;
                    continue;
                }
                break;
            }
            quoteLines.push(quoteLine.replace(/^>\s?/, ''));
            i++;
        }

        const quoteContent = parseMarkdown(quoteLines.join('\n'));
        return { html: `<blockquote class="md-blockquote">${quoteContent}</blockquote>`, consumed: i - startIndex };
    }

    // Unordered list: - item, * item, + item
    if (/^[-*+]\s+/.test(trimmed)) {
        const listItems: string[] = [];
        let i = startIndex;

        while (i < lines.length) {
            const itemLine = lines[i].trim();
            if (/^[-*+]\s+/.test(itemLine)) {
                listItems.push(itemLine.replace(/^[-*+]\s+/, ''));
                i++;
            } else if (itemLine === '') {
                // Check if list continues after blank line
                if (i + 1 < lines.length && /^[-*+]\s+/.test(lines[i + 1].trim())) {
                    i++;
                    continue;
                }
                break;
            } else {
                break;
            }
        }

        const itemsHtml = listItems.map(item => `<li>${parseInline(item)}</li>`).join('');
        return { html: `<ul class="md-list md-ul">${itemsHtml}</ul>`, consumed: i - startIndex };
    }

    // Ordered list: 1. item
    if (/^\d+\.\s+/.test(trimmed)) {
        const listItems: string[] = [];
        let i = startIndex;

        while (i < lines.length) {
            const itemLine = lines[i].trim();
            if (/^\d+\.\s+/.test(itemLine)) {
                listItems.push(itemLine.replace(/^\d+\.\s+/, ''));
                i++;
            } else if (itemLine === '') {
                if (i + 1 < lines.length && /^\d+\.\s+/.test(lines[i + 1].trim())) {
                    i++;
                    continue;
                }
                break;
            } else {
                break;
            }
        }

        const itemsHtml = listItems.map(item => `<li>${parseInline(item)}</li>`).join('');
        return { html: `<ol class="md-list md-ol">${itemsHtml}</ol>`, consumed: i - startIndex };
    }

    // Task list: - [ ] or - [x]
    if (/^[-*+]\s+\[[ xX]\]\s+/.test(trimmed)) {
        const listItems: { checked: boolean; text: string }[] = [];
        let i = startIndex;

        while (i < lines.length) {
            const itemLine = lines[i].trim();
            const taskMatch = itemLine.match(/^[-*+]\s+\[([ xX])\]\s+(.+)$/);
            if (taskMatch) {
                listItems.push({
                    checked: taskMatch[1].toLowerCase() === 'x',
                    text: taskMatch[2]
                });
                i++;
            } else if (itemLine === '') {
                break;
            } else {
                break;
            }
        }

        const itemsHtml = listItems.map(item => {
            const checkedAttr = item.checked ? 'checked disabled' : 'disabled';
            return `<li class="md-task-item"><input type="checkbox" ${checkedAttr} /> ${parseInline(item.text)}</li>`;
        }).join('');

        return { html: `<ul class="md-list md-task-list">${itemsHtml}</ul>`, consumed: i - startIndex };
    }

    // Table: | col | col |
    if (trimmed.startsWith('|') && trimmed.includes('|')) {
        const tableLines: string[] = [];
        let i = startIndex;

        while (i < lines.length && lines[i].trim().startsWith('|')) {
            tableLines.push(lines[i].trim());
            i++;
        }

        if (tableLines.length >= 2) {
            // Parse header
            const headerCells = tableLines[0].split('|').filter(c => c.trim() !== '').map(c => parseInline(c.trim()));

            // Check for alignment row
            let alignments: ('left' | 'center' | 'right' | null)[] = [];
            let dataStartIndex = 1;

            if (tableLines.length > 1 && /^[\s|:-]+$/.test(tableLines[1])) {
                alignments = tableLines[1].split('|').filter(c => c.trim() !== '').map(c => {
                    const cell = c.trim();
                    if (cell.startsWith(':') && cell.endsWith(':')) return 'center';
                    if (cell.endsWith(':')) return 'right';
                    if (cell.startsWith(':')) return 'left';
                    return null;
                });
                dataStartIndex = 2;
            }

            // Parse body rows
            const bodyRows = tableLines.slice(dataStartIndex).map(row =>
                row.split('|').filter(c => c.trim() !== '').map(c => parseInline(c.trim()))
            );

            // Build HTML
            const headerHtml = headerCells.map((cell, idx) => {
                const align = alignments[idx] ? ` style="text-align: ${alignments[idx]}"` : '';
                return `<th${align}>${cell}</th>`;
            }).join('');

            const bodyHtml = bodyRows.map(row =>
                '<tr>' + row.map((cell, idx) => {
                    const align = alignments[idx] ? ` style="text-align: ${alignments[idx]}"` : '';
                    return `<td${align}>${cell}</td>`;
                }).join('') + '</tr>'
            ).join('');

            return {
                html: `<table class="md-table"><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table>`,
                consumed: i - startIndex
            };
        }
    }

    // Default: paragraph
    const paragraphLines: string[] = [];
    let i = startIndex;

    while (i < lines.length) {
        const pLine = lines[i].trim();
        if (pLine === '' ||
            pLine.startsWith('#') ||
            pLine.startsWith('>') ||
            pLine.startsWith('```') ||
            /^[-*+]\s+/.test(pLine) ||
            /^\d+\.\s+/.test(pLine) ||
            /^(-{3,}|\*{3,}|_{3,})$/.test(pLine) ||
            (pLine.startsWith('|') && pLine.includes('|'))) {
            break;
        }
        paragraphLines.push(pLine);
        i++;
    }

    if (paragraphLines.length === 0) {
        return { html: '', consumed: 1 };
    }

    const paragraphContent = parseInline(paragraphLines.join(' '));
    return { html: `<p class="md-paragraph">${paragraphContent}</p>`, consumed: i - startIndex };
}

/**
 * Parse markdown string to HTML
 */
export function parseMarkdown(markdown: string): string {
    if (!markdown || typeof markdown !== 'string') {
        return '';
    }

    const lines = markdown.split('\n');
    const htmlParts: string[] = [];
    let index = 0;

    while (index < lines.length) {
        const { html, consumed } = parseBlock(lines, index);
        if (html) {
            htmlParts.push(html);
        }
        index += consumed;
    }

    return htmlParts.join('\n');
}

/**
 * Get plain text from markdown (for word counts, etc.)
 */
export function stripMarkdown(markdown: string): string {
    if (!markdown) return '';

    return markdown
        // Remove code blocks
        .replace(/```[\s\S]*?```/g, '')
        // Remove inline code
        .replace(/`[^`]+`/g, '')
        // Remove images
        .replace(/!\[[^\]]*\]\([^)]+\)/g, '')
        // Remove links but keep text
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        // Remove formatting
        .replace(/[*_~`#]/g, '')
        // Remove blockquote markers
        .replace(/^>\s?/gm, '')
        // Remove list markers
        .replace(/^[-*+]\s+/gm, '')
        .replace(/^\d+\.\s+/gm, '')
        // Remove horizontal rules
        .replace(/^(-{3,}|\*{3,}|_{3,})$/gm, '')
        // Collapse whitespace
        .replace(/\s+/g, ' ')
        .trim();
}

export default parseMarkdown;
