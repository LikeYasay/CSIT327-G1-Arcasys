# 📂 Marketing Archive  

Arcasys: Marketing Archive Manager is a Django Full Stack web application for **Cebu Institute of Technology – University (CIT-U)** that centralizes event management and archiving. It consolidates scattered event postings into one platform with role-based access, smart search and filters, and integration with external platforms—improving communication, transparency, and accessibility across the university.  

---

## ⚙️ Initial Setup (First Time Only)  

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/your-repo/MarketingArchive.git
   cd MarketingArchive/Arcasys
   ```

2. **Create and Activate a Virtual Environment**  
   ```bash
   python -m venv env
   ..\env\Scripts\activate   # for Windows
   source env/bin/activate   # for macOS/Linux
   ```

3. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` File**  
   In the `Arcasys` folder (same level as `manage.py`), create a file named `.env` and paste the following:  

   ```env
   # Supabase PostgreSQL (Session Pooler)
   DATABASE_URL='postgresql://postgres.thpjejmmcfijbdaflpcf:Arc@sys02584569173@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require'

   # Django Settings
   SECRET_KEY='django-insecure-&j*xdu_jyq+41qu6fyp&y*%x(#_ob9pu9pc_&i50_x-2ddowkx'
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com

   # Email Configuration (Gmail)
   EMAIL_HOST_USER=arcasys.marketing.archive@gmail.com
   EMAIL_HOST_PASSWORD=cjndfhippkvqwmww
   DEFAULT_FROM_EMAIL='Marketing Archive <arcasys.marketing.archive@gmail.com>'
   ```

   > ⚠️ Everyone will connect to the same Supabase database. Please be careful when applying migrations or modifying data.  

5. **Apply Database Migrations**  
   ```bash
   python manage.py migrate
   ```

---

## 🚀 Running the Project  

Whenever you want to run the project:  

1. Activate the virtual environment:  
   ```bash
   ..\env\Scripts\activate   # Windows
   source env/bin/activate   # macOS/Linux
   ```

2. Start the development server:  
   ```bash
   python manage.py runserver
   ```

3. Open your browser at 👉 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  

---

## 🛠 Git Workflow (Best Practices)  

1. Check Current Status  
   ```bash
   git status
   ```

2. Update Local Main  
   ```bash
   git checkout main
   git pull origin main
   ```

3. Create a New Branch  
   ```bash
   git checkout -b feature/your-feature-name
   ```
   Examples:
   - feature/user-accounts  
   - feature/ui-redesign  
   - fix/logout-bug  

4. Stage & Commit Changes  
   ```bash
   git add .
   git commit -m "feature(App-Name): add logout + password reset"
   ```

5. Push Branch to GitHub  
   ```bash
   git push origin feature/your-feature-name
   ```

6. Open Pull Request (PR) on GitHub  
   - Compare your branch → main  
   - Add description  
   - Request review and merge once approved  

7. Sync After Merge  
   ```bash
   git checkout main
   git pull origin main
   ```

8. Clean Up Old Branches  
   ```bash
   git branch -d feature/your-feature-name                  # delete locally
   git push origin --delete feature/your-feature-name       # delete on GitHub
   ```
