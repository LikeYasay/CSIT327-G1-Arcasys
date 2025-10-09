# 📂 Arcasys: Marketing Archive Manage 

Arcasys: Marketing Archive Manager is a Django Full Stack web application for **Cebu Institute of Technology – University (CIT-U)** that centralizes event management and archiving. It consolidates scattered event postings into one platform with role-based access, smart search and filters, and integration with external platforms—improving communication, transparency, and accessibility across the university. 

---

## 🛠 Tech Stack  
- **Backend:** Python, Django  
- **Frontend:** HTML, CSS  
- **Database & Deployment:** Supabase, Render
  

### 🚀 Setup & run instructions

When you open VS Code:  

1. Open the terminal (`` Ctrl + ` ``).  
2. Navigate to the project folder:  
```bash
cd MarketingArchive
cd Arcasys   # go inside where manage.py is
```
3. Activate your virtual environment:
```bash
..\env\Scripts\activate
```
4. Run the Django development server:
```bash
python manage.py runserver
```
5. Open your browser at 👉 http://127.0.0.1:8000/

### 🛠 Git Workflow (Best Practices)
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

Follow the branch naming convention below:
```bash
main task/module/short description
```
Main Task Types:
| Task Type   | Prefix   | 
|-------------|----------|
| Technical   | tech     | 
| Feature     | feature  | 
| Bug Fix     | fix      | 
| Setup       | setup    | 

Examples:
- git branch feature/login/create_login ui
- git branch tech/login/change library
- git branch fix/login/color of the button
- git branch setup/login/authentication library

4. Stage & Commit Changes
```bash
git add .
git commit -m "feature(login): create login ui"
```
Commit Using Proper Format
```bash
main task(module): short description
```
Examples:
- git commit -m "feature(login): create login ui"
- git commit -m "tech(login): change library"
- git commit -m "fix(login): color of the button"
- git commit -m "setup(login): authentication library"

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

## 👥 Team Members  

| Name                             | Role                | CIT-U Email                                |
|----------------------------------|---------------------|--------------------------------------------|
| Valmera, Harvey Rod Chirstian L. | Product Owner       | harveyrodchristian.valmera@cit.edu         |
| Yungco, Riggy Maryl L.           | Business Analyst    | riggymaryl.yungco@cit.edu                  |
| Vilocura, Justine C.             | Scrum Master        | justine.vilocura@cit.edu                   |
| Uy, Emman Jay                    | Back-End Developer  | emmanjay.uy@cit.edu                        |
| Ursulo, Lichael Yashua           | Front-End Developer | lichaelyashua.ursulo@cit.edu               |
| Villadarez, Niña Nicole          | Assistant Developer | ninanicole.villadarez@cit.edu              |





