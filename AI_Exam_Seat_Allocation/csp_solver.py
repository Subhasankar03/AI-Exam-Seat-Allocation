"""A beginner-friendly CSP solver for examination seating."""

from collections import Counter


REQUIRED_COLUMNS = [
    "student_id",
    "name",
    "department",
    "year",
    "section",
    "exam_subject",
]
VALID_DEPARTMENTS = {"AI&DS", "CSE", "ECE"}
VALID_YEARS = {"1", "2", "3"}
VALID_SECTIONS = {"A", "B"}


def validate_students(dataframe):
    """Check the uploaded table and return clean student dictionaries."""
    if dataframe is None or dataframe.empty:
        raise ValueError("The student CSV is empty. Add at least one student.")

    students_frame = dataframe.copy()
    students_frame.columns = [str(column).strip() for column in students_frame.columns]
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in students_frame.columns
    ]
    if missing_columns:
        raise ValueError(
            "Missing required CSV column(s): " + ", ".join(missing_columns)
        )

    students = []
    for row_number, row in enumerate(
        students_frame[REQUIRED_COLUMNS].to_dict(orient="records"), start=2
    ):
        student = {}
        for column in REQUIRED_COLUMNS:
            value = row[column]
            if value is None:
                value = ""
            else:
                try:
                    if value != value:  # Handles pandas NaN without extra dependencies.
                        value = ""
                except TypeError:
                    pass
            student[column] = str(value).strip()

        if not student["student_id"]:
            raise ValueError(f"A student_id is missing on CSV row {row_number}.")
        if not student["name"]:
            raise ValueError(f"A student name is missing on CSV row {row_number}.")
        if student["department"] not in VALID_DEPARTMENTS:
            raise ValueError(
                f"Invalid department on CSV row {row_number}: "
                f"{student['department']}. Use AI&DS, CSE, or ECE."
            )
        if student["year"] not in VALID_YEARS:
            raise ValueError(
                f"Invalid year on CSV row {row_number}: {student['year']}. "
                "Use 1, 2, or 3."
            )
        if student["section"] not in VALID_SECTIONS:
            raise ValueError(
                f"Invalid section on CSV row {row_number}: {student['section']}. "
                "Use A or B."
            )
        if not student["exam_subject"]:
            raise ValueError(f"An exam_subject is missing on CSV row {row_number}.")
        students.append(student)

    student_ids = [student["student_id"] for student in students]
    duplicate_ids = sorted(
        student_id
        for student_id, count in Counter(student_ids).items()
        if count > 1
    )
    if duplicate_ids:
        raise ValueError("Duplicate student_id value(s): " + ", ".join(duplicate_ids))

    return students


def _count_same_department_in_hall(student, seat, seat_to_student, seat_details):
    """Return how many already assigned students from this department share a hall."""
    count = 0
    for assigned_seat_id, assigned_student in seat_to_student.items():
        if (
            seat_details[assigned_seat_id]["hall"] == seat["hall"]
            and assigned_student["department"] == student["department"]
        ):
            count += 1
    return count


def solve_seating(students, seats):
    """Assign every student a unique seat using recursive backtracking.

    The hard constraint is unique seat use. Soft constraints are used to rank
    candidates: avoid same-department and same-section neighbors, then spread
    each department across halls where possible.
    """
    if not students:
        raise ValueError("There are no students to allocate.")
    if len(students) > len(seats):
        raise ValueError(
            f"There are {len(students)} students but only {len(seats)} seats."
        )

    seat_ids = [seat["seat_id"] for seat in seats]
    if len(seat_ids) != len(set(seat_ids)):
        raise ValueError("Seat identifiers must be unique.")

    seat_details = {seat["seat_id"]: seat for seat in seats}
    neighbor_map = {seat_id: [] for seat_id in seat_ids}
    for first_seat in seats:
        for second_seat in seats:
            same_hall = first_seat["hall"] == second_seat["hall"]
            distance = abs(first_seat["row"] - second_seat["row"]) + abs(
                first_seat["column"] - second_seat["column"]
            )
            if same_hall and distance == 1:
                neighbor_map[first_seat["seat_id"]].append(second_seat["seat_id"])

    student_by_id = {student["student_id"]: student for student in students}
    original_order = {
        student["student_id"]: index for index, student in enumerate(students)
    }
    assignments = {}
    seat_to_student = {}
    initial_domains = {
        student["student_id"]: set(seat_ids) for student in students
    }

    def choose_student(unassigned_ids, domains):
        """Use MRV; break ties by handling the largest remaining department first."""
        department_counts = Counter(
            student_by_id[student_id]["department"]
            for student_id in unassigned_ids
        )
        return min(
            unassigned_ids,
            key=lambda student_id: (
                len(domains[student_id]),
                -department_counts[student_by_id[student_id]["department"]],
                original_order[student_id],
            ),
        )

    def candidate_score(student, seat_id):
        """Estimate the soft-constraint cost of placing this student here."""
        same_department_neighbors = 0
        same_section_neighbors = 0
        for neighbor_id in neighbor_map[seat_id]:
            neighbor_student = seat_to_student.get(neighbor_id)
            if neighbor_student is None:
                continue
            if neighbor_student["department"] == student["department"]:
                same_department_neighbors += 1
            if neighbor_student["section"] == student["section"]:
                same_section_neighbors += 1

        hall_department_count = _count_same_department_in_hall(
            student, seat_details[seat_id], seat_to_student, seat_details
        )
        return (
            5 * same_department_neighbors
            + 3 * same_section_neighbors
            + 0.5 * hall_department_count
        )

    def backtrack(unassigned_ids, domains):
        """Try assignments recursively and undo a choice if it blocks the search."""
        if not unassigned_ids:
            return True

        student_id = choose_student(unassigned_ids, domains)
        student = student_by_id[student_id]
        available_seats = list(domains[student_id])

        # Soft propagation: try non-neighbor seats first for the same department.
        # Keep neighboring seats as fallbacks so this preference never blocks a solution.
        non_neighbor_seats = [
            seat_id
            for seat_id in available_seats
            if all(
                neighbor_id not in seat_to_student
                or seat_to_student[neighbor_id]["department"] != student["department"]
                for neighbor_id in neighbor_map[seat_id]
            )
        ]
        if non_neighbor_seats:
            available_seats = non_neighbor_seats

        available_seats.sort(
            key=lambda seat_id: (
                candidate_score(student, seat_id),
                seat_ids.index(seat_id),
            )
        )

        for seat_id in available_seats:
            # Hard check: a seat is valid only if no other student already uses it.
            if seat_id not in domains[student_id] or seat_id in seat_to_student:
                continue

            assignments[student_id] = seat_id
            seat_to_student[seat_id] = student

            # Constraint propagation: remove this seat from every remaining domain.
            # A domain becoming empty means the current choice cannot lead to a solution.
            next_unassigned = [
                other_id for other_id in unassigned_ids if other_id != student_id
            ]
            next_domains = {}
            domains_are_valid = True
            for other_id in next_unassigned:
                next_domains[other_id] = domains[other_id] - {seat_id}
                if not next_domains[other_id]:
                    domains_are_valid = False
                    break

            if domains_are_valid and backtrack(next_unassigned, next_domains):
                return True

            # This branch failed, so undo the assignment and try the next seat.
            del assignments[student_id]
            del seat_to_student[seat_id]

        return False

    student_ids = [student["student_id"] for student in students]
    if not backtrack(student_ids, initial_domains):
        return None
    return assignments
