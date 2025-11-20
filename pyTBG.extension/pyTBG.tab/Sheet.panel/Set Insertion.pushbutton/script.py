# -*- coding: utf-8 -*-
# pyRevit script: Move viewports and schedules to specified offset on sheet
# Supports filtering Legends and Schedules by name

from pyrevit import revit, DB, script, forms

output = script.get_output()
doc = revit.doc

# Step 1: Collect selected sheets
selection = revit.get_selection()
sheets = [el for el in selection if isinstance(el, DB.ViewSheet)]

if not sheets:
    output.print_md("No sheets selected. Please select at least one sheet.")
    script.exit()

# Step 2: Gather unique ViewTypes (for viewports only)
view_types_set = set()
for sheet in sheets:
    collector = DB.FilteredElementCollector(doc, sheet.Id).OfClass(DB.Viewport)
    for el in collector:
        view = doc.GetElement(el.ViewId)
        view_types_set.add(str(view.ViewType))

# Add "Schedule" as a pseudo type if schedules exist
schedule_exists = False
for sheet in sheets:
    schedule_collector = DB.FilteredElementCollector(doc, sheet.Id).OfClass(DB.ScheduleSheetInstance)
    if schedule_collector.GetElementCount() > 0:
        schedule_exists = True
        break
if schedule_exists:
    view_types_set.add("Schedule")

view_types_list = sorted(list(view_types_set))

# Step 3: Ask user to select ViewTypes
selected_view_types = forms.SelectFromList.show(
    view_types_list,
    multiselect=True,
    title="Select ViewTypes to Move",
    width=400,
    height=300
)

if not selected_view_types:
    output.print_md("No ViewTypes selected. Script stopped.")
    script.exit()

# Step 4: If Legend or Schedule selected, ask for names
selected_legends = []
selected_schedules = []

legend_names_set = set()
schedule_names_set = set()

# Collect names from all selected sheets
for sheet in sheets:
    # Legends
    viewport_collector = DB.FilteredElementCollector(doc, sheet.Id).OfClass(DB.Viewport)
    for el in viewport_collector:
        view = doc.GetElement(el.ViewId)
        if str(view.ViewType) == "Legend":
            legend_names_set.add(view.Name)

    # Schedules
    schedule_collector = DB.FilteredElementCollector(doc, sheet.Id).OfClass(DB.ScheduleSheetInstance)
    for sched in schedule_collector:
        schedule_view = doc.GetElement(sched.ScheduleId)
        schedule_names_set.add(schedule_view.Name)

# Ask for legend names if Legend selected
if "Legend" in selected_view_types and legend_names_set:
    selected_legends = forms.SelectFromList.show(
        sorted(list(legend_names_set)),
        multiselect=True,
        title="Select Legend Names to Move",
        width=400,
        height=300
    )
    if not selected_legends:
        output.print_md("No legend names selected. Script stopped.")
        script.exit()

# Ask for schedule names if Schedule selected
if "Schedule" in selected_view_types and schedule_names_set:
    selected_schedules = forms.SelectFromList.show(
        sorted(list(schedule_names_set)),
        multiselect=True,
        title="Select Schedule Names to Move",
        width=400,
        height=300
    )
    if not selected_schedules:
        output.print_md("No schedule names selected. Script stopped.")
        script.exit()

# Step 5: Ask user for X and Y offsets
x_offset_str = forms.ask_for_string(prompt="Enter X offset from left edge (mm):", default="50")
y_offset_str = forms.ask_for_string(prompt="Enter Y offset from bottom edge (mm):", default="50")

try:
    x_offset_mm = float(x_offset_str)
    y_offset_mm = float(y_offset_str)
except:
    output.print_md("Invalid input. Please enter numeric values.")
    script.exit()

# Convert mm to feet
x_offset_ft = x_offset_mm / 304.8
y_offset_ft = y_offset_mm / 304.8

# Step 6: Move viewports and schedules
with revit.Transaction("Move Viewports and Schedules"):
    for sheet in sheets:
        output.print_md("#### Sheet: {0} - {1}".format(sheet.SheetNumber, sheet.Name))
        moved_count = 0

        # Move viewports
        viewport_collector = DB.FilteredElementCollector(doc, sheet.Id).OfClass(DB.Viewport)
        for el in viewport_collector:
            view = doc.GetElement(el.ViewId)
            view_type = str(view.ViewType)

            if view_type in selected_view_types:
                if view_type == "Legend" and selected_legends and view.Name not in selected_legends:
                    continue

                outline = el.GetBoxOutline()
                vp_min = outline.MinimumPoint  # bottom-left of viewport
                translation = DB.XYZ(x_offset_ft - vp_min.X, y_offset_ft - vp_min.Y, 0)
                DB.ElementTransformUtils.MoveElement(doc, el.Id, translation)
                moved_count += 1
                output.print_md("- Moved {0} ({1}) to offset X={2:.2f}mm, Y={3:.2f}mm".format(
                    view.Name, view.ViewType, x_offset_mm, y_offset_mm
                ))

        # Move schedules
        if "Schedule" in selected_view_types:
            schedule_collector = DB.FilteredElementCollector(doc, sheet.Id).OfClass(DB.ScheduleSheetInstance)
            for sched in schedule_collector:
                schedule_view = doc.GetElement(sched.ScheduleId)
                if selected_schedules and schedule_view.Name not in selected_schedules:
                    continue

                current_point = sched.Point
                translation = DB.XYZ(x_offset_ft - current_point.X, y_offset_ft - current_point.Y, 0)
                DB.ElementTransformUtils.MoveElement(doc, sched.Id, translation)
                moved_count += 1
                output.print_md("- Moved Schedule: {0} to offset X={1:.2f}mm, Y={2:.2f}mm".format(
                    schedule_view.Name, x_offset_mm, y_offset_mm
                ))

        if moved_count == 0:
            output.print_md("_No matching items moved on this sheet_")