### Prompt for Generating Modern Layouts with React Islands Planning

**Objective**: Create a modern, responsive layout design for the provided written copy, identifying which sections should be **static Jinja2 content** (SEO-optimized) and which should be **React Islands** (interactive components). The output guides implementation in Verso's hybrid architecture.

---

## Architecture Context

Verso uses **React Islands Architecture**:
- Static content renders server-side via Jinja2 (SEO-friendly, fast initial load)
- Interactive elements mount as React "islands" within the Jinja2 template
- Each island is independent and can be lazy-loaded

### Decision Framework

| Section Type | Render Method | Reasoning |
|--------------|---------------|-----------|
| Hero banner with text | Jinja2 | SEO-critical, no interactivity |
| Navigation menu | React Island | Interactive dropdowns, mobile menu |
| Feature list | Jinja2 | Static content, SEO value |
| Image gallery | React Island | Carousel, lightbox interactivity |
| Pricing table | Jinja2 | Static, SEO-important |
| Calculator/configurator | React Island | Complex client-side logic |
| Testimonials (static) | Jinja2 | SEO value |
| Testimonials (carousel) | React Island | Animation/interaction |
| Contact form (simple) | Jinja2 | Server validation |
| Contact form (multi-step) | React Island | Client-side state |
| Data tables with sort/filter | React Island | Complex interactivity |
| Blog content | Jinja2 | SEO-critical |
| Charts/visualizations | React Island | Dynamic rendering |

---

## Instructions

### Input
User-provided written copy including:
- Headings and paragraphs
- Lists and structured content
- Calls to action
- Interactive requirements (if any)

### Output
A detailed layout specification with:

1. **Section breakdown** - Logical grouping of content
2. **Render method** - Jinja2 (static) or React Island (interactive)
3. **Component mapping** - Which React component to use (if applicable)
4. **Design specifications** - Visual structure and responsiveness
5. **SEO considerations** - Title, meta description, structured data needs

---

## Section Specification Format

For each section in the layout:

```markdown
### Section [N]: [Section Name]

**Purpose**: [Goal/function of this section]

**Render Method**: 
- [ ] Jinja2 (static, server-rendered)
- [ ] React Island (interactive, client-rendered)

**React Component** (if applicable): `ComponentName`

**Content Mapping**:
- Heading: "[relevant copy]"
- Body: "[relevant copy]"
- [other elements]

**Design**:
- Layout: [grid, flexbox, single-column]
- Background: [glass, solid, gradient]
- Spacing: [compact, standard, spacious]
- Visual elements: [icons, images, decorative]

**Responsive Behavior**:
- Mobile: [stacked, collapsed, hidden]
- Tablet: [2-column, partial]
- Desktop: [full layout]

**SEO Notes**:
- [Heading level, structured data, critical content flags]
```

---

## Available React Components

When planning React Islands, reference available components:

| Component | Use Case | Mount Pattern |
|-----------|----------|---------------|
| `Header` | Site navigation | Layout level |
| `Footer` | Site footer | Layout level |
| `ImageGallery` | Image carousels | `data-react-props='{"images": [...]}'` |
| `BookingWizard` | Multi-step forms | No props needed |
| `AdminDataTable` | Sortable/filterable tables | `{"columns": [...], "data": [...]}` |
| `KanbanBoard` | Drag-drop boards | `{"stages": [...], "items": [...]}` |
| `Chart` | Data visualization | `{"type": "line", "data": {...}}` |
| `Calendar` | Event calendars | `{"events": [...]}` |
| `ProductView` | Product details | `{"product": {...}}` |
| `CartPage` | Shopping cart | No props needed |

---

## Example Output

### Input Copy:
```
Welcome to Verso Industries
We build the future of business operations.

Our Services:
- Appointment Scheduling
- E-commerce Solutions  
- CRM & Lead Management

Trusted by 500+ businesses worldwide.

View our pricing plans
Contact us to get started
```

### Output Layout:

---

#### Section 1: Hero Banner

**Purpose**: Immediate value proposition and brand statement

**Render Method**: ✅ Jinja2 (static, server-rendered)

**Content Mapping**:
- H1: "Welcome to Verso Industries"
- Tagline: "We build the future of business operations"
- CTA: "Contact us to get started" → Link to contact page

**Design**:
- Layout: Centered, single-column
- Background: Gradient with glassmorphism overlay
- Spacing: Generous vertical padding (4rem mobile, 6rem desktop)
- Visual: Background pattern or subtle animation (CSS-only)

**Responsive Behavior**:
- Mobile: Full-width, stacked elements
- Desktop: Max-width container, larger typography

**SEO Notes**:
- H1 tag for main heading
- Include in meta description
- Consider Organization structured data

---

#### Section 2: Services Grid

**Purpose**: Showcase core offerings

**Render Method**: ✅ Jinja2 (static, server-rendered)

**Content Mapping**:
- Heading: "Our Services"
- Cards:
  - "Appointment Scheduling" + relevant icon
  - "E-commerce Solutions" + relevant icon
  - "CRM & Lead Management" + relevant icon

**Design**:
- Layout: CSS Grid, 3 columns on desktop
- Background: Glass cards
- Spacing: Gap between cards (1.5rem)
- Visual: FontAwesome icons for each service

**Responsive Behavior**:
- Mobile: Single column, stacked cards
- Tablet: 2 columns
- Desktop: 3 columns

**SEO Notes**:
- H2 for section heading
- Consider Service structured data for each

---

#### Section 3: Social Proof

**Purpose**: Build trust with usage statistics

**Render Method**: ✅ Jinja2 (static, server-rendered)

**Content Mapping**:
- Statement: "Trusted by 500+ businesses worldwide"

**Design**:
- Layout: Centered text with optional stat cards
- Background: Subtle differentiation from adjacent sections
- Visual: Counter animation (CSS-only) or static number

---

#### Section 4: Pricing CTA

**Purpose**: Convert visitors to comparison/contact

**Render Method**: ✅ Jinja2 (static, server-rendered)

**Content Mapping**:
- CTA Button: "View our pricing plans" → Link to pricing page

**Design**:
- Layout: Centered, prominent button
- Visual: Gradient button with hover effect

---

## Design Principles

1. **SEO First**: Keep critical content in Jinja2 unless interactivity is essential
2. **Progressive Enhancement**: Site should be usable without JavaScript
3. **Lazy Loading**: React Islands load only when needed
4. **Consistent Spacing**: Use CSS variable spacing scale
5. **Mobile First**: Design for mobile, enhance for larger screens
6. **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation

---

## Prompt Template

```
Generate a modern layout design for the following content. For each section, specify whether it should be rendered as static Jinja2 (SEO-optimized) or as a React Island (interactive). Include design specifications and responsive behavior.

Content:
[paste written copy here]

Interactivity requirements:
[describe any interactive features needed]

Target audience:
[describe primary users]

SEO priority:
[high/medium/low - affects Jinja2 vs React decisions]
```

||

{Replace with your written copy, interactivity requirements, and design preferences.}