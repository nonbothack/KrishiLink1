# Shared interface primitives

Import `Button`, `Card`, `Badge`, `StatusPill`, `Field`, `Notice`, `DataState`, `Skeleton`, and `PageHeading` from `Experience.jsx`. These components use the single token and app stylesheet imported by `main.jsx`; do not add component-level colors or spacing values.

- Use native elements through `Card as="article"` or `Card as="section"` when the content has that meaning.
- Give icon-only buttons an `aria-label`; retain normal button text for primary farmer actions. `Button` is a native button and defaults to `type="button"`; use `type="submit"` inside forms.
- Pass translated text from `useLanguage()` into labels, badges, status pills, and `DataState` stale/offline messages. The reusable primitives do not own farmer-facing copy.
- `Field` associates its label and optional hint/error text, and leaves browser autocomplete enabled unless the caller explicitly sets `autoComplete`.
- Use `DataState` for loading, error, and empty results. Pass stale/offline messages only when the displayed data is actually cached or the application has confirmed the connection state.
- `Skeleton` is decorative; pair it with an announced loading label or a containing `role="status"`.
- Status color always accompanies visible status text. Do not rely on color alone to communicate an outcome.

Run `npm run test` and `npm run test:e2e` when changing these primitives. No Storybook is retained in this repository; Vitest and Playwright are the current interactive documentation and verification surfaces.
