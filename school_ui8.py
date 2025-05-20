import streamlit as st
import pyodbc
import smtplib
from datetime import datetime
from email.message import EmailMessage
import pandas as pd
import os

# DB connection setup
conn = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=tempdb;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

st.set_page_config(page_title="School Management System", layout="centered")
st.title("\U0001F3EB School Management System")

# Sidebar navigation
menu = st.sidebar.radio("\U0001F4C2 Select a Page", [
    "Add Class",
    "Add Parent & Student",
    "Mark Attendance",
    "Enter Term Marks",
    "View Summaries",
    "Send Email Report",
    "Delete Records"
])
# page 1 Add class------------

# Page: Add Class
if menu == "Add Class":
    st.header("\U0001F3EB Add Class")
    class_id = st.text_input("Class ID (integer)")
    grade = st.number_input("Grade (integer)", min_value=1, max_value=13, step=1)
    section = st.text_input("Section (e.g., A, B, C)")

    if st.button("Add Class"):
        if not class_id or not section:
            st.error("Please fill all fields.")
        else:
            try:
                # Ensure class_id is integer
                class_id_int = int(class_id)
                cursor.execute(
                    "INSERT INTO Class (ClassID, Grade, Section) VALUES (?, ?, ?)",
                    class_id_int, grade, section
                )
                conn.commit()
                st.success(f"Class '{grade} - {section}' added!")
            except pyodbc.IntegrityError as e:
                st.error(f"Integrity error: {e}")
            except ValueError:
                st.error("Class ID must be an integer.")
            except Exception as e:
                st.error(f"Error adding class: {e}")




# Page 2: Add Parent & Student
elif menu == "Add Parent & Student":
    st.header("\U0001F468‍\U0001F469‍\U0001F467 Add Parent")
    parent_id = st.text_input("Parent ID")
    parent_name = st.text_input("Parent Name")
    parent_email = st.text_input("Parent Email")
    parent_phone = st.text_input("Parent Phone")

    if st.button("Add Parent"):
        if not parent_id or not parent_name or not parent_email or not parent_phone:
            st.error("Please fill all fields.")
        else:
            cursor.execute(
                "INSERT INTO Parent (ParentID, Name, Email, Phone) VALUES (?, ?, ?, ?)",
                parent_id, parent_name, parent_email, parent_phone
            )
            conn.commit()
            st.success(f"Parent '{parent_name}' added!")

    st.markdown("---")
    st.header("\U0001F467 Add Student")
    student_id = st.text_input("Student ID")
    student_name = st.text_input("Student Name")
    dob = st.date_input("Date of Birth")
    gender = st.selectbox("Gender", ["M", "F", "O"])
    class_id_fk = st.text_input("Class ID (FK)")
    parent_id_fk = st.text_input("Parent ID (FK)")

    if st.button("Add Student"):
        if not student_id or not student_name or not class_id_fk or not parent_id_fk:
            st.error("Please complete all fields.")
        else:
            cursor.execute(
                "INSERT INTO Student (StudentID, Name, DOB, Gender, ClassID, ParentID) VALUES (?, ?, ?, ?, ?, ?)",
                student_id, student_name, dob, gender, class_id_fk, parent_id_fk
            )
            conn.commit()
            st.success(f"Student '{student_name}' added!")

# Page 3: Mark Attendance
elif menu == "Mark Attendance":
    st.header("\U0001F4DD Add Attendance Record")
    attendance_id = st.text_input("Attendance ID")
    student_id_att = st.text_input("Student ID")
    attendance_date = st.date_input("Date")
    time_in = st.time_input("Time In")
    status = st.selectbox("Status", ["Present", "Absent"])

    if st.button("Add Attendance"):
        if not attendance_id or not student_id_att:
            st.error("Please fill required fields.")
        else:
            cursor.execute(
                "INSERT INTO Attendance (AttendanceID, StudentID, Date, TimeIn, Status) VALUES (?, ?, ?, ?, ?)",
                attendance_id, student_id_att, attendance_date, time_in, status
            )
            conn.commit()
            st.success("Attendance record added!")

# Page 4: Enter Term Marks
elif menu == "Enter Term Marks":
    st.header("\U0001F4CA Enter Term Marks")
    mark_id = st.text_input("Mark ID")
    student_id_tm = st.text_input("Student ID")
    subject_id_tm = st.text_input("Subject ID")
    term = st.text_input("Term (e.g., Term 1)")
    mark = st.number_input("Mark", min_value=0, max_value=100)

    if st.button("Add Term Mark"):
        if not mark_id or not student_id_tm or not subject_id_tm or not term:
            st.error("Please fill required fields.")
        else:
            cursor.execute(
                "INSERT INTO TermMark (MarkID, StudentID, SubjectID, Term, Mark) VALUES (?, ?, ?, ?, ?)",
                mark_id, student_id_tm, subject_id_tm, term, mark
            )
            conn.commit()
            st.success("Term mark added!")

# Page 5: View Summaries
elif menu == "View Summaries":
    st.header("\U0001F4C8 Student Summaries")
    st.subheader("Attendance Summary")
    attendance_df = pd.read_sql_query("SELECT * FROM vw_StudentAttendanceSummary", conn)
    st.dataframe(attendance_df)

    st.subheader("Student-Parent Information")
    parent_info_df = pd.read_sql_query("SELECT * FROM vw_StudentParentInfo", conn)
    st.dataframe(parent_info_df)

# Page 6: Send Email Report
elif menu == "Send Email Report":
    st.header("\U0001F4E7 Send Student Report")

    student_id = st.text_input("Enter Student ID")

    if st.button("Fetch Student Data"):
        if not student_id:
            st.warning("Please enter a Student ID.")
        else:
            try:
                query = "SELECT * FROM vw_StudentTermPerformance2 WHERE StudentID = ?"
                student_data = pd.read_sql_query(query, conn, params=[student_id])
                if not student_data.empty:
                    st.session_state.student_data = student_data
                    st.success("Student data fetched successfully.")
                    st.dataframe(student_data)
                else:
                    st.error("No records found.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")

    if "student_data" in st.session_state:
        student_data = st.session_state.student_data
        sender_email = st.text_input("Your Email")
        app_password = st.text_input("App Password", type="password")
        recipient_email = st.text_input("Parent Email")
        subject = st.text_input("Email Subject", value="Student Report")
        body = st.text_area("Message Body", value="Attached is your child's report.")

        if st.button("Send Report"):
            def send_student_report_email(sender_email, app_password, recipient_email, subject, body, student_data, file_name="student_report.xlsx"):
                try:
                    df = pd.DataFrame(student_data)
                    df.to_excel(file_name, index=False)
                    msg = EmailMessage()
                    msg['Subject'] = subject
                    msg['From'] = sender_email
                    msg['To'] = recipient_email
                    msg.set_content(body)
                    with open(file_name, 'rb') as f:
                        msg.add_attachment(f.read(), maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=file_name)
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(sender_email, app_password)
                        smtp.send_message(msg)
                    os.remove(file_name)
                    return True
                except Exception as e:
                    return str(e)

            result = send_student_report_email(sender_email, app_password, recipient_email, subject, body, student_data)
            if result == True:
                st.success("Email sent successfully!")
            else:
                st.error(f"Failed to send email: {result}")

# Page 7: Delete Records
elif menu == "Delete Records":
    st.subheader("🗑️ Delete Students or Parents")

    delete_option = st.radio("What would you like to delete?", ["Student", "Parent"])

    # ----------------------------
    # 🔸 DELETE STUDENT
    # ----------------------------
    if delete_option == "Student":
        cursor.execute("SELECT StudentID, Name FROM Student")
        students = cursor.fetchall()

        if students:
            student_dict = {f"{s[0]} - {s[1]}": s[0] for s in students}
            selected = st.selectbox("Select Student to Delete", list(student_dict.keys()))
            student_id_to_delete = student_dict[selected]

            if st.button("Delete Student"):
                try:
                    # 1. Delete dependent records first
                    cursor.execute("DELETE FROM Attendance WHERE StudentID = ?", student_id_to_delete)
                    cursor.execute("DELETE FROM TermMark WHERE StudentID = ?", student_id_to_delete)
                    cursor.execute("DELETE FROM EmailNotificationLog WHERE StudentID = ?", student_id_to_delete)

                    # 2. Delete the student record
                    cursor.execute("DELETE FROM Student WHERE StudentID = ?", student_id_to_delete)
                    conn.commit()
                    st.success("✅ Student and related records deleted successfully.")
                except Exception as e:
                    st.error(f"❌ Error deleting student: {e}")
        else:
            st.warning("No students found.")

    # ----------------------------
    # 🔸 DELETE PARENT
    # ----------------------------
    elif delete_option == "Parent":
        cursor.execute("SELECT ParentID, Name FROM Parent")
        parents = cursor.fetchall()

        if parents:
            parent_dict = {f"{p[0]} - {p[1]}": p[0] for p in parents}
            selected = st.selectbox("Select Parent to Delete", list(parent_dict.keys()))
            parent_id_to_delete = parent_dict[selected]

            if st.button("Delete Parent"):
                try:
                    # 1. Find all students linked to this parent
                    cursor.execute("SELECT StudentID FROM Student WHERE ParentID = ?", parent_id_to_delete)
                    students_to_delete = cursor.fetchall()

                    for student in students_to_delete:
                        sid = student[0]
                        # Delete all dependent student records
                        cursor.execute("DELETE FROM Attendance WHERE StudentID = ?", sid)
                        cursor.execute("DELETE FROM TermMark WHERE StudentID = ?", sid)
                        cursor.execute("DELETE FROM EmailNotificationLog WHERE StudentID = ?", sid)
                        cursor.execute("DELETE FROM Student WHERE StudentID = ?", sid)

                    # 2. Delete the parent
                    cursor.execute("DELETE FROM Parent WHERE ParentID = ?", parent_id_to_delete)
                    conn.commit()
                    st.success("✅ Parent and all linked student records deleted successfully.")
                except Exception as e:
                    st.error(f"❌ Error deleting parent: {e}")
        else:
            st.warning("No parents found.")


