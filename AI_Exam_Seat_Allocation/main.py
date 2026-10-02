"""Command-line demonstration of the CSP exam seating solver."""

from pathlib import Path

import pandas as pd

from csp_solver import solve_seating, validate_students
from seating import build_hall_tables, calculate_statistics, create_seats


def main():
    """Load the sample input, allocate seats, and print the result."""
    project_folder = Path(__file__).resolve().parent
    student_file = project_folder / "data" / "students.csv"

    try:
        students = validate_students(pd.read_csv(student_file))
        seats = create_seats(number_of_halls=3, seats_per_hall=20)
        assignments = solve_seating(students, seats)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as error:
        print(f"Could not generate the seating arrangement: {error}")
        return

    if assignments is None:
        print("No valid seating arrangement was found.")
        return

    print("AI-Based Intelligent Exam Hall Seat Allocation System")
    print(f"Students: {len(students)} | Available seats: {len(seats)}")
    for hall_name, hall_table in build_hall_tables(assignments, seats, students).items():
        print(f"\n{hall_name.upper()}")
        print(hall_table.to_string())

    statistics = calculate_statistics(assignments, students, seats)
    print("\nConstraint statistics")
    print(f"Students assigned: {statistics['total_students_assigned']}")
    print(f"Seats used: {statistics['total_seats_used']}")
    print(
        "Same-department adjacent pairs: "
        f"{statistics['same_department_adjacent_pairs']}"
    )
    print(f"Same-section adjacent pairs: {statistics['same_section_adjacent_pairs']}")
    print("Students in each hall:")
    for hall_name, count in statistics["hall_counts"].items():
        print(f"  {hall_name}: {count}")


if __name__ == "__main__":
    main()
