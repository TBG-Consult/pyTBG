
# -*- coding: utf-8 -*-
import sys
from pyrevit import revit, DB, forms


# script Info
__title__ = "Remove Tag"
__authors__ = ["Aran Mardoukhi | TBG Consult AB"]

doc = revit.doc

# STEP 1: Get currently selected views
selected_elements = revit.get_selection()
views = [el for el in selected_elements if isinstance(el, DB.View) and not el.IsTemplate]

if not views:
    print("No views selected in Revit. Please select one or more views and run the script.")
    sys.exit()

# STEP 2: Get ONLY Tag Categories
tag_categories = []
for cat in doc.Settings.Categories:
    if cat.IsTagCategory:  # Only tag categories
        tag_categories.append(cat.Name)

tag_categories = sorted(tag_categories)

# STEP 3: User selects tag categories
selected_tag_categories = forms.SelectFromList.show(tag_categories, multiselect=True, title="Select Tag Categories to Delete")
if not selected_tag_categories:
    print("No tag categories selected. Script cancelled.")
    sys.exit()

report_lines = []

# STEP 4: Delete tags per view and category
with revit.Transaction("Delete Tags by Category"):
    for view in views:
        report_lines.append("View: {0}".format(view.Name))
        for tag_cat_name in selected_tag_categories:
            count = 0
            collector = DB.FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType()
            for el in collector:
                if el.Category and el.Category.Name == tag_cat_name:
                    doc.Delete(el.Id)
                    count += 1
            report_lines.append("    {0}: {1} tags deleted".format(tag_cat_name, count))
        report_lines.append("")

# STEP 5: Print report to PowerShell
for line in report_lines:
    print(line)
