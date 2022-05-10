import os
import sys
import math
import traceback
from os.path import exists

from reedsolo import RSCodec, ReedSolomonError

firstBlock = None


def checkBlock(block, uid):
    rsc = RSCodec(16)

    shieldedBlock = block[4:257]
    try:
        global firstBlock
        firstBlock = rsc.decode(shieldedBlock)

        fUid = firstBlock[0][0:6]

        if fUid == uid:
            return True
        return False
    except Exception as e:
        return False


def scan():
    # initialize Reed-Solomon Codes with 16 parity bytes and open file/media to scan
    rsc = RSCodec(16)
    error = 0

    try:
        file = sys.argv[1]
        if not exists(file):
            file = "\\\\.\\\F:"
            print('No file found with name: '+sys.argv[1])
    except Exception as e:
        file = "\\\\.\\\F:"

    with open(file, 'rb') as f:
        print("Disk Open")
        counter = 0
        loseBlocks = 'n'

        while True:
            # get 512 Bytes from media and print status
            data = f.read(512)
            counter += 512
            print(f"\r{math.floor(counter / 1000)} kBytes durchsucht", end="")
            sys.stdout.flush()

            # check if Meta-Block found
            if data[0:5] == 'SBxGB'.encode():
                try:
                    decodedData, errorsInFirstBlock = rsc.decode(data[5:256])[0], len(rsc.decode(data[5:256])[2])
                    if errorsInFirstBlock != 0:
                        error += errorsInFirstBlock

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
                            '\nDie Datei wurde gefunden ' + fName.decode() + ' erstellt am: ' + fDate + ' - Größe: ' + str(
                                bam) + ' Blöcke')

                        option = input(
                            'Do you want to recover this file? 1 = Yes - 2 = No and continue searching - 3 = No and stop the search.\n')

                        # start recovering file with given UID
                        if option == '1':

                            loseBlocks = input('lose block y or n?\nIf this option is no, then defect blocks will be added to the file aswell.\n')

                            print('start recovering')
                            fout = open('recovered_' + fName.decode(),
                                        "wb")  # open file with saved name and 'recovered_' in the beginning

                            # initialize information data

                            recoveredData = 0
                            blockIndex = -1
                            lostBlocks = 0
                            global firstBlock

                            while recoveredData <= filesize:  # check if file was completly recovered

                                data = f.read(512)

                                if checkBlock(data, fUid):  # check if its an SBxG Block and if the fUid matches

                                    if len(firstBlock[2]) != 0:
                                        error += len(firstBlock[2])

                                    correctedIndex = int.from_bytes(firstBlock[0][6:10], 'big')

                                    # check if its the next block, or if blocks were skipped
                                    if blockIndex + 1 != correctedIndex:
                                        lostBlocks += correctedIndex - blockIndex - 1
                                        recoveredData += 466 * (correctedIndex - blockIndex - 1)

                                    blockIndex = correctedIndex

                                    # check if its the last block
                                    if blockIndex == bam - 1:
                                        sizeLastBlockNotFormat = (filesize / (227 + 239)) % 1
                                        sizeLastBlock = round(
                                            (227 + 239) * sizeLastBlockNotFormat)  # get size of data in last block

                                        if sizeLastBlock <= 227:
                                            if len(firstBlock[2]) != 0:
                                                error += len(firstBlock[2])

                                            fout.write(firstBlock[0][10:sizeLastBlock + 10])
                                            recoveredData += sizeLastBlock

                                            print(
                                                f'\r{round((recoveredData / filesize) * 100, 0)}% wiederhergestellt. Defekte Blöcke: ' + str(
                                                    lostBlocks) + ' reparierte Bytes: ' + str(error), end=". ")
                                            sys.stdout.flush()
                                            fout.close()
                                            exit()

                                        fout.write(firstBlock[0][10:sizeLastBlock + 10])
                                        recoveredData += 227

                                        try:
                                            decodedData = rsc.decode(data[257:512])

                                            if len(decodedData[2]) != 0:
                                                error += len(decodedData[2])

                                            fout.write(decodedData[0][0:sizeLastBlock - 227])
                                            recoveredData += sizeLastBlock - 227
                                            print(
                                                f'\r{round((recoveredData / filesize) * 100, 0)}% wiederhergestellt. Defekte Blöcke: ' + str(
                                                    lostBlocks) + ' reparierte Bytes: ' + str(error), end=". ")
                                            sys.stdout.flush()
                                            fout.close()
                                            exit()
                                        except Exception as e:
                                            lostBlocks += 1
                                            fout.write(data[257:257 + (sizeLastBlock - 227)])
                                            recoveredData += sizeLastBlock - 227
                                            print(
                                                f'\r{round((recoveredData / filesize) * 100, 0)}% wiederhergestellt. Defekte Blöcke: ' + str(
                                                    lostBlocks) + ' reparierte Bytes: ' + str(error), end=". ")
                                            sys.stdout.flush()
                                            fout.close()
                                            exit()
                                    # /check if its the last block

                                    # decode first half of the block
                                    recoveredData += 227

                                    decodedData = firstBlock

                                    fout.write(decodedData[0][10:None])

                                    shieldedBlock = data[257:512]
                                    recoveredData += 239

                                    try:
                                        decodedData = rsc.decode(shieldedBlock)
                                        if len(decodedData[2]) != 0:
                                            error += len(decodedData[2])
                                        fout.write(decodedData[0])
                                    except Exception as e:
                                        fout.write(data[257:512 - 16])
                                        lostBlocks += 1
                                        print(e)

                                elif data[0:4] == 'SBxG'.encode() and data[4:10] == fUid:       #if block can't be decoded, check if identifier and uid matches and then decode
                                    lostBlocks += 1
                                    fout.write(data[14:257 - 16])
                                    recoveredData += 227
                                    fout.write(data[257:512 - 16])
                                    recoveredData += 239

                                elif loseBlocks == 'n':
                                    print('Block could not be recovered without errors!')       #if user wants, block can still be added with errors
                                    lostBlocks += 1
                                    blockIndex += 1
                                    fout.write(data[14:257 - 16])
                                    recoveredData += 227
                                    try:
                                        decodedData = rsc.decode(data[257:512])
                                        if len(decodedData[2]) != 0:
                                            error += len(decodedData[2])
                                        fout.write(decodedData[0])
                                        recoveredData += 239

                                    except:
                                        fout.write(data[257:512 - 16])
                                        recoveredData += 239

                                print(
                                    f'\r{round((recoveredData / filesize) * 100, 2)}% wiederhergestellt. Defekte Blöcke: ' + str(
                                        lostBlocks) + ' reparierte Bytes: ' + str(error), end="")
                                sys.stdout.flush()

                            fout.close()
                            exit()
                        if option == '3':
                            break

                except SystemExit:
                    exit()
                except Exception as e:
                    print('\nError found')
                    print(e)


def main():
    try:
        scan()

    except Exception as e:
        print(traceback.format_exc())
        pass


if __name__ == '__main__':
    main()


