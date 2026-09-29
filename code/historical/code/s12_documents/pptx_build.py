# -*- coding: utf-8 -*-
"""
pptx_build.py —— 用 PowerPoint COM 作为「渲染/组装引擎」构建 PPTX
流程：
  1. COM 建一个含 N 张空白版式页的演示文稿 → 模板（自带 presProps/viewProps/tableStyles/theme）
  2. 解包模板，保留除 ppt/slides/* 之外的全部部件
  3. 用生成的 slide{i}.xml 覆盖 ppt/slides/slide{i}.xml
  4. 重新打包 → 必定可被 PowerPoint 打开的 .pptx
"""
import os, re, shutil, zipfile, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PS = ["powershell", "-NoProfile", "-Command"]


def _run(ps, timeout=900):
    r = subprocess.run(PS + [ps], capture_output=True, timeout=timeout)
    return ((r.stdout or b"").decode("utf-8", "replace")
            + (r.stderr or b"").decode("utf-8", "replace")).strip()


def list_layouts():
    ps = ('$pp = New-Object -ComObject PowerPoint.Application;'
          '$pres = $pp.Presentations.Add($false); $i=1;'
          'foreach ($l in $pres.SlideMaster.CustomLayouts) { Write-Output "$i`t$($l.Name)"; $i++ };'
          '$pres.Close(); $pp.Quit()')
    return _run(ps, 300)


def make_template(n_slides, out_pptx, layout_index=12):
    ps = f'''
$ErrorActionPreference = "Stop"
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Add($false)
$lay = $pres.SlideMaster.CustomLayouts.Item({layout_index})
for ($i = 0; $i -lt {n_slides}; $i++) {{ $null = $pres.Slides.AddSlide($pres.Slides.Count + 1, $lay) }}
$pres.SaveAs("{out_pptx}")
$pres.Close(); $pp.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null
Write-Output "TEMPLATE_OK"
'''
    out = _run(ps, 900)
    return ("TEMPLATE_OK" in out), out


def build(slide_xml_list, out_pptx, workdir=None, layout_index=7):
    n = len(slide_xml_list)
    # 注意：PowerPoint COM 写不到 DSH 的临时目录，工作区必须放在项目目录下
    wd = workdir or os.path.join(HERE, "_work")
    os.makedirs(wd, exist_ok=True)
    out_pptx = os.path.abspath(out_pptx).replace("/", "\\")
    tpl = os.path.join(wd, "_tpl.pptx")
    ok, log = make_template(n, tpl, layout_index)
    if not ok:
        raise RuntimeError("COM template failed:\n" + log[-2000:])

    ex = os.path.join(wd, "x")
    if os.path.isdir(ex):
        shutil.rmtree(ex)
    with zipfile.ZipFile(tpl) as z:
        z.extractall(ex)

    sdir = os.path.join(ex, "ppt", "slides")
    os.makedirs(sdir, exist_ok=True)
    for fn in list(os.listdir(sdir)):
        if re.match(r'^slide\d+\.xml$', fn):
            os.remove(os.path.join(sdir, fn))
    for i, xml in enumerate(slide_xml_list, 1):
        with open(os.path.join(sdir, f"slide{i}.xml"), "w", encoding="utf-8") as fh:
            fh.write(xml)

    names = []
    for root, dirs, files in os.walk(ex):
        for f in files:
            names.append(os.path.relpath(os.path.join(root, f), ex).replace("\\", "/"))
    ct = "[Content_Types].xml"
    names.sort(key=lambda x: (x != ct, x))
    if os.path.exists(out_pptx):
        os.remove(out_pptx)
    with zipfile.ZipFile(out_pptx, "w", zipfile.ZIP_DEFLATED) as z:
        for nm in names:
            z.write(os.path.join(ex, nm.replace("/", os.sep)), nm)
    return out_pptx


def verify(pptx, pdf_out=None):
    pptx = os.path.abspath(pptx).replace("/", "\\")
    if pdf_out:
        pdf_out = os.path.abspath(pdf_out).replace("/", "\\")
        os.makedirs(os.path.dirname(pdf_out), exist_ok=True)
    pdf_line = f'$pres.SaveAs("{pdf_out}", 32); Write-Output "PDF_OK";' if pdf_out else ""
    ps = f'''
$ErrorActionPreference = "Stop"
try {{
  $pp = New-Object -ComObject PowerPoint.Application
  $pres = $pp.Presentations.Open("{pptx}", $true, $false, $false)
  Write-Output "VERIFY_OK slides=$($pres.Slides.Count)"
  {pdf_line}
  $pres.Close(); $pp.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null
}} catch {{ Write-Output "VERIFY_FAIL $($_.Exception.Message)" }}
'''
    out = _run(ps, 900)
    return ("VERIFY_OK" in out), out


def export_png(pptx, outdir, width=1600, height=900):
    pptx = os.path.abspath(pptx).replace("/", "\\")
    outdir = os.path.abspath(outdir).replace("/", "\\")
    os.makedirs(outdir, exist_ok=True)
    ps = f'''
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open("{pptx}", $true, $false, $false)
$pres.Export("{outdir}", "PNG", {width}, {height})
$pres.Close(); $pp.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null
Write-Output "PNG_OK"
'''
    out = _run(ps, 900)
    return "PNG_OK" in out, out


if __name__ == "__main__":
    print(list_layouts())
