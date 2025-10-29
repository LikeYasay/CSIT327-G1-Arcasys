from django.db import migrations

DEPARTMENTS = [
    "Marketing Office (MO)",
    "University Registrar’s Office (URO)",
    "Office of Admissions & Scholarships (OAS)",
    "Enrollment Technical Office (ETO)",
    "Finance & Accounting Office (FAO)",
    "Student Success Office (SSO)",
    "Technical Support Group (TSG)",
    "Guidance Center",
    "College of Engineering & Architecture (CEA)",
    "College of Computer Studies (CCS)",
    "College of Arts, Sciences & Education (CASE)",
    "College of Management, Business & Accountancy (CMBA)",
    "College of Nursing & Allied Health Sciences (CNAHS)",
    "College of Criminal Justice (CCJ)",
]

def add_department_data(apps, schema_editor):
    Department = apps.get_model('events', 'Department')
    for dept_name in DEPARTMENTS:
        Department.objects.create(DepartmentName=dept_name)

class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_department_data),
    ]
