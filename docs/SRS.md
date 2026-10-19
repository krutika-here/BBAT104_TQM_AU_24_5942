# Software Requirements Specification (SRS)

**Project Title:** Secure Online Quiz System  
**Course Code & Name:** BBAT104 – Fundamentals of Total Quality Management (TQM)  
**Academic Session:** 2026–2027  
**Candidate Roll Number:** 39  
**Candidate Name:** Krutika Agrawal  
**University Registration Number:** AU-24-5942  
**Assigned Topic Digit:** 9 – Online Quiz System  
**Assigned Quality Goal:** Q04 — Improve Security  
**Core Objective:** Ensure secure quiz submissions, protect user data, and prevent unauthorized access  
**Specification Standard:** IEEE 830-1998 Aligned / TQM Quality Engineering Framework  
**Deliverable Scope:** Review 1 (Setup & SRS) and Review 2 (Base System & CRUD)  
**Document Revision:** 2.0 (Security Engineering Specification)  

---

## Table of Contents
1. [1.0 Introduction & Baseline Objectives](#10-introduction--baseline-objectives)  
   1.1 [Purpose](#11-purpose)  
   1.2 [Document Conventions](#12-document-conventions)  
   1.3 [Intended Audience](#13-intended-audience)  
   1.4 [Problem Statement & Background](#14-problem-statement--background)  
   1.5 [Core TQM Quality Goal (Q04 — Improve Security)](#15-core-tqm-quality-goal-q04--improve-security)  
   1.6 [References & Standards](#16-references--standards)  
2. [2.0 User Roles, Classes & Responsibilities](#20-user-roles-classes--responsibilities)  
   2.1 [User Persona 1: Student / Examinee](#21-user-persona-1-student--examinee)  
   2.2 [User Persona 2: Faculty / Quiz Creator](#22-user-persona-2-faculty--quiz-creator)  
   2.3 [User Persona 3: System Administrator](#23-user-persona-3-system-administrator)  
   2.4 [User Persona 4: TQM Quality Auditor](#24-user-persona-4-tqm-quality-auditor)  
   2.5 [Role & Privileges Matrix](#25-role--privileges-matrix)  
3. [3.0 Functional Requirements (FR)](#30-functional-requirements-fr)  
   3.1 [Module 1: Authentication & Account Management](#31-module-1-authentication--account-management)  
   3.2 [Module 2: Password Recovery & Reset Lifecycle](#32-module-2-password-recovery--reset-lifecycle)  
   3.3 [Module 3: Quiz Management (CRUD)](#33-module-3-quiz-management-crud)  
   3.4 [Module 4: Question & Answer Bank Management (CRUD)](#34-module-4-question--answer-bank-management-crud)  
   3.5 [Module 5: Student Examination Portal & Live Timer](#35-module-5-student-examination-portal--live-timer)  
   3.6 [Module 6: Answer Evaluation & Secure Score Calculation](#36-module-6-answer-evaluation--secure-score-calculation)  
   3.7 [Module 7: Result Management & Historical Gradebook](#37-module-7-result-management--historical-gradebook)  
   3.8 [Module 8: Security Audit Trail & Event Logging](#38-module-8-security-audit-trail--event-logging)  
4. [4.0 Security Requirements (SEC)](#40-security-requirements-sec)  
   4.1 [Role-Based Access Control & Privilege Escalation Defense](#41-role-based-access-control--privilege-escalation-defense)  
   4.2 [Password Hashing & Sensitive Data Protection](#42-password-hashing--sensitive-data-protection)  
   4.3 [Input Validation, Sanitization & Safe Parameterization](#43-input-validation-sanitization--safe-parameterization)  
   4.4 [Anti-CSRF & Session Security](#44-anti-csrf--session-security)  
   4.5 [Answer Key Confidentiality & Anti-Cheat Boundary](#45-answer-key-confidentiality--anti-cheat-boundary)  
5. [5.0 Non-Functional Requirements (NFR)](#50-non-functional-requirements-nfr)  
   5.1 [Performance & Response Latency](#51-performance--response-latency)  
   5.2 [Reliability, Availability & Fault Tolerance](#52-reliability-availability--fault-tolerance)  
   5.3 [Data Integrity & ACID Persistence](#53-data-integrity--acid-persistence)  
   5.4 [Usability & Poka-Yoke Mistake-Proofing](#54-usability--poka-yoke-mistake-proofing)  
   5.5 [Maintainability & Code Quality](#55-maintainability--code-quality)  
6. [6.0 Interface, Data & Privacy Requirements](#60-interface-data--privacy-requirements)  
   6.1 [User Interface Requirements](#61-user-interface-requirements)  
   6.2 [Data Requirements & Schema Relationships](#62-data-requirements--schema-relationships)  
   6.3 [Privacy & Data Protection Requirements](#63-privacy--data-protection-requirements)  
7. [7.0 Deployment, Testing & Acceptance Criteria](#70-deployment-testing--acceptance-criteria)  
   7.1 [Deployment Environment & Constraints](#71-deployment-environment--constraints)  
   7.2 [Verification & Testing Strategy](#72-verification--testing-strategy)  
   7.3 [Formal Acceptance Criteria](#73-formal-acceptance-criteria)  
   7.4 [Assumptions, Dependencies & Limitations](#74-assumptions-dependencies--limitations)  

---

## 1.0 Introduction & Baseline Objectives

### 1.1 Purpose
This Software Requirements Specification (SRS) defines the functional, non-functional, architectural, and security requirements for the **Secure Online Quiz System**. Developed for **BBAT104: Fundamentals of Total Quality Management**, this document establishes the binding engineering specification for **Review 1 (Setup & SRS)** and **Review 2 (Base System & CRUD)**, explicitly focused on Quality Goal **Q04 — Improve Security**.

### 1.2 Document Conventions
* **FR-[MOD]-[NUM]:** Functional Requirement identifier.
* **SEC-[MOD]-[NUM]:** Security Requirement identifier.
* **NFR-[CAT]-[NUM]:** Non-Functional Requirement identifier.
* **Poka-Yoke:** Mistake-proofing mechanism preventing erroneous or malicious state transitions.
* **RBAC:** Role-Based Access Control.
* **Shall / Must:** Mandatory contractual obligation for review compliance.

### 1.3 Intended Audience
* **Academic Evaluators & Faculty:** To assess Course Outcome 1 (CO1) and Course Outcome 2 (CO2) compliance against BBAT104 guidelines.
* **Security & Quality Engineers:** To audit access boundaries, cryptography, tamper-resistance, and error handling.
* **Developers & Maintainers:** To implement and test database models, route controllers, and UI views.

### 1.4 Problem Statement & Background
Computer-Based Assessment (CBA) systems operate in adversarial environments. Unsecured educational platforms frequently exhibit catastrophic vulnerabilities:
1. **Broken Access Control & Insecure Direct Object References (IDOR):** Students modifying quiz IDs in URLs can inspect unreleased tests, tamper with other students' grades, or alter question answers.
2. **Answer Key Leakage:** Client-rendered assessment forms frequently embed the correct answer or solution keys directly inside hidden HTML inputs or client-side JavaScript payloads.
3. **Session Tampering & Replay Attacks:** Students submitting duplicate quiz payloads or replaying requests after deadlines expire to overwrite previously calculated scores.
4. **Credential Vulnerabilities:** Plaintext or reversibly encrypted password storage, combined with insecure password recovery links that expose accounts to takeover.
5. **Absence of Accountability:** Inability to audit unauthorized access attempts, grade modifications, or administrative changes due to lacking security audit logs.

### 1.5 Core TQM Quality Goal (Q04 — Improve Security)
Under BBAT104 guidelines for Roll Number 39 (Topic Digit 9), the assigned quality objective is:
> **"Q04 — Improve Security: Ensure secure quiz submissions, protect user data, and prevent unauthorized access."**

To fulfill this quality mandate, the system establishes five required security features:
1. **Role-Based Login:** Strict cryptographic authentication and server-enforced role separation (Administrator, Instructor, Student).
2. **Password Reset:** Cryptographically randomized, single-use, time-limited reset tokens stored as hashes, with session revocation.
3. **Input Validation:** Exhaustive server-side type and range validation, contextual escaping (XSS prevention), and SQL parameterization.
4. **Audit Trail:** Persistent, append-only security audit log recording logins, failures, password resets, CRUD events, and security violations.
5. **Encryption & Sensitive Data Protection:** Strong salted password hashing (PBKDF2/scrypt), secret isolation outside source control, HTTPS-ready session security, and complete answer-key confidentiality.

### 1.6 References & Standards
1. *BBAT104 TQM Project Guidelines, Session 2026–2027.*
2. *IEEE Std 830-1998:* Recommended Practice for Software Requirements Specifications.
3. *OWASP Top 10 Web Application Security Risks (2021).*
4. *NIST Special Publication 800-63B:* Digital Identity Guidelines — Authentication and Lifecycle Management.

---

## 2.0 User Roles, Classes & Responsibilities

The system defines four distinct user classes with strictly separated privilege profiles:

### 2.1 User Persona 1: Student / Examinee
* **Description:** Enrolled students participating in timed quizzes.
* **Permitted Actions:** Register account, authenticate, browse published quizzes, initiate quiz attempts, select answers, track live time limit, submit quizzes, view immediate private scorecards, and view own historical attempts.
* **Restricted Actions:** Cannot create/edit/delete quizzes or questions; cannot inspect answer keys; cannot view other students' submissions or audit trails.

### 2.2 User Persona 2: Faculty / Quiz Creator
* **Description:** Academic instructors designing curriculum assessments.
* **Permitted Actions:** Full CRUD control over assigned Quizzes and Questions; configure time limits, pass percentages, and marks; view global student result gradebooks and calculate pass/fail statistics; inspect TQM defect checksheets.
* **Restricted Actions:** Cannot modify system administrator accounts or alter security audit log records.

### 2.3 User Persona 3: System Administrator
* **Description:** Platform owner maintaining system security, user accounts, and infrastructure.
* **Permitted Actions:** Full access across all modules; user account and role management; review and filter the Security Audit Trail (`audit_logs`); manage system configuration; perform database maintenance.
* **Restricted Actions:** Audit trail records are append-only; cannot tamper with or delete audit event logs.

### 2.4 User Persona 4: TQM Quality Auditor
* **Description:** Quality assurance evaluator auditing adherence to TQM quality parameters.
* **Permitted Actions:** Read-only inspection of the live TQM defect logs, audit trail summary statistics, and CTQ parameter metrics.

### 2.5 Role & Privileges Matrix

| Capability / Endpoint | Student | Quiz Creator / Instructor | Administrator | Auditor |
| :--- | :---: | :---: | :---: | :---: |
| Self-Registration & Account Creation | **Yes** | No (Invited/Seeded) | No (Seeded) | No |
| Login / Logout / Password Reset | **Yes** | **Yes** | **Yes** | **Yes** |
| Browse Quizzes & Launch Attempt | **Yes** | **Yes** | **Yes** | Read-Only |
| Submit Quiz Attempt & View Personal Result | **Yes** | **Yes** | **Yes** | Read-Only |
| View Personal Attempt History | **Yes** (Self) | **Yes** (Self) | **Yes** (Self) | No |
| Create / Edit / Delete Quizzes (Quiz CRUD)| No | **Yes** | **Yes** | Read-Only |
| Create / Edit / Delete Questions (Q CRUD) | No | **Yes** | **Yes** | Read-Only |
| View Global Student Gradebook | No | **Yes** (All students) | **Yes** (All students) | Read-Only |
| View Security Audit Trail (`audit_logs`)  | No | No | **Yes** (Full) | Read-Only |
| View TQM Defect Log Checksheet           | No | **Yes** | **Yes** | **Yes** (Full) |
| Manage User Roles & Account Activation   | No | No | **Yes** | No |

---

## 3.0 Functional Requirements (FR)

### 3.1 Module 1: Authentication & Account Management
* **FR-AUTH-01 (Account Registration):** The system shall allow new students to self-register by providing a unique username, valid email, and secure password. Default role shall strictly be assigned as `student`.
* **FR-AUTH-02 (Role-Based Authentication):** The system shall authenticate users via username/email and password. Upon successful verification, the user session shall store `user_id`, `username`, and `role`.
* **FR-AUTH-03 (Session Invalidation & Logout):** Logging out shall immediately invalidate the server session, clear session cookies, and redirect the user to the login screen.
* **FR-AUTH-04 (Role-Based Route Protection):** Protected routes shall strictly enforce role authorization via server decorators. Unauthorized access attempts shall trigger HTTP 403 Forbidden and record an audit event.

### 3.2 Module 2: Password Recovery & Reset Lifecycle
* **FR-PWD-01 (Password Reset Request):** A user shall be able to request a password reset by providing their registered email address. The system shall respond with a generic success confirmation to prevent user enumeration.
* **FR-PWD-02 (Cryptographic Token Generation & Hashing):** The system shall generate a cryptographically secure token (minimum 32 URL-safe random bytes), compute its SHA-256 hash, and store the hash in `password_resets` with an expiration timestamp of $T + 15\text{ minutes}$.
* **FR-PWD-03 (Token Consumption & Password Update):** When a user accesses `/reset-password/<token>`, the system shall verify the token hash, check that `expires_at > CURRENT_TIMESTAMP` and `used = 0`. Upon submitting a valid new password, the system shall update the user's password hash, mark `used = 1`, and terminate all existing active sessions for that user.

### 3.3 Module 3: Quiz Management (CRUD)
* **FR-QM-01 (Create Quiz):** Authorized instructors and administrators shall be able to create a new quiz specifying `title`, `description`, `time_limit_mins` ($\ge 1$), and `pass_percentage` ($1.0 \le p \le 100.0$).
* **FR-QM-02 (Read Quizzes):** The system shall list all quizzes with associated question counts, durations, and passing standards in an interactive catalog.
* **FR-QM-03 (Update Quiz):** Instructors and administrators shall be able to update title, description, time limit, and pass percentage for an existing quiz.
* **FR-QM-04 (Delete Quiz with Cascade):** Instructors and administrators shall be able to delete a quiz. Deleting a quiz shall cascade and delete all associated questions to maintain referential integrity.

### 3.4 Module 4: Question & Answer Bank Management (CRUD)
* **FR-QB-01 (Create Question):** Authorized users shall be able to add multiple-choice questions (MCQs) to a quiz, supplying question text, 4 options (A, B, C, D), correct option choice ($\in \{A, B, C, D\}$), and marks allocation ($\ge 1$).
* **FR-QB-02 (Read Questions):** Instructors and administrators shall be able to view all questions for a given quiz with designated correct options. Students taking the quiz shall receive question stems and options WITHOUT the correct option attribute.
* **FR-QB-03 (Update Question):** Authorized users shall be able to update question text, options, correct option, and marks.
* **FR-QB-04 (Delete Question):** Authorized users shall be able to delete an individual question.

### 3.5 Module 5: Student Examination Portal & Live Timer
* **FR-AT-01 (Attempt Initialization):** An authenticated student selecting an eligible quiz shall initiate an attempt. The system shall generate a unique single-use `submission_token`, record `started_at`, and compute deadline timestamp.
* **FR-AT-02 (Question Navigation):** Students shall navigate questions sequentially or via direct jump, with choices persisted across navigation events in an encrypted or session-backed buffer.
* **FR-AT-03 (Live Countdown Timer):** A non-blocking client-side timer shall display remaining minutes and seconds. The server shall validate the submission deadline independently of client clocks.
* **FR-AT-04 (Auto-Submit on Expiry):** When elapsed time exceeds the allotted duration, the system shall automatically freeze input controls and trigger submission.

### 3.6 Module 6: Answer Evaluation & Secure Score Calculation
* **FR-GR-01 (Answer Key Confidentiality):** Evaluation shall take place exclusively on the server by querying the database's `correct_option` column.
* **FR-GR-02 (Scoring Formula):** The grading engine shall evaluate:
  $$\text{Score} = \sum_{q \in Q} (\text{Marks}_q \times \mathbb{I}(\text{Answer}_q == \text{CorrectOption}_q))$$
  $$\text{Percentage} = \left(\frac{\text{Score}}{\sum_{q \in Q} \text{Marks}_q}\right) \times 100$$
  $$\text{Status} = \begin{cases} \text{"Passed"}, & \text{if Percentage} \ge \text{PassPercentage} \\ \text{"Failed"}, & \text{otherwise} \end{cases}$$
* **FR-GR-03 (Single-Submission Lock):** The engine shall acquire an atomic submission lock on the `submission_token`. Replay submissions shall be rejected with an informative notice.
* **FR-GR-04 (Private Scorecard Display):** Upon successful grading, the system shall redirect the student to a private scorecard accessible solely via a one-time session token.

### 3.7 Module 7: Result Management & Historical Gradebook
* **FR-RES-01 (Personal Attempt History):** Authenticated students shall be able to review their own past quiz attempts, scores, percentages, and pass/fail statuses.
* **FR-RES-02 (Instructor Gradebook View):** Instructors and administrators shall be able to inspect all student attempts across quizzes, with sorting and filtering by quiz ID.
* **FR-RES-03 (Access Boundaries):** Students attempting to view other students' result IDs shall be denied access (HTTP 403 / 404).

### 3.8 Module 8: Security Audit Trail & Event Logging
* **FR-AUD-01 (Security Event Recording):** The system shall log security-relevant transactions into `audit_logs`, including:
  - `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILURE`, `AUTH_LOGOUT`
  - `PASSWORD_RESET_REQUESTED`, `PASSWORD_RESET_COMPLETED`, `PASSWORD_RESET_INVALID`
  - `QUIZ_CREATED`, `QUIZ_UPDATED`, `QUIZ_DELETED`
  - `QUESTION_CREATED`, `QUESTION_UPDATED`, `QUESTION_DELETED`
  - `QUIZ_ATTEMPT_SUBMITTED`
  - `UNAUTHORIZED_ACCESS_ATTEMPT`
* **FR-AUD-02 (Audit Trail Metadata):** Each audit record shall capture `timestamp`, `event_type`, `actor_username`, `actor_role`, `target_entity`, `outcome`, `ip_address`, and `details`.
* **FR-AUD-03 (Audit Trail Protection):** The audit log shall be append-only. Only users with the `admin` role shall have permission to view the audit log. Plaintext passwords and secret tokens shall NEVER be logged.

---

## 4.0 Security Requirements (SEC)

### 4.1 Role-Based Access Control & Privilege Escalation Defense
* **SEC-RBAC-01:** Authorization checks shall be performed server-side on every restricted route. Client-side UI controls (such as hiding buttons) shall be treated solely as ergonomic enhancements.
* **SEC-RBAC-02:** User role assignment shall be protected. Self-registration shall strictly enforce `role = 'student'`. Elevation to `instructor` or `admin` shall require administrative credentials or pre-configured database seeding.
* **SEC-RBAC-03:** Insecure Direct Object References (IDOR) shall be prevented by validating that accessed attempt records belong to the currently logged-in student or an authorized instructor/admin.

### 4.2 Password Hashing & Sensitive Data Protection
* **SEC-CRY-01:** User passwords shall never be stored in plaintext or reversible encryption. Passwords shall be hashed using modern cryptographic hash functions with unique per-password salts (`scrypt` or `pbkdf2:sha256` via Werkzeug security primitives).
* **SEC-CRY-02:** Application secrets (e.g., `FLASK_SECRET_KEY`) shall be loaded from environment variables and never committed to source control repositories.
* **SEC-CRY-03:** Sensitive database fields such as `password_hash` shall be excluded from all public API outputs, templates, and logs.

### 4.3 Input Validation, Sanitization & Safe Parameterization
* **SEC-VAL-01:** All user inputs (registration, login, quiz title, questions, options, marks, answers) shall be validated server-side for length, type, character set, and range limits.
* **SEC-VAL-02:** Database queries shall strictly use parameterized SQL placeholders (`?`) to prevent SQL injection vulnerabilities.
* **SEC-VAL-03:** Rendered HTML output shall be auto-escaped by the Jinja2 template engine to prevent Cross-Site Scripting (XSS). User inputs shall never be rendered using `|safe` unless sanitized against strict HTML whitelists.

### 4.4 Anti-CSRF & Session Security
* **SEC-SES-01:** All state-changing HTTP requests (POST, PUT, DELETE) shall require a valid Anti-CSRF synchronizer token matching the token stored in the authenticated user session.
* **SEC-SES-02:** Session cookies shall have `HttpOnly=True` to prevent JavaScript cookie theft and `SameSite=Lax` to prevent cross-site request leakage. When deployed under HTTPS, `Secure=True` shall be enforced.
* **SEC-SES-03:** The system shall regenerate or rotate session identifiers upon successful authentication to eliminate session fixation risks.

### 4.5 Answer Key Confidentiality & Anti-Cheat Boundary
* **SEC-KEY-01:** The `correct_option` attribute shall NEVER be rendered in client HTML, serialized into JavaScript variables, or sent in JSON responses while a quiz is active.
* **SEC-KEY-02:** Question submissions shall be timestamped and compared against `started_at + time_limit_seconds`. Submissions arriving after deadline shall be flagged and graded with expired state.

---

## 5.0 Non-Functional Requirements (NFR)

### 5.1 Performance & Response Latency
* **NFR-PERF-01:** Score calculation and scorecard rendering shall complete in under $50\text{ ms}$ upon submission.
* **NFR-PERF-02:** Page load time for quiz catalog and question screens shall be under $200\text{ ms}$ on local and broadband connections.

### 5.2 Reliability, Availability & Fault Tolerance
* **NFR-REL-01:** The system shall guarantee zero data loss for completed quiz submissions through transactional SQLite commits.
* **NFR-REL-02:** In the event of network disruption during a quiz, students' previously submitted answers shall remain intact in server session storage.

### 5.3 Data Integrity & ACID Persistence
* **NFR-INT-01:** All write operations shall adhere to ACID transaction properties. Deleting a quiz shall cascade to questions and preserve foreign key referential integrity (`PRAGMA foreign_keys = ON`).

### 5.4 Usability & Poka-Yoke Mistake-Proofing
* **NFR-USA-01:** Forms shall provide clear, actionable error feedback without exposing system internals or stack traces.
* **NFR-USA-02:** Submit buttons shall be locked upon click to eliminate accidental duplicate requests.

### 5.5 Maintainability & Code Quality
* **NFR-MNT-01:** Codebase shall adhere to PEP 8 style standards with modular separation between `database.py`, `app.py`, `gui.py`, and `main.py`.
* **NFR-MNT-02:** Minimum 30 meaningful Git commits tracking incremental architectural evolution.

---

## 6.0 Interface, Data & Privacy Requirements

### 6.1 User Interface Requirements
* Responsive layout compatible with desktop monitors and mobile displays ($360\text{px}$ to $1920\text{px}$).
* Accessible color contrast adhering to WCAG 2.1 AA standards with optional high-contrast theme toggle.

### 6.2 Data Requirements & Schema Relationships
* Entities: `users`, `password_resets`, `quizzes`, `questions`, `attempts`, `audit_logs`, `defect_logs`.
* Relationships:
  - 1 User to Many Password Resets (1:N)
  - 1 User to Many Attempts (1:N)
  - 1 Quiz to Many Questions (1:N, Cascade on Delete)
  - 1 Quiz to Many Attempts (1:N)

### 6.3 Privacy & Data Protection Requirements
* Passwords hashed via non-reversible adaptive hashing.
* Student attempt records accessible exclusively by the examinee and authorized faculty/admin.
* No personal data or credentials leaked into logs.

---

## 7.0 Deployment, Testing & Acceptance Criteria

### 7.1 Deployment Environment & Constraints
* Target Runtime: Python 3.10+ on Linux / Windows / macOS.
* Production WSGI Application Server: Gunicorn or Waitress.
* Database: SQLite3 with Write-Ahead Logging (WAL).
* Transport: HTTPS with strict TLS in cloud environments.

### 7.2 Verification & Testing Strategy
* Automated unit tests covering all authentication routes, RBAC boundaries, CRUD operations, password reset lifecycle, input bounds, and audit logging.
* Regression testing ensuring 100% pass rate across the full test suite.

### 7.3 Formal Acceptance Criteria
1. **Review 1 Deliverables:** GitHub repository verified, System Architecture Flowchart complete, SRS document complete with unique IDs, Scope definition complete, README aligned.
2. **Review 2 Deliverables:** Working CRUD for Quizzes and Questions; all five Q04 security features functioning with empirical test verification.
3. **Zero Critical Vulnerabilities:** No unparameterized queries, no plaintext passwords, no exposed answer keys.

### 7.4 Assumptions, Dependencies & Limitations
* **Assumptions:** Local system has Python 3.10+ installed; email notifications utilize local token retrieval for environments without external SMTP credentials.
* **Dependencies:** Python standard libraries, Flask >= 3.0.0, Werkzeug >= 3.0.0.
* **Limitations:** Database-at-rest encryption relies on underlying OS/disk encryption (LUKS/BitLocker); SQLite file is secured via file permissions.
