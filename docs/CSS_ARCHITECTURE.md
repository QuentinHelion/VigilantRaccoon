# CSS Architecture

VigilantRaccoon uses a centralized CSS architecture for better maintainability, performance, and consistency across all web interfaces.

## Structure

```
static/
└── css/
    └── main.css          # Main stylesheet with all application styles
```

## Features

### CSS Variables (Custom Properties)
The application uses CSS custom properties for consistent theming:

```css
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
    --light-color: #f8f9fa;
    --dark-color: #343a40;
    --white: #ffffff;
    --gray-100: #f8f9fa;
    --gray-200: #e9ecef;
    --gray-300: #dee2e6;
    --gray-400: #ced4da;
    --gray-500: #adb5bd;
    --gray-600: #6c757d;
    --gray-700: #495057;
    --gray-800: #343a40;
    --gray-900: #212529;
    
    --border-radius: 0.375rem;
    --box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    --box-shadow-lg: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    --transition: all 0.15s ease-in-out;
}
```

### Component-Based Architecture
Styles are organized by component type:

- **Layout & Navigation**: Navbar, main content, containers
- **Cards & Components**: Cards, action cards, forms
- **Buttons**: All button variants and states
- **Forms**: Input fields, labels, validation
- **Tables**: Data tables with responsive design
- **Alerts & Notifications**: Status messages and alerts
- **Statistics & Metrics**: Dashboard statistics display
- **Filters & Search**: Search and filtering interfaces
- **Status Indicators**: Badges and status displays
- **Utilities**: Helper classes for spacing, alignment, etc.

### Responsive Design
The CSS includes comprehensive responsive breakpoints:

```css
@media (max-width: 768px) {
    /* Tablet and mobile styles */
}

@media (max-width: 576px) {
    /* Mobile-specific styles */
}
```

### Accessibility Features
- High contrast mode support
- Focus indicators for keyboard navigation
- Screen reader support
- Semantic HTML structure

## Usage

### In Templates
All templates now use the centralized CSS file:

```html
{% extends "layout.html" %}
<!-- CSS is automatically included via layout.html -->
```

### CSS Classes
Common utility classes available:

```html
<!-- Spacing -->
<div class="mt-3 mb-2 p-4">Content</div>

<!-- Text alignment -->
<p class="text-center text-muted">Centered text</p>

<!-- Display utilities -->
<div class="d-none d-md-block">Hidden on mobile</div>

<!-- Flexbox utilities -->
<div class="d-flex justify-content-between align-items-center">
    <span>Left content</span>
    <span>Right content</span>
</div>
```

### Component Classes
Standard component classes:

```html
<!-- Cards -->
<div class="card">
    <div class="card-header">
        <h3>Card Title</h3>
    </div>
    <div class="card-body">
        Card content
    </div>
</div>

<!-- Buttons -->
<button class="btn btn-primary">Primary Button</button>
<button class="btn btn-success btn-sm">Small Success Button</button>

<!-- Forms -->
<div class="form-group">
    <label for="input" class="form-label">Label</label>
    <input type="text" class="form-control" id="input">
</div>

<!-- Tables -->
<div class="table-responsive">
    <table class="table">
        <!-- Table content -->
    </table>
</div>
```

## Benefits

### Maintainability
- **Single source of truth**: All styles in one file
- **Consistent naming**: Standardized class naming conventions
- **Easy updates**: Change once, applies everywhere
- **No duplication**: Eliminates inline styles and duplicate CSS

### Performance
- **Caching**: Browser can cache the CSS file
- **Reduced HTML size**: No inline styles in templates
- **Faster rendering**: CSS is loaded once and reused
- **Optimized delivery**: Single HTTP request for styles

### Consistency
- **Unified design**: All pages use the same visual language
- **Standardized components**: Consistent button, form, and card styles
- **Theme consistency**: Easy to maintain brand colors and styling
- **Cross-page uniformity**: Navigation and layout consistency

### Development Experience
- **Easier debugging**: CSS issues isolated to one file
- **Faster development**: Reusable component classes
- **Better collaboration**: Developers can work on CSS without touching templates
- **Version control**: Clear history of style changes

## Migration from Inline Styles

The application has been migrated from inline styles and `<style>` blocks to the centralized CSS file:

### Before (Inline Styles)
```html
<div style="background: white; border-radius: 12px; padding: 2rem;">
    <h3 style="color: #495057; margin-bottom: 1.5rem;">Title</h3>
</div>
```

### After (CSS Classes)
```html
<div class="card">
    <h3 class="card-header">Title</h3>
</div>
```

### Before (Style Blocks)
```html
<style>
    .custom-style {
        background: white;
        border-radius: 12px;
    }
</style>
```

### After (External CSS)
```css
/* In main.css */
.card {
    background: var(--white);
    border-radius: var(--border-radius);
}
```

## Future Enhancements

### Dark Mode
CSS variables make it easy to implement dark mode:

```css
@media (prefers-color-scheme: dark) {
    :root {
        --primary-color: #4dabf7;
        --background-color: #212529;
        --text-color: #f8f9fa;
    }
}
```

### Theme System
Multiple themes can be implemented:

```css
[data-theme="light"] {
    --background-color: #ffffff;
    --text-color: #212529;
}

[data-theme="dark"] {
    --background-color: #212529;
    --text-color: #f8f9fa;
}
```

### CSS-in-JS Alternative
For future React/Vue.js migration, CSS modules or styled-components can be used while maintaining the same design system.

## Best Practices

### Adding New Styles
1. **Use existing classes** when possible
2. **Follow naming conventions** (BEM methodology)
3. **Use CSS variables** for colors and spacing
4. **Add responsive variants** for mobile compatibility
5. **Document complex selectors** with comments

### Modifying Existing Styles
1. **Test across all pages** to ensure consistency
2. **Update CSS variables** rather than hardcoded values
3. **Maintain backward compatibility** when possible
4. **Update documentation** for any new utility classes

### Performance Considerations
1. **Minimize CSS size** by removing unused styles
2. **Use efficient selectors** (avoid deep nesting)
3. **Optimize media queries** for mobile-first approach
4. **Consider CSS purging** for production builds

## Conclusion

The centralized CSS architecture provides a solid foundation for maintaining and extending the VigilantRaccoon web interface. It ensures consistency, improves performance, and makes the codebase more maintainable for future development.
