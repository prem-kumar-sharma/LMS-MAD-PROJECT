# LMS-MAD_PROJECT

## Overview
This project is a Learning Management System designed to streamline the management and delivery of educational content. The LMS includes functionalities for course creation, user authentication, and course browsing, with a focus on simplicity and modularity.

---

## Features
- **Admin Dashboard**: Create, edit, and manage courses.
- **Authentication System**: Admin and user login/register functionalities.
- **Course Management**: View a list of courses, individual course details, and related content.
- **User-Friendly Interface**: Templates for various pages like dashboards and course management.

---

## Folder Structure

LMS/ ├── backend/ │ ├── instance/ │ ├── uploads/ │ └── app.py # Main backend application ├── frontend/templates/ │ ├── admin/ │ │ ├── create_course.html # Template for creating a new course │ │ ├── dashboard.html # Admin dashboard │ │ ├── edit_course.html # Template for editing a course │ │ └── manage_courses.html # Template for managing courses │ ├── auth/ │ │ ├── admin_login.html # Admin login page │ │ ├── login.html # User login page │ │ └── register.html # User registration page │ ├── courses/ │ │ ├── list.html # List of available courses │ │ ├── view.html # Detailed course view │ │ ├── base.html # Base template for reuse │ │ └── dashboard.html # Dashboard for general users ├── .gitignore # Git ignore file ├── README.md # Project documentation └── requirements.txt # Python dependencies


---

## Prerequisites
- Python 3.8 or higher
- Flask Framework
- Virtual Environment setup (recommended)

---

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd LMS


python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

pip install -r requirements.txt
python backend/app.py

