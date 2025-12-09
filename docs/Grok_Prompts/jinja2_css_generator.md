### Prompt for Generating Modern CSS for Verso Components

**Objective**: Generate modern, responsive CSS for a specific component or section, optimized for the Verso Flask application's **React Islands + Jinja2 hybrid architecture**. The CSS should use CSS custom properties from `base.css`, follow mobile-first principles, and work for both Jinja2 templates and React components.

---

## Architecture Context

Verso uses:
- **CSS Custom Properties** defined in `app/static/css/base.css`
- **Component-level CSS files** in `app/static/css/components/`
- **No Tailwind CSS** - all styling is custom
- **Mobile-first responsive design**
- **Glassmorphism and modern aesthetic**

---

## CSS File Organization

```
app/static/css/
├── base.css                    # Global CSS variables and base styles
├── components/
│   ├── index.css               # Import aggregator for all components
│   ├── admin-dashboard.css     # Admin-specific styles
│   ├── booking-wizard.css      # Booking component styles
│   ├── image-gallery.css       # Gallery component styles
│   └── [your-component].css    # New component styles
├── layout-header.css           # Header layout styles
├── layout-footer.css           # Footer layout styles
└── homepage-layout.css         # Homepage-specific styles
```

---

## Available CSS Variables

Reference these from `base.css`:

```css
:root {
    /* Backgrounds */
    --primary-bg: linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%);
    --glass-bg: rgba(31, 31, 31, 0.8);
    --card-bg: rgba(42, 42, 42, 0.9);
    
    /* Colors */
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --accent-blue: #4169e1;
    --accent-blue-dark: #1348e7;
    --accent-green: #28a745;
    --accent-red: #dc3545;
    
    /* Dynamic theme (from BusinessConfig) */
    --primary-color: #4169e1;      /* Customizable via Theme Editor */
    --secondary-color: #6c757d;
    --accent-color: #28a745;
    
    /* Effects */
    --shadow-light: 0 4px 12px rgba(0, 0, 0, 0.5);
    --shadow-hover: 0 12px 32px rgba(0, 0, 0, 0.6);
    --pulse-effect: radial-gradient(circle, rgba(82, 80, 194, 0.2) 0%, transparent 70%);
    --btn-gradient: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    
    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    
    /* Border Radius */
    --theme-radius: 8px;
    --radius-sm: 4px;
    --radius-lg: 12px;
    --radius-round: 50%;
}
```

---

## Instructions

### Input
A written description of a component or section, detailing:
- Purpose and functionality
- Content structure
- Desired visual effects
- Responsive behavior needs

### Output
CSS code that:
1. **Uses custom properties** from `base.css` for colors, spacing, etc.
2. **Follows BEM-style naming** for clarity (e.g., `.card`, `.card__header`, `.card--highlighted`)
3. **Implements mobile-first** with `min-width` media queries
4. **Works for both contexts** (Jinja2 templates and React components)
5. **Includes hover states** and subtle animations
6. **Applies glassmorphism** where appropriate

---

## Component CSS Template

```css
/* =============================================================================
   Component: [Component Name]
   Description: [Brief description of the component]
   Usage: Both Jinja2 templates and React components
   ============================================================================= */

/* Base Component Styles (Mobile First) */
.component-name {
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: var(--theme-radius);
    padding: var(--spacing-md);
    box-shadow: var(--shadow-light);
    transition: all 0.3s ease;
}

/* Component Elements */
.component-name__header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
}

.component-name__title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}

.component-name__content {
    color: var(--text-secondary);
    line-height: 1.6;
}

/* Component Modifiers */
.component-name--highlighted {
    border-left: 3px solid var(--accent-blue);
}

.component-name--compact {
    padding: var(--spacing-sm);
}

/* Interactive States */
.component-name:hover {
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
}

.component-name:focus-within {
    outline: 2px solid var(--accent-blue);
    outline-offset: 2px;
}

/* Icons (FontAwesome) */
.component-name__icon {
    color: var(--accent-blue);
    font-size: 1.25rem;
    transition: transform 0.3s ease;
}

.component-name:hover .component-name__icon {
    transform: scale(1.1);
}

/* Buttons within Component */
.component-name__action {
    background: var(--btn-gradient);
    color: var(--text-primary);
    border: none;
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s ease;
}

.component-name__action:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
}

/* =============================================================================
   Responsive Breakpoints
   ============================================================================= */

/* Tablet (768px and up) */
@media (min-width: 768px) {
    .component-name {
        padding: var(--spacing-lg);
    }
    
    .component-name__title {
        font-size: 1.5rem;
    }
}

/* Desktop (1024px and up) */
@media (min-width: 1024px) {
    .component-name {
        padding: var(--spacing-xl);
    }
}

/* Small screens (480px and below) */
@media (max-width: 480px) {
    .component-name {
        padding: var(--spacing-sm);
        border-radius: var(--radius-sm);
    }
    
    .component-name__title {
        font-size: 1rem;
    }
}
```

---

## Integration Steps

After generating CSS:

1. **Save the file**:
   ```
   app/static/css/components/[component-name].css
   ```

2. **Import in component index**:
   ```css
   /* app/static/css/components/index.css */
   @import './[component-name].css';
   ```

3. **Use classes in templates**:
   
   **Jinja2:**
   ```html
   <div class="component-name component-name--highlighted">
       <div class="component-name__header">
           <i class="fas fa-star component-name__icon"></i>
           <h2 class="component-name__title">{{ title }}</h2>
       </div>
       <div class="component-name__content">
           {{ content }}
       </div>
   </div>
   ```
   
   **React:**
   ```tsx
   <div className="component-name component-name--highlighted">
       <div className="component-name__header">
           <i className="fas fa-star component-name__icon" />
           <h2 className="component-name__title">{title}</h2>
       </div>
       <div className="component-name__content">
           {content}
       </div>
   </div>
   ```

---

## Design Principles

1. **Glassmorphism**: Use `backdrop-filter: blur()` with semi-transparent backgrounds
2. **Dark theme**: Maintain the dark aesthetic from `base.css`
3. **Subtle animations**: Keep transitions under 0.3s, use `ease` or `ease-out`
4. **Consistent spacing**: Always use CSS variables for spacing
5. **Accessible focus states**: Visible focus indicators on interactive elements
6. **GPU-accelerated animations**: Use `transform` and `opacity` for smooth animations

---

## Prompt Template

```
Generate modern, responsive CSS for the following component in the Verso application. Use CSS custom properties from base.css, follow mobile-first principles, and ensure the styles work for both Jinja2 templates and React components.

Component: [name]
Purpose: [what it does]
Structure: [key elements - header, content, actions, etc.]
Visual style: [glassmorphism, cards, list, grid, etc.]
Interactive states: [hover effects, active states, etc.]
Responsive needs: [specific breakpoint requirements]
```

||

{Replace with your component description, structure, and visual requirements.}
