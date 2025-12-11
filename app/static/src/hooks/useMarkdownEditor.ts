/**
 * useMarkdownEditor - React hook for markdown editor functionality
 * 
 * Provides:
 * - Text selection tracking
 * - Markdown insertion helpers
 * - Undo/redo stack (50 levels)
 * - Keyboard shortcuts (Ctrl+B, Ctrl+I, Ctrl+K, etc.)
 * - Auto-indent for lists
 */

import { useCallback, useRef, useState, useEffect } from 'react';

export interface EditorState {
    content: string;
    selectionStart: number;
    selectionEnd: number;
}

interface HistoryEntry {
    content: string;
    cursorPosition: number;
}

interface UseMarkdownEditorOptions {
    initialContent?: string;
    maxHistorySize?: number;
    onChange?: (content: string) => void;
}

interface MarkdownAction {
    type: 'wrap' | 'prefix' | 'insert' | 'block';
    before: string;
    after?: string;
    placeholder?: string;
}

// Markdown action definitions
const MARKDOWN_ACTIONS: Record<string, MarkdownAction> = {
    bold: { type: 'wrap', before: '**', after: '**', placeholder: 'bold text' },
    italic: { type: 'wrap', before: '*', after: '*', placeholder: 'italic text' },
    strikethrough: { type: 'wrap', before: '~~', after: '~~', placeholder: 'strikethrough text' },
    code: { type: 'wrap', before: '`', after: '`', placeholder: 'code' },
    link: { type: 'wrap', before: '[', after: '](url)', placeholder: 'link text' },
    image: { type: 'insert', before: '![alt text](', after: ')', placeholder: 'image url' },
    h1: { type: 'prefix', before: '# ', placeholder: 'Heading 1' },
    h2: { type: 'prefix', before: '## ', placeholder: 'Heading 2' },
    h3: { type: 'prefix', before: '### ', placeholder: 'Heading 3' },
    quote: { type: 'prefix', before: '> ', placeholder: 'quote' },
    ul: { type: 'prefix', before: '- ', placeholder: 'list item' },
    ol: { type: 'prefix', before: '1. ', placeholder: 'list item' },
    task: { type: 'prefix', before: '- [ ] ', placeholder: 'task' },
    hr: { type: 'block', before: '\n---\n' },
    codeBlock: { type: 'block', before: '\n```\n', after: '\n```\n', placeholder: 'code here' },
};

export function useMarkdownEditor(options: UseMarkdownEditorOptions = {}) {
    const {
        initialContent = '',
        maxHistorySize = 50,
        onChange
    } = options;

    const [content, setContent] = useState(initialContent);
    const [selectionStart, setSelectionStart] = useState(0);
    const [selectionEnd, setSelectionEnd] = useState(0);

    const textareaRef = useRef<HTMLTextAreaElement | null>(null);
    const historyRef = useRef<HistoryEntry[]>([{ content: initialContent, cursorPosition: 0 }]);
    const historyIndexRef = useRef(0);
    const isUndoRedoRef = useRef(false);

    // Track selection changes
    const updateSelection = useCallback(() => {
        if (textareaRef.current) {
            setSelectionStart(textareaRef.current.selectionStart);
            setSelectionEnd(textareaRef.current.selectionEnd);
        }
    }, []);

    // Save to history
    const saveToHistory = useCallback((newContent: string, cursorPosition: number) => {
        if (isUndoRedoRef.current) {
            isUndoRedoRef.current = false;
            return;
        }

        const history = historyRef.current;
        const currentIndex = historyIndexRef.current;

        // Remove any redo history
        history.splice(currentIndex + 1);

        // Add new entry
        history.push({ content: newContent, cursorPosition });

        // Limit history size
        if (history.length > maxHistorySize) {
            history.shift();
        }

        historyIndexRef.current = history.length - 1;
    }, [maxHistorySize]);

    // Update content with history tracking
    const updateContent = useCallback((newContent: string, newCursorPosition?: number) => {
        setContent(newContent);
        onChange?.(newContent);

        const pos = newCursorPosition ?? newContent.length;
        saveToHistory(newContent, pos);

        // Set cursor position after React renders
        requestAnimationFrame(() => {
            if (textareaRef.current) {
                textareaRef.current.selectionStart = pos;
                textareaRef.current.selectionEnd = pos;
                textareaRef.current.focus();
            }
        });
    }, [onChange, saveToHistory]);

    // Undo
    const undo = useCallback(() => {
        const history = historyRef.current;
        const currentIndex = historyIndexRef.current;

        if (currentIndex > 0) {
            isUndoRedoRef.current = true;
            historyIndexRef.current = currentIndex - 1;
            const entry = history[historyIndexRef.current];
            setContent(entry.content);
            onChange?.(entry.content);

            requestAnimationFrame(() => {
                if (textareaRef.current) {
                    textareaRef.current.selectionStart = entry.cursorPosition;
                    textareaRef.current.selectionEnd = entry.cursorPosition;
                    textareaRef.current.focus();
                }
            });
        }
    }, [onChange]);

    // Redo
    const redo = useCallback(() => {
        const history = historyRef.current;
        const currentIndex = historyIndexRef.current;

        if (currentIndex < history.length - 1) {
            isUndoRedoRef.current = true;
            historyIndexRef.current = currentIndex + 1;
            const entry = history[historyIndexRef.current];
            setContent(entry.content);
            onChange?.(entry.content);

            requestAnimationFrame(() => {
                if (textareaRef.current) {
                    textareaRef.current.selectionStart = entry.cursorPosition;
                    textareaRef.current.selectionEnd = entry.cursorPosition;
                    textareaRef.current.focus();
                }
            });
        }
    }, [onChange]);

    // Apply markdown action
    const applyAction = useCallback((actionName: keyof typeof MARKDOWN_ACTIONS) => {
        const action = MARKDOWN_ACTIONS[actionName];
        if (!action || !textareaRef.current) return;

        const textarea = textareaRef.current;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = content.substring(start, end);
        const beforeText = content.substring(0, start);
        const afterText = content.substring(end);

        let newContent: string;
        let newCursorPos: number;

        switch (action.type) {
            case 'wrap': {
                const textToWrap = selectedText || action.placeholder || '';
                newContent = beforeText + action.before + textToWrap + (action.after || '') + afterText;

                if (selectedText) {
                    // Keep selection around wrapped text
                    newCursorPos = start + action.before.length + textToWrap.length + (action.after?.length || 0);
                } else {
                    // Place cursor at placeholder
                    newCursorPos = start + action.before.length + textToWrap.length;
                }
                break;
            }

            case 'prefix': {
                // Find start of current line
                const lineStart = beforeText.lastIndexOf('\n') + 1;
                const beforeLine = content.substring(0, lineStart);
                const currentLine = content.substring(lineStart, end);

                const textToPrefix = selectedText || currentLine || action.placeholder || '';
                const cleanLine = textToPrefix.replace(/^(#{1,6}\s|>\s|-\s|\d+\.\s|- \[[ x]\]\s)/, '');

                newContent = beforeLine + action.before + cleanLine + afterText;
                newCursorPos = lineStart + action.before.length + cleanLine.length;
                break;
            }

            case 'insert': {
                const textToInsert = selectedText || action.placeholder || '';
                newContent = beforeText + action.before + textToInsert + (action.after || '') + afterText;
                newCursorPos = start + action.before.length + textToInsert.length;
                break;
            }

            case 'block': {
                const textToInsert = selectedText || action.placeholder || '';
                newContent = beforeText + action.before + textToInsert + (action.after || '') + afterText;
                newCursorPos = start + action.before.length + textToInsert.length;
                break;
            }

            default:
                return;
        }

        updateContent(newContent, newCursorPos);
    }, [content, updateContent]);

    // Insert link with URL
    const insertLink = useCallback((text: string, url: string) => {
        if (!textareaRef.current) return;

        const textarea = textareaRef.current;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const beforeText = content.substring(0, start);
        const afterText = content.substring(end);

        const linkMarkdown = `[${text}](${url})`;
        const newContent = beforeText + linkMarkdown + afterText;
        const newCursorPos = start + linkMarkdown.length;

        updateContent(newContent, newCursorPos);
    }, [content, updateContent]);

    // Insert image with URL
    const insertImage = useCallback((alt: string, url: string) => {
        if (!textareaRef.current) return;

        const textarea = textareaRef.current;
        const start = textarea.selectionStart;
        const beforeText = content.substring(0, start);
        const afterText = content.substring(textarea.selectionEnd);

        const imageMarkdown = `![${alt}](${url})`;
        const newContent = beforeText + imageMarkdown + afterText;
        const newCursorPos = start + imageMarkdown.length;

        updateContent(newContent, newCursorPos);
    }, [content, updateContent]);

    // Cycle through heading levels
    const cycleHeading = useCallback(() => {
        if (!textareaRef.current) return;

        const textarea = textareaRef.current;
        const start = textarea.selectionStart;
        const lineStart = content.lastIndexOf('\n', start - 1) + 1;
        const lineEnd = content.indexOf('\n', start);
        const currentLine = content.substring(lineStart, lineEnd === -1 ? undefined : lineEnd);

        const headingMatch = currentLine.match(/^(#{1,6})\s/);
        let newPrefix = '# ';

        if (headingMatch) {
            const level = headingMatch[1].length;
            if (level >= 6) {
                // Remove heading
                newPrefix = '';
            } else {
                newPrefix = '#'.repeat(level + 1) + ' ';
            }
        }

        const cleanLine = currentLine.replace(/^#{1,6}\s/, '');
        const beforeLine = content.substring(0, lineStart);
        const afterLine = lineEnd === -1 ? '' : content.substring(lineEnd);

        const newContent = beforeLine + newPrefix + cleanLine + afterLine;
        const newCursorPos = lineStart + newPrefix.length + cleanLine.length;

        updateContent(newContent, newCursorPos);
    }, [content, updateContent]);

    // Handle keyboard shortcuts
    const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        const isCtrl = e.ctrlKey || e.metaKey;

        // Tab handling for code blocks
        if (e.key === 'Tab') {
            e.preventDefault();
            const textarea = e.currentTarget;
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;

            if (e.shiftKey) {
                // Outdent: remove leading spaces/tabs
                const lineStart = content.lastIndexOf('\n', start - 1) + 1;
                const currentLine = content.substring(lineStart);
                if (currentLine.startsWith('    ') || currentLine.startsWith('\t')) {
                    const removeCount = currentLine.startsWith('\t') ? 1 : 4;
                    const newContent = content.substring(0, lineStart) + content.substring(lineStart + removeCount);
                    updateContent(newContent, Math.max(start - removeCount, lineStart));
                }
            } else {
                // Indent: insert spaces
                const spaces = '    ';
                const newContent = content.substring(0, start) + spaces + content.substring(end);
                updateContent(newContent, start + spaces.length);
            }
            return;
        }

        // Auto-continue lists on Enter
        if (e.key === 'Enter') {
            const textarea = e.currentTarget;
            const start = textarea.selectionStart;
            const lineStart = content.lastIndexOf('\n', start - 1) + 1;
            const currentLine = content.substring(lineStart, start);

            // Unordered list continuation
            const ulMatch = currentLine.match(/^(\s*)([-*+])\s(.*)$/);
            if (ulMatch) {
                const [, indent, marker, text] = ulMatch;
                if (text.trim() === '') {
                    // Empty list item - remove it
                    e.preventDefault();
                    const newContent = content.substring(0, lineStart) + '\n' + content.substring(start);
                    updateContent(newContent, lineStart + 1);
                    return;
                }
                e.preventDefault();
                const continuation = `\n${indent}${marker} `;
                const newContent = content.substring(0, start) + continuation + content.substring(start);
                updateContent(newContent, start + continuation.length);
                return;
            }

            // Ordered list continuation
            const olMatch = currentLine.match(/^(\s*)(\d+)\.\s(.*)$/);
            if (olMatch) {
                const [, indent, num, text] = olMatch;
                if (text.trim() === '') {
                    e.preventDefault();
                    const newContent = content.substring(0, lineStart) + '\n' + content.substring(start);
                    updateContent(newContent, lineStart + 1);
                    return;
                }
                e.preventDefault();
                const nextNum = parseInt(num, 10) + 1;
                const continuation = `\n${indent}${nextNum}. `;
                const newContent = content.substring(0, start) + continuation + content.substring(start);
                updateContent(newContent, start + continuation.length);
                return;
            }

            // Task list continuation
            const taskMatch = currentLine.match(/^(\s*)(-)\s\[[ x]\]\s(.*)$/);
            if (taskMatch) {
                const [, indent, , text] = taskMatch;
                if (text.trim() === '') {
                    e.preventDefault();
                    const newContent = content.substring(0, lineStart) + '\n' + content.substring(start);
                    updateContent(newContent, lineStart + 1);
                    return;
                }
                e.preventDefault();
                const continuation = `\n${indent}- [ ] `;
                const newContent = content.substring(0, start) + continuation + content.substring(start);
                updateContent(newContent, start + continuation.length);
                return;
            }

            // Blockquote continuation
            const quoteMatch = currentLine.match(/^(>\s*)(.*)$/);
            if (quoteMatch) {
                const [, prefix, text] = quoteMatch;
                if (text.trim() === '') {
                    e.preventDefault();
                    const newContent = content.substring(0, lineStart) + '\n' + content.substring(start);
                    updateContent(newContent, lineStart + 1);
                    return;
                }
                e.preventDefault();
                const continuation = `\n${prefix}`;
                const newContent = content.substring(0, start) + continuation + content.substring(start);
                updateContent(newContent, start + continuation.length);
                return;
            }
        }

        // Keyboard shortcuts
        if (isCtrl) {
            switch (e.key.toLowerCase()) {
                case 'b':
                    e.preventDefault();
                    applyAction('bold');
                    break;
                case 'i':
                    e.preventDefault();
                    applyAction('italic');
                    break;
                case 'k':
                    e.preventDefault();
                    if (e.shiftKey) {
                        applyAction('code');
                    } else {
                        applyAction('link');
                    }
                    break;
                case 'h':
                    e.preventDefault();
                    cycleHeading();
                    break;
                case 'z':
                    e.preventDefault();
                    if (e.shiftKey) {
                        redo();
                    } else {
                        undo();
                    }
                    break;
                case 'y':
                    e.preventDefault();
                    redo();
                    break;
            }
        }
    }, [content, updateContent, applyAction, cycleHeading, undo, redo]);

    // Set textarea ref and add event listeners
    const setTextareaRef = useCallback((element: HTMLTextAreaElement | null) => {
        textareaRef.current = element;
        if (element) {
            // Track selection changes
            element.addEventListener('select', updateSelection);
            element.addEventListener('click', updateSelection);
            element.addEventListener('keyup', updateSelection);
        }
    }, [updateSelection]);

    // Cleanup
    useEffect(() => {
        return () => {
            const textarea = textareaRef.current;
            if (textarea) {
                textarea.removeEventListener('select', updateSelection);
                textarea.removeEventListener('click', updateSelection);
                textarea.removeEventListener('keyup', updateSelection);
            }
        };
    }, [updateSelection]);

    // Handle content changes from external source
    const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newContent = e.target.value;
        setContent(newContent);
        onChange?.(newContent);
        saveToHistory(newContent, e.target.selectionStart);
    }, [onChange, saveToHistory]);

    return {
        // State
        content,
        selectionStart,
        selectionEnd,

        // Refs
        setTextareaRef,

        // Handlers
        handleChange,
        handleKeyDown,

        // Actions
        applyAction,
        insertLink,
        insertImage,
        cycleHeading,
        undo,
        redo,

        // Direct content control
        setContent: updateContent,

        // History info
        canUndo: historyIndexRef.current > 0,
        canRedo: historyIndexRef.current < historyRef.current.length - 1,
    };
}

export default useMarkdownEditor;
