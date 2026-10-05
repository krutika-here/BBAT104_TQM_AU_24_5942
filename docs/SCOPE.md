# Project Scope Definition & Governance Document

**Project Title:** Online Quiz System  
**Course Code:** BBAT104 – Fundamentals of Total Quality Management (TQM)  
**Academic Session:** 2026–27  
**Candidate Name:** Krutika Agrawal  
**Roll / Registration Number:** AU-24-5942  
**Assigned Digit & Baseline System:** Digit 9 – Online Quiz System  
**Assigned Quality Goal:** Ensure zero latency during submissions & auto-grading  
**Document Revision:** 1.0 (Review 1 Deliverable – Scope Definition)  

---

## 1.0 Executive Scope Summary

The objective of the **Online Quiz System** project is to design, develop, and benchmark an automated computer-based assessment system that enforces Total Quality Management (TQM) principles across all stages of execution. 

A primary failure mode in modern computer-based examination platforms is **submission latency**—the noticeable lag, buffering, or screen freezing that occurs when candidates submit their examination papers. Under high traffic or unoptimized database operations, latency triggers student anxiety, duplicate submissions, server race conditions, and corrupted attempts.

This project defines clear architectural and functional boundaries to address this defect head-on:
1. Deliver a fully functioning, locally hosted, high-speed testing application.
2. Implement **zero-latency submission handling** ($< 20\text{ ms}$ perceived turnaround) via in-memory caching and decoupled asynchronous persistence.
3. Apply rigorous Statistical Quality Control (SQC) tools, defect tracking checksheets, Failure Mode and Effects Analysis (FMEA), and Deming Plan-Do-Check-Act (PDCA) continuous improvement cycles.

---

## 2.0 In-Scope System Capabilities

The following capabilities, modules, and features fall strictly within the implementation boundary of the project:

### 2.1 Core CRUD Operations
* **Quizzes CRUD:**
  * **Create:** Add new quiz titles, descriptions, configurable time limits (in minutes), and passing cutoff percentages.
  * **Read:** Display all existing quizzes in an interactive, formatted table alongside question counts and parameters.
  * **Update:** Modify quiz metadata, duration, or passing standards.
  * **Delete:** Remove obsolete quizzes with cascade deletion of related questions to eliminate orphaned database records.
* **Questions CRUD:**
  * **Create:** Add multiple-choice questions (MCQs) with four options (A, B, C, D), designated correct answer key, and custom mark allocation.
  * **Read:** Filter and list questions dynamically by parent quiz ID.
  * **Update:** Edit question stems, choices, marks, or answer keys.
  * **Delete:** Remove individual questions from a quiz.

### 2.2 In-Memory Quiz Delivery & Live Countdown Engine
* **Pre-cached Question Ingestion:** Fetch all quiz data in a single read transaction upon quiz start and hold it in Python RAM memory structures (`list[dict]`).
* **Interactive Navigation:** Seamless next/previous question switching with instantaneous state persistence.
* **Option Selection & Deselection:** Direct radio button selection and "Clear Answer" functionality with immediate hash map updates.
* **Real-time Non-blocking Countdown Timer:** 1-second interval timer synchronized with the Tkinter event pump, featuring warning indicators and automated zero-latency submission on expiry (`00:00`).

### 2.3 Zero-Latency Submission & In-Memory Auto-Grading
* **Poka-Yoke Debounce Lock:** Immediate deactivation of the submission button upon trigger to prevent accidental duplicate submissions.
* **$O(1)$ Hash Map Answer Evaluation:** Evaluation of student choices against correct keys performed entirely in-memory within CPU registers (measured execution time $< 0.5\text{ ms}$).
* **Dynamic Score & Outcome Calculation:** Immediate generation of total marks, scored marks, percentage, and passing status (`Passed` / `Failed`).
* **Instant Scorecard Display:** Visual transition to the scorecard screen in $< 20\text{ ms}$ perceived latency, presenting a full question-by-question breakdown.
* **Asynchronous Persistence Queue:** Offloading of attempt records to SQLite storage without blocking the UI main thread.

### 2.4 Gradebook & Historical Performance Metrics
* **Student Results History:** Persistent logging of every attempt, capturing timestamp, student name, roll number, quiz title, score, total marks, percentage, and pass/fail status.
* **Administrative Analytics:** Dynamic summary statistics reporting total test attempts, number of passing candidates, and aggregate pass rate percentage.

### 2.5 TQM Defect Logging & SQC Checksheets
* **Live Defect Audit Trail:** Dedicated `defect_logs` SQLite table acting as a digital checksheet for tracking system defects and anomalies.
* **Poka-Yoke Defect Logging:** Automatic logging of validation failures (e.g., missing student identity) as resolved defects.
* **Manual Quality Event Logging:** Interactive UI panel enabling instructors and auditors to record category, description, severity (Low, Medium, High, Critical), and resolution status (Open, In Progress, Resolved).

### 2.6 Dual Execution Architecture
* **Graphical User Interface (GUI):** Modern, clean desktop application built using Python `tkinter` and `ttk` themed widgets.
* **Terminal CLI Fallback Runner:** Headless command-line interface (`main.py --cli`) ensuring 100% feature accessibility on non-GUI or remote terminal environments.

---

## 3.0 Out-of-Scope Capabilities (Explicit Boundaries)

To ensure high depth of execution, rigorous quality standards, and adherence to the BBAT104 academic timeline, the following capabilities are explicitly classified as **Out of Scope**:

```
+──────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────+
| Out-of-Scope Feature                                     | Technical & Pedagogical Justification                    |
+──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────+
| 1. Live Video / AI-Based Webcam Proctoring               | Requires heavyweight computer vision dependencies        |
|    (e.g., OpenCV, facial recognition, eye tracking)      | (OpenCV, PyTorch) that induce high CPU overhead, memory  |
|                                                          | thrashing, and directly violate the Zero-Latency SLA.    |
+──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────+
| 2. External LMS Integrations                             | Enterprise integrations require complex authentication   |
|    (e.g., Canvas, Moodle, Blackboard LTI 1.3)            | layers, OAuth2 handshakes, and remote API dependencies   |
|                                                          | that introduce uncontrolled network-induced delays.      |
+──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────+
| 3. Commercial Payment Gateways                           | The system is an educational assessment platform; billing|
|    (e.g., Stripe, PayPal, Razorpay)                      | logic, financial webhooks, and PCI-DSS compliance are     |
|                                                          | irrelevant to academic quiz evaluation.                  |
+──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────+
| 4. Multi-Tenant Cloud Microservices Infrastructure       | Distributed systems introduce network latency (REST/gRPC)|
|    (e.g., Kubernetes, Kafka, Distributed Sharding)       | that conflict with our local zero-latency quality goal.  |
|                                                          | Local SQLite3 with WAL mode delivers superior sub-10ms   |
|                                                          | transactional determinism.                               |
+──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────+
| 5. Subjective / Essay Long-Answer NLP Grading            | Natural Language Processing models (transformers) are    |
|                                                          | non-deterministic and computationally expensive, causing |
|                                                          | multi-second evaluation lag incompatible with instant    |
|                                                          | scorecard presentation.                                  |
+──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────+
| 6. Cryptographic Blockchain Credential Verification      | Excessive hashing overhead with zero added value for     |
|                                                          | internal college course quality audits.                  |
+──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────+
```

---

## 4.0 User Role Matrix & Access Control Policies

The system implements Role-Based Access Control (RBAC) to enforce separation of concerns, protect evaluation integrity, and prevent administrative errors.

### 4.1 Defined User Roles
1. **Student / Examinee:** Authorized to take quizzes, review active questions, navigate options, trigger submissions, and view immediate scorecards. Restricted from viewing answer keys prior to submission and from altering quiz content.
2. **Faculty / Course Instructor:** Authorized to manage quizzes and questions (full CRUD), configure passing thresholds, inspect student results, and review evaluation metrics.
3. **TQM Quality Auditor:** Evaluates system adherence to quality standards, inspects the defect checksheet, verifies Poka-Yoke error handling, and validates latency benchmarks.
4. **System Administrator:** Maintains database schema, resolves critical defects, and oversees environment configuration.

### 4.2 RBAC Permissions Matrix

| Functional Capability | Student | Faculty | TQM Auditor | System Admin |
| :--- | :---: | :---: | :---: | :---: |
| Access Student Quiz Portal | ✅ Permitted | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| Attempt & Submit Quiz | ✅ Permitted | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| View Immediate Personal Scorecard | ✅ Permitted | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| Create / Add New Quizzes | ❌ Denied | ✅ Permitted | 👁️ Read-Only | ✅ Permitted |
| Edit Existing Quiz Parameters | ❌ Denied | ✅ Permitted | 👁️ Read-Only | ✅ Permitted |
| Delete Quizzes (Cascade) | ❌ Denied | ✅ Permitted | ❌ Denied | ✅ Permitted |
| Add / Edit / Delete Questions | ❌ Denied | ✅ Permitted | 👁️ Read-Only | ✅ Permitted |
| View Global Student Results Gradebook | ❌ Denied | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| View TQM Defect Log & Checksheet | ❌ Denied | 👁️ Read-Only | ✅ Permitted | ✅ Permitted |
| Log / Update Quality Defects (PDCA) | ❌ Denied | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| Direct Database Schema Alterations | ❌ Denied | ❌ Denied | ❌ Denied | ✅ Permitted |

### 4.3 Poka-Yoke Access & Operational Protections
* **Answer Concealment Guard:** During an active quiz, the student UI only binds to question stems and options. The `correct_option` field is held securely in the engine's internal memory buffer and is never exposed in radio button metadata or labels until the submission event completes.
* **Accidental Loss Guard:** When an instructor triggers quiz deletion, the application presents a two-step confirmation dialogue explicitly warning that all child questions will be permanently deleted.
* **Identity Completeness Guard:** Students cannot start an assessment without non-empty Name and Roll Number entries.

---

## 5.0 Project Milestone & Review Roadmap

The development, quality auditing, and evaluation of this system are strictly aligned with the four progressive milestones of the **BBAT104 Evaluation Deliverables & Marking Scheme (70 Raw Marks)**:

```
+──────────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    BBAT104 TQM COURSE ROADMAP                                        |
+──────────────────────────────────────────────────────────────────────────────────────────────────────+
|  [ REVIEW 1: Setup & SRS ] ➔ CO1 (10 Marks) [CURRENT MILESTONE]                                      |
|  • GitHub Repository Initialization: `BBAT104_TQM_AU_24_5942`                                         |
|  • System Architecture Flowchart (`docs/ARCHITECTURE.md`) with Mermaid & ASCII flow diagrams         |
|  • Software Requirements Specification (`docs/SRS.md`) aligned with IEEE 830 & TQM principles        |
|  • Scope Definition Document (`docs/SCOPE.md`) with In-Scope/Out-of-Scope boundaries & RBAC Matrix   |
|  • Comprehensive Root README (`README.md`) with navigation and setup instructions                    |
+───────────────────────────────────────────────────┬──────────────────────────────────────────────────+
                                                    │
                                                    ▼
+──────────────────────────────────────────────────────────────────────────────────────────────────────+
|  [ REVIEW 2: Base System & CRUD ] ➔ CO1, CO2 (15 Marks)                                              |
|  • Fully functional base CRUD operations (Quizzes & Questions management)                            |
|  • Operational In-Memory Quiz Engine with Live Countdown Timer                                       |
|  • Execution of assigned 5 Quality Goal features (Zero Latency Submissions & Auto-Grading)           |
+───────────────────────────────────────────────────┬──────────────────────────────────────────────────+
                                                    │
                                                    ▼
+──────────────────────────────────────────────────────────────────────────────────────────────────────+
|  [ REVIEW 3: FMEA & Risk Audit ] ➔ CO2 (15 Marks)                                                    |
|  • Construction of Failure Mode and Effects Analysis (FMEA) Matrix with RPN calculations             |
|  • Process mapping using SIPOC (Suppliers, Inputs, Process, Outputs, Customers)                      |
|  • Critical-to-Quality (CTQ) Tree formulation and defect logging audits                              |
+───────────────────────────────────────────────────┬──────────────────────────────────────────────────+
                                                    │
                                                    ▼
+──────────────────────────────────────────────────────────────────────────────────────────────────────+
|  [ REVIEW 4: SQC & Continuous Improvement ] ➔ CO2, CO3 (15 Marks)                                    |
|  • Pareto Analysis (80/20 Rule) charting defect frequencies via Matplotlib                           |
|  • Ishikawa (Fishbone) Diagram for root-cause analysis (People, Process, Code, Infrastructure)       |
|  • Standardized Checksheets and Deming Plan-Do-Check-Act (PDCA) continuous improvement cycle log    |
+───────────────────────────────────────────────────┬──────────────────────────────────────────────────+
                                                    │
                                                    ▼
+──────────────────────────────────────────────────────────────────────────────────────────────────────+
|  [ FINAL REVIEW: Viva Defense & GitHub Health ] ➔ CO3 (15 Marks: 10 Viva + 5 GitHub Health)          |
|  • Live interactive software demonstration and bug-handling defense                                  |
|  • Viva voce on TQM tool selection and statistical analysis                                          |
|  • GitHub repository health verification (>= 30 meaningful commits, clean issue tracking)            |
+──────────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 6.0 Scope Change Control & Governance

Any proposed modification to the project boundaries defined in this document must undergo formal change evaluation:
1. **Impact Assessment:** Proposed changes must be analyzed for their effect on the **Zero-Latency SLA** ($< 100\text{ ms}$ threshold). Any feature adding blocking I/O to the submission path will be rejected.
2. **TQM Principle Alignment:** Additions must demonstrate compliance with at least one core TQM methodology (Poka-Yoke error prevention, Kaizen continuous improvement, or fact-based SQC decision-making).
3. **Audit Trail Documentation:** Approved changes shall be documented in the repository commit history and logged within the TQM defect/improvement register.

---

## 7.0 Document Approvals & Sign-Off

* **Project Author:** Krutika Agrawal (AU-24-5942)  
* **Course:** BBAT104 – Fundamentals of TQM  
* **Date:** October 2026  
* **Evaluation Status:** Submitted for Review 1 Review & Evaluation  
