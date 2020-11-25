from    os    import remove
from   sys    import argv
from    .     import Do
if __name__ == "__main__":
    fn1, fn2, fn3 = argv[1:4]
    fdata1, fdata2 = open(fn1, "rb").read(), open(fn2, "rb").read()
    fdata1, fdata2, ftype1, ftype2 = fdata1 + b"\1" * (-len(fdata1)), fdata2 + b"\1" * (-len(fdata2)), None, None
    for parser in Do(None, None, None, None, None):
        f1, f2 = parser(fdata1), parser(fdata2)
        ftype1, ftype2 = (f1 if f1.identify() else ftype1), (f2 if f2.identify() else ftype2)
    if len({ftype1, ftype2, None}) != 3: exit("Unknown file type or same file types")
    try: Do(ftype1, ftype2, fn1, fn2, fn3)
    except:
        try: remove(fn3)
        except: pass
        Do(ftype2, ftype1, fn2, fn1, fn3)
