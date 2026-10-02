"""
Main Entry Point for Online Quiz System
Course: BBAT104 - Fundamentals of Total Quality Management
Registration: AU-24-5942
"""

import sys
import os
import database

def run_cli_mode():
    """Fallback interactive CLI mode if graphical display / Tkinter is unavailable."""
    print("=" * 60)
    print("      ONLINE QUIZ SYSTEM (CLI TEST RUNNER)")
    print("      BBAT104: Fundamentals of TQM | Reg. AU-24-5942")
    print("=" * 60)

    database.init_db()

    while True:
        print("\nMain Menu:")
        print("1. Take a Quiz (Student)")
        print("2. List All Quizzes & Questions (CRUD Read)")
        print("3. Add New Quiz (CRUD Create)")
        print("4. View Student Result History")
        print("5. View TQM Defect Log & Checksheet")
        print("6. Exit")

        choice = input("\nEnter choice (1-6): ").strip()

        if choice == "1":
            quizzes = database.get_all_quizzes()
            if not quizzes:
                print("No quizzes available.")
                continue
            print("\nAvailable Quizzes:")
            for idx, q in enumerate(quizzes, 1):
                print(f"[{idx}] {q['title']} (Time: {q['time_limit_mins']} mins, Pass: {q['pass_percentage']}%)")
            
            try:
                q_idx = int(input("Select quiz number: ").strip()) - 1
                selected_quiz = quizzes[q_idx]
            except (ValueError, IndexError):
                print("Invalid selection.")
                continue

            name = input("Enter Student Name: ").strip() or "Anonymous Student"
            roll = input("Enter Roll Number: ").strip() or "AU-24-5942"

            questions = database.get_questions_by_quiz(selected_quiz["id"])
            if not questions:
                print("No questions found for this quiz.")
                continue

            score = 0
            total_marks = 0

            print(f"\n--- Starting Quiz: {selected_quiz['title']} ---")
            for i, q in enumerate(questions, 1):
                total_marks += q["marks"]
                print(f"\nQ{i}: {q['question_text']} [Marks: {q['marks']}]")
                print(f"  A) {q['option_a']}")
                print(f"  B) {q['option_b']}")
                print(f"  C) {q['option_c']}")
                print(f"  D) {q['option_d']}")
                
                ans = input("Your answer (A/B/C/D): ").strip().upper()
                if ans == q["correct_option"]:
                    print("✓ Correct!")
                    score += q["marks"]
                else:
                    print(f"✗ Incorrect. Correct answer was {q['correct_option']}.")

            percentage = round((score / total_marks * 100) if total_marks > 0 else 0, 2)
            status = "Passed" if percentage >= selected_quiz["pass_percentage"] else "Failed"

            database.save_attempt(name, roll, selected_quiz["id"], score, total_marks, percentage, status)
            print("\n" + "=" * 40)
            print(f"RESULTS FOR {name} ({roll}):")
            print(f"Score: {score} / {total_marks} ({percentage}%)")
            print(f"Status: {status.upper()}")
            print("=" * 40)

        elif choice == "2":
            quizzes = database.get_all_quizzes()
            print("\n--- All Quizzes in SQLite Database ---")
            for q in quizzes:
                print(f"\n[ID {q['id']}] {q['title']}")
                print(f"    Description: {q['description']}")
                print(f"    Time: {q['time_limit_mins']} mins | Pass: {q['pass_percentage']}% | Total Questions: {q['question_count']}")
                qs = database.get_questions_by_quiz(q["id"])
                for i, qu in enumerate(qs, 1):
                    print(f"      {i}. {qu['question_text']} -> Key: {qu['correct_option']}")

        elif choice == "3":
            print("\n--- Add New Quiz ---")
            title = input("Quiz Title: ").strip()
            if not title:
                print("Title cannot be empty.")
                continue
            desc = input("Description: ").strip()
            time_mins = input("Time Limit in minutes (default 10): ").strip() or "10"
            pass_p = input("Pass Percentage (default 50.0): ").strip() or "50.0"
            
            try:
                new_id = database.create_quiz(title, desc, int(time_mins), float(pass_p))
                print(f"Quiz created successfully with ID: {new_id}!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "4":
            attempts = database.get_all_attempts()
            print("\n--- Student Result Records ---")
            if not attempts:
                print("No attempts recorded yet.")
            else:
                for a in attempts:
                    print(f"[{a['completed_at']}] {a['student_name']} ({a['student_roll']}) - {a['quiz_title']}: {a['score']}/{a['total_marks']} ({a['percentage']}%) -> {a['status']}")

        elif choice == "5":
            defects = database.get_all_defects()
            print("\n--- TQM Checksheet & Defect Log ---")
            for d in defects:
                print(f"[{d['logged_at']}] [{d['severity']}] {d['category']}: {d['description']} (Status: {d['status']})")

        elif choice == "6":
            print("\nExiting. Thank you!")
            break
        else:
            print("Invalid selection. Please choose 1-6.")

def main():
    if "--cli" in sys.argv:
        run_cli_mode()
        return

    try:
        import tkinter
        from gui import run_app
        print("Launching Tkinter Graphical Interface...")
        run_app()
    except ModuleNotFoundError as e:
        if "tkinter" in str(e):
            print("\n" + "!" * 65)
            print("NOTICE: 'tkinter' is not yet installed on this Ubuntu system.")
            print("To enable the graphical interface, run this command in your terminal:")
            print("\n    sudo apt update && sudo apt install -y python3-tk\n")
            print("In the meantime, launching CLI mode so you can test all features right now.")
            print("!" * 65 + "\n")
            run_cli_mode()
        else:
            raise e

if __name__ == "__main__":
    main()
