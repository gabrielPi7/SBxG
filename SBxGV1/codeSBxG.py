import datetime
import os
import random
import math
import sys
import traceback
from os.path import exists

from reedsolo import RSCodec

rsc = RSCodec(16)                                       #initialize RS-Codes with 16 Byte
maxerrors, maxerasures = rsc.maxerrata(verbose=True)


def enc(fileToSave):
    fin = open(fileToSave, "rb")                        #open file to save
    fout = open(fileToSave + '.ec', "wb")               #open file that gets new content
    file_size = os.path.getsize(fileToSave)             #get files size
    counter = 0                                         #initialize counter

    # ----------------------- create data-block with information about the file

    uid = random.getrandbits(6 * 8).to_bytes(6, byteorder='big')
    fileName = fileToSave
    index = 0

    out = b''
    out += 'FSZ'.encode() + file_size.to_bytes(length=4, byteorder='big')  # Block Amount
    out += 'FNM'.encode() + bytes([len(fileName)]) + fileName.encode()  # File Name
    out += 'UID'.encode() + uid  # UID
    out += 'FTS'.encode() + datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S").encode()  # Time Stamp
    out += 'A'.encode() * (235 - len(out))  # Padding to 256 Bytes
    out = rsc.encode(out)

    firstBlock = 'SBxGB'.encode() + out + 'A'.encode() * 256       #build block

    fout.write(firstBlock)      #write first block to file

    # -----------------------

    while 1:
        buffer = fin.read(227)      #read in first 227 Bytes

        counter = counter + len(buffer)     #add bytes to counter

        if len(buffer) == 0:       #check, if file is completly saved
            print()
            return

        if len(buffer) < 227:       #pad read Bytes to 227
            buffer += 'A'.encode() * (227-len(buffer))

        out = 'SBxG'.encode() + rsc.encode(uid + index.to_bytes(4, byteorder='big') + buffer)   #add first half of block to variable

        buffer = fin.read(239)      #read in second half of block

        if len(buffer) == 0:        #check, if there are bytes left
            print(f"\r{math.floor(counter / file_size * 100)}% abgeschlossen", end="")
            fout.write(out)
            print()
            return

        counter = counter + len(buffer)         #add bytes to counter

        if len(buffer) < 239:      #pad read Bytes to 239
            buffer += 'A'.encode() * (239 - len(buffer))

        out += rsc.encode(buffer)       #add second half to variable out

        print(f"\r{math.floor(counter / file_size * 100)}% abgeschlossen", end="")
        sys.stdout.flush()
        fout.write(out)         #write block to file
        index += 1              #count index up


def dec(fileToRecover):
    error = 0
    correctedIndex = -1

    fin = open(fileToRecover, "rb", buffering=1024 * 1024)
    file_size = os.path.getsize(fileToRecover)
    counter = 0

    # read first block
    buffer = fin.read(512)
    counter += len(buffer)
    try:        #decode first block
        buffer = buffer[5:256]

        decodedData, dataErrors = rsc.decode(buffer)[0], rsc.decode(buffer)[2]

        if len(dataErrors) != 0:
            error += len(dataErrors)

        fNamePos = decodedData.find('FNM'.encode())
        fNameLen = decodedData[fNamePos + 3]
        fName = decodedData[fNamePos + 4: fNamePos + 4 + fNameLen]

        fileSizePos = decodedData.find('FSZ'.encode())
        bam = decodedData[fileSizePos + 3: fileSizePos + 7]
        filesize = int.from_bytes(bam, 'big')
        bam = math.ceil(filesize / (227 + 239))

        fout = open('recovered_' + fName.decode(), "wb", buffering=1024 * 1024)

        print('\nDie Datei wurde gefunden ' + fName.decode())

        # --------------------------------------

        while 1:

            # ----- read Block
            buffer = fin.read(257)

            if int.from_bytes(buffer[10:14], 'big') != correctedIndex+1:
                print('\nFile misses a Block. Please retry.')
                exit()

            correctedIndex = int.from_bytes(buffer[10:14], 'big')

            #check if it's last block
            if correctedIndex == bam-1:
                sizeLastBlockNotFormat = (filesize / (227 + 239)) % 1
                sizeLastBlock = round((227 + 239) * sizeLastBlockNotFormat)  # get size of data in last block

                if sizeLastBlock <= 227:    #decode only first half of block, if size of last block is less than 227
                    try:
                        decodedData = rsc.decode(buffer[4:257])
                        fout.write(decodedData[0][10:sizeLastBlock+10])
                        counter += len(buffer)
                        print(f"\r{math.floor(counter / file_size * 100)}% abgeschlossen", end="")
                        fout.close()
                        print('\nFile has no errors.')
                        exit()
                    except Exception as e:
                        print('\nFile has an error. Please retry.')
                        exit()

                try:        #decode first half of last block
                    decodedData = rsc.decode(buffer[4:257])
                    counter += len(buffer)
                    fout.write(decodedData[0][10:None])

                    buffer = fin.read(255)
                    decodedData = rsc.decode(buffer)

                    fout.write(decodedData[0][0:sizeLastBlock - 227])
                    fout.close()

                    counter += len(buffer)
                    print(f"\r{math.floor(counter / file_size * 100)}% abgeschlossen", end="")

                    print('\nFile has no errors.')
                    exit()

                except Exception as e:
                    print('\nFile has an error. Please retry.')
                    exit()

            counter += len(buffer)
            print(f"\r{math.floor(counter / file_size * 100)}% abgeschlossen", end="")

            if len(buffer) == 0:
                print('\nNumber of errors: ' + str(error))
                fin.close()
                return

            try:        #try to decode block
                temp = buffer[4:257]        #decode first half of block
                decodedData = rsc.decode(temp)
                if len(decodedData[2]) != 0:
                    error += len(decodedData[2])

                fout.write(decodedData[0][10:None])

                buffer = fin.read(255)
                counter += len(buffer)
                print(f"\r{math.floor(counter / file_size * 100)}% abgeschlossen", end="")

                if len(buffer) == 0:
                    print('\nNumber of errors: ' + str(error))
                    fin.close()
                    return

                temp = buffer[0:255]        #decode second half of block

                decodedData = rsc.decode(temp)
                if len(decodedData[2]) != 0:
                    error += len(decodedData[2])

                # print('Number of errors:', len(test[2]))
                fout.write(decodedData[0])
            except Exception as e:
                print('\nThere is an error in the file. Please shield it again.')
                exit()
    except Exception as e:
        print('\nFile has an error. Please retry.')
        exit()


# start of code
if __name__ == '__main__':

    fileToSave = sys.argv[1]

    if not exists(fileToSave):
        print('The File "' + fileToSave + '" does not exist!')
        exit()

    option = input('1 = Encode - 2 = Decode.\n')

    if option == '1':
        enc(fileToSave)
    elif option == '2':
        dec(fileToSave)
