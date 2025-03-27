import cv2
import os
import sqlite3
from tkinter import Tk, Button, Label, Entry, Toplevel, simpledialog, messagebox
from deepface import DeepFace
import datetime
import time
import tkinter as tk
from PIL import Image, ImageTk
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import sqlite3
import os



# Setup the database if not already present
def setup_database():
    conn = sqlite3.connect('studentss.db')
    c = conn.cursor()
    
    # Create students table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number INTEGER UNIQUE NOT NULL,
            department TEXT NOT NULL,
            address TEXT NOT NULL,
            image_folder TEXT NOT NULL
        )
    ''')

    # Create attendance table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number INTEGER NOT NULL,
            login_time TEXT,
            logout_time TEXT,
            FOREIGN KEY (roll_number) REFERENCES students (roll_number)
        )
    ''')

    conn.commit()
    conn.close()


def add_new_student(root):
    form_window = tk.Toplevel(root)
    form_window.title("Enter Student Details")

    # Set window size and center it
    form_window.geometry("450x400")
  
    form_window.config(bg="#E3F2FD")

    # Function to move focus between fields when 'Enter' is pressed
    def focus_next_widget(event):
        event.widget.tk_focusNext().focus()
        return "break"

    # Close window gracefully
    def on_close():
        messagebox.showinfo("Cancelled", "Student registration was cancelled.")
        form_window.destroy()

    form_window.protocol("WM_DELETE_WINDOW", on_close)

    # Stylish Label and Entry Design
    label_style = {'font': ('Arial', 12), 'bg': "#E3F2FD", 'fg': '#1E88E5', 'padx': 10, 'pady': 10}
    entry_style = {'width': 30, 'font': ('Arial', 12), 'bd': 3, 'fg': '#1565C0'}

    # Adding Text Instructions at the top
    instruction_label = tk.Label(form_window, text="Please enter the student details below:", font=('Arial', 14), bg="#E3F2FD", fg="#1E88E5")
    instruction_label.grid(row=0, column=0, columnspan=2, pady=20)

    # Labels and Entries for Student Name, Roll Number, Department, and Address
    tk.Label(form_window, text="Student Name:", **label_style).grid(row=1, column=0, sticky='w', padx=20, pady=10)
    name_entry = tk.Entry(form_window, **entry_style)
    name_entry.grid(row=1, column=1, pady=10)
    name_entry.bind("<Return>", focus_next_widget)

    tk.Label(form_window, text="Roll Number:", **label_style).grid(row=2, column=0, sticky='w', padx=20, pady=10)
    roll_number_entry = tk.Entry(form_window, **entry_style)
    roll_number_entry.grid(row=2, column=1, pady=10)
    roll_number_entry.bind("<Return>", focus_next_widget)

    tk.Label(form_window, text="Department:", **label_style).grid(row=3, column=0, sticky='w', padx=20, pady=10)
    department_entry = tk.Entry(form_window, **entry_style)
    department_entry.grid(row=3, column=1, pady=10)
    department_entry.bind("<Return>", focus_next_widget)

    tk.Label(form_window, text="Address:", **label_style).grid(row=4, column=0, sticky='w', padx=20, pady=10)
    address_entry = tk.Entry(form_window, **entry_style)
    address_entry.grid(row=4, column=1, pady=10)
    address_entry.bind("<Return>", focus_next_widget)

     # Button styling
    button_style = {'font': ('Arial', 12, 'bold'), 'bg': '#1E88E5', 'fg': 'white', 'width': 20, 'relief': 'raised'}

    # Submit function
    def submit_details():
        name = name_entry.get()
        roll_number = roll_number_entry.get()
        department = department_entry.get()
        address = address_entry.get()

        if not name or not roll_number or not department or not address:
            messagebox.showerror("Input Error", "All fields are required.")
            return
        if not roll_number.isdigit():
            messagebox.showerror("Input Error", "Roll Number must be an integer.")
            return

        roll_number = int(roll_number)
        
        # Check if the roll number already exists in the database
        conn = sqlite3.connect('studentss.db')
        c = conn.cursor()
        c.execute("SELECT roll_number FROM students WHERE roll_number = ?", (roll_number,))
        if c.fetchone():
            messagebox.showerror("Error", "A student with this Roll Number already exists.")
            conn.close()
            return
        conn.close()

        # Create image folder
        image_folder = os.path.join("known_faces", str(roll_number))
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        cap = cv2.VideoCapture(1)
        img_count = 0
        max_images = 5

        while img_count < max_images:
            ret, frame = cap.read()
            if not ret:
                messagebox.showerror("Error", "Failed to capture image.")
                cap.release()
                return

            cv2.imshow(f"Capturing Images ({img_count+1}/{max_images})", frame)
            cv2.imwrite(os.path.join(image_folder, f"{roll_number}_{img_count}.jpg"), frame)
            img_count += 1
            time.sleep(1)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                response = messagebox.askyesno("Stop Capturing", "Do you want to stop capturing images?")
                if not response:
                    break

        cap.release()
        cv2.destroyAllWindows()

        if img_count == max_images:
            conn = sqlite3.connect('studentss.db')
            c = conn.cursor()
            c.execute("INSERT INTO students (name, roll_number, department, address, image_folder) VALUES (?, ?, ?, ?, ?)",
                      (name, roll_number, department, address, image_folder))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Student information and images added successfully!")
        else:
            messagebox.showinfo("Cancelled", "Student registration was stopped by the user.")

        form_window.destroy()

    # Submit button with unique style
    submit_button = tk.Button(form_window, text="Submit", command=submit_details, **button_style)
    submit_button.grid(row=5, column=0, columnspan=2, pady=40)


# Function to recognize a face and log login/logout times
def recognize_face():
    cap = cv2.VideoCapture(1)
    
    start_time = time.time()
    recognized = False
    captured_image_path = 'known_faces/temp.jpg'

    while True:
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture video.")
            cap.release()
            return
        
        cv2.imshow("Recognizing Face - Wait 2 seconds", frame)

        if time.time() - start_time >= 4:
            cv2.imwrite(captured_image_path, frame)
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            response = messagebox.askyesno("Stop Recognition", "You have stopped recognizing. Do you want to continue?")
            if not response:  # If the user chooses 'No'
                cap.release()
                cv2.destroyAllWindows()
                messagebox.showinfo("Cancelled", "Face recognition was stopped by the user.")
                return

    cap.release()
    cv2.destroyAllWindows()

    conn = sqlite3.connect('studentss.db')
    c = conn.cursor()
    c.execute("SELECT name, roll_number, image_folder FROM students")
    students = c.fetchall()

    for student in students:
        name, roll_number, image_folder = student
        try:
            for img_file in os.listdir(image_folder):
                img_path = os.path.join(image_folder, img_file)
                
                
                result = DeepFace.verify(captured_image_path, img_path, model_name="Facenet", distance_metric="cosine", enforce_detection=True, threshold=0.4)  # Adjust threshold
                
                # Check for errors and no face detection
                '''if result.get('error') and 'No face detected' in result['error']:
                    messagebox.showwarning("No Face Detected", "No face detected in the captured image. Please try again.")
                    return'''


                # If face is verified
                if result['verified']:
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Check if the student is already logged in today
                    c.execute("SELECT id, login_time, logout_time FROM attendance WHERE roll_number = ? AND DATE(login_time) = DATE('now')", (roll_number,))
                    record = c.fetchone()
                    
                    if record:
                        # Student is already logged in today; check if they need to log out
                        if record[2] is None:  # No logout time means they are still logged in
                            # Ask if the student wants to log out
                            if messagebox.askyesno("Logout", f"{name} ({roll_number}) is already logged in today. Do you want to log out?"):
                                # Update the existing record with logout time
                                c.execute("UPDATE attendance SET logout_time = ? WHERE id = ?", (current_time, record[0]))
                                conn.commit()
                                messagebox.showinfo("Logout", f"Goodbye {name} ({roll_number})! Logout time recorded at {current_time}.")
                        else:
                            messagebox.showinfo("Already Logged In", f"{name} ({roll_number}) is already logged in today.")
                    else:
                        # Insert a new record with login time
                        c.execute("INSERT INTO attendance (roll_number, login_time) VALUES (?, ?)", (roll_number, current_time))
                        conn.commit()
                        messagebox.showinfo("Login", f"Welcome {name} ({roll_number})! Login time recorded at {current_time}.")
                    
                    recognized = True
                    break
            if recognized:
                break
        except Exception as e:
            print(f"Error verifying {name}: {e}")
    
    if not recognized:
        messagebox.showwarning("Not Recognized", "Student not recognized. Please register.")

    if os.path.exists(captured_image_path):
        os.remove(captured_image_path)

    conn.close()

def check_attendance():
    roll_number = simpledialog.askstring("Attendance Check", "Enter Roll Number:")
    
    if roll_number is None:
        # User cancelled the input dialog
        messagebox.showinfo("Cancelled", "Attendance check was cancelled.")
        return
    
    if not roll_number:
        messagebox.showwarning("Input Error", "Roll Number is required.")
        return

    if not roll_number.isdigit():
        messagebox.showerror("Input Error", "Roll Number must be an integer.")
        return

    roll_number = int(roll_number)

    conn = sqlite3.connect('studentss.db')
    c = conn.cursor()
    
    # Query to fetch all attendance records for the specified roll number
    c.execute("SELECT login_time, logout_time FROM attendance WHERE roll_number = ?", (roll_number,))
    attendance_records = c.fetchall()

    # Count total attendance and group by date
    total_attendance = len(attendance_records)
    date_records = {}

    for record in attendance_records:
        login_time, logout_time = record
        date = login_time.split(" ")[0]  # Get only the date part
        
        if date not in date_records:
            date_records[date] = []
        date_records[date].append((login_time, logout_time))

    conn.close()

    # Calculate attendance percentage out of 100 days
    total_days = 100  # Assuming we're tracking attendance over 100 days
    attendance_percentage = (total_attendance / total_days) * 100

    # Prepare the attendance summary message
    if total_attendance > 0:
        attendance_info = f"Total Attendance: {total_attendance} out of {total_days} days ({attendance_percentage:.2f}%)\n\n"
        for date, records in date_records.items():
            attendance_info += f"{date}:\n"
            for login_time, logout_time in records:
                attendance_info += f"  Login: {login_time}  Logout: {logout_time if logout_time else 'N/A'}\n"
        messagebox.showinfo("Attendance Records", f"Attendance for Roll Number {roll_number}:\n\n{attendance_info}")
    else:

        messagebox.showinfo("No Records", "No attendance records found for this Roll Number.")

def generate_student_info_pdf():
    conn = sqlite3.connect('studentss.db')
    c = conn.cursor()
    
    # Query to fetch all students' information
    c.execute("SELECT name, department, roll_number FROM students")
    students = c.fetchall()
    
    # Create a PDF document
    pdf_file = "student_info_report.pdf"
    document = SimpleDocTemplate(pdf_file, pagesize=letter)
    
    # Create a list to hold the table data
    data = [["Name", "Department", "Roll Number", "Attendance Percentage"]]
    row_styles = []
    
    total_days = 100  # Assuming we're tracking attendance over 100 days
    for index, student in enumerate(students, start=1):
        name, department, roll_number = student
        
        # Calculate attendance percentage
        c.execute("SELECT COUNT(*) FROM attendance WHERE roll_number = ?", (roll_number,))
        total_attendance = c.fetchone()[0]
        attendance_percentage = (total_attendance / total_days) * 100 if total_days > 0 else 0
        
        # Append the student data to the table
        data.append([name, department, roll_number, f"{attendance_percentage:.2f}%"])
        
        # Add style for rows with attendance < 3%
        if attendance_percentage < 3:
            row_styles.append(('BACKGROUND', (0, index), (-1, index), colors.red))
        else:
            row_styles.append(('BACKGROUND', (0, index), (-1, index), colors.green))

    conn.close()

    # Create a table with the data
    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])

    # Apply conditional styles
    for row_style in row_styles:
        style.add(*row_style)

    table.setStyle(style)

    # Build the PDF
    document.build([table])
    messagebox.showinfo(
        "Report Generated",
        f"Student information report has been successfully generated!\n\n"
        f"File Name: student_info_report.pdf\n"
        f"Location: {os.path.abspath(pdf_file)}\n\n"
        f"You can now view or share the report."
    )
    os.startfile(pdf_file)
    

def main():
    # Create the main window
    root = tk.Tk()
    root.title("Face Recognition Attendance System")
    root.geometry("1900x1050")  # Adjusted window size
   

    
    # Load the background image
    try:
        bg_image = Image.open("background.jpg")  # Replace with your background image path
        bg_image = bg_image.resize((1500, 1000), Image.Resampling.LANCZOS)  # Resize to fit the window
        bg_photo = ImageTk.PhotoImage(bg_image)
    except FileNotFoundError:
        print("Error: Background image file not found.")
        return

    # Create a Label widget to display the background image
    bg_label = tk.Label(root, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)  # Cover the entire window

    # Add a text label on top of the background image
    title_label = tk.Label(
        root,
        text="Face Recognition Attendance System",
        font=("Arial", 35, "bold"),
        fg="white",
        bg="#0073e6",  # Background of the text label (can be transparent if you prefer)
        padx=10,
        pady=15
    )
    title_label.place(x=400, y=80)  # Position it at the top center


    # Load the image for the buttons    
    try:
        img = Image.open("register.png")  
        img = img.resize((220, 220), Image.Resampling.LANCZOS)
        photo_img = ImageTk.PhotoImage(img)

        img_student = Image.open("face-recognition-System-scaled-1.png") 
        img_student = img_student.resize((220, 220), Image.Resampling.LANCZOS)
        photo_img1 = ImageTk.PhotoImage(img_student)
        
        img_student1 = Image.open("attendanceimg.png")  
        img_student1 = img_student1.resize((220, 220), Image.Resampling.LANCZOS)
        photo_img2 = ImageTk.PhotoImage(img_student1)

        img_student2 = Image.open("exit-button-emergency-icon-3d-rendering-illustration-png.png") 
        img_student2 = img_student2.resize((220, 220), Image.Resampling.LANCZOS)
        photo_img3 = ImageTk.PhotoImage(img_student2)    
        
        img_ex = Image.open("export.png")  
        img_ex = img_ex.resize((220, 220), Image.Resampling.LANCZOS)
        photo_ex = ImageTk.PhotoImage(img_ex)
    except FileNotFoundError:
        print("Error: Button image file not found.")
        return

    
    # Frame for "Register"
    student_frame = tk.Frame(root, bg="#cce6ff", bd=5, relief="ridge")
    student_frame.place(x=50, y=300, width=250, height=300)
    b1 = tk.Button(student_frame, image=photo_img, cursor="hand2", borderwidth=0,command=lambda: add_new_student(root),)
    b1.place(x=10, y=10, width=220, height=220)

    b1_label = tk.Button(student_frame, text="Register", font=("Arial", 14),command=lambda: add_new_student(root), cursor="hand2",
                         bg="#0073e6", fg="white", borderwidth=0)
    b1_label.place(x=10, y=240, width=220, height=40)

    # Frame for "Face Recognition"
    register_frame = tk.Frame(root, bg="#cce6ff", bd=5, relief="ridge")
    register_frame.place(x=350, y=300, width=250, height=300)

    b2 = tk.Button(register_frame, image=photo_img1, cursor="hand2",command=recognize_face, borderwidth=0)
    b2.place(x=10, y=10, width=220, height=220)

    b2_label = tk.Button(register_frame, text="Face Recognition", command=recognize_face,font=("Arial", 14), cursor="hand2",
                         bg="#0073e6", fg="white", borderwidth=0)
    b2_label.place(x=10, y=240, width=220, height=40)

    # Frame for "Check Attendance"
    recognition_frame = tk.Frame(root, bg="#cce6ff", bd=5, relief="ridge")
    recognition_frame.place(x=630, y=300, width=250, height=300)

    b3 = tk.Button(recognition_frame, image=photo_img2, cursor="hand2", command=check_attendance,borderwidth=0)
    b3.place(x=10, y=10, width=220, height=220)

    b3_label = tk.Button(recognition_frame, text="Check Attendance",command=check_attendance, font=("Arial", 14), cursor="hand2",
                         bg="#0073e6", fg="white", borderwidth=0)
    b3_label.place(x=10, y=240, width=220, height=40)

    # Frame for "Exit" with similar image style
    exit_frame = tk.Frame(root, bg="#cce6ff", bd=5, relief="ridge")
    exit_frame.place(x=1200, y=300, width=250, height=300)

    b4 = tk.Button(exit_frame, image=photo_img3, cursor="hand2", borderwidth=0, command=root.quit)
    b4.place(x=10, y=10, width=220, height=220)

    b4_label = tk.Button(exit_frame, text="Exit", font=("Arial", 14), cursor="hand2",
                         bg="#e60000", fg="white", borderwidth=0, command=root.quit)
    b4_label.place(x=10, y=240, width=220, height=40)
    # Frame for "Export Attendance"
    export_frame = tk.Frame(root, bg="#cce6ff", bd=5, relief="ridge")
    export_frame.place(x=900, y=300, width=250, height=300)

    export_button = tk.Button(export_frame, image=photo_ex, cursor="hand2", borderwidth=0, command=generate_student_info_pdf)
    export_button.place(x=10, y=10, width=220, height=220)

    export_label = tk.Button(export_frame, text="Export Attendance", font=("Arial", 14), command=generate_student_info_pdf, 
                         cursor="hand2", bg="#0073e6", fg="white", relief="raised")
    export_label.place(x=10, y=240, width=220, height=40)


    # Run the application
    root.mainloop()

# Run the main function
if __name__ == "__main__":
    main()
