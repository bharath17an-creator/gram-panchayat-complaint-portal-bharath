# Gram Panchayat Complaint Management Portal

A web-based digital grievance redressal system built to connect citizens with their local Gram Panchayat authorities. This platform allows citizens to report civic issues, track their progress, and enables administrative staff to manage and resolve public complaints efficiently.

## Features

* **Citizen Portal:** Register, log in, submit new civic complaints, and track the real-time status of reported issues.
* **Admin Dashboard:** Monitor all incoming complaints, view analytics, assign tasks to specific departments, and communicate updates to citizens.
* **Staff Dashboard:** Dedicated portal for Panchayat workers (electricians, plumbers, etc.) to view assigned tasks and mark them as resolved.
* **History Tracking:** A complete timeline of remarks and status changes for every complaint.

## Tech Stack

* **Backend:** Python, Flask framework
* **Database:** SQLite (built-in)
* **Frontend:** HTML5, CSS3, Bootstrap 5
* **Authentication:** Werkzeug security (Password Hashing)

## How to Run This Project

1. Clone this repository to your local machine.
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment.
4. Install the required packages: `pip install -r requirements.txt`
5. Run the application: `python app.py`
6. Open a web browser and navigate to `http://127.0.0.1:5000`

## Multilanguage support

The portal includes English, Kannada and Hindi UI translations.

- Select a language using the language dropdown shown on each page.
- The selected language is stored in the Flask session and remains selected while navigating the portal.
- UI labels, navigation, forms, dashboards, complaint statuses and GPS messages use the selected language.
- Complaint descriptions, titles, remarks and other text entered by citizens or staff are kept as originally entered.

The language feature uses the `translations.py` file and the `/set-language` Flask route. Keep `translations.py` in the same folder as `app.py`.
