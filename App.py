import streamlit as st
import nltk
import spacy
import re
import time
import datetime
import pymysql
import base64
from pdfminer.high_level import extract_text
from PIL import Image

# Download NLTK stopwords if not already downloaded
nltk.download('stopwords')
spacy.load('en_core_web_sm')

# Database connection
connection = pymysql.connect(host='localhost', user='root', password='', db='sra')
cursor = connection.cursor()

# Function to read PDF file
def pdf_reader(file):
    text = extract_text(file)
    return text

# Function to show uploaded PDF
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Function to insert user data into the database
def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    DB_table_name = 'user_data'
    insert_sql = f"INSERT INTO {DB_table_name} (Name, Email_ID, resume_score, Timestamp, Page_no, Predicted_Field, User_level, Actual_skills, Recommended_skills, Recommended_courses) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    rec_values = (name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

# Function to extract name from text
def extract_name(text):
    name_pattern = r"(?<!\w)([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+){0,2})(?!\w)"
    names = re.findall(name_pattern, text)
    return names[0] if names else "Name Not Found"

# Function to extract email from text
def extract_email(text):
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else "Email Not Found"

# Function to extract skills from resume text
def extract_skills(text):
    skills_list = ["Python", "Java", "C++", "JavaScript", "HTML", "CSS", "SQL", "Data Analysis", "Machine Learning"]
    found_skills = [skill for skill in skills_list if skill.lower() in text.lower()]
    return found_skills

# Function to calculate resume score based on extracted data
def calculate_resume_score(skills, cand_level):
    base_score = 0
    # Base score calculation based on skills
    if skills:
        base_score += len(skills) * 10  # Each skill gives 10 points

    # Candidate level scoring
    if cand_level == "Fresher":
        base_score += 5  # Add 5 points for being a fresher
    elif cand_level == "Intermediate":
        base_score += 10  # Add 10 points for intermediate
    elif cand_level == "Experienced":
        base_score += 15  # Add 15 points for experienced

    return base_score

# Streamlit page configuration
st.set_page_config(page_title="Smart Resume Analyzer")

# Main function
def run():
    st.title("Smart Resume Analyzer")
    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    img = Image.open('./chameleon.png')  # Update path if needed
    img = img.resize((250, 250))
    st.image(img)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)

    # Create table
    DB_table_name = 'user_data'
    table_sql = f"""
        CREATE TABLE IF NOT EXISTS {DB_table_name} (
            ID INT NOT NULL AUTO_INCREMENT,
            Name VARCHAR(100) NOT NULL,
            Email_ID VARCHAR(50) NOT NULL,
            resume_score VARCHAR(8) NOT NULL,
            Timestamp VARCHAR(50) NOT NULL,
            Page_no VARCHAR(5) NOT NULL,
            Predicted_Field VARCHAR(25) NOT NULL,
            User_level VARCHAR(30) NOT NULL,
            Actual_skills VARCHAR(300) NOT NULL,
            Recommended_skills VARCHAR(300) NOT NULL,
            Recommended_courses VARCHAR(600) NOT NULL,
            PRIMARY KEY (ID)
        );
    """
    cursor.execute(table_sql)
    
    if choice == 'Normal User': 
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            # Read resume text using pdf_reader function
            resume_text = pdf_reader(save_image_path)

            st.header("**Resume Analysis**")
            name = extract_name(resume_text)
            email = extract_email(resume_text)
            skills = extract_skills(resume_text)
            no_of_pages = 1  # You might want to implement actual page count logic

            st.success("Hello " + name)
            st.subheader("**Your Basic Info**")
            st.text('Name: ' + name)
            st.text('Email: ' + email)
            st.text('Resume pages: ' + str(no_of_pages))
            
            # Example candidate level based on number of pages
            cand_level = "Fresher" if no_of_pages == 1 else "Intermediate" if no_of_pages == 2 else "Experienced"
            st.markdown(f'<h4 style="text-align: left; color: #1ed760;">You are looking {cand_level}.</h4>', unsafe_allow_html=True)

            st.subheader("**Skills Extracted💡**")
            st.write(skills)

            # Calculate resume score
            resume_score = calculate_resume_score(skills, cand_level)
            st.subheader("**Resume Score🏆**")
            st.write(f"Your resume score is: {resume_score}")

            # Insert into table
            ts = time.time()
            cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            timestamp = str(cur_date + '_' + cur_time)

            # Insert the data into the database
            insert_data(name, email, resume_score, timestamp, no_of_pages, "Field", cand_level, str(skills), str([]), str([]))

# Run the application
if __name__ == '__main__':
    run()
