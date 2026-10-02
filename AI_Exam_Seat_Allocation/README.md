# AI-Based Intelligent Exam Hall Seat Allocation System Using Constraint Satisfaction

## Problem Statement
Manually assigning students to examination seats takes time and can place students from the same department or section next to one another. This project creates a valid seating plan automatically while respecting seat capacity and reducing those undesirable adjacencies.

## Objective
Build a small, explainable Artificial Intelligence system that assigns each student one seat in one of three examination halls. The project uses a Constraint Satisfaction Problem (CSP), constraint propagation, and recursive backtracking. It does not use machine learning or deep learning.

## AI Techniques Used
- Constraint Satisfaction Problem formulation
- Constraint propagation through student seat domains
- Recursive backtracking search
- Minimum Remaining Values (MRV) variable selection
- Heuristic candidate ordering for soft-constraint optimization

## CSP Formulation

### Variables
Each student is a variable. For the sample input there are 60 student variables.

### Domains
A student's initial domain contains every configured seat, for example `A-R1-C1`. After a seat is assigned, that seat is removed from the domains of all unassigned students.

### Hard Constraints
- A seat can contain only one student.
- A student can be assigned only one seat.
- Assignments must use seats created for the configured halls.
- The number of students must not exceed the total seat capacity.

### Soft Constraints
- Avoid adjacent students from the same department.
- Avoid adjacent students from the same section.
- Spread students from each department across halls where possible.

The solver always protects the hard constraints. It ranks seat choices by the new same-department and same-section adjacency cost, then by how many students of the same department are already in that hall. Soft preferences never remove a student's last possible seat, so they cannot make an otherwise valid allocation fail. The heuristic seeks a lower-cost result but does not claim a mathematical proof of global optimality.

## Backtracking Algorithm
1. Select an unassigned student using MRV; break ties by prioritizing the largest remaining department group.
2. List that student's available seats and rank them by their soft-constraint cost.
3. Check the hard rule that the selected seat is still available.
4. Assign the student and remove the seat from all other domains (forward checking).
5. Recursively try to assign the remaining students.
6. If a branch cannot continue, undo the assignment and try the next seat.
7. Stop when all students have been assigned, or report that no solution was found.

## Constraint Propagation
The solver propagates the all-different seat constraint by removing each chosen seat from every unassigned student's domain. It also tries seats with no already-assigned same-department neighbor first. This neighbor rule is a soft preference: neighboring seats remain as fallbacks so that the search stays complete.

## Project Modules
- `data/students.csv`: 60 sample student records.
- `csp_solver.py`: input validation, CSP domains, heuristic ordering, and recursive backtracking.
- `seating.py`: hall seat creation, seating-grid tables, statistics, and export table.
- `app.py`: Streamlit interface, file upload, visual tables, statistics, and downloads.
- `main.py`: command-line demonstration using the included sample file.

## Installation
Open a VS Code terminal in the `AI_Exam_Seat_Allocation` folder and run:

```powershell
python -m pip install -r requirements.txt
```

## How to Run
Run the Streamlit interface:

```powershell
streamlit run app.py
```

Run the command-line version:

```powershell
python main.py
```

The included sample uses three halls with 20 seats each. In the web app, the sidebar can change the number of halls and seats per hall or accept another CSV with the same required columns.

## Sample Input
The CSV must contain these columns:

```csv
student_id,name,department,year,section,exam_subject
STU001,Aarav Sharma,AI&DS,1,A,Artificial Intelligence
STU002,Ananya Iyer,CSE,2,B,Data Structures
```

Departments must be `AI&DS`, `CSE`, or `ECE`; years must be `1`, `2`, or `3`; and sections must be `A` or `B`. Student IDs must be unique.

## Sample Output
The command-line program prints one table per hall, followed by allocation statistics. With the supplied data and default settings, all 60 students fit in the 60 seats:

```text
HALL A
         Column 1          Column 2          Column 3          Column 4
Row 1    STU001 - ...      STU002 - ...      STU003 - ...      STU004 - ...
...
Constraint statistics
Students assigned: 60
Seats used: 60
Students in each hall:
  Hall A: 20
  Hall B: 20
  Hall C: 20
```

Exact adjacency counts depend on the heuristic and the input order. The Streamlit page also provides downloadable CSV and Excel workbooks.

## Error Handling
The application displays understandable errors for empty input, missing columns, duplicate IDs, invalid department/year/section values, and more students than available seats. Empty names and exam subjects are also rejected.

## Future Enhancements
- Add locked seats, accessibility requirements, and invigilator zones.
- Add exam-subject separation as another soft or hard constraint.
- Compare multiple search heuristics and show their scores.
- Save generated plans and allow administrators to edit or lock assignments.
