# Accessibility Manual QA Checklist (WCAG 2.1 AA)

Use this checklist to manually verify accessibility compliance for new features and regressions.

## 1. Keyboard Navigation
- [ ] **Tab Order**: Navigate through the page using only the `Tab` key. Focus should move logically from top to bottom, left to right.
- [ ] **Focus Indicators**: Every interactive element (links, buttons, inputs) must have a clearly visible focus style (e.g., outline).
- [ ] **Skip Links**: The "Skip to main content" link should appear when tabbing into the page and correctly jump to the main content area.
- [ ] **No Traps**: Keyboard focus should never get "trapped" in an element (like a modal) without a way to exit (e.g., Esc key).

## 2. Forms & Interaction
- [ ] **Labels**: All form inputs must have a visible label or `aria-label`.
- [ ] **Error Messages**: Validation errors should be linked to their inputs via `aria-describedby` and be announced by screen readers.
- [ ] **Required Fields**: Required fields should be marked with `aria-required="true"`.
- [ ] **Button Text**: Buttons should have descriptive text (avoid "Click here").

## 3. Visuals & Semantics
- [ ] **Headings**: Heading levels (H1-H6) should be nested correctly without skipping levels.
- [ ] **Landmarks**: Page should use `<header>`, `<nav>`, `<main>`, `<footer>` landmarks.
- [ ] **Zoom**: content should be readable and functional at 200% zoom.
- [ ] **Color Contrast**: Text should have a contrast ratio of at least 4.5:1 against the background.
- [ ] **Alt Text**: Informative images must have `alt` text; decorative images should have empty `alt=""`.

## 4. Screen Reader (Simulation)
- [ ] **Announcements**: Dynamic content updates (like notifications) should be announced using `aria-live`.
- [ ] **Hidden Content**: Content visually hidden but relevant to screen readers (like icon labels) should use a `.sr-only` class.
