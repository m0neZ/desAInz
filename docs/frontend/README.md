# Frontend Accessibility

The admin dashboard follows WCAG guidelines. Interactive controls include `aria-label` attributes and keyboard handlers so screen reader and keyboard users can operate all features. Jest and React Testing Library verify components respond to keyboard events and remain free of accessibility violations via `jest-axe`.

Key widgets like the language switcher and toggle button expose labels that describe their action. Chart range selectors provide accessible labels, and lists identify their content for assistive technologies.
