
# -*- coding: utf-8 -*-
"""
Workset Summary (IronPython-compatible)

Print all worksets with:
- total instance element count per workset
- list of categories per workset (with per-category counts if enabled)

Config:
- INCLUDE_VIEW_WORKSETS: include View Worksets in the report
- SHOW_CATEGORY_COUNTS: show counts per category (True) or just unique names (False)
- SKIP_EMPTY_WORKSETS: hide worksets with zero elements
"""

# script Info
__title__ = "Worksets Report"
__authors__ = ["Aran Mardoukhi | TBG Consult AB"]

from pyrevit import revit, DB, script

doc = revit.doc
output = script.get_output()

# ---- CONFIG ----
INCLUDE_VIEW_WORKSETS = False   # set True to include View Worksets
SHOW_CATEGORY_COUNTS = True     # set False to show only unique category names per workset
SKIP_EMPTY_WORKSETS = False     # set True to hide worksets with zero counted elements
# ----------------

def get_worksets(curdoc, include_view_worksets):
    """Return a list of Workset objects (sorted by name)."""
    ws_collector = DB.FilteredWorksetCollector(curdoc)
    worksets = list(ws_collector.OfKind(DB.WorksetKind.UserWorkset))
    if include_view_worksets:
        worksets.extend(list(DB.FilteredWorksetCollector(curdoc).OfKind(DB.WorksetKind.ViewWorkset)))
    worksets.sort(key=lambda w: w.Name)
    return worksets

def get_elements_on_workset(curdoc, workset):
    """Return a list of instance elements on the given workset."""
    ws_filter = DB.ElementWorksetFilter(workset.Id)
    collector = DB.FilteredElementCollector(curdoc).WherePasses(ws_filter).WhereElementIsNotElementType()
    return list(collector.ToElements())

def summarize_categories(elements):
    """Return dict: {category_name: count}; skip elements with no category."""
    cat_counts = {}
    for el in elements:
        cat = el.Category
        if cat is None:
            continue
        name = cat.Name
        if name in cat_counts:
            cat_counts[name] += 1
        else:
            cat_counts[name] = 1
    return cat_counts

def main():
    if not doc.IsWorkshared:
        output.print_md(u"⚠️ **This model is not workshared.** Enable Worksharing to use worksets.")
        return

    worksets = get_worksets(doc, INCLUDE_VIEW_WORKSETS)

    if len(worksets) == 0:
        output.print_md(u"ℹ️ **No worksets found** with the current filters.")
        return

    header = u"# Workset Summary\n- Included kinds: **{0}**\n- Counting: **Instance elements** (element types excluded)\n---".format(
        u"User + View" if INCLUDE_VIEW_WORKSETS else u"User only"
    )
    output.print_md(header)

    for ws in worksets:
        elements = get_elements_on_workset(doc, ws)
        total_count = len(elements)

        if SKIP_EMPTY_WORKSETS and total_count == 0:
            continue

        cat_counts = summarize_categories(elements)
        unique_categories = sorted(cat_counts.keys())

        output.print_md(u"## {0}".format(ws.Name))
        output.print_md(u"- Workset ID: `{0}`".format(ws.Id.IntegerValue))
        output.print_md(u"- Total elements: **{0}**".format(total_count))

        if len(unique_categories) == 0:
            output.print_md(u"- Categories: *(none)*")
            output.print_md(u"---")
            continue

        if SHOW_CATEGORY_COUNTS:
            output.print_md(u"**Categories (with counts):**")
            for cat_name in sorted(cat_counts.keys()):
                output.print_md(u"- {0}: `{1}`".format(cat_name, cat_counts[cat_name]))
        else:
            output.print_md(u"**Categories:** " + u", ".join(unique_categories))

        output.print_md(u"---")

if __name__ == "__main__":
    main()
