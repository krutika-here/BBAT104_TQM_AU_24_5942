# Project Scope Definition Document

**Project Title:** Secure Online Quiz System  
**Course Code & Name:** BBAT104 – Fundamentals of Total Quality Management (TQM)  
**Academic Session:** 2026–2027  
**Candidate Roll Number:** 39  
**Candidate Name:** Krutika Agrawal  
**University Registration Number:** AU-24-5942  
**Assigned Topic Digit:** 9 – Online Quiz System  
**Assigned Quality Goal:** Q04 — Improve Security  
**Core Objective:** Ensure secure quiz submissions, protect user data, and prevent unauthorized access  
**Evaluation Scope:** Review 1 (Setup & SRS) and Review 2 (Base System & CRUD)  
**Document Revision:** 2.0 (Security Scope Definition)  

---

## 1. Project Purpose & Executive Summary

The purpose of the **Secure Online Quiz System** is to provide an educational computer-based testing environment that embeds strict application security controls into its core architecture. In conventional online examination platforms, insufficient access control, unvalidated input, insecure password recovery, answer key leakage, and lack of audit logging undermine the integrity of academic assessments.

This project delivers a robust, secure, browser-accessible online quiz application aligned with Total Quality Management (TQM) principles. For the current evaluation phase (**Review 1: Setup & SRS** and **Review 2: Base System & CRUD**), the system establishes complete CRUD capabilities across quizzes, questions, users, and results, reinforced by all five features of the assigned Quality Goal **Q04 — Improve Security**.

---

## 2. In-Scope Functionality for Review 1 & Review 2

The boundaries of the current implementation encompass the following deliverables:

### 2.1 Review 1 Scope (Setup & SRS — 10 Raw Marks)
* **GitHub Repository Verification & Health:** Active public Git repository (`BBAT104_TQM_AU_24_5942`), branch synchronization, clean commit history exceeding standard milestones, and comprehensive documentation.
* **System Architecture Flowchart:** Detailed architectural design document (`docs/ARCHITECTURE.md`) with Mermaid flowcharts, sequence diagrams, state transitions, and entity-relationship models depicting security layers, request dispatching, and persistence.
* **Software Requirements Specification (SRS):** Formal IEEE 830-aligned specification (`docs/SRS.md`) defining unique functional requirements (`FR-xx`), security requirements (`SEC-xx`), non-functional requirements (`NFR-xx`), and acceptance criteria.
* **Scope Definition Document:** Explicit boundaries, role matrices, CRUD specifications, and exclusions (`docs/SCOPE.md`).
* **Documentation Alignment:** Fully consistent `README.md` reflecting Roll Number 39, baseline System 9, and Quality Goal Q04.

### 2.2 Review 2 Scope (Base System & CRUD — 15 Raw Marks)
* **User & Account Management:**
  * Self-registration for students with default role assignment.
  * Role-based authentication (Administrator, Quiz Creator / Instructor, Student).
  * Secure logout and session invalidation.
* **Quiz Management (CRUD):**
  * **Create:** Authorized instructors/admins can create new quizzes with titles, descriptions, durations, and passing cutoff percentages.
  * **Read:** All authenticated and anonymous users can browse available quizzes and details.
  * **Update:** Authorized instructors/admins can update quiz metadata.
  * **Delete:** Authorized instructors/admins can delete obsolete quizzes with cascade deletion of questions.
* **Question & Answer Management (CRUD):**
  * **Create:** Add multiple-choice questions with 4 distinct options, correct key configuration, and customizable mark allocation.
  * **Read:** Instructors/admins can view question lists with answer keys. Students taking tests receive question stems and options WITHOUT answer keys.
  * **Update:** Edit question stems, choices, marks, and correct answer keys.
  * **Delete:** Remove individual questions safely from quizzes.
* **Quiz Attempts & Examination Delivery:**
  * Interactive browser quiz player with question navigation (Next / Previous / Jump).
  * Non-blocking real-time countdown timer synchronized with server-side deadlines.
  * Single-use submission token to eliminate duplicate submission race conditions.
  * Server-side grading engine computing scores and pass/fail statuses.
  * Private, session-delimited scorecard generation.
* **Result Management & Gradebook (CRUD):**
  * Students can read their own historical quiz scores and attempt records.
  * Instructors and administrators can view global attempt gradebooks with summary pass/fail metrics.
  * Direct score tampering or unauthorized cross-student result access is strictly prevented.

### 2.3 Assigned Quality Goal: Five Q04 Security Features
1. **Feature 1 — Role-Based Login:**
   * Cryptographic password verification.
   * Server-side `@role_required` access enforcement across routes.
   * Access-denied handling (HTTP 403 Forbidden with security audit logging).
   * Session fixation prevention via session regeneration.
   * Anti-CSRF protection on all state-changing POST requests.
2. **Feature 2 — Password Reset:**
   * Secure, unpredictable 32-byte URL-safe reset tokens.
   * Tokens stored exclusively as SHA-256 hashes in `password_resets`.
   * Strict 15-minute expiration window and single-use invalidation.
   * User enumeration prevention with generic user-facing responses.
   * Invalidation of active sessions upon successful credential update.
3. **Feature 3 — Input Validation:**
   * Strict server-side type coercion and bounds checking for all request parameters.
   * Sanitization and contextual HTML auto-escaping to eliminate XSS risks.
   * Parameterized SQLite queries (`?` placeholders) to eliminate SQL injection.
   * User-friendly error messaging without leaking stack traces or internal secrets.
4. **Feature 4 — Audit Trail:**
   * Dedicated, append-only `audit_logs` database table.
   * Automatic recording of logins, failures, logouts, password resets, CRUD actions, and unauthorized access attempts.
   * Metadata captured: timestamp, event type, actor username, actor role, target entity, outcome, IP address, and details.
   * Exclusive read access granted solely to Administrators.
   * Strict prohibition on logging plaintext passwords or raw reset tokens.
5. **Feature 5 — Encryption & Sensitive Data Protection:**
   * Salted, adaptive cryptographic password hashing (PBKDF2-HMAC-SHA256 / scrypt).
   * Sensitive secrets isolated in environment variables (`FLASK_SECRET_KEY`).
   * Production-ready session cookie flags (`HttpOnly=True`, `SameSite=Lax`, `Secure` when HTTPS enabled).
   * Server-side confinement of quiz answer keys.

---

## 3. User Roles & Responsibilities

| Role | Responsibilities | Scope Boundaries |
| :--- | :--- | :--- |
| **Student** | Self-registers, logs in, undertakes timed quizzes, views personal scorecards, and reviews own attempt history. | Cannot access administrative views, edit quizzes, inspect answer keys, or view other students' records. |
| **Instructor / Quiz Creator** | Creates, reads, updates, and deletes quizzes and questions; monitors global student gradebook; reviews TQM defect checksheets. | Cannot modify administrator accounts or alter security audit logs. |
| **Administrator** | Full platform oversight; manages user accounts and roles; reviews and filters the Security Audit Trail (`audit_logs`); performs system administration. | Audit log records are append-only and cannot be altered or erased. |
| **Auditor** | Quality assurance inspector evaluating TQM compliance and defect logs. | Read-only inspection of TQM defect logs and security summary metrics. |

---

## 4. Entity CRUD Matrix

| Entity | Create (C) | Read (R) | Update (U) | Delete (D) |
| :--- | :---: | :---: | :---: | :---: |
| **Users** | Student Self-Registration / Admin | Profile / Admin User List | Password Reset / Admin Role Edit | Admin Deactivation |
| **Quizzes** | Instructor / Admin | All Users (Public Catalog) | Instructor / Admin | Instructor / Admin (Cascade) |
| **Questions** | Instructor / Admin | Instructor / Admin (Full Keys)<br/>Student (Stems & Options Only) | Instructor / Admin | Instructor / Admin |
| **Attempts / Results**| Automated Exam Engine upon Submission | Student (Self Only)<br/>Instructor/Admin (All Students) | N/A (Immutable Exam Record) | Admin (Integrity Preserving) |
| **Audit Logs** | Automated Event Interceptor | Admin (Exclusive View) | Prohibited (Append-Only) | Prohibited (Append-Only) |

---

## 5. Technology, Persistence & Deployment Scope

### 5.1 Technology Stack
* **Language:** Python 3.10+ (compatible through Python 3.14).
* **Web Framework:** Flask 3.x (lightweight, modular WSGI framework).
* **Frontend:** Responsive HTML5, CSS3, modern accessible layouts with dark/light theme support.
* **Preserved Fallbacks:** Tkinter desktop GUI (`gui.py`) and CLI test runner (`main.py`).

### 5.2 Persistence Tier
* **Database:** SQLite3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and foreign key constraints (`PRAGMA foreign_keys=ON`).
* **Tables:** `users`, `password_resets`, `quizzes`, `questions`, `attempts`, `audit_logs`, `defect_logs`.
* **Integrity:** Strict cascade deletions from quizzes to questions; atomic transactions for grading and attempt logging.

### 5.3 Hosting & Deployment Scope
* **WSGI Production Application Server:** Configured for Gunicorn / Waitress.
* **HTTPS Transport:** Secure cookie headers enabled for HTTPS deployments.
* **Secrets Management:** Environment variable loading (`os.environ.get('FLASK_SECRET_KEY')`) with dynamic fallback for local development.

---

## 6. Testing & Quality Assurance Scope

* **Unit Testing:** Automated test suite (`unittest`) validating all route endpoints, status codes, and template variables.
* **Security Testing:**
  - Authentication boundary and unauthorized access denial (HTTP 401 / 403).
  - CSRF omission and invalid token rejection (HTTP 400).
  - Password reset token single-use and expiration enforcement.
  - SQL injection prevention using parameterized queries.
  - XSS mitigation via Jinja2 auto-escaping.
  - Answer key confidentiality during active quiz attempts.
  - Duplicate submission lockout.
* **CRUD Verification:** Create, Read, Update, and Delete tests for quizzes, questions, and users.
* **Database Integrity:** Foreign key constraint validation and cascade deletion testing.

---

## 7. Explicit Exclusions & Out-of-Scope Items

To prevent scope creep and maintain alignment with Review 1 and Review 2 grading rubrics, the following components are explicitly designated as **Future Work (Scheduled for Reviews 3 & 4)**:
* **Review 3 Deliverables:** Failure Mode and Effects Analysis (FMEA) Matrix with RPN calculations, SIPOC Process Map, CTQ Tree, and formal Defect Logging Checksheets.
* **Review 4 Deliverables:** Statistical Quality Control (SQC) tools, including automated Pareto Charts (80/20 analysis), Ishikawa Fishbone Root-Cause Diagrams, and Deming Plan-Do-Check-Act (PDCA) Continuous Improvement tracking logs.
* **Third-Party Email Relay:** Production SMTP gateway integration (e.g., SendGrid/AWS SES) is out-of-scope for local academic evaluation; the system implements token generation, storage, and retrieval workflows locally.
* **Biometric Proctoring:** Video/audio monitoring and browser lockdown extensions are outside the scope of this project.

---

## 8. Assumptions, Constraints & Risks

### 8.1 Assumptions
1. Candidates and faculty access the application using modern web browsers supporting HTML5 and JavaScript.
2. The runtime environment possesses Python 3.10 or higher with standard library dependencies.
3. Persistent storage is available locally or via volume mounts in containerized environments.

### 8.2 Constraints
1. **Zero External Heavy Dependencies:** The project strictly avoids heavy external database engines or bloated frameworks to maintain fast startup, zero-latency execution, and academic reproducibility.
2. **Commit Count Standard:** The project repository must maintain at least 30 meaningful Git commits across the development lifecycle.

### 8.3 Risks & Mitigation Strategies
* **Risk 1 (Session Hijacking):** Mitigated via `HttpOnly` and `SameSite=Lax` cookies, combined with session regeneration upon login.
* **Risk 2 (Duplicate Quiz Submissions):** Mitigated via thread locks, single-use `submission_token`, and immediate state purging upon grading.
* **Risk 3 (Credential Exposure):** Mitigated via adaptive salted hashing (PBKDF2/scrypt) and excluding secret keys from Git tracking.

---

## 9. Acceptance Criteria for Review 1 & Review 2

| Review Phase | Acceptance Milestone | Success Criteria |
| :--- | :--- | :--- |
| **Review 1** | Repository & Architecture | Clean Git repository on branch `main` with active remote; detailed `docs/ARCHITECTURE.md` with Mermaid diagrams; comprehensive `docs/SRS.md`; formal `docs/SCOPE.md`; aligned `README.md`. |
| **Review 2** | Base System & CRUD | Fully functional Quiz CRUD (Create, Read, Update, Delete) and Question CRUD; student examination delivery with timer and accurate scoring; role-governed result access. |
| **Review 2** | Q04 Security Features | Working Role-Based Login (Admin, Instructor, Student); secure single-use Password Reset flow; server-side Input Validation; tamper-evident Audit Trail; cryptographic Password Hashing & Secret Protection. |
| **Quality** | Automated Test Suite | 100% pass rate across all automated unit and security tests. |
