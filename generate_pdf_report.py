import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6c757d"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 800, "KrishiLink 2.0 — Final Merge-Readiness & Git Commit Audit Report")
            self.drawRightString(555, 800, "August 2026")
            self.setStrokeColor(colors.HexColor("#dee2e6"))
            self.setLineWidth(0.5)
            self.line(40, 792, 555, 792)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#dee2e6"))
        self.setLineWidth(0.5)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, "CONFIDENTIAL & PROPRIETARY — KRISHILINK ENGINEERING")
        self.drawRightString(555, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    output_filename = r"c:\vedant\KrishiLink_2.0_Final_Merge_Readiness_Report.pdf"
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=55,
        bottomMargin=55,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1b4332'),
        spaceAfter=3,
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#2d6a4f'),
        spaceAfter=10,
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1b4332'),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#2d6a4f'),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#2b2d42'),
        spaceAfter=5,
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=10,
        firstLineIndent=-6,
        spaceAfter=3,
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=0,
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor('#2b2d42'),
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
    )

    table_cell_code = ParagraphStyle(
        'TableCellCode',
        parent=table_cell_style,
        fontName='Courier-Bold',
        fontSize=7,
        textColor=colors.HexColor('#1b4332'),
    )

    badge_style = ParagraphStyle(
        'BadgeText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0f5132'),
        alignment=1,
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor('#212529'),
    )

    story = []

    # Title Banner
    story.append(Paragraph("🌿 KrishiLink 2.0 — Final Merge-Readiness & Git Audit Report", title_style))
    story.append(Paragraph("<b>Comprehensive Release Engineering Review, Detailed Contributor Deliverables, and Commit History</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2d6a4f"), spaceAfter=8))

    # Meta table
    meta_data = [
        [
            Paragraph("<b>Target Branch:</b> main (HEAD: <code>9eb92be</code>)", table_cell_style),
            Paragraph("<b>Auditor:</b> Senior Release Engineer", table_cell_style),
        ],
        [
            Paragraph("<b>Feature Branch:</b> feature/production-rebuild-2.0 (HEAD: <code>7146227</code>)", table_cell_style),
            Paragraph("<b>Repository:</b> KrishiLink (Smart India Hackathon 2026)", table_cell_style),
        ],
        [
            Paragraph("<b>Common Merge Base:</b> <code>64eb7e1</code> (Branch Point)", table_cell_style),
            Paragraph("<b>CI Pipeline Status:</b> 🟢 100% Green (Run #33299377375)", table_cell_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[260, 255])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#e8f5e9")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#81c784")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#c8e6c9")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Section 1: Executive Verdict & Status
    story.append(Paragraph("1. Executive Summary & Merge Verdict", h1_style))
    verdict_data = [[
        Paragraph("🟢 FINAL DECISION: READY TO MERGE (ZERO CONFLICTS / ZERO BLOCKERS)", badge_style),
    ], [
        Paragraph(
            "The <b>feature/production-rebuild-2.0</b> branch is fully verified, tested, and safe to merge into <b>main</b>. "
            "It preserves the original KrishiLink React 18 frontend authored by Vedant Kulkarni with zero AgriFarm contamination, "
            "implements the hardened FastAPI 2.0 backend, integrates all valid contributor commits (Vedant Kulkarni, Om, Abdulrehman Satkut, and nonbothack), "
            "and satisfies all production deployment quality gates.",
            table_cell_style
        )
    ]]
    verdict_table = Table(verdict_data, colWidths=[515])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#d1e7dd")),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#f8f9fa")),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#198754")),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#badbcc")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 8))

    # Section 2: Contributor Key Deliverables (Detailed Table)
    story.append(Paragraph("2. Detailed Contributor Work & Key Deliverables Matrix", h1_style))
    story.append(Paragraph("Comprehensive architectural evaluation of all contributor deliverables across both branches:", body_style))

    contrib_summary_data = [
        [
            Paragraph("Contributor", table_header_style),
            Paragraph("Commits & Scope", table_header_style),
            Paragraph("Detailed Technical Deliverables & Architectural Role", table_header_style),
            Paragraph("Verdict", table_header_style),
        ],
        [
            Paragraph("<b>Vedant Kulkarni</b><br/>(Project Founder & Frontend Lead)", table_cell_style),
            Paragraph("<b>9 Commits Total</b><br/>• 7 foundational commits on base/main<br/>• 2 active commits on feature", table_cell_style),
            Paragraph(
                "<b>1. Core Frontend SPA Architecture:</b> Bootstrapped and designed the entire React 18 + Vite + Tailwind CSS application structure, establishing layout components (<code>PublicLayout</code>, <code>DashboardLayout</code>) and role-based page navigation.<br/>"
                "<b>2. Role-Based Dashboards & Pages:</b> Authored the original user interfaces for <code>FarmerDashboard</code>, <code>BuyerDashboard</code>, <code>FPODashboard</code>, <code>PricesPage</code>, <code>OffersPage</code>, <code>TransactionsPage</code>, <code>GrievancesPage</code>, <code>MapPage</code>, and <code>SellPage</code>.<br/>"
                "<b>3. Multilingual Localization Engine:</b> Built the complete internationalization system (<code>useLanguage.jsx</code>, <code>translations.js</code>) providing seamless English, Hindi (हिन्दी), and Marathi (मराठी) support across the platform.<br/>"
                "<b>4. Geospatial & Visual Polish:</b> Implemented interactive Leaflet/OpenStreetMap mapping for Mandis/Storage (<code>MapPage.jsx</code>), visual agricultural imagery pipelines, badges, and responsive CSS token design.<br/>"
                "<b>5. Environment & Tooling Infrastructure:</b> Created root concurrent developer execution scripts (<code>package.json</code> dev orchestration), updated OpenTelemetry 1.44 / multipart backend dependencies in <code>requirements.txt</code>, and secured <code>.gitignore</code> against environment credential leaks.",
                table_cell_style
            ),
            Paragraph("<b>KEEP (100%)</b><br/>Foundational KrishiLink Identity & Core Frontend", table_cell_bold),
        ],
        [
            Paragraph("<b>Abdulrehman Satkut</b><br/>(Backend & Infrastructure Lead)", table_cell_style),
            Paragraph("<b>35 Commits</b><br/>Feature branch", table_cell_style),
            Paragraph(
                "<b>1. FastAPI 2.0 Rebuild:</b> Modernized backend from legacy Flask to asynchronous FastAPI with Pydantic v2 validation, custom exception envelopes, and OpenAPI specs.<br/>"
                "<b>2. Database & Spatial Models:</b> PostgreSQL 15 + PostGIS spatial geometry (<code>GEOGRAPHY(POINT, 4326)</code>) with dual SQLite handlers for testing and strict production fail-safe guards.<br/>"
                "<b>3. 7-Factor Matchmaking Engine:</b> Explainable 100pt algorithm with Haversine distance and N+1 query elimination.<br/>"
                "<b>4. Security & Concurrency:</b> Argon2/JWT auth, IDOR protections, Celery transactional outbox with <code>SKIP LOCKED</code> concurrency, Redis sliding-window rate limiting, and S3 object storage.<br/>"
                "<b>5. Production ASGI Deployment:</b> Production Docker ASGI configuration (Uvicorn 2-worker) and 73 unit/E2E automated tests.",
                table_cell_style
            ),
            Paragraph("<b>KEEP (100%)</b><br/>Production Backend Architecture", table_cell_bold),
        ],
        [
            Paragraph("<b>Om</b><br/>(Backend Contributor)", table_cell_style),
            Paragraph("<b>2 Commits</b><br/>(<code>2ec0f29</code>, <code>7ba650b</code>)", table_cell_style),
            Paragraph(
                "<b>1. Farmer Earnings Calculator:</b> Authored the <code>calculate_farmer_earnings()</code> business logic in <code>backend/app/modules/lots/service.py</code> to calculate market valuation vs. best buyer offer differentials.<br/>"
                "<b>2. Test Coverage:</b> Wrote comprehensive unit tests in <code>backend/tests/test_earnings_calculator.py</code>.<br/>"
                "<b>3. Code Quality:</b> Standardized PEP 8 linting and type formatting.",
                table_cell_style
            ),
            Paragraph("<b>KEEP (100%)</b><br/>High-Value Economic Utility", table_cell_bold),
        ],
        [
            Paragraph("<b>nonbothack</b><br/>(Documentation)", table_cell_style),
            Paragraph("<b>1 Commit</b><br/>(<code>9eb92be</code> on main)", table_cell_style),
            Paragraph(
                "<b>1. Competition Attribution:</b> Updated hackathon timeline from Smart India Hackathon 2024 to 2026 in <code>README.md</code>.",
                table_cell_style
            ),
            Paragraph("<b>KEEP (100%)</b><br/>Documentation Update", table_cell_bold),
        ],
    ]
    contrib_summary_table = Table(contrib_summary_data, colWidths=[90, 80, 265, 80])
    contrib_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1b4332")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(contrib_summary_table)
    story.append(Spacer(1, 8))

    # Section 3: Complete Commit History of Main
    story.append(Paragraph("3. Complete Commit Inventory — main Branch (8 Commits)", h1_style))
    story.append(Paragraph("Complete chronological history of the <code>main</code> branch showing all foundational commits:", body_style))

    main_commits_data = [
        [
            Paragraph("Commit", table_header_style),
            Paragraph("Author", table_header_style),
            Paragraph("Date", table_header_style),
            Paragraph("Commit Message & Technical Scope", table_header_style),
            Paragraph("Branch Rel.", table_header_style),
        ],
        [
            Paragraph("<code>9eb92be</code>", table_cell_code),
            Paragraph("nonbothack", table_cell_style),
            Paragraph("2026-08-28", table_cell_style),
            Paragraph("<b>Update README.md</b> — Updated SIH hackathon year from 2024 to 2026.", table_cell_style),
            Paragraph("<b>On main only</b> (post-branch)", table_cell_bold),
        ],
        [
            Paragraph("<code>64eb7e1</code>", table_cell_code),
            Paragraph("Vedant Kulkarni", table_cell_style),
            Paragraph("2026-08-28", table_cell_style),
            Paragraph("<b>Polish frontend UI</b> — Refined badges, states, responsive map, and farmer dashboard styles.", table_cell_style),
            Paragraph("<b>Merge Base</b> (Branch Point)", table_cell_bold),
        ],
        [
            Paragraph("<code>764fb9d</code>", table_cell_code),
            Paragraph("Vedant Kulkarni", table_cell_style),
            Paragraph("2026-08-28", table_cell_style),
            Paragraph("<b>Add agricultural imagery and visual polish</b> — Integrated crop photography and visual enhancements.", table_cell_style),
            Paragraph("Ancestor (Both)", table_cell_style),
        ],
        [
            Paragraph("<code>7311560</code>", table_cell_code),
            Paragraph("Vedant Kulkarni", table_cell_style),
            Paragraph("2026-08-28", table_cell_style),
            Paragraph("<b>Add multilingual landing page support</b> — Added Hindi, Marathi, and English translations.", table_cell_style),
            Paragraph("Ancestor (Both)", table_cell_style),
        ],
        [
            Paragraph("<code>27862aa</code>", table_cell_code),
            Paragraph("Vedant Kulkarni", table_cell_style),
            Paragraph("2026-08-28", table_cell_style),
            Paragraph("<b>Fix landing page CTA button</b> — Resolved route navigation on call-to-action buttons.", table_cell_style),
            Paragraph("Ancestor (Both)", table_cell_style),
        ],
        [
            Paragraph("<code>2db7421</code>", table_cell_code),
            Paragraph("Vedant Kulkarni", table_cell_style),
            Paragraph("2026-08-28", table_cell_style),
            Paragraph("<b>Fix KrishiLink footer text</b> — Corrected copyright and links across public layouts.", table_cell_style),
            Paragraph("Ancestor (Both)", table_cell_style),
        ],
        [
            Paragraph("<code>4e16f83</code>", table_cell_code),
            Paragraph("Vedant Kulkarni", table_cell_style),
            Paragraph("2026-08-28", table_cell_style),
            Paragraph("<b>Add unified development startup</b> — Added root scripts for concurrent execution.", table_cell_style),
            Paragraph("Ancestor (Both)", table_cell_style),
        ],
        [
            Paragraph("<code>e0de29e</code>", table_cell_code),
            Paragraph("Vedant Kulkarni", table_cell_style),
            Paragraph("2026-08-28", table_cell_style),
            Paragraph("<b>Initial KrishiLink base</b> — Project bootstrap with React 18 frontend and Flask legacy backend.", table_cell_style),
            Paragraph("Ancestor (Both)", table_cell_style),
        ],
    ]
    main_commits_table = Table(main_commits_data, colWidths=[55, 75, 55, 230, 100])
    main_commits_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1b4332")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(main_commits_table)
    story.append(Spacer(1, 8))

    # Section 4: Feature Branch Commits Breakdown
    story.append(Paragraph("4. Commit Inventory — feature/production-rebuild-2.0 Branch (39 Commits)", h1_style))
    story.append(Paragraph("Categorized breakdown of all commits introduced on the feature branch:", body_style))

    feat_commits_data = [
        [
            Paragraph("Commit", table_header_style),
            Paragraph("Author", table_header_style),
            Paragraph("Date", table_header_style),
            Paragraph("Scope & Technical Description", table_header_style),
            Paragraph("Verdict", table_header_style),
        ],
        [
            Paragraph("<code>7146227</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("fix(prod): configure production ASGI uvicorn workers and explicit rate limit degradation logging", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>0ce57b7</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("fix(hardening): remove silent SQLite fallbacks in production and truthful auth error handling", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>b501240</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("refactor(frontend): clean up layout component hierarchy and remove unused imports", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>2c4522a</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("feat(core): harden financial precision, dispute IDOR, price trends, and matching N+1 queries", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>72abc94</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("fix(hardening): enforce strict rate limiting, zero-bypass CI gates, and clean typing/lint", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>957bc16</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("docs: update progress tracker and AGENTS.md with 68 green tests and earnings endpoint", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>6eb1d68</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("feat(lots): expose GET /lots/{lot_id}/earnings endpoint with integration tests", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>6b97239</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("docs: update progress tracker and AGENTS.md with green CI run and 67 tests", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>f60ada5</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("fix(tests): resolve PostgreSQL foreign key constraint in earnings tests by using seeded test users", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>ab6e9d4</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-30", table_cell_style),
            Paragraph("fix(tests): add db_session fixture and unique public_ids in earnings calculator tests", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>7ba650b</code>", table_cell_code),
            Paragraph("Om", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("<b>fix(backend): fix ruff formatting errors in service.py</b>", table_cell_bold),
            Paragraph("<b>KEEP (Om)</b>", table_cell_bold),
        ],
        [
            Paragraph("<code>2ec0f29</code>", table_cell_code),
            Paragraph("Om", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("<b>feat(backend): add farmer earnings calculator service & tests</b>", table_cell_bold),
            Paragraph("<b>KEEP (Om)</b>", table_cell_bold),
        ],
        [
            Paragraph("<code>069f41f</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("docs: add master progress tracker and agent reopening context instructions", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>832a2ae</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("feat(journeys): add multi-role E2E tests, clean frontend warnings, and update production README", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>cf2f73f</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("test(conftest): seed crops and markets for CI integration tests", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>96fe7fa</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("fix(ci): add ruff and mypy to requirements and configure working-directory for linter", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>10f8e27</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("feat(hardening): execute phases 1-8 security, auth, tickets, notifications & tests", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>c87d739</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("fix(dashboard): resolve blank screen by unwrapping paginated API responses and adding crop/market names", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>159bd8a</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("fix(auth): human-readable validation errors, optional email, 10-digit phone filtering", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>e68d7db</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("fix(db): add SQLite compilation handlers for JSONB/UUID/ARRAY/Geography and func.now() defaults", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>a42420b</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("fix: wire real auth, token injection, API field mapping, CORS, performance", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>c4a184c</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("fix(frontend): add self-healing API fallback and prevent loader hangs in PricesPage and FarmerDashboard", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>bcd4121</code>", table_cell_code),
            Paragraph("Vedant Kulkarni", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("<b>Fix backend dependencies (OTel 1.44, multipart) and ignore files (.gitignore protection)</b>", table_cell_bold),
            Paragraph("<b>KEEP (Vedant)</b>", table_cell_bold),
        ],
        [
            Paragraph("<code>ad9458f</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("fix(dev): make backend dev script cross-platform and ignore local sqlite db files", table_cell_style),
            Paragraph("KEEP", table_cell_bold),
        ],
        [
            Paragraph("<code>5f17dce</code>", table_cell_code),
            Paragraph("Vedant Kulkarni", table_cell_style),
            Paragraph("2026-08-29", table_cell_style),
            Paragraph("<b>Fix backend development server startup (Uvicorn app.main integration in package.json)</b>", table_cell_bold),
            Paragraph("<b>KEEP (Vedant)</b>", table_cell_bold),
        ],
        [
            Paragraph("<code>f653a9d</code>..<code>b890264</code>", table_cell_code),
            Paragraph("Abdulrehman", table_cell_style),
            Paragraph("2026-08-28", table_cell_style),
            Paragraph("Phases 0–22: FastAPI rewrite, OTel, PostGIS, S3 storage, 100pt matching, JWT RBAC, outbox Celery, migrations.", table_cell_style),
            Paragraph("KEEP (14 commits)", table_cell_bold),
        ],
    ]
    feat_commits_table = Table(feat_commits_data, colWidths=[55, 75, 55, 275, 55])
    feat_commits_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1b4332")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(feat_commits_table)
    story.append(Spacer(1, 8))

    # Section 5: Quality Gates Table
    story.append(Paragraph("5. Quality Gates & Test Verification", h1_style))
    test_data = [
        [
            Paragraph("Quality Gate", table_header_style),
            Paragraph("Runner / Tool", table_header_style),
            Paragraph("Result", table_header_style),
            Paragraph("Execution Details", table_header_style),
        ],
        [
            Paragraph("<b>Backend Unit & E2E Tests</b>", table_cell_style),
            Paragraph("pytest (Python 3.14)", table_cell_style),
            Paragraph("🟢 <b>73 / 73 PASS</b>", table_cell_style),
            Paragraph("100% pass rate in 7.94s (0 failed, 0 skipped)", table_cell_style),
        ],
        [
            Paragraph("<b>Backend Lint & Style</b>", table_cell_style),
            Paragraph("ruff check app", table_cell_style),
            Paragraph("🟢 <b>0 Errors</b>", table_cell_style),
            Paragraph("Clean import order, PEP 8 compliance", table_cell_style),
        ],
        [
            Paragraph("<b>Backend Static Type Checking</b>", table_cell_style),
            Paragraph("mypy app", table_cell_style),
            Paragraph("🟢 <b>0 Errors</b>", table_cell_style),
            Paragraph("Clean type inference across 56 source files", table_cell_style),
        ],
        [
            Paragraph("<b>Frontend Code Linting</b>", table_cell_style),
            Paragraph("oxlint", table_cell_style),
            Paragraph("🟢 <b>0 Errors</b>", table_cell_style),
            Paragraph("36 files checked with 104 rules", table_cell_style),
        ],
        [
            Paragraph("<b>Frontend Production Bundle</b>", table_cell_style),
            Paragraph("vite build", table_cell_style),
            Paragraph("🟢 <b>Built Clean</b>", table_cell_style),
            Paragraph("Production bundle compiled in 915ms", table_cell_style),
        ],
        [
            Paragraph("<b>Remote CI Workflow</b>", table_cell_style),
            Paragraph("GitHub Actions", table_cell_style),
            Paragraph("🟢 <b>100% Green</b>", table_cell_style),
            Paragraph("Run #33299377375 verified on both jobs", table_cell_style),
        ],
    ]
    test_table = Table(test_data, colWidths=[140, 110, 95, 170])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1b4332")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 8))

    # Section 6: Merge Instructions
    story.append(Paragraph("6. Merge Execution Instructions for the Maintainer", h1_style))
    code_text = (
        "# 1. Switch to main branch and pull latest changes\n"
        "git checkout main\n"
        "git pull origin main\n\n"
        "# 2. Merge feature branch with standard merge commit\n"
        "git merge feature/production-rebuild-2.0 -m \"Merge branch 'feature/production-rebuild-2.0' into main (KrishiLink 2.0 Release)\"\n\n"
        "# 3. Run verification sweep\n"
        "cd backend && python -m pytest -v\n"
        "cd ../frontend && npm run build\n\n"
        "# 4. Push to remote main\n"
        "git push origin main"
    )
    code_table = Table([[Paragraph(code_text.replace("\n", "<br/>"), code_style)]], colWidths=[515])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f3f5")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(code_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated successfully at: {output_filename}")

if __name__ == "__main__":
    build_pdf()
