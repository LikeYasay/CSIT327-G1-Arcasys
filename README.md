# 📂 Arcasys: Marketing Archive Manager

Arcasys: Marketing Archive Manager is a Django Full Stack web application for **Cebu Institute of Technology – University (CIT-U)** that centralizes event management and archiving. It consolidates scattered event postings into one platform with role-based access, smart search and filters, and integration with external platforms—improving communication, transparency, and accessibility across the university.

---

## 🛠 Tech Stack

- **Backend:** Python, Django  
- **Frontend:** HTML, CSS  
- **Database & Deployment:** Supabase, Render

---

## 🚀 Setup & Run Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/LikeYasay/CSIT327-G1-Arcasys.git
```

### 2. Navigate to the Project Folder
```bash
cd MarketingArchive
```

### 3. Create & Activate a Virtual Environment
Make sure you’re still in the MarketingArchive root directory (the same folder that contains Arcasys/).

If you don’t have a virtual environment yet, create one:

```bash
python -m venv env
```

Then activate it:

**On Windows (Command Prompt / PowerShell)**
```bash
env\Scripts\activate
```

**On macOS/Linux**
```bash
source env/bin/activate
```

✅ If you already have a virtual environment (e.g., env), just activate it using the appropriate command above.

### 4. Navigate to the Arcasys Folder
Once your virtual environment is activated, go inside the Django project folder:

```bash
cd Arcasys
```

### 5. Install Project Dependencies
```bash
pip install -r requirements.txt
```

### 6. Create a .env File
In the Arcasys folder (same level as manage.py), create a file named `.env`.

⚠️ **Do NOT share or upload this file publicly.**
It contains sensitive credentials for the shared Supabase database and email service.

➡️ Ask the project admin or repository maintainer for the correct `.env` configuration.

Example placeholder format:

```env
DATABASE_URL='your-database-url-here'
SECRET_KEY='your-django-secret-key'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com

EMAIL_HOST_USER='your-email-here'
EMAIL_HOST_PASSWORD='your-app-password-here'
DEFAULT_FROM_EMAIL='Marketing Archive <your-email-here>'
```

### 7. Set Up Admin Access & Supabase Invitation
Before proceeding, contact the project admin to request:

- The official `.env` credentials.  
- An invitation to the Supabase project for database access.

Once access is confirmed, continue with the next steps.

### 8. Apply Database Migrations
Once your environment and dependencies are ready, apply migrations:

```bash
python manage.py migrate
```

### 9. Create a Superuser (Admin Account)
⚠️ **Heads-up:** Before running this step, make sure you have already been invited to the Supabase project and your access has been confirmed. Without the invitation, the database connection will fail.

After successful migrations, create your local Django admin account:

```bash
python manage.py createsuperuser
```

Follow the prompts to enter your email and full name.  
The system will create your account without a password initially.

🔐 **Set Your Password After Creation:**
After creating the superuser, you need to set a password using the Django shell:

```bash
python manage.py shell
```

In the Python shell, run these commands (replace with your actual email and password):

```python
from apps.users.models import User

user = User.objects.get(UserEmail='your-email@example.com')
user.set_password('your-secure-password')
user.save()
exit()
```

🔐 **Note:** Setting a password manually is required because Arcasys uses a custom user model.  
This password will allow you to log in to the **Django Admin Dashboard** and the **Arcasys Admin Page**.

### 10. Run the Django Development Server
Make sure your virtual environment is still active and you’re inside the Arcasys folder:

```bash
python manage.py runserver
```

### 11. Open the Application
Open your browser and visit 👉 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🧠 Notes

- Always activate your virtual environment before running Django commands.  
- If `pip` or `python` points to the wrong version, try using `python3` / `pip3`.  
- You can verify dependencies with:

```bash
pip list
```

---

## 🛠 Git Workflow (Best Practices)

### 1. Check Current Status
```bash
git status
```

### 2. Update Local Main
```bash
git checkout main
git pull origin main
```

### 3. Create a New Branch
```bash
git checkout -b feature/your-feature-name
```
Examples:
- feature/user-accounts
- feature/ui-redesign
- fix/logout-bug

Follow the branch naming convention below:

```bash
main task/module/short description
```

Main Task Types:

| Task Type | Prefix |
|------------|----------|
| Technical | tech |
| Feature | feature |
| Bug Fix | fix |
| Setup | setup |

Examples:
- git branch feature/login/create_login_ui  
- git branch tech/login/change_library  
- git branch fix/login/color_of_button  
- git branch setup/login/auth_library  

### 4. Stage & Commit Changes
```bash
git add .
git commit -m "feature(login): create login ui"
```

Commit Using Proper Format:

```bash
main task(module): short description
```

Examples:
- git commit -m "feature(login): create login ui"  
- git commit -m "tech(login): change library"  
- git commit -m "fix(login): color of the button"  
- git commit -m "setup(login): authentication library"  

### 5. Push Branch to GitHub
```bash
git push origin feature/your-feature-name
```

### 6. Open Pull Request (PR) on GitHub
- Compare your branch → main  
- Add description  
- Request review and merge once approved  

### 7. Sync After Merge
```bash
git checkout main
git pull origin main
```

### 8. Clean Up Old Branches (Optional)
```bash
git branch -d feature/your-feature-name                  # delete locally
git push origin --delete feature/your-feature-name       # delete on GitHub
```

---

## 👥 Team Members

| Name                             | Role                | CIT-U Email                                |
|----------------------------------|---------------------|--------------------------------------------|
| Valmera, Harvey Rod Chirstian L. | Product Owner       | harveyrodchristian.valmera@cit.edu         |
| Yungco, Riggy Maryl L.           | Business Analyst    | riggymaryl.yungco@cit.edu                  |
| Vilocura, Justine C.             | Scrum Master        | justine.vilocura@cit.edu                   |
| Uy, Emman Jay                    | Back-End Developer  | emmanjay.uy@cit.edu                        |
| Ursulo, Lichael Yashua           | Front-End Developer | lichaelyashua.ursulo@cit.edu               |
| Villadarez, Niña Nicole          | Assistant Developer | ninanicole.villadarez@cit.edu              |

---

## 🌐 Deployed Link
Deployment in progress.
