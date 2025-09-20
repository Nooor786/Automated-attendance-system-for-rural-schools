import streamlit as st
import pandas as pd
import numpy as np
import face_recognition
from datetime import datetime
import os
from PIL import Image
import io

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
    if isinstance(image_file, io.BytesIO) or hasattr(image_file, "read"):
        img = Image.open(image_file).convert("RGB")
        img = np.array(img)
    else:
        img = np.array(Image.open(image_file).convert("RGB"))

    encodings = face_recognition.face_encodings(img)
    if len(encodings) > 0:
        known_encodings.append(encodings[0])
        known_names.append(name)
        np.save(ENCODINGS_FILE, known_encodings, allow_pickle=True)
        np.save(NAMES_FILE, known_names, allow_pickle=True)
        st.success("✅ Student Registered Successfully!")
    else:
        st.error("⚠️ No face detected. Please provide a clear photo.")

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

    # Quick Stats
    st.subheader("📊 Dashboard")
    st.metric("👨‍🎓 Registered Students", len(known_names))
    df_attendance = pd.read_excel(ATTENDANCE_FILE)
    st.metric("🕒 Total Attendance Records", len(df_attendance))

elif menu == "📝 Register Student":
    st.header("Register Student")

    name = st.text_input("Full Name")
    student_class = st.text_input("Class")
    roll_no = st.text_input("Roll Number")

    option = st.radio("Choose Input Method", ["📤 Upload Image", "📷 Capture via Browser"])

    image_file = None
    if option == "📤 Upload Image":
        image_file = st.file_uploader("Upload Student Image", type=["jpg", "jpeg", "png"])

    elif option == "📷 Capture via Browser":
        image_file = st.camera_input("📷 Capture Student Photo")

    if st.button("✅ Register Student"):
        if name and student_class and roll_no and image_file is not None:
            add_student(name, student_class, roll_no, image_file)
        else:
            st.error("⚠️ Please fill all fields and provide a photo.")

elif menu == "📸 Mark Attendance (Face)":
    st.header("Mark Attendance using Face Recognition")

    img_file = st.camera_input("📷 Capture Student Photo for Attendance")
    if st.button("✅ Mark Attendance"):
        if img_file is None:
            st.error("⚠️ Please capture a photo first.")
        else:
            img = Image.open(img_file).convert("RGB")
            img = np.array(img)
            encs = face_recognition.face_encodings(img)
            if len(encs) == 0:
                st.error("⚠️ No face detected. Try again.")
            else:
                matches = face_recognition.compare_faces(known_encodings, encs[0])
                if True in matches:
                    index = matches.index(True)
                    name = known_names[index]
                    mark_attendance(name)
                else:
                    st.warning("⚠️ Unknown face detected. Register student first.")

elif menu == "📊 Attendance Report":
    st.header("Attendance Report")
    df = pd.read_excel(ATTENDANCE_FILE)
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        student = st.selectbox("Select Student", df["Name"].unique())
        student_data = df[df["Name"] == student]
        st.write(f"📌 Attendance for {student}")
        st.dataframe(student_data, use_container_width=True)

        # CSV download
        csv = student_data.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download CSV", data=csv, file_name=f"{student}_attendance.csv", mime="text/csv")

        # Excel download
        with pd.ExcelWriter(f"{student}_attendance.xlsx", engine="openpyxl") as writer:
            student_data.to_excel(writer, index=False)
        with open(f"{student}_attendance.xlsx", "rb") as f:
            st.download_button("⬇️ Download Excel", data=f, file_name=f"{student}_attendance.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif menu == "⚙️ Manage Encodings":
    st.header("Manage Encodings & Students")

    st.write(f"👨‍🎓 Registered Students: {len(known_names)}")
    if known_names:
        st.dataframe(pd.DataFrame({"Name": known_names}), use_container_width=True)

    if st.button("🗑️ Clear All Data"):
        if os.path.exists(ENCODINGS_FILE): os.remove(ENCODINGS_FILE)
        if os.path.exists(NAMES_FILE): os.remove(NAMES_FILE)
        pd.DataFrame(columns=["Name", "Class", "Roll No"]).to_excel(STUDENTS_FILE, index=False)
        pd.DataFrame(columns=["Name", "Date", "Time"]).to_excel(ATTENDANCE_FILE, index=False)
        known_encodings.clear()
        known_names.clear()
        st.success("✅ All encodings and student data cleared.")
