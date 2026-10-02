"""Streamlit interface for the exam hall seat allocation project."""

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from csp_solver import solve_seating, validate_students
from seating import (
    build_hall_tables,
    calculate_statistics,
    create_export_dataframe,
    create_seats,
)


st.set_page_config(page_title="Exam Seat Allocation", layout="wide")
st.title("AI-Based Intelligent Exam Hall Seat Allocation System")
st.caption("Constraint Satisfaction Problem (CSP) with recursive backtracking")

with st.sidebar:
    st.header("Allocation settings")
    number_of_halls = st.number_input("Number of halls", min_value=1, max_value=6, value=3)
    seats_per_hall = st.number_input(
        "Seats per hall", min_value=1, max_value=40, value=20
    )
    uploaded_file = st.file_uploader("Upload students.csv", type=["csv"])
    generate_button = st.button(
        "Generate Seating Arrangement", type="primary", use_container_width=True
    )

sample_path = Path(__file__).resolve().parent / "data" / "students.csv"
try:
    if uploaded_file is None:
        source_frame = pd.read_csv(sample_path)
        st.info("Using the included sample file. Upload another CSV from the sidebar to replace it.")
    else:
        source_frame = pd.read_csv(uploaded_file)
    students = validate_students(source_frame)
except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as error:
    students = []
    st.error(str(error))

seats = create_seats(int(number_of_halls), int(seats_per_hall))
col_students, col_seats, col_capacity = st.columns(3)
col_students.metric("Students", len(students))
col_seats.metric("Available seats", len(seats))
col_capacity.metric("Capacity check", "Sufficient" if len(students) <= len(seats) else "Not enough seats")

if generate_button and students:
    try:
        assignments = solve_seating(students, seats)
        if assignments is None:
            st.session_state.pop("allocation", None)
            st.error("No valid arrangement was found with the current hall settings.")
        else:
            st.session_state["allocation"] = {
                "assignments": assignments,
                "students": students,
                "seats": seats,
            }
    except ValueError as error:
        st.session_state.pop("allocation", None)
        st.error(str(error))

allocation = st.session_state.get("allocation")
if allocation:
    assignments = allocation["assignments"]
    allocated_students = allocation["students"]
    allocated_seats = allocation["seats"]
    st.success("A valid seating arrangement was found.")

    hall_tables = build_hall_tables(assignments, allocated_seats, allocated_students)
    for hall_name, hall_table in hall_tables.items():
        st.subheader(hall_name.upper())
        st.table(hall_table)

    statistics = calculate_statistics(assignments, allocated_students, allocated_seats)
    st.subheader("Constraint statistics")
    stat_columns = st.columns(4)
    stat_columns[0].metric("Students assigned", statistics["total_students_assigned"])
    stat_columns[1].metric("Seats used", statistics["total_seats_used"])
    stat_columns[2].metric(
        "Same-department adjacent pairs",
        statistics["same_department_adjacent_pairs"],
    )
    stat_columns[3].metric(
        "Same-section adjacent pairs", statistics["same_section_adjacent_pairs"]
    )
    st.write("Students in each hall")
    st.dataframe(
        pd.DataFrame(
            list(statistics["hall_counts"].items()),
            columns=["Hall", "Students"],
        ),
        hide_index=True,
        use_container_width=True,
    )

    export_frame = create_export_dataframe(
        assignments, allocated_students, allocated_seats
    )
    csv_bytes = export_frame.to_csv(index=False).encode("utf-8")
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        export_frame.to_excel(writer, index=False, sheet_name="Seat Allocation")

    download_columns = st.columns(2)
    download_columns[0].download_button(
        "Download CSV",
        data=csv_bytes,
        file_name="exam_seat_allocation.csv",
        mime="text/csv",
    )
    download_columns[1].download_button(
        "Download Excel",
        data=excel_buffer.getvalue(),
        file_name="exam_seat_allocation.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
