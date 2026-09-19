# Accessibility and GIGW readiness

Target: WCAG 2.2 AA quality and preparation for the applicable GIGW assessment. Automated axe results are evidence of tested paths, not certification.

| Area | Local evidence | Status | Manual follow-up |
|---|---|---|---|
| Keyboard and focus | Shared focus primitives and Playwright/axe coverage | IMPLEMENTED_AND_TESTED | Complete keyboard-only task script on deployed build |
| Labels/errors/dialogs | Form semantics, error announcements and browser journeys | IMPLEMENTED_AND_TESTED | Screen-reader confirmation |
| Contrast/status | Design tokens and axe checks | IMPLEMENTED_NOT_EXTERNALLY_VERIFIED | Human contrast review at 200% zoom |
| Reduced motion | CSS reduced-motion rules | IMPLEMENTED_AND_TESTED | Verify device/browser preference |
| Responsive/mobile | 360, 390, 768 and 1440 browser checks in Packets 06/08/12 | IMPLEMENTED_AND_TESTED | Test target government devices |
| EN/HI/MR | Translation catalogue and route tests | PARTIAL | Native-speaker terminology review |
| Accessible documents/PDF | No production document-accessibility certification | NOT_IMPLEMENTED | Review every procurement/receipt PDF before release |
| TalkBack | Manual plan only | DOCUMENTED_ONLY | Android TalkBack session with evidence capture |
| Broken links/search | Public prerender/SEO scripts | IMPLEMENTED_AND_TESTED | Final-domain crawl and content owner sign-off |
| PWA/offline state | Packet 12 shell/offline checks | IMPLEMENTED_AND_TESTED | Manual offline and assistive-tech review |

## Manual script

Run against staging with seeded non-production data: (1) keyboard-only login, Sell, offer and Trade Room; (2) TalkBack farmer dashboard, price lookup and support; (3) desktop screen reader if available; (4) 200% zoom and text reflow; (5) reduced motion; (6) EN/HI/MR; (7) offline shell and retry; (8) staff operations; (9) public price lookup. Record browser/device, route, observed issue, screenshot/video where permitted, severity and retest result. Do not mark this script executed from automated axe output.
