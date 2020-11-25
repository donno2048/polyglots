from    binascii    import    crc32
from       io       import    BytesIO
from       os       import    remove, system
from     struct     import    unpack, pack
from     tarfile    import    TarFile, open as topen
from     zipfile    import    ZipInfo, ZipFile
class FType(object):
    def __init__(self, data=""): self.precav_o, self.precav_s, self.prewrap, self.postwrap, self.start_o, self.bAppData, self.type, self.data, self.cut, self.bParasite, self.parasite_o, self.parasite_s, self.bZipper = 0, 0, 0, 0, 0, True, "", data, None, False, None, None, False
    def identify(self): return self.data.startswith(self.MAGIC)
    def fixformat(self, data, delta=0): return data
    def wrap(self, data): return data
    def getCut(self): return self.cut
    def getPrewrap(self, parasite_s): return self.prewrap
    def fixparasite(self, parasite): return parasite
    def normalize(self): return
    def wrappend(self, data): return data
    def wrapparasite(self, fparasite, d, cut): return d if not fparasite.wrappend(b"") else d + fparasite.wrappend(b"\0" * self.postwrap + self.data[cut:])[:len(fparasite.wrappend(b"\0" * self.postwrap + self.data[cut:])) - len(b"\0" * self.postwrap + self.data[cut:])]
    def cutparasite(self, fparasite, d, cut):
        prewrap_s = self.getPrewrap(len(d))
        if fparasite.precav_s:d = d[cut+prewrap_s:]
        return (None, []) if (fparasite.precav_s and self.getPrewrap(len(d[cut+prewrap_s:])) != prewrap_s) else (prewrap_s, d)
    def parasitize(self, fparasite):
        self.normalize()
        cut = self.getCut()
        prewrap_s, parasite = self.cutparasite(fparasite, self.wrapparasite(fparasite, self.fixparasite(fparasite.data), cut), cut).items()
        return (None, []) if prewrap_s is None or len(self.fixparasite(fparasite.data)) > self.parasite_s else (self.fixformat(self.data[:cut] + self.wrap(parasite) + self.data[cut:], len(self.wrap(parasite))), [cut + prewrap_s, cut + len(self.wrap(parasite)) - self.postwrap,])
    def zipper(self, fhost): return None, []
class _7z(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.start_o, self.bParasite = "7-Zip", "7Z", b"7z\xbc\xaf\x27\x1C", data, 4*1024*1024, False
class ar(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.MAGIC_s, self.data, self.bParasite, self.parasite_s, self.bAppData, self.hdr_s, self.cut, self.parasite_o, self.prewrap = "Ar / Unix archiver", "AR", b"!<arch>\n", 8, data, True, 0xffffff, True, 60, 8, 68, 60
    def makeHdr(self, filename, timestamp=0, owner=0, group=0, perms=0, size=0): return b"".join([filename.ljust(16, b" "), (b"%i" % timestamp).ljust(12, b" "), (b"%i" % owner).ljust(6, b" "), (b"%i" % group).ljust(6, b" "), (b"%03i" % perms).ljust(8, b" "), (b"%i" % size).ljust(10, b" "), b"`\n"])
    def wrap(self, data):
        if len(data) % 2: data += b"\n"
        return self.makeHdr(b"\43"+b"1/0", size=len(data)) + data
    def wrappend(self, data): return self.wrap(data)
class arj(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.start_o = "Arj / Archived by Robert Jung", "Arj", bytes([0x60, 0xEA]), data, False, 131072
class bmp(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.cut, self.parasite_o, self.parasite_s = "BMP / Windows Bitmap", "BMP", b"BM", data, True, 0x40, 0x40, 0xFFFFFFFF - 1
    def getCut(self):
        self.cut = unpack("<I", self.data[0xA:0xA+4])[0]
        return self.cut
    def fixformat(self, d, delta):
        d = d[:2] + pack("<I", unpack("<I", d[2:2+4])[0] + delta) + d[2+4:]
        return d[:0xA] + pack("<I", unpack("<I", d[0xA:0xA+4])[0] + delta) + d[0xA+4:]
class bpg(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.FLAGS_o, self.cut, self.prewrap, self.data, self.bAppData, self.bParasite, self.parasite_o, self.parasite_s = "BPG / Better Portable Graphics", "BPG", b"BPG\xFB", 5, 9, 3, data, False, True, 0x10, 0xffffff
    def wrap(self, data): return bytes(bpg1(len(bytes(bpg1(len(data)))) + len(tag_s) + len(data))) + bytes(bpg1(1)) + bytes(bpg1(len(data))) + data
    def fixformat(self, d, delta): return d[:self.FLAGS_o] + bytes([d[self.FLAGS_o] | 8]) + d[self.FLAGS_o + 1:]
    def getCut(self):
        width, delta = bpg2(self.data[self.FLAGS_o + 1:])
        height, delta = bpg2(self.data[self.FLAGS_o + 1 + delta:])
        image_l, delta = bpg2(self.data[self.FLAGS_o + 1 + 2 * delta:])
        off = self.FLAGS_o + 1 + 3 * delta
        if self.data[self.FLAGS_o] >> 3:
                ext_l, delta = bpg2(self.data[off:])
                off += delta
                toff = 0
                while (toff < ext_l):
                    ext_tag, delta = bpg2(self.data[off + toff:])
                    toff += delta
                    ext_tag_l, delta = bpg2(self.data[off + toff:])
                    toff += delta
                    toff += ext_tag_l
                off += ext_l
        self.cut = off
        return self.cut
    def getPrewrap(self, parasite_s):
        assert len(self.wrap(b"\0" * parasite_s)) - parasite_s >= self.prewrap
        self.prewrap = len(self.wrap(b"\0" * parasite_s)) - parasite_s
        return len(self.wrap(b"\0" * parasite_s)) - parasite_s
class bzip2(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite = "BZ2 / bzip2", "BZ2", b"BZh", data, False
class cab(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.coffFiles_o, self.cFolders_o, self.CFHEADER_s, self.coffCabStart_o, self.CFFOLDER_s, self.DESC, self.TYPE, self.MAGIC, self.cbCabinet_o, self.data, self.start_o, self.bAppData, self.bParasite, self.parasite_s, self.prewrap, self.parasite_o, self.cut = 0x10, 0x1a, 0x24, 0, 0x8, "CAB / Microsoft Cabinet", "CAB", b"MSCF", 0x8, data, 0, True, True, 0xffffff, 0, 0x24, 0x24
    def identify(self):
        if not self.data.startswith(self.MAGIC): return False
        self.cFolders = unpack("<H", self.data[self.cFolders_o:self.cFolders_o+2])[0]
        return True
    def getCut(self):
        self.cut += 0x8 * self.cFolders
        return self.cut
    def fixformat(self, d, delta):
        d = d[:self.cbCabinet_o] + pack("<I", unpack("<I", d[self.cbCabinet_o:self.cbCabinet_o+4])[0] + delta) + d[self.cbCabinet_o+4:]
        d, o = d[:self.coffFiles_o] + pack("<I", unpack("<I", d[self.coffFiles_o:self.coffFiles_o+4])[0] + delta) + d[self.coffFiles_o+4:], self.CFHEADER_s
        for i in range(self.cFolders):
             d = d[:o + self.coffCabStart_o] + pack("<I", unpack("<I", d[o + self.coffCabStart_o:o + self.coffCabStart_o+4])[0] + delta) + d[o + self.coffCabStart_o+4:]
             o += self.CFFOLDER_s
        return d
class cpio(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.HDR_s, self.trailer, self.data, self.bParasite, self.parasite_s, self.start_o, self.bAppData, self.cut, self.parasite_o, self.prewrap = "CPIO", "CPIO", b"\xc7\x71", 0x1A, b"TRAILER!!!", data, True, 0xffffffff, 0, True, 0, 0x1A, 0x1A
    def makeHdr(self, filename, data): return b"".join([b"\xc7\x71\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0", pack("<H", len(filename) + 1), b"\0\0", pack("<H", len(data) + 1), filename , b"\0"*((len(filename) + 1) % 2 + 1), data])
    def fixformat(self, d, delta):
        if len(d) % 512: d = d + b"\0" * (512 - (len(d) % 512))
        assert not(len(d) % 512)
        return d
    def wrap(self, data): return self.makeHdr(b"", data)
class dcm(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.precav_s, self.cut, self.bAppData, self.bParasite, self.parasite_o, self.parasite_s, self.prewrap, self.bZipper = "DICOM / Digital Imaging and Communications in Medicine", "DCM", b"DICM", data, 128, 0x84, True, True, 0x160, 0xFFFFFFFF, 12, True
    def identify(self): return self.data[0x80:].startswith(self.MAGIC)
    def wrap(self, parasite): return b"".join([b"\x09\0\0\0OB\0\0", pack("<I", len(parasite)), parasite])
    def wrappend(self, data): return self.wrap(data)
    def getCut(self): return self.cut
    def zipper(self, zero):
        zero.normalize()
        tdata = self.data[:self.cut] + self.wrap(zero.postwrap * b"\0" + zero.data[zero.cut:]) + self.data[self.cut:]
        nhead = tdata[zero.cut + zero.prewrap:self.cut + self.prewrap]
        nheadwrap = zero.wrap(nhead)
        return (None, []) if ((len(nhead) > zero.parasite_s) or zero.cut is None or not(zero.bAppData) or (zero.cut + zero.prewrap > self.precav_s)) else (zero.fixformat(b"".join([zero.data[:zero.cut], nheadwrap, tdata[self.cut + self.prewrap + zero.postwrap:]]), len(nheadwrap)), [self.precav_s, self.cut + self.prewrap, self.cut + self.prewrap + zero.postwrap - zero.cut + len(zero.data) + self.postwrap])
class ebml(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.data, self.MAGIC = "EBML / Extensible Binary Meta Language [container]", "EBML", data,  b"\x1A\x45\xDF\xA3"
class flac(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bAppData, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap, self.postwrap = "Flac / native Free Lossless Audio Codec", "Flac", b"fLaC", data, True, True, 8, 0xFFFFFF, 4, 8, 0
    def getCut(self): return 8 + unpack(">I", (b"\0" + self.data)[5:8][0:4])[0]
    def wrap(self, data, id=b"junk"): return b"".join([b"\4", pack(">I", len(data) + 4)[1:], id, data])
class flv(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut = "FLV / Flash Video", "FLV", b"FLV\1", data, True, 9, 4294967294, 9
    def fixformat(self, d, delta): return d[:5] + pack(">I", unpack(">I", d[5:9])[0] + delta) + d[9:]
class gif(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap, self.postwrap = "GIF / Graphics Interchange Format", "GIF", data, True, 16, 255, 13, 3, 1
    def identify(self): return self.data.startswith(b"GIF87a") or self.data.startswith(b"GIF89a")
    def wrap(self, parasite): return b"!\xfe" + bytes([len(parasite)]) + parasite + b"\0"
    def getCut(self):
        f, flags = self.data[0xA], {}
        for l in [["GlobalColorTable",1], ["ColorResolution", 3], ["Sort", 1], ["GCTSize", 3]][::-1]:
            flags[l[0]] = f & (2**(l[1]+1)-1)
            f >>= l[1]
        self.cut = 13 + (3 * (2<<(flags["GCTSize"])) if flags["GlobalColorTable"] == 1 else 0)
        return self.cut
class gzip(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.start_o, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "gzip", "GZ", b"\x1f\x8b", data, 0, True, 12, 0xFFFF, 10, 2
    def wrap(self, data): return b"".join([pack("<H", len(data)), data])
    def fixformat(self, d, delta): return d[:3] + bytes([d[3] + 4]) + d[4:]
class icc(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.size_o, self.size_s, self.tagcount_s, self.table_o, self.tagcount_o, self.sig_s, self.sig_o, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "ICC / International Color Consortium profiles", "ICC", b"acsp", 0, 4, 4, 132, 0x80, 4, 0x24, data, True, 132, 0xFFFFFFFF, 132, 0
    def identify(self):
        if self.data[self.sig_o:self.sig_o+self.sig_s] != self.MAGIC: return False
        self.size =  unpack(">I", self.data[self.size_o:self.size_o+4])[0]
        self.tagcount = unpack(">I", self.data[self.tagcount_o:self.tagcount_o+4])[0]
        return True
    def getCut(self):
        self.cut = self.parasite_o + 3*4*(self.tagcount+1)
        return self.cut
    def fixformat(self, d, delta):
        ptr = self.tagcount_o + self.tagcount_s + 4
        for i in range(self.tagcount):
            d = d[:ptr] + pack(">I", unpack(">I", d[ptr:ptr+4])[0] + delta + 12) + d[ptr+4:]
            ptr += 3*4
        self.tagcount += 1
        self.size += delta + 12
        return b"".join([pack(">I", self.size), d[self.size_s+self.size_o:self.tagcount_o], pack(">I", self.tagcount), b"junk", pack(">I", self.table_o + 12 * self.tagcount), pack(">I", delta), d[self.table_o:]])
class ico(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.data, self.bParasite, self.parasite_o, self.parasite_s = "ICO", "ICO", data, True, 0x70, 0xFFFFFFFF
    def identify(self):
        if not self.data.startswith(b"\0\0\1\0"): return False
        self.count = unpack("<H", self.data[4:6])[0]
        return True
    def getCut(self):
        self.cut = 6 + self.count * 0x10
        return self.cut
    def fixformat(self, d, delta):
        offset = 18
        for i in range(self.count):
            d = d[:offset] + pack("<I", unpack("<I", d[offset:offset+4])[0] + delta) + d[offset+4:]
            offset += 0x10
        return d
class id3v1(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.start_o, self.bParasite, self.bAppData = "ID3v1 [Tag]", "ID3v1", b"TAG", data, 0, False, False
    def identify(self): return self.data[-128:].startswith(self.MAGIC)
class id3v2(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.cut, self.parasite_o, self.parasite_s, self.bAppData, self.prewrap = "ID3v2 [Tag]", "ID3v2", b"ID3\3\0", data, True, 0xA, 0x14, 0xffffff, True, 10
    def wrap(self, data, type_=b"JUNK"): return b"".join([type_, id3v2_1(len(data)), b"\0\0", data])
    def fixformat(self, d, delta):
        b3, b2, b1, b0 = unpack('>4B', d[6:10][:4])
        return b"".join([d[:6], id3v2_1(((b3 * 0x80 + b2) * 0x80 + b1) * 0x80 + b0 + delta), d[10:]])
class ilda(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "ILDA / International Laser Display Association vector images", "ILDA", b"ILDA", data, True, 32, 196605, 0, 32
    def fixparasite(self, parasite): return parasite + (3-(len(parasite) % 3)) * b"\0" if (len(parasite) % 3) else parasite
    def wrap(self, data): return b"".join([b"ILDA", b"\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", pack(">H", len(data) // 3), b"\x00\x00\x00\x00\x00\x00", data])
class iso(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.data, self.bParasite, self.precav_s = "ISO 9660 image [dump]", "ISO", data, False, 0x8000
    def identify(self): return self.data[0x8000:].startswith(b"\1CD001\1")
class java(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.bAppData, self.cut, self.poolcount_o, self.prewrap = "Java Class", "Java", b"\xca\xfe\xba\xbe", data, True, 0x9, 0xffff, False, 0x0a, 8, 3
    def identify(self):
        if not self.data.startswith(self.MAGIC): return False
        self.poolcount = unpack(">H", self.data[self.poolcount_o:self.poolcount_o + 2])[0]
        return True
    def getCut(self):
        off = 0x0a
        for _ in range(self.poolcount - 1):
            if self.data[off] == 1: off += unpack(">H", self.data[off:off+2])[0] + 3
            elif self.data[off] in [7, 8, 16]: off += 3
            elif self.data[off] == 15: off += 4
            elif self.data[off] in [3, 4, 9, 10, 11, 12, 18]: off += 5
            elif self.data[off] in [5, 6]: off += 9
            else: return None
        self.cut = off
        return self.cut
    def wrap(self, parasite): return b"\1" + pack(">H", len(parasite)) + parasite
    def fixformat(self, d, delta): return d[:self.poolcount_o] + pack(">H", self.poolcount + 1) + d[self.poolcount_o+2:]
class jp2(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "JP2 / JPEG 2000", "JP2", b"\0\0\0\x0cjP  ", data, True, 0x28, 0xFFFFFFFF, 0x20, 8
    def identify(self): return self.data.startswith(self.MAGIC)
    def wrap(self, data): return pack(">I", len(data) + 8) + b"free" + data
class jpg(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "JFIF / JPEG File Interchange Format", "JPG", b"\xFF\xD8", data, True, 6, 65533, 2, 4
    def wrap(self, parasite, marker=b"\xFE"): return b"".join([b"\xFF", marker, pack(">H", len(parasite)+2), parasite])
class lnk(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite = "Shell Link", "LNK", b'L\x00\x00\x00\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00F', data, False
class mp4(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.ATOM, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "MP4 / Iso Base Media Format [container]", "MP4", b"ftyp", data, True, 0x8, 0xFFFFFFFF, 0, 8
    def identify(self): return (self.data[4:8] == self.ATOM) and (self.data[8:11] != b"hei")
    def wrap(self, data): return pack(">I", len(data) + 8) + b"free" + data
    def fixformat(self, d, delta):
        offset = 0
        for i in range(d.count(b"stco")):
            offset = d.find(b"stco", offset)
            offcount = unpack(">I", d[offset+8:offset+12])[0]
            if (unpack(">I", d[offset+4:offset+8])[0]) or ((offcount + 4) * 4 != unpack(">I", d[offset-4:offset])[0]): continue
            offset += 12
            offsets = unpack(">%iI" % offcount, d[offset:offset + offcount * 4])
            offsets = [i + delta for i in offsets]
            d = d[:offset] + pack(">%iI" % offcount, *offsets) + d[offset+offcount*4:]
            offset += 4 * offcount
        return d
class nes(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.TRAINER_o, self.TRAINER_s, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "iNES rom", "NES", b"NES\x1a", 16, 512, data, True, 16, 512, 16, 0
    def normalize(self):
        self.data = bytearray(self.data)
        self.data[6] |= 4
    def fixparasite(self, parasite): return parasite + bytes([0]) * (512-len(parasite))
class ogg(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bAppData, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap, self.postwrap = "Ogg [container]", "OGG", b"OggS", data, True, True, 0x1C, 0xFFFF, 0, 0x1c, 0
    def getCut(self):
        self.cut = self.data[1:].find(b"OggS") + 1
        return self.cut
    def getPrewrap(self, parasite_s):
        self.prewrap = len(self.wrap(b"\0" * parasite_s)) - parasite_s
        return self.prewrap
    def wrap(self, data, id=b"junk"):
        header, val = b"".join([b"OggS\0\2\0\0\0\0\0\0\0\0JUNK\0\0\0\0\0\0\0\0", bytes([1 + len(data) // 256]), bytes([0xff] * (1 + len(data) // 256 - 1) + [len(data) % 256])]), 0
        for s in (header + data): val = ((val << 8) ^ [0, 79764919, 159529838, 222504665, 319059676, 398814059, 445009330, 507990021, 638119352, 583659535, 797628118, 726387553, 890018660, 835552979, 1015980042, 944750013, 1276238704, 1221641927, 1167319070, 1095957929, 1595256236, 1540665371, 1452775106, 1381403509, 1780037320, 1859660671, 1671105958, 1733955601, 2031960084, 2111593891, 1889500026, 1952343757, 2552477408, 2632100695, 2443283854, 2506133561, 2334638140, 2414271883, 2191915858, 2254759653, 3190512472, 3135915759, 3081330742, 3009969537, 2905550212, 2850959411, 2762807018, 2691435357, 3560074640, 3505614887, 3719321342, 3648080713, 3342211916, 3287746299, 3467911202, 3396681109, 4063920168, 4143685023, 4223187782, 4286162673, 3779000052, 3858754371, 3904687514, 3967668269, 881225847, 809987520, 1023691545, 969234094, 662832811, 591600412, 771767749, 717299826, 311336399, 374308984, 453813921, 533576470, 25881363, 88864420, 134795389, 214552010, 2023205639, 2086057648, 1897238633, 1976864222, 1804852699, 1867694188, 1645340341, 1724971778, 1587496639, 1516133128, 1461550545, 1406951526, 1302016099, 1230646740, 1142491917, 1087903418, 2896545431, 2825181984, 2770861561, 2716262478, 3215044683, 3143675388, 3055782693, 3001194130, 2326604591, 2389456536, 2200899649, 2280525302, 2578013683, 2640855108, 2418763421, 2498394922, 3769900519, 3832873040, 3912640137, 3992402750, 4088425275, 4151408268, 4197601365, 4277358050, 3334271071, 3263032808, 3476998961, 3422541446, 3585640067, 3514407732, 3694837229, 3640369242, 1762451694, 1842216281, 1619975040, 1682949687, 2047383090, 2127137669, 1938468188, 2001449195, 1325665622, 1271206113, 1183200824, 1111960463, 1543535498, 1489069629, 1434599652, 1363369299, 622672798, 568075817, 748617968, 677256519, 907627842, 853037301, 1067152940, 995781531, 51762726, 131386257, 177728840, 240578815, 269590778, 349224269, 429104020, 491947555, 4046411278, 4126034873, 4172115296, 4234965207, 3794477266, 3874110821, 3953728444, 4016571915, 3609705398, 3555108353, 3735388376, 3664026991, 3290680682, 3236090077, 3449943556, 3378572211, 3174993278, 3120533705, 3032266256, 2961025959, 2923101090, 2868635157, 2813903052, 2742672763, 2604032198, 2683796849, 2461293480, 2524268063, 2284983834, 2364738477, 2175806836, 2238787779, 1569362073, 1498123566, 1409854455, 1355396672, 1317987909, 1246755826, 1192025387, 1137557660, 2072149281, 2135122070, 1912620623, 1992383480, 1753615357, 1816598090, 1627664531, 1707420964, 295390185, 358241886, 404320391, 483945776, 43990325, 106832002, 186451547, 266083308, 932423249, 861060070, 1041341759, 986742920, 613929101, 542559546, 756411363, 701822548, 3316196985, 3244833742, 3425377559, 3370778784, 3601682597, 3530312978, 3744426955, 3689838204, 3819031489, 3881883254, 3928223919, 4007849240, 4037393693, 4100235434, 4180117107, 4259748804, 2310601993, 2373574846, 2151335527, 2231098320, 2596047829, 2659030626, 2470359227, 2550115596, 2947551409, 2876312838, 2788305887, 2733848168, 3165939309, 3094707162, 3040238851, 2985771188][s ^ (val >> 24)]) & 0xffffffff
        return (header + data)[:0x16] + pack("<I", val) + (header + data)[0x16+4:]
class pcap(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bAppData, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "Packet Capture", "PCAP", b"\xd4\xc3\xb2\xa1", data, False, True, 0x5E, 2621444, 0x18, 70
    def wrap(self, parasite): return b"".join([b"\0\0\0\0\0\0\0\0", 2 * pack("<I", len(parasite) + 54), b'\0\0\0\0\0\0\0\0\0\0\0\0\x08\0E\0\0\0\0\0@\0\0\x06\0\0\0\0\0\x01\0\0\0\x01\0\0\0\0\0\0\0\0\0\0\0\0P\x18\x02\0\0\0\0\0']) + parasite
class pcapng(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bAppData, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap, self.postwrap = "Packet Capture Next Generation", "PCAPNG", b"\x0a\x0d\x0d\x0a", data, False, True, 0x28, 0xFFFFFFFF, 0x1c, 12, 4
    def fixparasite(self, parasite): return parasite + (4-(len(parasite) % 4)) * b"\0" if len(parasite) % 4 else parasite
    def wrap(self, parasite): return b"".join([b"\xAD\x0B\0\x40", pack("<I", len(parasite) + 16), b"Ange", parasite, pack("<I", len(parasite) + 16)])
class pdf(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.start_o, self.bAppData, self.bParasite, self.parasite_o, self.parasite_s, self.cut = "Portable Document Format", "PDF", b"%PDF-1", data, 1016, True, True, 0x30, 0xFFFFFFFF, 0x30
    def fixformat(self, contents, delta):
        startXREF = contents.find(b"\nxref\n0 ") + 1
        xrefLines = [b"xref", b"0 %i" % int(contents[startXREF:contents.find(b" \n\n", startXREF) + 1].splitlines()[1].split(b" ")[1]), b"0000000000 00001 f "]
        for i in range(1, int(contents[startXREF:contents.find(b" \n\n", startXREF) + 1].splitlines()[1].split(b" ")[1])): xrefLines.append(b"%010i 00000 n " % (contents.find(b"\n%i 0 obj\n" % i) + 1))
        contents = contents[:startXREF] + b"\n".join(xrefLines) + contents[contents.find(b" \n\n", startXREF) + 1:]
        return (contents[:contents.find(b"\nstartxref\n", contents.find(b" \n\n", startXREF) + 1) + len(b"\nstartxref\n")] + b"%i" % startXREF + contents[contents.find(b"\n%%EOF", contents.find(b"\nstartxref\n", contents.find(b" \n\n", startXREF) + 1) + len(b"\nstartxref\n")):]).replace(b"_PAYLOADL_", b"%010i" % delta)[:-1]
    def normalize(self):
        open("host.pdf", "wb").write(self.data)
        open("blank.pdf", "wb").write(b'%PDF-1.3\n%\x00\xb5\xc2\xb6\n\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n\n2 0 obj\n<</Kids[3 0 R]/Type/Pages>>\nendobj\n\n3 0 obj\n<</Type/Page/Contents 4 0 R>>\nendobj\n\n4 0 obj\n<<>>\nendobj\n\nxref\n0 5\n0000000000 65536 f \n0000000016 00000 n \n0000000062 00000 n \n0000000106 00000 n \n0000000152 00000 n \n\ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n173\n%%EOF\n')
        rval = system('mutool merge -o merged.pdf blank.pdf host.pdf') #
        remove('host.pdf')
        remove('blank.pdf')
        dm = open("merged.pdf", "rb").read()
        remove('merged.pdf')
        count, kids = int(dm[dm.find(b"/Count ") + 7:dm.find(b"/", dm.find(b"/Count ") + 7)]) - 1, dm[dm.find(b"/Kids[") + 6:dm.find(b"]", dm.find(b"/Kids[") + 6)][6:]
        assert kids.startswith(b"4 0 R ")
        self.data = (b"%%PDF-1.3\n%%\xC2\xB5\xC2\n\n1 0 obj\n<</Length 2 0 R>>\nstream\n\nendstream\nendobj\n\n2 0 obj\n_PAYLOADL_\nendobj\n\n3 0 obj\n<<\n  /Type /Catalog\n\n /Pages 4 0 R\n>>\nendobj\n\n4 0 obj\n<</Type/Pages/Count %(count)i/Kids[%(kids)s]>>\nendobj\n" % {"count".encode():locals()["count"], "kids".encode():locals()["kids"]}) + dm[dm.find(b"5 0 obj"):].replace(b"/Parent 2 0 R", b"/Parent 4 0 R").replace(b"/Root 1 0 R", b"/Root 3 0 R")
class pdfc(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.MAGIC_o, self.data, self.start_o, self.precav_s, self.bAppData, self.bParasite = "Portable Document Format", "PDF", b"%PDF-1", 1018, data, 0, 1018, True, False
    def identify(self): return self.data[self.MAGIC_o:self.MAGIC_o + 20].startswith(self.MAGIC)
class pe_hdr(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bAppData, self.bParasite, self.cut, self.prewrap, self.parasite_o, self.parasite_s = "Portable Executable (hdr)", "PE(hdr)", b"MZ", data, True, True, 2, 0, 0x50, 0x100
    def fixparasite(self, parasite): return parasite + (4-(len(parasite) % 4)) * b"\0" if len(parasite) % 4 else parasite
    def parasitize(self, fparasite):
        peHDR = self.data[self.data.find(b"PE\0\0"):0x200].rstrip(b"\0")
        return (None, []) if (0x40 + len(self.fixparasite(fparasite.data)) + len(peHDR) > 0x200) else (b"".join([b"MZ", b"\0" * 58, pack("<I", 0x40 + len(self.fixparasite(fparasite.data))), self.fixparasite(fparasite.data), peHDR[:0x54] + pack("<I", unpack("<I", peHDR[0x54:88])[0] + len(self.fixparasite(fparasite.data))) + peHDR[88:], b"\0" * (448 + len(self.fixparasite(fparasite.data)) - len(peHDR[:0x54] + pack("<I", unpack("<I", peHDR[0x54:88])[0] + len(self.fixparasite(fparasite.data))) + peHDR[88:])), self.data[0x200:]]), [0x40, 0x40 + len(self.fixparasite(fparasite.data))])
class pe_sec(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut = "Portable Executable (hdr)", "PE(sec)", b"MZ", data, True, 0x200, 0xFFFFFFFF, 0x200
    def parasitize(self, fparasite):
        peHDR = self.data[self.data.find(b"PE\0\0"):]
        if unpack("<H", peHDR[4:6])[0] not in [0x014C, 0x8664]: exit(print("ERROR: unknown arch"))
        SecTblOff = 120 + unpack("<I", peHDR[0x74:120])[0] * 8 if unpack("<H", peHDR[4:6])[0] == 0x014C else 136 + unpack("<I", peHDR[0x84:136])[0] * 8
        PEoff, HdrLen, NumSec, SecTblOff, SectsStart = self.data.find(b"PE\0\0"), SecTblOff + unpack("<H", peHDR[6:8])[0] * 0x28, unpack("<H", peHDR[6:8])[0], self.data.find(b"PE\0\0") + SecTblOff, unpack("<I", peHDR[SecTblOff+0x14:SecTblOff+0x14+4])[0]
        parasite = fparasite.data + b"\0" * (self.parasite_o - (len(fparasite.data) % self.parasite_o))
        host = self.data[:unpack("<I", self.data[SecTblOff + 0x14:SecTblOff + 24])[0]] + parasite + self.data[unpack("<I", self.data[SecTblOff + 0x14:SecTblOff + 24])[0]:]
        for i in range(NumSec): host = host[:SecTblOff + i*0x28 + 0x14] + pack("<I", unpack("<I", host[SecTblOff + i * 0x28 + 0x14:SecTblOff + i * 0x28 + 24])[0] + len(parasite)) + host[SecTblOff + i*0x28 + 24:]
        return host, []
class png(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap, self.postwrap = "PNG / Portable Network Graphics", "PNG", b"\x89PNG\r\n\x1a\n", data, True, 0x10, 0xFFFFFFFF, 8, 8, 4
    def wrap(self, data, type_=b"cOMM"): return b"".join([pack(">I", len(data)), type_, data, pack(">I", crc32(type_ + data) % 0x100000000)])
class postscript(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.PREWRAP, self.POSTWRAP, self.data, self.bParasite, self.start_o, self.cut, self.prewrap, self.postwrap, self.parasite_o, self.parasite_s = "PS / PostScript", "PS", b"%!PS", b"/{(", b"\n)\n}\n", data, True, 0, 0, 3, 5, 3, 0xFFFFFF
    def wrap(self, data): return b"".join([self.PREWRAP, data, self.POSTWRAP])
class psd(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.COLOR_MODE_DATA_o, self.IMAGE_RESOURCE_BLOCK_s, self.data, self.bParasite, self.cut, self.parasite_o, self.parasite_s, self.prewrap = "PSD / Photoshop", "PSD", b"8BPS", 0x1a, 12, data, True, 34, 34, 0xFFFFFFFF, 12
    def getCut(self):
        self.cmd_s = unpack(">I", self.data[self.COLOR_MODE_DATA_o:self.COLOR_MODE_DATA_o+4])[0]
        self.resource_o = self.COLOR_MODE_DATA_o + 4 + self.cmd_s
        self.cut = self.resource_o + 4
        return self.cut
    def identify(self):
        if not self.data.startswith(self.MAGIC): return False
        self.getCut()
        return True
    def fixparasite(self, parasite): return parasite + b"\0" if (len(parasite) % 2) else parasite
    def wrap(self, parasite): return b"".join([b"8BIM\0\0\0\0", pack(">I", len(parasite)), parasite])
    def fixformat(self, d, delta): return d[:self.resource_o] + pack(">I", unpack(">I", d[self.resource_o:self.resource_o+4])[0] + delta) + d[self.resource_o+4:]
class rar(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC14, self.MAGIC4, self.MAGIC5, self.data, self.bParasite, self.start_o = "RAR / Roshal Archive", "RAR", b"RE~^\7\0", b"Rar!\x1A\7\0", b"Rar!\x1A\7\1\0", data, False, 4194304
    def identify(self): return self.data.startswith(self.MAGIC4) or  self.data.startswith(self.MAGIC5)
class riff(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGICl, self.MAGICb, self.WEBPTYPE, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "RIFF / Resource Interchange File Format [container]", "RIFF", b"RIFF", b"RIFX", b"WEBP", data, True, 12, 0xFFFFFFFF, 12, 8
    def identify(self):
        if self.data[8:12] == self.WEBPTYPE or (not(self.data.startswith(self.MAGICb)) and not(self.data.startswith(self.MAGICl))): return False
        self.endianness = ">" if self.data.startswith(self.MAGICb) else "<"
        return True
    def wrap(self, data, type_=b"JUNK"): return b"".join([type_, pack(self.endianness + "I", len(data)), data])
    def fixparasite(self, parasite): return parasite + b"\0" if (len(parasite) % 2) else parasite
    def fixformat(self, d, delta): return d[:4] + pack(self.endianness + "I", len(d) - 8) + d[8:]
class rtf(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.TEMPLATE, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "RTF / Rich Text Format", "RTF", b"{\\rtf1", rb"{\pict\bin%06i ", data, True, 0x17, 999999, 6, 17
    def identify(self): return self.data.startswith(self.MAGIC)
    def wrap(self, parasite): return b"".join([self.TEMPLATE % len(parasite), parasite, b"}"])
class svg(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.bAppData, self.parasite_o, self.parasite_s = "SVG / Scalable Vector Graphics", "SVG", b"<svg ", data, False, False , 0x80, 0xFFFFFFFF
    def parasitize(self, fparasite): return self.data[:data.find(b"><") + 1] + b"".join([b"<!--", fparasite.data, b"-->"]) + self.data[data.find(b"><") + 1:], []
class tar(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.MAGIC_o, self.data, self.bAppData, self.start_o, self.bParasite, self.cut, self.parasite_o, self.parasite_s, self.bZipper = "TAR / Tape Archive", "TAR", b"\0ustar", 0x100, data, True, 0, True, 512, 512, 0xffffff, True
    def identify(self): return self.data[self.MAGIC_o:self.MAGIC_o + 6] == self.MAGIC
    def parasitize_(self, fparasite):
        Hparasite, tarinfo = BytesIO(fparasite.data), TarInfo(name=".")
        tarinfo.mode, tarinfo.size, Hfile = 0, len(Hparasite.getvalue()), BytesIO()
        topen(fileobj=Hfile, mode="w").addfile(tarinfo=tarinfo, fileobj=Hparasite)
        return Hfile.getvalue()[:-0x2400] + self.data, []
    def normalize(self): self.data = self.emptyHdr() + self.data
    def fixchecksum(self, d):
        hdr = list(d[:512])
        for i in range(8): hdr[i + 0x94] = 32
        for i, j in enumerate(oct(sum(hdr))[2:]): hdr[i + 0x94] = ord(j)
        hdr[154] = 0
        return bytes(hdr) + d[512:]
    def fixformat(self, d, delta):
        self.data = self.fixchecksum(d[:0x7c] + oct(delta)[2:].rjust(11, "0").encode() + d[135:])
        return self.data
    def fixparasite(self, parasite): return parasite + b"\0" * (512 - len(parasite) % 512) if len(parasite) % 512 else parasite
    def emptyHdr(self):
        l, off = 512 * [0], 0x64
        l[0] = 46
        for count, length in [[3,7], [2,11]]:
            for _ in range(count):
                for i in range(length):
                    l[off] = 48
                    off += 1
                off += 1
        for i, c in enumerate(b"\0ustar  "): l[0x100 + i] = c
        return bytes(l)
    def zipper(self, zero):
        tdata, zcut = self.data, zero.getCut()
        self.data = (self.emptyHdr() + tdata)[zcut + zero.prewrap:]
        zipper, swaps = zero.parasitize(self)
        return (None, []) if (zipper is None or zcut is None or (zcut + zero.prewrap > 0x63)) else (self.fixchecksum(zipper), swaps)
class tiff(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGICb, self.MAGICl, self.ifdptr_o, self.ifdptr_s, self.data_o, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "TIFF / Tagged Image File Format", "TIFF", b"MM\0\x2a", b"II\x2a\0", 4, 4, 8, data, True, 8, 0xFFFFFFFF, 8, 0
    def identify(self):
        if not(self.data.startswith(self.MAGICb)) and not(self.data.startswith(self.MAGICl)): return False
        self.endianness = ">" if self.data.startswith(self.MAGICb) else "<"
        return True
    def fixparasite(self, parasite): return parasite + b"\0" if (len(parasite) % 2) else parasite
    def fixformat(self, d, delta):
        o = self.ifdptr_o
        while o != 0:
            d = d[:o] + pack(self.endianness[0] + "I", unpack(self.endianness[0] + "I", d[o:o+4])[0]+delta) + d[o+4:]
            o = unpack(self.endianness + "I", d[o:o+4])[0]
            c = unpack(self.endianness + "H", d[o:o+2])[0]
            o += 2
            for i in range(c):
                o += 8
                if unpack(self.endianness + "H", d[o - 8:o - 6])[0] == 273: d = d[:o] + pack(self.endianness[0] + "I", unpack(self.endianness[0] + "I", d[o:o+4])[0]+delta) + d[o+4:]
                o += 4
            o = unpack(self.endianness + "I", d[o:o+4])[0]
        return d
class wasm(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bAppData, self.bParasite, self.parasite_o, self.parasite_s, self.cut, self.prewrap = "WASM / WebAssembly", "WASM", b"\0asm\1\0\0\0", data, False, True, 0xC, 0xFFFFFFFF, 8, 4
    def getPrewrap(self, parasite_s):
        self.prewrap = len(self.wrap(b"\0" * parasite_s)) - parasite_s
        return prewrap
    def wrap(self, parasite, name=b""):
        n, buf = len(pack(">H", len(name)) + name + parasite), []
        while True:
            out = n & 0x7f
            n >>= 7
            if n: buf += [out | 0x80]
            else:
                buf += [out]
                break
        return b"\0" + bytes(buf) + pack(">H", len(name)) + name + parasite
class xz(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bAppData, self.bParasite = "XZ", "XZ", b"\xFD7zXZ\0", data, False, False
    def identify(self): return self.data.startswith(self.MAGIC)
class zip_(FType):
    def __init__(self, data=""):
        FType.__init__(self, data)
        self.DESC, self.TYPE, self.MAGIC, self.data, self.bParasite, self.parasite_o, self.parasite_s, self.start_o = "Zip", "Zip", b"PK\3\4", data, True, 0x1E, 0xffffff, 4194304
    def identify(self): return self.data.startswith(self.MAGIC)
    def parasitize(self, fparasite):
        hHost, hFinal = BytesIO(self.data), BytesIO()
        with ZipFile(hFinal, 'w', 0) as final:
            final.writestr(ZipInfo(filename='', date_time=(1981, 2, 3, 4, 5, 6)), fparasite.data)
            with ZipFile(hHost, "r") as zf:
                for n in zf.namelist():
                        contents = zf.open(n).read()
                        final.writestr(zf.getinfo(n), contents, compress_type=8)
        return hFinal.getvalue(), [0x1e, 0x1e + len(fparasite.data)]
def id3v2_1(n):
    l = []
    for i in range(4):
        l += [n % 0x80]
        n = n // 0x80
    return bytes(l[::-1])
def bpg1(n):
    if not n: return [0]
    l = []
    while n:
        l += [(n & 0x7f)]
        n = n >> 7
    for i in range(len(l) - 1): l[i + 1] = l[i + 1] | 0x80
    return l[::-1]
def bpg2(s):
    n = 0
    for i, c in enumerate(s):
        n = (n << 7) | (c & 0x7f)
        if c <= 0x80: break
    return n, i + 1
def Do(ftype1, ftype2, fn1, fn2, target):
    if ftype1 == ftype2 == fn1 == fn2 == target == None: return [arj, ar, bmp, bpg, cpio, cab, ebml, flac, flv, gif, icc, ico, ilda, java, jp2, jpg, lnk, id3v2, nes, ogg, pcap, pcapng, pe_hdr, pe_sec, png, psd, riff, svg, tiff, wasm, xz, _7z, mp4, pdf, gzip, bzip2, postscript, zip_, rar, rtf, dcm, tar, pdfc, iso, id3v1] # ;)
    if ftype1.bAppData and ftype2.start_o and len(ftype1.data) < ftype2.start_o: open(target, "wb").write(ftype1.data + ftype1.wrappend(ftype2.data))
    if ftype1.bParasite and (ftype1.parasite_o <= ftype2.start_o + ftype2.precav_s) and ftype1.parasite_s >= len(ftype2.data):
        parasitized, swaps = ftype1.parasitize(ftype2)
        if parasitized: open(target, "wb").write(parasitized)
    if ftype1.bZipper and ftype1.bParasite and ftype2.bParasite:
        zipper, swaps = ftype1.zipper(ftype2)
        if (zipper is not None) or swaps: open(target, "wb").write(zipper)
    if ftype1.bAppData and ftype2.precav_s and len(ftype1.data) <= ftype2.precav_s: open(target, "wb").write(ftype1.data + ftype1.wrappend(ftype2.data[len(ftype1.data + ftype1.wrappend(b"")):]))
