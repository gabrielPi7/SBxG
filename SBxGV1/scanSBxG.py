import math
import os
import sqlite3
import sys
import traceback
from os.path import exists

from reedsolo import RSCodec

rsc = RSCodec(16)
sbxBlock = b''


def checkFirstBlock(block):        #check, if the scanned first block is a RS-Codes block
    global rsc
    global sbxBlock
    shieldedBlock = block[5:256]
    try:
        sbxBlock = rsc.decode(shieldedBlock)[0]
        if sbxBlock[0:3] == 'FSZ'.encode():
            return True
        return False
    except Exception as e:
        return False


def checkBlock(block, uid):         #check, if the scanned block is a RS-Codes block
    global rsc
    global sbxBlock
    shieldedBlock = block[4:257]
    try:
        firstBlock = rsc.decode(shieldedBlock)
        fUid = firstBlock[0][0:6]

        if fUid == uid:
            sbxBlock = 'SBxG'.encode() + firstBlock[0] + block[251:257]
            return True
        return False
    except Exception as e:
        return False


def scan():                         #scan file for secured files
    try:
        file = sys.argv[1]          #get filename
        if not exists(file):
            print('No file found with name: ' + sys.argv[1])
            file = "\\\\.\\\F:"
            f = open(file, 'rb')
            print('\nOpened "\\\\.\\\F:" instead.')
        else:
            f = open(file, 'rb')
            print('File opened: ' + sys.argv[1])


    except Exception as e:
        print('Please enter a valid file!')
        exit()

    counter = 0

    inputFirstBlockScan = input('Fast Scan = 1 - Slow Scan = 2\n')      #fast scan: only the first chars are checked - slow scan: tries to decode every block and see, if its and SBxGB

    while True:
        # get 512 Bytes from media and print status
        data = f.read(512)
        counter += 512
        print(f"\r{math.floor(counter / 1000)} kBytes durchsucht", end="")
        sys.stdout.flush()

        # check if Meta-Block found
        if data[0:5] == 'SBxGB'.encode() if (inputFirstBlockScan == '1') else checkFirstBlock(data):
            try:
                decodedData = rsc.decode(data[5:256])[0]
                # get filename from Meta-Block
                fNamePos = decodedData.find('FNM'.encode())
                fNameLen = decodedData[fNamePos + 3]
                fName = decodedData[fNamePos + 4: fNamePos + 4 + fNameLen]

                # get date from Meta-Block
                fTimeStampPos = decodedData.find('FTS'.encode())
                fDate = decodedData[fTimeStampPos + 3: fTimeStampPos + 22].decode()

                # get filesize from Meta-Block
                fileSizePos = decodedData.find('FSZ'.encode())
                bam = decodedData[fileSizePos + 3: fileSizePos + 7]
                filesize = int.from_bytes(bam, 'big')
                bam = math.ceil(filesize / (227 + 239))

                # get uid from Meta-Block
                fUidPos = decodedData.find('UID'.encode())
                fUid = decodedData[fUidPos + 3: fUidPos + 9]

                if fName.decode():
                    print(
                        '\n\nDie Datei wurde gefunden ' + fName.decode() + ' erstellt am: ' + fDate + ' - Größe: ' + str(
                            bam) + ' Blöcke')

                    option = input(
                        'Do you want to recover this file? 1 = Yes - 2 = No and continue searching - 3 = No and stop the search.\n')

                    # start recovering file with given UID
                    if option == '1':
                        if inputFirstBlockScan == '1':
                            fout = open(fName.decode() + '.ec', "wb")
                            fout.write(data)
                        else:
                            fout = open(fName.decode() + '.ec', "wb")  # write first block to file
                            fout.write('SBxGB'.encode() + data[5:512])

                        dbfilename = 'scan.db3'
                        if os.path.exists(dbfilename):
                            os.remove(dbfilename)

                        conn = sqlite3.connect(dbfilename)              # open connection to sqlite
                        c = conn.cursor()
                        c.execute("CREATE TABLE file_offsets (uid INTEGER, offset INTEGER, ind INTEGER)")

                        blocksFound = 0
                        offset = 0

                        option2 = input(
                            '1: Slow scan. (errors in Bytes will be corrected) - 2: Fast Scan. (errors wont be corrected, may cause switched data-blocks!\n')
                        print('Searching Blocks...')        #every block gets decoded first and checked for byte-errors
                        try:
                            if option2 == '1':
                                while blocksFound < bam or len(buffer) == 0:
                                    f.seek(offset, 0)
                                    buffer = f.read(512)
                                    if checkBlock(buffer, fUid):    #check, if the block is part of the file with decoding it first
                                        index = int.from_bytes(sbxBlock[10:14], 'big')
                                        c.execute(
                                            "INSERT INTO file_offsets (uid, offset, ind) VALUES (?, ?, ?)",
                                            (int.from_bytes(fUid, 'big'), offset, index))
                                        conn.commit()
                                        print(
                                            f'\r{round(offset / 1000000, 2)} MBytes searched. ' + str(
                                                blocksFound) + '/' + str(
                                                bam) + ' Blocks found.',
                                            end=". ")
                                        sys.stdout.flush()

                                        blocksFound += 1
                                    offset += 512
                                    print(
                                        f'\r{round(offset / 1000000, 2)} MBytes searched. ' + str(
                                            blocksFound) + '/' + str(
                                            bam) + ' Blocks found.',
                                        end=". ")
                                    sys.stdout.flush()
                            else:                                   #check, if block is part of the file, without decoding it wit rsc first
                                while blocksFound < bam or len(buffer) == 0:
                                    f.seek(offset, 0)
                                    buffer = f.read(512)
                                    if buffer[0:4] == 'SBxG'.encode() and buffer[4:10] == fUid:
                                        index = int.from_bytes(buffer[10:14], 'big')
                                        c.execute(
                                            "INSERT INTO file_offsets (uid, offset, ind) VALUES (?, ?, ?)",
                                            (int.from_bytes(fUid, 'big'), offset, index))
                                        conn.commit()
                                        print(
                                            f'\r{round(offset / 1000, 2)} kBytes searched. ' + str(
                                                blocksFound) + '/' + str(
                                                bam) + ' Blocks found.',
                                            end=". ")
                                        sys.stdout.flush()

                                        blocksFound += 1
                                    offset += 512
                                    print(
                                        f'\r{round(offset / 1000000, 2)} MBytes searched. ' + str(
                                            blocksFound) + '/' + str(bam) + ' Blocks found.',
                                        end=". ")
                                    sys.stdout.flush()
                        except KeyboardInterrupt:
                            print('Not all Blocks have been found.')
                            print('Start creating Backupfile...')
                            fout = open(fName.decode() + '.ec', "wb")
                            fout.write(data)

                            for row in c.execute('SELECT * FROM file_offsets ORDER BY ind;'):
                                offset = row[1]
                                f.seek(offset, 0)
                                buffer = f.read(512)
                                fout.write(buffer)
                            print('\nFile created!')
                            print('Please insert the created file "' + fName.decode() + '.ec" into recover.py')
                            f.close()
                            exit()

                        print('All Blocks have been found.')
                        print('Start creating Backupfile...')

                        for row in c.execute('SELECT * FROM file_offsets ORDER BY ind;'):
                            offset = row[1]
                            f.seek(offset, 0)
                            buffer = f.read(512)
                            fout.write(buffer)
                        print('\nFile created!')
                        print('Please insert the created file "' + fName.decode() + '.ec" into recoverSBxG.py to decode it.')
                        f.close()
                        exit()
                    if option == '3':
                        exit()

            except Exception as e:
                print(traceback.format_exc())


if __name__ == '__main__':
    scan()
