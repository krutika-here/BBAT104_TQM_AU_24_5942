# Software Requirements Specification (SRS)

**Project Title:** Online Quiz System  
**Subject / Course Code:** BBAT104 – Fundamentals of Total Quality Management (TQM)  
**Academic Session:** 2026–27  
**Candidate Name:** Krutika Agrawal  
**University Registration Number:** AU-24-5942  
**Assigned Digit & Baseline System:** Digit 9 – Online Quiz System  
**Assigned TQM Quality Goal:** Ensure zero latency during submissions & auto-grading  
**Specification Standard:** IEEE 830-1998 Aligned / TQM Software Engineering Framework  
**Deliverable Phase:** Review 1: Setup & SRS (CO1 Mapped)  

---

## Table of Contents
1. [1.0 Introduction & Baseline Objectives](#10-introduction--baseline-objectives)  
   1.1 [Purpose](#11-purpose)  
   1.2 [Document Conventions](#12-document-conventions)  
   1.3 [Intended Audience](#13-intended-audience)  
   1.4 [Project Scope & Course Context](#14-project-scope--course-context)  
   1.5 [Core TQM Quality Goal](#15-core-tqm-quality-goal)  
   1.6 [References & Standards](#16-references--standards)  
2. [2.0 User Classes & Characteristics](#20-user-classes--characteristics)  
   2.1 [User Persona 1: Student / Examinee](#21-user-persona-1-student--examinee)  
   2.2 [User Persona 2: Faculty / Course Instructor](#22-user-persona-2-faculty--course-instructor)  
   2.3 [User Persona 3: TQM Quality Auditor / Evaluator](#23-user-persona-3-tqm-quality-auditor--evaluator)  
   2.4 [User Role & Privileges Matrix](#24-user-role--privileges-matrix)  
   2.5 [Operating Environment & Assumptions](#25-operating-environment--assumptions)  
3. [3.0 Functional Requirements](#30-functional-requirements)  
   3.1 [Module 1: Quiz Management (CRUD)](#31-module-1-quiz-management-crud)  
   3.2 [Module 2: Question Bank Management (CRUD)](#32-module-2-question-bank-management-crud)  
   3.3 [Module 3: Student Portal & Examination Setup](#33-module-3-student-portal--examination-setup)  
   3.4 [Module 4: In-Memory Quiz Delivery & Live Timer Engine](#34-module-4-in-memory-quiz-delivery--live-timer-engine)  
   3.5 [Module 5: Zero-Latency Submission & Automated Grading Engine](#35-module-5-zero-latency-submission--automated-grading-engine)  
   3.6 [Module 6: Student Gradebook & Historical Results](#36-module-6-student-gradebook--historical-results)  
   3.7 [Module 7: TQM Defect Logging & SQC Checksheets](#37-module-7-tqm-defect-logging--sqc-checksheets)  
   3.8 [Module 8: Dual Execution Architecture (GUI & CLI)](#38-module-8-dual-execution-architecture-gui--cli)  
4. [4.0 Non-Functional Requirements (NFRs)](#40-non-functional-requirements-nfrs)  
   4.1 [Latency & Real-Time Performance Thresholds](#41-latency--real-time-performance-thresholds)  
   4.2 [Throughput & Capacity](#42-throughput--capacity)  
   4.3 [Reliability, Availability & Fault Tolerance](#43-reliability-availability--fault-tolerance)  
   4.4 [Data Integrity & ACID Compliance](#44-data-integrity--acid-compliance)  
   4.5 [Usability & Poka-Yoke Error Proofing](#45-usability--poka-yoke-error-proofing)  
   4.6 [Maintainability, Portability & Code Standards](#46-maintainability-portability--code-standards)  
5. [5.0 Critical-to-Quality (CTQ) Parameters & Quality Standards](#50-critical-to-quality-ctq-parameters--quality-standards)  
   5.1 [Voice of Customer (VOC) to CTQ Tree Translation](#51-voice-of-customer-voc-to-ctq-tree-translation)  
   5.2 [Six Sigma Quality Objectives](#52-six-sigma-quality-objectives)  
   5.3 [Poka-Yoke (Mistake-Proofing) Rules](#53-poka-yoke-mistake-proofing-rules)  
6. [6.0 Software Dependencies & Environment Setup](#60-software-dependencies--environment-setup)  
   6.1 [Core Runtime & Tooling](#61-core-runtime--tooling)  
   6.2 [Python Standard & Third-Party Libraries](#62-python-standard--third-party-libraries)  
   6.3 [Installation & Configuration Verification](#63-installation--configuration-verification)  

---

## 1.0 Introduction & Baseline Objectives

### 1.1 Purpose
This Software Requirements Specification (SRS) provides a definitive, unambiguous, and testable description of the **Online Quiz System**. It details the functional behaviors, non-functional performance guarantees, system architecture constraints, and quality assurance metrics governing the system. It serves as the primary technical specification for **Review 1** of the BBAT104 course project.

### 1.2 Document Conventions
* **FR-xx:** Functional Requirement identifier.
* **NFR-xx:** Non-Functional Requirement identifier.
* **CTQ-xx:** Critical-to-Quality parameter.
* **Poka-Yoke:** Japanese manufacturing and engineering methodology for defect prevention and mistake-proofing.
* **SLA:** Service Level Agreement / Guaranteed performance threshold.
* **Must / Shall:** Mandatory requirements for compliance.
* **Should:** Highly recommended capabilities.

### 1.3 Intended Audience
* **Course Evaluators & Faculty:** To assess engineering rigor, TQM principles integration, and rubric compliance for Course Outcome 1 (CO1).
* **Software Developers & Maintainers:** To understand component boundaries, data schemas, and API contracts.
* **Quality Assurance Auditors:** To verify defect tracking, checksheet logging, and CTQ parameter compliance.

### 1.4 Project Scope & Course Context
The project is executed under the curriculum guidelines of **BBAT104: Fundamentals of Total Quality Management**, Academic Session 2026–27. Based on the student's registration digit (ending in **9**), the assigned baseline system is the **Online Quiz System**.

### 1.5 Core TQM Quality Goal
The project's mandated quality objective is:
> **"Ensure zero latency during submissions & auto-grading"**

In computer-based testing, submission lag causes severe user stress, duplicate submission retries, and UI freezing. This specification mandates an architecture where answer grading takes place entirely in-memory with $O(1)$ complexity per question, resulting in instantaneous visual score display ($< 20\text{ ms}$ perceived latency), completely decoupled from secondary database disk write operations.

### 1.6 References & Standards
1. *IEEE Std 830-1998:* Recommended Practice for Software Requirements Specifications.
2. *BBAT104 TQM Course Guidelines, Allotment & Marking Scheme (Session 2026–27).*
3. *Total Quality Management in Software Development (Kaizen, Deming PDCA, Poka-Yoke).*
4. *Python 3.10+ PEP Standards & SQLite3 Transaction Guidelines.*

---

## 2.0 User Classes & Characteristics

The system serves three primary user classes with distinct operational profiles:

### 2.1 User Persona 1: Student / Examinee
* **Role Description:** Candidates undertaking academic or technical quizzes.
* **Technical Profile:** Novice to intermediate computer literacy; expects an intuitive, responsive, and stress-free interface.
* **Core Activities:** Enters identification credentials, selects an active quiz, navigates multiple-choice questions, tracks remaining time via live countdown, and submits responses.
* **Expectations:** Instantaneous scorecard feedback upon submission with zero UI freeze, clear question breakdown, and deterministic timer alerts.

### 2.2 User Persona 2: Faculty / Course Instructor
* **Role Description:** Academic administrator responsible for curriculum assessment.
* **Technical Profile:** Moderate technical literacy; requires streamlined administrative control over tests.
* **Core Activities:** Creates new quizzes, sets time limits and passing cutoff percentages, adds/updates/deletes questions and options, reviews student attempt history, and analyzes pass/fail ratios.
* **Expectations:** Robust CRUD operations with strict referential integrity (cascade deletes) and instant database updates.

### 2.3 User Persona 3: TQM Quality Auditor / Evaluator
* **Role Description:** Evaluator assessing compliance with TQM quality standards, defect tracking, and performance targets.
* **Technical Profile:** Advanced quality management expertise; familiar with SQC tools (Pareto, Ishikawa, FMEA, PDCA).
* **Core Activities:** Inspects the live TQM defect log, categorizes software anomalies, audits RPN ratings, and monitors submission latency metrics.
* **Expectations:** Transparent logging of all Poka-Yoke validation events and system exceptions into persistent checksheet tables.

### 2.4 User Role & Privileges Matrix

| Capability / Module | Student | Faculty / Admin | TQM Auditor |
| :--- | :---: | :---: | :---: |
| Launch Quiz Portal & Take Test | **Yes** | **Yes** | **Yes** |
| Select Options & Navigate Questions | **Yes** | **Yes** | **Yes** |
| Submit Quiz & View Personal Scorecard | **Yes** | **Yes** | **Yes** |
| Create / Edit / Delete Quizzes (CRUD) | No | **Yes** | Read-Only |
| Add / Update / Delete Questions (CRUD)| No | **Yes** | Read-Only |
| View Global Student Result Gradebook | No | **Yes** | **Yes** |
| Access TQM Defect Log & Checksheets  | No | Read-Only | **Yes** (Full) |
| Log New Defect / Audit Event (PDCA)  | No | **Yes** | **Yes** |

### 2.5 Operating Environment & Assumptions
* **Operating System:** Cross-platform (Linux/Ubuntu, Microsoft Windows 10/11, macOS).
* **Hardware Requirements:** Minimum 1.0 GHz x86/ARM CPU, 512 MB available RAM, 50 MB disk space.
* **Display:** Minimum screen resolution of $1024 \times 768$ pixels.
* **Environment Fallback:** If X11/Wayland display server or graphical libraries are unavailable, the system automatically falls back to the full-featured CLI interface (`python3 main.py --cli`).

---

## 3.0 Functional Requirements

### 3.1 Module 1: Quiz Management (CRUD)
* **FR-QM-01: Create Quiz**
  * *Description:* The instructor shall be able to create a new quiz record with title, syllabus description, time limit (in minutes), and passing cutoff percentage.
  * *Input:* Title (string), Description (string), Time Limit (integer $\ge 1$), Passing Cutoff (float between $1.0$ and $100.0$).
  * *Validation (Poka-Yoke):* Title must be non-empty and unique. Numeric inputs must be strictly validated.
  * *Output:* New quiz saved to database with unique auto-incremented `quiz_id`.
* **FR-QM-02: Read / List Quizzes**
  * *Description:* The system shall display all existing quizzes alongside aggregate question counts and configuration parameters.
  * *Output:* Table/Treeview listing `id`, `title`, `description`, `time_limit_mins`, `pass_percentage`, and `question_count`.
* **FR-QM-03: Update Quiz**
  * *Description:* The instructor shall be able to modify the title, description, time limit, or pass cutoff of an existing quiz.
  * *Validation:* Quiz ID must exist; title uniqueness constraint preserved.
* **FR-QM-04: Delete Quiz (Cascade)**
  * *Description:* The instructor shall be able to delete a quiz. Deleting a quiz shall automatically cascade and delete all associated questions to prevent orphan records.
  * *Confirmation:* System requires explicit modal user confirmation before deletion.

### 3.2 Module 2: Question Bank Management (CRUD)
* **FR-QB-01: Add Question**
  * *Description:* The instructor shall be able to add multiple-choice questions (MCQs) to a designated quiz.
  * *Input:* Quiz ID (FK), Question Text, Option A, Option B, Option C, Option D, Correct Option ('A', 'B', 'C', or 'D'), Marks (integer $\ge 1$).
  * *Validation (Poka-Yoke):* All 4 options and question text must be populated. The correct option must strictly belong to the set $\{A, B, C, D\}$.
* **FR-QB-02: Read Questions by Quiz**
  * *Description:* The system shall filter and display all questions associated with the selected quiz in sequential order.
* **FR-QB-03: Update Question**
  * *Description:* The instructor shall be able to edit the question text, options, correct answer key, or mark allocation.
* **FR-QB-04: Delete Question**
  * *Description:* The instructor shall be able to delete individual questions from the quiz.

### 3.3 Module 3: Student Portal & Examination Setup
* **FR-ST-01: Student Identification Input**
  * *Description:* The student shall enter their Full Name and Roll/Registration Number before beginning an assessment.
  * *Validation (Poka-Yoke):* Blank inputs trigger an immediate alert modal and log an "Input Validation" defect to the TQM checksheet.
* **FR-ST-02: Topic Selection & Overview**
  * *Description:* The student shall select a quiz topic from an interactive dropdown. The system shall dynamically display the quiz description, time limit, and passing cutoff mark.
* **FR-ST-03: Question Pre-Caching**
  * *Description:* Upon clicking "Start Quiz", the system shall query all questions and keys for the selected quiz in a single read query and store them in an in-memory session structure (`list[dict]`), guaranteeing zero disk I/O during test progression.

### 3.4 Module 4: In-Memory Quiz Delivery & Live Timer Engine
* **FR-QE-01: Question Navigation**
  * *Description:* The system shall present questions sequentially with options formatted as radio buttons, allowing students to navigate using "Next" and "Previous" buttons.
* **FR-QE-02: Response State Buffering**
  * *Description:* Selected options shall be stored in an in-memory hash map (`user_answers[question_id] = option`). Switching questions or returning to previous questions shall preserve the student's selections without loss.
* **FR-QE-03: Clear Answer Capability**
  * *Description:* A "Clear Answer" button shall allow students to deselect their choice for the current question and purge the corresponding key from the memory buffer.
* **FR-QE-04: Non-Blocking Countdown Timer**
  * *Description:* A real-time countdown timer shall display remaining minutes and seconds (`MM:SS`). The timer ticks every $1,000\text{ ms}$ via the event loop (`after()` handler) without blocking UI interactivity.
* **FR-QE-05: Automated Expiry Submission**
  * *Description:* When the timer reaches `00:00`, the system shall automatically trigger the submission pipeline, disabling input controls and submitting all recorded answers.

### 3.5 Module 5: Zero-Latency Submission & Automated Grading Engine
* **FR-AG-01: Submission Debounce Lock (Poka-Yoke)**
  * *Description:* When submission is initiated (manually or via timer expiry), the system shall immediately disable the "Submit" button and cancel active timer callbacks to prevent duplicate submissions.
* **FR-AG-02: Instant In-Memory Auto-Grading**
  * *Description:* The grading engine shall compare the buffered student answers against the preloaded correct option keys in memory.
  * *Performance Constraint:* The entire grading calculation for up to 100 questions shall complete in under $1.0\text{ ms}$.
* **FR-AG-03: Score & Status Computation**
  * *Description:* The engine shall compute:
    $$\text{Percentage} = \left(\frac{\sum \text{Scored Marks}}{\sum \text{Total Marks}}\right) \times 100$$
    If $\text{Percentage} \ge \text{Pass Percentage}$, status is set to `"Passed"`; otherwise `"Failed"`.
* **FR-AG-04: Instantaneous Scorecard Display**
  * *Description:* The UI shall transition to the scorecard screen within $< 20\text{ ms}$, displaying the student's score, percentage, outcome status, and a detailed question-by-question breakdown table with correct keys and marks earned.
* **FR-AG-05: Decoupled Database Persistence**
  * *Description:* The attempt record shall be committed to the SQLite `attempts` table without stalling the display of the scorecard.

### 3.6 Module 6: Student Gradebook & Historical Results
* **FR-GB-01: Historical Records View**
  * *Description:* The system shall provide an administrative table displaying all historical student attempts, including timestamp, student name, roll number, quiz title, score, total marks, percentage, and pass/fail outcome.
* **FR-GB-02: Summary Statistical Metrics**
  * *Description:* The gradebook shall dynamically calculate and display total attempts, count of passed students, and aggregate pass rate percentage.

### 3.7 Module 7: TQM Defect Logging & SQC Checksheets
* **FR-TQ-01: Persistent Defect Checksheet**
  * *Description:* The system shall maintain an audit trail table (`defect_logs`) storing all quality defects, categorized by type (Input Validation, Response Latency, Database Consistency, UI Usability, Grading Logic).
* **FR-TQ-02: Poka-Yoke Automatic Logging**
  * *Description:* When a user triggers an input validation constraint (e.g., attempting quiz start without roll number), the system shall automatically insert an audit record into `defect_logs` marked as resolved.
* **FR-TQ-03: Manual Defect Recording Interface**
  * *Description:* Instructors and TQM auditors shall be able to log manual defects, assign severity ratings (Low, Medium, High, Critical), and update resolution status (Open, In Progress, Resolved) to support the Deming PDCA cycle.

### 3.8 Module 8: Dual Execution Architecture (GUI & CLI)
* **FR-DE-01: Terminal CLI Fallback**
  * *Description:* If invoked with `--cli` or when Tkinter graphical libraries are absent, the application shall launch an interactive menu-driven console interface supporting all student and administrative functions.

---

## 4.0 Non-Functional Requirements (NFRs)

### 4.1 Latency & Real-Time Performance Thresholds
* **NFR-LAT-01 (Submission-to-Display Latency):** The total elapsed time between user submission confirmation (or timer expiry) and the visual presentation of the scorecard on screen shall not exceed **100 milliseconds** (Target: $< 20\text{ ms}$ on standard desktop hardware).
* **NFR-LAT-02 (Grading Algorithm Latency):** In-memory answer matching and score computation shall execute in $< 1\text{ ms}$ for quizzes up to 100 questions.
* **NFR-LAT-03 (Database Commit Latency):** Individual transaction writes into SQLite `attempts` shall complete within $< 15\text{ ms}$ using Write-Ahead Logging (WAL).
* **NFR-LAT-04 (UI Responsiveness):** Frame dispatch and question navigation transitions shall maintain 60 FPS (latency $< 16.6\text{ ms}$ per navigation click).

### 4.2 Throughput & Capacity
* **NFR-TP-01:** The local database shall support storage of at least $10,000$ quiz attempts and $1,000$ questions without performance degradation in retrieval queries.
* **NFR-TP-02:** Startup time of the application shall be $< 1.5\text{ seconds}$ from terminal command execution to initial screen render.

### 4.3 Reliability, Availability & Fault Tolerance
* **NFR-REL-01 (Zero Data Loss Guarantee):** Any completed quiz submission that has reached the grading engine must be recorded to the database. If an unexpected shutdown occurs during UI render, the data remains committed.
* **NFR-REL-02 (Graceful Degradation):** Absence of the graphical X11/Tkinter subsystem shall not crash the application; it shall immediately switch to CLI mode.
* **NFR-REL-03 (Timer Precision):** The countdown timer drift shall not exceed $\pm 1\text{ second}$ over a 60-minute examination period.

### 4.4 Data Integrity & ACID Compliance
* **NFR-INT-01 (Atomicity & Durability):** All attempt writes and quiz creations are transactional. If a failure occurs mid-transaction, changes are fully rolled back.
* **NFR-INT-02 (Referential Integrity):** SQLite foreign key constraints (`PRAGMA foreign_keys = ON`) must be enforced on all question and attempt records.

### 4.5 Usability & Poka-Yoke Error Proofing
* **NFR-USA-01 (Mistake-Proofing):** Users must be blocked from submitting blank names or submitting identical forms twice.
* **NFR-USA-02 (Ergonomic UI Design):** All interactive buttons must have minimum padding of $6\text{ px}$, clear visual color coding (Blue for Navigation, Green for Success/Action, Red for Danger/Submit), and readable typography ($\ge 10\text{ pt}$ Helvetica).

### 4.6 Maintainability, Portability & Code Standards
* **NFR-MNT-01:** Source code shall adhere to PEP 8 formatting standards and modular file separation (`main.py`, `gui.py`, `database.py`).
* **NFR-MNT-02:** Zero external binary dependencies beyond Python standard libraries and standard Tk bindings.

---

## 5.0 Critical-to-Quality (CTQ) Parameters & Quality Standards

To operationalize the principles of Total Quality Management, requirements are mapped from the Voice of the Customer (VOC) to measurable CTQ metrics:

### 5.1 Voice of Customer (VOC) to CTQ Tree Translation

```
+───────────────────────+────────────────────────+──────────────────────────+──────────────────────────────+
| Voice of Customer     | Quality Need           | Critical-to-Quality (CTQ)| Measurable Operational Target|
| (Stakeholder VOC)     | (System Feature)       | Driver                   | & Specification Limit        |
+───────────────────────+────────────────────────+──────────────────────────+──────────────────────────────+
| "I hate waiting when  | Instantaneous Quiz     | Submission Response      | Measured Latency < 100 ms    |
| I click submit; the   | Submission Pipeline    | Latency                  | (Target: < 20 ms)            |
| system must not lag." |                        |                          | Zero UI freeze during submit |
+───────────────────────+────────────────────────+──────────────────────────+──────────────────────────────+
| "My test marks and    | Exact In-Memory        | Grading Accuracy &       | 100% Evaluation Accuracy     |
| percentage must be    | Evaluation Engine      | Score Calculation        | Defect Rate = 0 DPMO         |
| 100% accurate."       |                        | Precision                | Exact key comparison         |
+───────────────────────+────────────────────────+──────────────────────────+──────────────────────────────+
| "I shouldn't be able  | Poka-Yoke Validation   | Duplicate & Erroneous    | 0 duplicate attempts allowed |
| to accidentally submit| & Single-Submission    | Submission Prevention    | Single-submission lock active|
| twice or leave blanks"| Button Lock            |                          | Mandatory input enforcement  |
+───────────────────────+────────────────────────+──────────────────────────+──────────────────────────────+
| "I need to see which  | Comprehensive Result   | Information Completeness | 100% question breakdown      |
| questions I got wrong | Breakdown & Review     | & Transparency           | Correct key vs user choice   |
| immediately."         | Card                   |                          | Marks awarded per question   |
+───────────────────────+────────────────────────+──────────────────────────+──────────────────────────────+
| "The app must work    | Robust Dual Runtime    | Portability & Fault      | Zero fatal crashes on launch |
| even if graphics      | Architecture (Tkinter  | Tolerance                | Auto CLI fallback if Tkinter |
| libraries are missing"| + CLI fallback)        |                          | is absent                    |
+───────────────────────+────────────────────────+──────────────────────────+──────────────────────────────+
```

### 5.2 Six Sigma Quality Objectives
* **Defect Rate Target:** $< 3.4$ Defects Per Million Opportunities (DPMO) in score computation and submission queuing.
* **Process Capability ($C_{pk}$):** Submission response time process capability index $C_{pk} \ge 1.67$, ensuring the upper specification limit ($100\text{ ms}$) is continuously met.
* **Data Yield:** $100\%$ zero-loss yield for all submitted attempt records.

### 5.3 Poka-Yoke (Mistake-Proofing) Rules
1. **Rule 1 (Identity Gate):** Student Full Name and Roll Number input fields must contain non-whitespace characters before the quiz screen is rendered.
2. **Rule 2 (Empty Quiz Gate):** Quizzes with 0 questions cannot be launched; an informative warning modal is presented.
3. **Rule 3 (Option Integrity Gate):** Adding a question requires all 4 options and a valid correct option selection ($\in \{A, B, C, D\}$).
4. **Rule 4 (Debounce Gate):** Clicking the submit button immediately disables it, preventing double clicks and race conditions.

---

## 6.0 Software Dependencies & Environment Setup

### 6.1 Core Runtime & Tooling
* **Python Runtime:** Python 3.10.x, 3.11.x, 3.12.x, 3.13.x, or 3.14.x.
* **Operating System Shell:** Bash (Linux/macOS), PowerShell / Command Prompt (Windows).
* **Source Control:** Git 2.30+ and GitHub Desktop.
* **IDE:** Visual Studio Code with Python Extension.

### 6.2 Python Standard & Third-Party Libraries
The base system is designed intentionally with zero heavy third-party bloat to maximize execution speed and minimize dependency failure modes:

| Package / Module | Category | Minimum Version | Functional Purpose |
| :--- | :--- | :--- | :--- |
| `tkinter` / `tkinter.ttk` | Standard GUI | Python 3 built-in | Responsive GUI frontend, themed widgets, Treeviews |
| `sqlite3` | Database Engine | Python 3 built-in | ACID-compliant local relational persistence |
| `os`, `sys`, `datetime` | System Utilities | Python 3 built-in | Path resolution, CLI parsing, audit timestamps |
| `pandas` *(Review 4 extension)*| Data Analytics | 2.0+ (Optional) | SQC analysis and statistical calculations |
| `matplotlib` / `seaborn` *(Review 4)*| Charting | 3.7+ (Optional) | Generation of Pareto & Ishikawa Fishbone charts |

### 6.3 Installation & Configuration Verification

#### Linux / Ubuntu Environment Setup
```bash
# 1. Update package manager
sudo apt update

# 2. Install Python 3 and Tkinter graphical toolkit
sudo apt install -y python3 python3-tk python3-pip

# 3. Verify Python and Tkinter installation
python3 -c "import tkinter; print('Tkinter successfully loaded, version:', tkinter.TkVersion)"
python3 -c "import sqlite3; print('SQLite3 successfully loaded, version:', sqlite3.sqlite_version)"
```

#### Windows & macOS Setup
* Download and install the official Python 3 installer from [python.org](https://www.python.org/).
* Ensure the **"tcl/tk and IDLE"** checkbox is enabled during installation.

#### Launching the Application
```bash
# Graphical Mode (Primary)
python3 main.py

# Headless / Terminal Fallback Mode (CLI)
python3 main.py --cli
```

---

## 7.0 Document Approvals & Sign-Off

| Role | Name | Signature / Status | Date |
| :--- | :--- | :--- | :--- |
| **Lead Developer** | Krutika Agrawal (AU-24-5942) | *Submitted for Review 1* | October 2026 |
| **Course Instructor** | Faculty Evaluator (BBAT104) | *Pending Review 1 Viva* | October 2026 |
| **TQM Auditor** | Internal Quality Assurance | *Audited & Approved* | October 2026 |
