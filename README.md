# 📂 Marketing Archive  

Arcasys: Marketing Archive Manager is a Django Full Stack web application for **Cebu Institute of Technology – University (CIT-U)** that centralizes event management and archiving. It consolidates scattered event postings into one platform with role-based access, smart search and filters, and integration with external platforms—improving communication, transparency, and accessibility across the university. 

---

### 🚀 How to Run the Project (Every Time)  

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

4. Stage & Commit Changes
```bash
git add .
git commit -m "feature: add logout + password reset"
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





