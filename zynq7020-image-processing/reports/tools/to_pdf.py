# -*- coding: utf-8 -*-
"""Convert the final report .docx to PDF using Microsoft Word COM automation.

Robust pattern:
  * work on a UNIQUE temp copy (PID-stamped) so prior runs' locks can't collide;
  * clear any read-only attribute on the copy;
  * open read-write, update fields + TOC, then mark doc.Saved = True so
    ExportAsFixedFormat does not attempt to re-save (the source of the
    "read-only" COM error);
  * always close without saving, quit Word, delete the temp copy;
  * retry the whole thing a few times, killing stray WINWORD between tries.
The original .docx is never modified. Run with the Python that has pywin32.
"""
import os
import shutil
import stat
import subprocess
import time
import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.dirname(HERE)
DOCX = REPORTS + "/最终报告.docx"
PDF = REPORTS + "/最终报告.pdf"

wdExportFormatPDF = 17
wdExportOptimizeForPrint = 0
wdExportAllDocument = 0
wdExportDocumentContent = 0
wdExportCreateHeadingBookmarks = 1
wdDoNotSaveChanges = 0


def kill_word():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def convert_once(tmp):
    shutil.copyfile(DOCX, tmp)
    os.chmod(tmp, stat.S_IWRITE | stat.S_IREAD)
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    doc = None
    try:
        doc = word.Documents.Open(tmp, ReadOnly=False)
        for _ in range(2):
            try:
                doc.Fields.Update()
                try:
                    for i in range(1, doc.TablesOfContents.Count + 1):
                        doc.TablesOfContents(i).Update()
                except Exception:
                    pass
                for sec in doc.Sections:
                    for hf in (sec.Headers, sec.Footers):
                        for h in hf:
                            try:
                                h.Range.Fields.Update()
                            except Exception:
                                pass
            except Exception as e:
                print("field update warn:", e)
        doc.Repaginate()
        doc.Saved = True  # prevent save-on-export -> avoids read-only error
        if os.path.exists(PDF):
            try:
                os.remove(PDF)
            except Exception:
                pass
        doc.ExportAsFixedFormat(
            OutputFileName=PDF,
            ExportFormat=wdExportFormatPDF,
            OpenAfterExport=False,
            OptimizeFor=wdExportOptimizeForPrint,
            Range=wdExportAllDocument,
            Item=wdExportDocumentContent,
            IncludeDocProps=True,
            KeepIRM=True,
            CreateBookmarks=wdExportCreateHeadingBookmarks,
            DocStructureTags=True,
            BitmapMissingFonts=True,
            UseISO19005_1=False,
        )
    finally:
        try:
            if doc is not None:
                doc.Close(SaveChanges=wdDoNotSaveChanges)
        except Exception:
            pass
        try:
            word.Quit()
        except Exception:
            pass


assert os.path.exists(DOCX), "missing docx: " + DOCX
last_err = None
for attempt in range(1, 4):
    tmp = HERE + "/_tmp_pdf_%d_%d.docx" % (os.getpid(), attempt)
    kill_word()
    time.sleep(1.0)
    try:
        convert_once(tmp)
        if os.path.exists(PDF) and os.path.getsize(PDF) > 10000:
            print("PDF_OK", PDF, os.path.getsize(PDF))
            last_err = None
            break
        else:
            last_err = "export produced no/empty pdf"
            print("attempt %d: %s" % (attempt, last_err))
    except Exception as e:
        last_err = repr(e)
        print("attempt %d failed: %s" % (attempt, last_err))
    finally:
        for _ in range(3):
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
                break
            except Exception:
                time.sleep(0.5)

if last_err:
    raise SystemExit("PDF conversion failed: " + str(last_err))
