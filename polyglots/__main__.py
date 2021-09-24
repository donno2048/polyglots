from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from os import remove
from os.path import isfile
from . import Types, save
def main():
    Tk().withdraw()
    types = ["*"] + list(map(lambda i: i.__name__.strip("_"), Types))
    fn1 = askopenfilename(filetypes = (((i + " files") if i != "*" else "Auto detect", "*." + i) for i in types))
    if not fn1: exit()
    fn2 = askopenfilename(filetypes = (((i + " files") if i != "*" else "Auto detect", "*." + i) for i in types if not fn1.endswith(i)))
    if not fn2: exit()
    fn3 = asksaveasfilename(filetypes = [("No extension", "*.*")])
    if not fn3: exit()
    fdata1, fdata2 = open(fn1, "rb").read(), open(fn2, "rb").read()
    fdata1, fdata2, ftype1, ftype2 = fdata1 + b"\1" * (-len(fdata1)), fdata2 + b"\1" * (-len(fdata2)), None, None
    for parser in Types:
        f1, f2 = parser(fdata1), parser(fdata2)
        ftype1, ftype2 = (f1 if f1.identify() else ftype1), (f2 if f2.identify() else ftype2)
    if len({ftype1, ftype2, None}) != 3: exit("Unknown file type or same file types")
    try: save(ftype1, ftype2, fn3)
    except:
        if isfile(fn3):
            remove(fn3)
        save(ftype2, ftype1, fn3)
if __name__ == "__main__": main()
