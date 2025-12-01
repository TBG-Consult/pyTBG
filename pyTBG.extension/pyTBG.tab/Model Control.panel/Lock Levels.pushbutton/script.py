# -*- coding: utf-8 -*-
# PyRevit Script: Pin all levels

# script Info
__title__ = "Lock Levels"
__authors__ = ["Aran Mardoukhi | TBG Consult AB"]

from Autodesk.Revit.DB import FilteredElementCollector, Level, Transaction

# Get the current document
doc = __revit__.ActiveUIDocument.Document

# Get all grids
levels = FilteredElementCollector(doc).OfClass(Level).ToElements()

# Start transaction
t = Transaction(doc, "Pin All Levels")
t.Start()

for level in levels:
    if not level.Pinned:
        level.Pinned = True
        print("Pinned Level: {}".format(level.Name))

t.Commit()

print("Pinned {} Level(s).".format(len(levels)))