
# -*- coding: utf-8 -*-
from pyrevit import forms, script
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
import sys


__title__ = "Add Tag"
__authors__ = ["Aran Mardoukhi | TBG Consult AB"]

output = script.get_output()  # Access pyRevit PowerShell console

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# 1. Get selected views
selected_ids = uidoc.Selection.GetElementIds()
views = [doc.GetElement(id) for id in selected_ids if isinstance(doc.GetElement(id), View)]

if not views:
    print("No views selected in Revit. Please select one or more views and run the script.")
    sys.exit()

# 2. Get all model categories and sort alphabetically
categories = [cat for cat in doc.Settings.Categories if cat.CategoryType == CategoryType.Model]
category_names = sorted([cat.Name for cat in categories])

selected_category_name = forms.SelectFromList.show(category_names, title="Select Category")
if not selected_category_name:
    sys.exit()

selected_category = next(cat for cat in categories if cat.Name == selected_category_name)

# 3. Collect ALL annotation family symbols (tag families)
collector = FilteredElementCollector(doc).OfClass(FamilySymbol)
all_tag_symbols = []
for fs in collector:
    if fs.Family and fs.Family.FamilyCategory and fs.Family.FamilyCategory.CategoryType == CategoryType.Annotation:
        all_tag_symbols.append(fs)

if not all_tag_symbols:
    TaskDialog.Show("Error", "No tag families found in the model. Please load tag families first.")
    sys.exit()

# Build list in "Family : Type" format safely
tag_names = []
for fs in all_tag_symbols:
    fam_name = fs.Family.Name if fs.Family else "Unknown Family"
    type_name = fs.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    tag_names.append("{} : {}".format(fam_name, type_name))

tag_names = sorted(tag_names)

selected_tag_fullname = forms.SelectFromList.show(tag_names, title="Select Tag Family Type")
if not selected_tag_fullname:
    sys.exit()

# Find selected tag symbol
selected_tag_symbol = None
for fs in all_tag_symbols:
    fam_name = fs.Family.Name if fs.Family else "Unknown Family"
    type_name = fs.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    if selected_tag_fullname == "{} : {}".format(fam_name, type_name):
        selected_tag_symbol = fs
        break

if not selected_tag_symbol:
    TaskDialog.Show("Error", "Could not find selected tag family type.")
    sys.exit()

# 4. Tag only visible elements in each view
t = Transaction(doc, "Tag Visible Elements")
t.Start()
for view in views:
    # Collect visible elements of the selected category in this view
    visible_elements = FilteredElementCollector(doc, view.Id).OfCategoryId(selected_category.Id).WhereElementIsNotElementType().ToElements()
    found_count = len(visible_elements)
    tagged_count = 0

    for elem in visible_elements:
        try:
            # Determine correct location
            location = None
            if hasattr(elem, "Location") and elem.Location:
                if hasattr(elem.Location, "Point"):  # LocationPoint
                    location = elem.Location.Point
                elif hasattr(elem.Location, "Curve"):  # LocationCurve
                    curve = elem.Location.Curve
                    location = curve.Evaluate(0.5, True)  # Midpoint
            if not location:
                location = XYZ(0, 0, 0)  # Fallback

            IndependentTag.Create(doc, selected_tag_symbol.Id, view.Id, Reference(elem), False, TagOrientation.Horizontal, location)
            tagged_count += 1
        except:
            pass

    # Print report for this view immediately
    print("✔ View: {} | Category: {} | Tag: {} : {} | Found: {} | Tagged: {}".format(
        view.Name,
        selected_category_name,
        selected_tag_symbol.Family.Name,
        selected_tag_symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(),
        found_count,
        tagged_count
    ))
t.Commit()

print("\n=== Tagging Completed for {} views ===".format(len(views)))
