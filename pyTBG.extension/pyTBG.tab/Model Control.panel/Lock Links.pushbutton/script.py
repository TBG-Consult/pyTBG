# -*- coding: utf-8 -*-
# PyRevit Script: Pin all links

# script Info
__title__ = "Lock Links"
__authors__ = ["Aran Mardoukhi | TBG Consult AB"]

from Autodesk.Revit.DB import FilteredElementCollector, RevitLinkInstance, Transaction

# Get the current document
doc = __revit__.ActiveUIDocument.Document

# Get all grids
links = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()

# Start transaction
t = Transaction(doc, "Pin All Links")
t.Start()

for link in links:
    if not link.Pinned:
        link.Pinned = True
        print("Pinned Link: {}".format(link.Name))

t.Commit()

print("Pinned {} link(s).".format(len(links)))