import streamlit as st
import cv2
import face_recognition
import numpy as np
import pandas as pd
import os
from datetime import datetime
from openpyxl import load_workbook

# -------------------------------
# File Setup
# -------------------------------
STUDENTS_FILE = "students.xlsx"
ATTENDANCE_FILE = "attendance.xlsx"
ENCODINGS_FILE = "encodings.npy"
NAMES_FILE = "names.npy"

# Ensure student & attendance files exist
if not os.path.exists(STUDENTS_FILE):
    pd.DataFrame(columns=["Name", "Class", "Roll No"]).to_excel(STUDENTS_FILE, index=False)

if not os.path.exists(ATTENDANCE_FILE):
    pd.DataFrame(columns=["Name", "Date", "Time"]).to_excel(ATTENDANCE_FILE, index=False)

# Load encodings if available
if os.path.exists(ENCODINGS_FILE) and os.path.exists(NAMES_FILE):
    known_encodings = list(np.load(ENCODINGS_FILE, allow_pickle=True))
    known_names = list(np.load(NAMES_FILE, allow_pickle=True))
else:
    known_encodings, known_names = [], []

# -------------------------------
# Styling (Red Headings)
# -------------------------------
st.markdown(
    """
    <style>
        h1, h2, h3 {
            color: red !important;
        }
        .reportview-container {
            background: #f8fafc;
        }
        .sidebar .sidebar-content {
            background: #1e293b;
            color: white;
        }
        .stButton button {
            border-radius: 12px;
            height: 3em;
            font-size: 16px;
        }
        .success-box {
            padding: 15px;
            border-radius: 10px;
            background: #d1fae5;
            color: #065f46;
            margin-bottom: 15px;
        }
        .warning-box {
            padding: 15px;
            border-radius: 10px;
            background: #fef3c7;
            color: #92400e;
            margin-bottom: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# Utility Functions
# -------------------------------
def save_students(df):
    with pd.ExcelWriter(STUDENTS_FILE, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, index=False)

def save_attendance(df):
    with pd.ExcelWriter(ATTENDANCE_FILE, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, index=False)

def mark_attendance(name):
    df = pd.read_excel(ATTENDANCE_FILE)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    if not ((df["Name"] == name) & (df["Date"] == date_str)).any():
        new_entry = {"Name": name, "Date": date_str, "Time": time_str}
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_attendance(df)
        st.success(f"✅ Attendance marked for {name}")
    else:
        st.info(f"ℹ️ {name} already marked today.")

def add_student(name, student_class, roll_no, image_file):
    df = pd.read_excel(STUDENTS_FILE)
    if (df["Roll No"] == roll_no).any():
        st.error("⚠️ Student with this Roll No already exists!")
        return

    # Save student data
    new_student = {"Name": name, "Class": student_class, "Roll No": roll_no}
    df = pd.concat([df, pd.DataFrame([new_student])], ignore_index=True)
    save_students(df)

    # Save face encoding
    image = face_recognition.load_image_file(image_file)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) > 0:
        known_encodings.append(encodings[0])
        known_names.append(name)
        np.save(ENCODINGS_FILE, known_encodings, allow_pickle=True)
        np.save(NAMES_FILE, known_names, allow_pickle=True)
        st.success("✅ Student Registered Successfully!")
    else:
        st.error("⚠️ No face detected. Please upload a clear image.")

# -------------------------------
# Streamlit Navigation
# -------------------------------
menu = st.sidebar.radio(
    "📌 Menu",
    ["🏠 Home", "📝 Register Student", "📸 Mark Attendance (Face)", "📊 Attendance Report", "⚙️ Manage Encodings"]
)

# -------------------------------
# Pages
# -------------------------------
if menu == "🏠 Home":
    st.title("📚 Automated Attendance System")
    st.header("Welcome, Teacher 👩‍🏫")
    st.write("This system helps rural schools **automate attendance** using face recognition.")
    st.write("👉 Navigate using the left menu.")

elif menu == "📝 Register Student":
    st.header("Register Student")

    name = st.text_input("Full Name")
    student_class = st.text_input("Class")
    roll_no = st.text_input("Roll Number")

    option = st.radio("Choose Input Method", ["📤 Upload Image", "📷 Capture from Camera"])

    image_file = None
    if option == "📤 Upload Image":
        image_file = st.file_uploader("Upload Student Image", type=["jpg", "jpeg", "png"])

    elif option == "📷 Capture from Camera":
        if st.button("📷 Start Camera"):
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()

            if ret:
                st.image(frame, channels="BGR")
                # Save captured frame as temporary file
                temp_path = "captured_student.jpg"
                cv2.imwrite(temp_path, frame)
                image_file = temp_path
            else:
                st.error("⚠️ Camera not detected. Try again.")

    if st.button("✅ Register Student"):
        if name and student_class and roll_no and image_file:
            add_student(name, student_class, roll_no, image_file)
        else:
            st.error("⚠️ Please fill all fields and provide an image.")


elif menu == "📸 Mark Attendance (Face)":
    st.header("Mark Attendance using Face Recognition")
    st.write("Click the button to start camera and mark attendance.")

    if st.button("📷 Start Camera"):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            st.error("⚠️ Failed to capture image. Try again.")
        else:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_locations(rgb_frame)
            encodings = face_recognition.face_encodings(rgb_frame, faces)

            for encoding in encodings:
                matches = face_recognition.compare_faces(known_encodings, encoding)
                if True in matches:
                    index = matches.index(True)
                    name = known_names[index]
                    mark_attendance(name)
                else:
                    st.warning("⚠️ Unknown face detected. Register student first.")

            st.image(frame, channels="BGR")

elif menu == "📊 Attendance Report":
    st.header("Attendance Report")
    df = pd.read_excel(ATTENDANCE_FILE)
    st.dataframe(df)

    if not df.empty:
        student = st.selectbox("Select Student", df["Name"].unique())
        student_data = df[df["Name"] == student]
        st.write(f"📌 Attendance for {student}")
        st.dataframe(student_data)

elif menu == "⚙️ Manage Encodings":
    st.header("Manage Encodings & Students")

    if st.button("🗑️ Clear All Data"):
        if os.path.exists(ENCODINGS_FILE): os.remove(ENCODINGS_FILE)
        if os.path.exists(NAMES_FILE): os.remove(NAMES_FILE)
        pd.DataFrame(columns=["Name", "Class", "Roll No"]).to_excel(STUDENTS_FILE, index=False)
        pd.DataFrame(columns=["Name", "Date", "Time"]).to_excel(ATTENDANCE_FILE, index=False)
        st.success("✅ All encodings and student data cleared.")
