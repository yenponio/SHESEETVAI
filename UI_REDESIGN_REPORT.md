# SHESEETVAI UI redesign report

Completed 24 September 2026. React + Vite remain the frontend; Django remains the API. No Django templates were introduced. Changes are uncommitted and have not been pushed. The earlier adviser workflow is documented separately in WORKFLOW_UPDATE.md.

## 1-2. Changed, created and removed files

The complete cumulative working-tree inventory below includes the preceding adviser workflow changes and this UI redesign. M = modified, D = removed unused stylesheet, ?? = new. This report itself is also new. frontend/tests/ contains ui.spec.js. No database, evidence, firmware or migration was deleted.

```text
 M .gitignore
 M SMTP_SETUP.md
 M backend/students/gate.py
 M backend/students/management/commands/gate_bridge.py
 M backend/students/models.py
 M backend/students/notifications.py
 M backend/students/records.py
 M backend/students/serializers.py
 M backend/students/test_evidence.py
 M backend/students/test_gate.py
 M backend/students/test_notifications.py
 M backend/students/test_records.py
 M backend/students/urls.py
 M backend/students/views.py
 M frontend/index.html
 M frontend/package-lock.json
 M frontend/package.json
 D frontend/src/App.css
 M frontend/src/App.jsx
 M frontend/src/components/ProtectedRoute.jsx
 D frontend/src/components/Sidebar.css
 M frontend/src/components/Sidebar.jsx
 M frontend/src/components/Topbar.jsx
 M frontend/src/components/ViolationEvidenceModal.jsx
 M frontend/src/components/ViolationTable.jsx
 M frontend/src/components/dashboard/CollegeChart.jsx
 M frontend/src/components/dashboard/ComplianceChart.jsx
 M frontend/src/components/dashboard/SearchBar.jsx
 M frontend/src/components/dashboard/StatCard.jsx
 M frontend/src/hooks/useGateCycle.js
 M frontend/src/hooks/useGateCycle.test.js
 M frontend/src/index.css
 M frontend/src/main.jsx
 M frontend/src/pages/ConfirmationPage.jsx
 M frontend/src/pages/Dashboard.jsx
 M frontend/src/pages/Login.jsx
 M frontend/src/pages/OSA.jsx
 M frontend/src/pages/Records.jsx
 M frontend/src/pages/ScanHistory.jsx
 M frontend/src/pages/SchoolRecords.jsx
 D frontend/src/pages/StudentPage.css
 M frontend/src/pages/StudentPage.jsx
 M frontend/src/pages/Students.jsx
 M frontend/src/pages/Violations.jsx
 D frontend/src/styles/Charts.css
 D frontend/src/styles/ConfirmationPage.css
 D frontend/src/styles/Dashboard.css
 D frontend/src/styles/Kiosk.css
 D frontend/src/styles/Records.css
 D frontend/src/styles/Sidebar.css
 D frontend/src/styles/Students.css
?? WORKFLOW_UPDATE.md
?? backend/students/migrations/0013_osa_entry_decisions.py
?? backend/students/offenses.py
?? backend/students/test_ui_data.py
?? backend/students/test_workflow.py
?? backend/students/ui_data.py
?? frontend/playwright.config.js
?? frontend/src/components/AppShell.jsx
?? frontend/src/components/ConfirmDecisionModal.jsx
?? frontend/src/components/EvidenceImage.jsx
?? frontend/src/components/Modal.jsx
?? frontend/src/components/UI.jsx
?? frontend/src/navigation.js
?? frontend/src/pages/EmailNotifications.jsx
?? frontend/src/pages/Settings.jsx
?? frontend/src/pages/StudentProfile.jsx
?? frontend/src/styles/theme.css
?? frontend/tests/
```

UI-specific backend work is limited to ui_data.py, test_ui_data.py, three added URLs and additive record response fields. Other backend changes listed above belong to the adviser workflow. All ten removed CSS files were checked for remaining imports/references; the shared theme replaces them.

## 3. Packages

- Bootstrap 5.3.8 (~5.3.8).
- Bootstrap Icons ^1.13.1.
- Locally bundled Inter, @fontsource/inter ^5.3.0.
- Development browser testing: @playwright/test ^1.63.0.

Bootstrap CSS and icons load in main.jsx. React controls dialogs and navigation; Bootstrap JavaScript is not loaded, avoiding competing DOM state.

## 4. Theme

Shared styles/theme.css defines the requested pastel-red/white variables, Inter typography, white rounded cards, borders, buttons, tables, badges and stable media containers. Removed conflicting legacy styles and consolidated layout rules. Responsive Bootstrap containers and grids keep long values readable.

## 5. Sidebar and navbar

White sidebar with pastel header, active links, Bootstrap Icons and all requested navigation destinations. Desktop collapse resizes the content grid. Mobile navigation is an accessible drawer with focus containment. Compact topbar includes page title, notification navigation and OSA account/logout controls. Existing authentication behavior is preserved.

Existing routes remain: /, /osa, /dashboard, /records, /records/:school, /scan-history and /chatbot. Added /students, /students/:studentNumber, /email-notifications and /settings.

## 6. Dashboard

Uses actual official offense totals, scan/entry/denial data, recent detections and entries, school summaries and system connection states. No mock production counters. Camera availability is queried separately; bridge status and gate-cycle status come from Django.

## 7. Live detection and OSA review

Updated the existing ConfirmationPage at /chatbot. Fixed-aspect evidence uses object-fit: contain. Student details and offense totals come from actual API data. All three full-width actions remain reachable through normal scrolling on small screens.

Each decision opens a confirmation dialog. Cancel sends nothing. Processing disables actions, with a synchronous in-flight guard against repeated clicks. API errors remain visible; successful decisions display returned workflow state.

- Confirm Violation and Allow Entry: submits the existing confirmed-allow decision. Backend authorizes Uno OPEN; offense waits for acknowledged opening and sensor-confirmed entry.
- No Violation: submits rejection. Backend authorizes entry; no offense.
- Confirm Violation and Deny Entry: submits denial. Gate remains closed; no official offense or offense email.

React does not calculate offense eligibility, duplicates or gate authorization. The scanner remains the camera/AI owner; OSA reviews its exact captured image instead of starting a competing AI stream. Fixed a null initial-state bug in useGateCycle while preserving its gate-cycle transitions.

## 8. Students and profiles

Replaced the previous mock roster with backend students, search, school/history filters, pagination and empty/error states. Profiles show identity, contact information, backend-derived minor/major totals, entry summary, official history and exact linked evidence. Current totals are not reset after conversion. No unsupported create/edit controls were added.

## 9. Records and evidence

Responsive official-record tables preserve school routes, search and supported filters. Exact evidence URLs drive thumbnails and accessible detail dialogs; missing images have an explicit fallback. No latest-screenshot guessing. Added read-only OSA decision, confirmed-entry and email-status response fields. All official rows already require entry, so a redundant entry-validity filter was not invented. Denials remain audit events.

## 10. Entry and audit logs

Read-only /api/students/audit/ exposes paginated actual attempts, linked inspection decisions and gate-cycle outcomes, with search and outcome filters. Sensor/entry results use recorded workflow state. Denial is visible here without becoming an official offense.

## 11. Email notifications

Read-only /api/students/notifications/ shows actual queue/delivery state, student email, dates, recorded errors and backend offense totals. Search/status filters and pagination work. Opening this page does not send mail. No unsupported resend control was added. Existing email worker and environment credentials remain responsible for SMTP.

## 12. Settings

Read-only /api/students/system-status/ exposes existing controller/cycle state, configured timezone and SMTP configuration availability without credentials. Settings clearly distinguish supported observations from unimplemented controls. Camera status is obtained from the camera service.

Rainy Day Mode is NOT implemented: the former toggle only changed React state, and there is no trained slippers detector or persistent backend rainy-mode setting. Removed the misleading working toggle. Current shoulder/midriff/knee detection remains active. This redesign does not train a slippers model.

## 13. IDs

Shared dialogs generate unique heading IDs and valid aria-labelledby references. Repeated rows use stable React keys rather than duplicated DOM IDs. Label/input associations and sidebar control targets are valid. Browser tests check duplicate IDs and broken ARIA targets across all routes and six widths.

## 14. Accessibility

Descriptive buttons, associated labels, evidence alt text, visible status text/icons, keyboard dialogs, Escape/cancel behavior, focus restoration and modal focus containment. Processing dialogs cannot be dismissed mid-submission. Mobile dialogs fit within the viewport and scroll when required.

## 15. Responsive fixes

Tested widths 1440, 1366, 1024, 768, 430 and 375 pixels. Tables scroll inside table-responsive wrappers. Page content does not horizontally overflow. Sidebar collapse changes available content width; mobile drawer does not permanently overlap content. Evidence/camera aspect ratios prevent layout jumps. Final desktop and mobile review screenshots were visually inspected using test-only evidence fixtures.

## 16-17. Unsupported fields and intentionally omitted controls

No fabricated AI confidence, course, year/section, student status, raw ultrasonic distances, independent exit-sensor status or physical gate-position measurement. Displayed gate state is the actual controller cycle state, not a separate position sensor. SMTP configured does not prove a running worker or successful delivery.

No unsupported camera-selection, serial-port editing, gate-timing editing, SMTP credential editing, test-email, resend, student CRUD or rainy-mode controls. Uno serial settings and pins remain in the working hardware integration. Current minor totals are displayed instead of inventing per-record historical offense ordinal values. No mock values are shipped in production pages; browser fixtures live only in tests.

## 18. Validation

- Django: 85 tests passed; system checks passed.
- Migration drift check: no changes detected. The UI adds no model or migration.
- Playwright: 21 tests passed, covering all routes at six widths, navigation/logout, scanner API payload, decision cancel/submit/error states, single submission, modal keyboard/mobile behavior, exact evidence, student/profile search/filter/pagination, record filters, audit/email filters, loading, empty and API failure states.
- Gate-state Node suite: 4 tests passed.
- ESLint: passed.
- Production build: passed, including builds throughout the implementation phases.
- git diff --check: passed.

Reproduce from the repository root in PowerShell:

```powershell
& backend/venv/Scripts/python.exe -B backend/manage.py check
& backend/venv/Scripts/python.exe -B backend/manage.py makemigrations --check --dry-run
& backend/venv/Scripts/python.exe -B backend/manage.py test students --noinput --buffer
Set-Location frontend
npm.cmd run lint
npm.cmd run build
node --test src/hooks/useGateCycle.test.js
npm.cmd run test:ui
```

Browser tests use installed Microsoft Edge with isolated API fixtures. They do not command the physical gate or send real SMTP emails. The passing suites verify software behavior; a supervised hardware walkthrough is still needed for the actual Uno, camera, sensors and mail account.

## 19. Remaining issues and startup

Restart Django to load the additional read-only endpoints, and reload the frontend. No new migration is required for the UI. Earlier workflow migration 0013_osa_entry_decisions was applied locally; deployment of that earlier change uses `backend/venv/Scripts/python.exe backend/manage.py migrate`.

npm audit reports five dependency advisories (four high, one moderate) involving brace-expansion, nanoid, postcss and react-router/react-router-dom. Broad dependency upgrades were not applied as part of this redesign. Rainy/slippers functionality remains unsupported as explained above. Changes have not been committed or pushed.

For the complete earlier workflow model/migration details, daily duplicate rule, evidence/SMTP ordering and three hardware walkthroughs, see WORKFLOW_UPDATE.md.
