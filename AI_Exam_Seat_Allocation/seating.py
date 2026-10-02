"""Hall and seating-layout helpers shared by the app and CLI."""

import pandas as pd


def create_seats(number_of_halls=3, seats_per_hall=20, columns=4):
    """Create seat records such as A-R1-C1 for each configured hall."""
    if number_of_halls < 1 or seats_per_hall < 1 or columns < 1:
        raise ValueError("Hall count, seat count, and column count must be positive.")

    seats = []
    for hall_index in range(number_of_halls):
        hall_code = chr(ord("A") + hall_index)
        for seat_number in range(seats_per_hall):
            row_number = seat_number // columns + 1
            column_number = seat_number % columns + 1
            seats.append(
                {
                    "seat_id": f"{hall_code}-R{row_number}-C{column_number}",
                    "hall": f"Hall {hall_code}",
                    "hall_code": hall_code,
                    "row": row_number,
                    "column": column_number,
                }
            )
    return seats


def build_hall_tables(assignments, seats, students):
    """Return a row-by-column DataFrame for each hall."""
    student_by_id = {student["student_id"]: student for student in students}
    hall_seats = {}
    for seat in seats:
        hall_seats.setdefault(seat["hall"], []).append(seat)

    hall_tables = {}
    for hall_name, hall_seat_list in hall_seats.items():
        row_count = max(seat["row"] for seat in hall_seat_list)
        column_count = max(seat["column"] for seat in hall_seat_list)
        rows = [["(empty)" for _ in range(column_count)] for _ in range(row_count)]

        for seat in hall_seat_list:
            student_id = next(
                (
                    assigned_id
                    for assigned_id, assigned_seat in assignments.items()
                    if assigned_seat == seat["seat_id"]
                ),
                None,
            )
            if student_id is not None:
                student = student_by_id[student_id]
                rows[seat["row"] - 1][seat["column"] - 1] = (
                    f"{student_id} - {student['name']}"
                )

        table = pd.DataFrame(
            rows,
            index=[f"Row {row_number}" for row_number in range(1, row_count + 1)],
            columns=[f"Column {column_number}" for column_number in range(1, column_count + 1)],
        )
        table.index.name = "Seat row"
        hall_tables[hall_name] = table

    return hall_tables


def calculate_statistics(assignments, students, seats):
    """Count used seats, adjacent soft-constraint violations, and hall totals."""
    student_by_id = {student["student_id"]: student for student in students}
    seat_by_id = {seat["seat_id"]: seat for seat in seats}
    seat_to_student = {
        seat_id: student_by_id[student_id]
        for student_id, seat_id in assignments.items()
    }
    same_department_pairs = 0
    same_section_pairs = 0

    # Check only the right and lower neighbor so every adjacent pair is counted once.
    for seat_id, student in seat_to_student.items():
        seat = seat_by_id[seat_id]
        for row_step, column_step in ((0, 1), (1, 0)):
            neighbor_id = (
                f"{seat['hall_code']}-R{seat['row'] + row_step}-"
                f"C{seat['column'] + column_step}"
            )
            neighbor = seat_to_student.get(neighbor_id)
            if neighbor is None:
                continue
            if student["department"] == neighbor["department"]:
                same_department_pairs += 1
            if student["section"] == neighbor["section"]:
                same_section_pairs += 1

    hall_counts = {hall_name: 0 for hall_name in dict.fromkeys(seat["hall"] for seat in seats)}
    for seat_id in assignments.values():
        hall_counts[seat_by_id[seat_id]["hall"]] += 1

    return {
        "total_students_assigned": len(assignments),
        "total_seats_used": len(set(assignments.values())),
        "same_department_adjacent_pairs": same_department_pairs,
        "same_section_adjacent_pairs": same_section_pairs,
        "hall_counts": hall_counts,
    }


def create_export_dataframe(assignments, students, seats):
    """Create a detailed one-row-per-seat table for CSV and Excel downloads."""
    student_by_id = {student["student_id"]: student for student in students}
    rows = []
    for seat in seats:
        student_id = next(
            (
                assigned_id
                for assigned_id, assigned_seat in assignments.items()
                if assigned_seat == seat["seat_id"]
            ),
            "",
        )
        student = student_by_id.get(student_id, {})
        rows.append(
            {
                "hall": seat["hall"],
                "seat_id": seat["seat_id"],
                "row": seat["row"],
                "column": seat["column"],
                "student_id": student_id,
                "name": student.get("name", ""),
                "department": student.get("department", ""),
                "year": student.get("year", ""),
                "section": student.get("section", ""),
                "exam_subject": student.get("exam_subject", ""),
            }
        )
    return pd.DataFrame(rows)
