import hashlib
import sys

BUF_SIZE = 65536

md5_f1 = hashlib.md5()
md5_f2 = hashlib.md5()


def checkFiles():
    with open(sys.argv[1], 'rb') as f1:
        while True:
            data = f1.read(BUF_SIZE)
            if not data:
                break
            md5_f1.update(data)

    with open(sys.argv[2], 'rb') as f2:
        while True:
            data = f2.read(BUF_SIZE)
            if not data:
                break
            md5_f2.update(data)

    print("MD5 der ersten übergebenen Datei: {0}".format(md5_f1.hexdigest()))
    print("MD5 der zweiten übergebenen Datei: {0}".format(md5_f2.hexdigest()))

    if md5_f1.hexdigest() == md5_f2.hexdigest():
        print('Hash stimmt überein.')
        exit()

    print('Hash stimmt nicht überein.')


def checkFilesWithParam(file1, file2):
    md5_f1 = hashlib.md5()
    md5_f2 = hashlib.md5()

    with open(file1, 'rb') as f1:
        while True:
            data = f1.read(BUF_SIZE)
            if not data:
                break
            md5_f1.update(data)

    with open(file2, 'rb') as f2:
        while True:
            data = f2.read(BUF_SIZE)
            if not data:
                break
            md5_f2.update(data)

    print("MD5 der ersten übergebenen Datei: {0}".format(md5_f1.hexdigest()))
    print("MD5 der zweiten übergebenen Datei: {0}".format(md5_f2.hexdigest()))

    if md5_f1.hexdigest() == md5_f2.hexdigest():
        print('Hash stimmt überein.')
        f1.close()
        f2.close()
        return True

    print('Hash stimmt nicht überein.')
    f1.close()
    f2.close()
    return False


if __name__ == '__main__':
    checkFiles()
