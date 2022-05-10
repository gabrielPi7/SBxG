import datetime
import os
import random
import math
import sqlite3
import sys
from os.path import exists

from reedsolo import RSCodec

rsc = RSCodec(32)  # initialize RS-Codes with 32 Byte
#maxerrors, maxerasures = rsc.maxerrata(verbose=True)


def enc(fileToSave):
    RSBufferOne = []
    exitEncoding = False

    fin = open(fileToSave, "rb")  # open file to save
    fout = open(fileToSave + '.ec', "wb")  # open file that gets new content
    file_size = os.path.getsize(fileToSave)  # get files size
    counter = 0  # initialize counter

    # ----------------------- create data-block with information about the file

    uid = random.getrandbits(6 * 8).to_bytes(6, byteorder='big')
    fileName = fileToSave
    index = 0

    out = b''
    out += 'FSZ'.encode() + file_size.to_bytes(length=4, byteorder='big')  # Block Amount
    out += 'FNM'.encode() + bytes([len(fileName)]) + fileName.encode()  # File Name
    out += 'UID'.encode() + uid  # UID
    out += 'FTS'.encode() + datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S").encode()  # Time Stamp
    out += 'A'.encode() * (219 - len(out))  # Padding to 256 Bytes
    out = rsc.encode(out)

    firstBlock = 'SBxGB'.encode() + out + 'A'.encode() * 256  # build block

    fout.write(firstBlock)  # write first block to file

    # -----------------------
    read_data = 0

    while 1:
        for i in range(0, 100):     #get content of first 100 blocks
            buffer = fin.read(436)
            read_data += len(buffer)
            #------------if read data is not 436 Bytes, then pad it to 436 Bytes
            if len(buffer) == 0:
                buffer = 'B'.encode() * 436
                exitEncoding = True
            elif len(buffer) < 436:
                buffer += 'B'.encode() * (436 - len(buffer))
                exitEncoding = True
            #------------------------------------------------------

            firstHalf = rsc.encode(buffer[0:213])  # add first half of block to variable
            secondHalf = rsc.encode(buffer[213:None])  # add second half to variable out

            RSBufferOne.append([firstHalf + secondHalf])         #add both halfs to array

        for y in range(0, 100):

            out = 'SB'.encode() + uid + index.to_bytes(4, byteorder='big')     #add identifier to block
            for i in range(0, 100):
                out += RSBufferOne[i][0][y * 5:(y + 1) * 5]         #add byte sequence to block

            fout.write(out)
            index += 1
        RSBufferOne.clear()     #clear array to get next 100 blocks
        print(
            f'\r{round(read_data / file_size * 100, 2)}% done. ',
            end=". ")
        sys.stdout.flush()
        if exitEncoding:
            exit()


def checkFirstBlock(block):     #check, if first block is an rsc block
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


def dec():      #search for secured blocks in image file
    try:
        file = sys.argv[1]
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

    inputFirstBlockScan = input('Fast Scan = 1 - Slow Scan = 2\n')      #fast scan - only identifier of first block gets checked : slow scan - every block gets decoded and then checked

    while True:
        # get 512 Bytes from media and print status
        data = f.read(512)
        counter += 512
        print(f"\r{math.floor(counter / 1000)} kBytes durchsucht", end="")
        sys.stdout.flush()

        # check if Meta-Block found
        if data[0:5] == 'SBxGB'.encode() if (inputFirstBlockScan == '1') else checkFirstBlock(data):
            try:        #get information about the file
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
                bam = math.ceil(filesize / (212 + 223))

                # get uid from Meta-Block
                fUidPos = decodedData.find('UID'.encode())
                fUid = decodedData[fUidPos + 3: fUidPos + 9]

                if fName.decode():
                    print(
                        '\n\nFile found: ' + fName.decode() + ' - created: ' + fDate + ' - size: ' + str(
                            bam) + ' blocks')

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

                        conn = sqlite3.connect(dbfilename)      #add connection to sqlite
                        c = conn.cursor()
                        c.execute("CREATE TABLE file_offsets (uid INTEGER, offset INTEGER, ind INTEGER)")       #create table

                        blocksFound = 0
                        offset = 0

                        bam = bam / 100                         #get block amount
                        bam = math.ceil(bam)
                        bam = bam * 100


                        alreadySorted = False
                        try:
                            while blocksFound < bam:            #search blocks
                                f.seek(offset, 0)
                                buffer = f.read(512)

                                if buffer[0:2] == 'SB'.encode() and buffer[2:8] == fUid:        #check if the the block belongs to the file
                                    index = int.from_bytes(buffer[8:12], 'big')
                                    c.execute(
                                        "INSERT INTO file_offsets (uid, offset, ind) VALUES (?, ?, ?)",
                                        (int.from_bytes(fUid, 'big'), offset, index))
                                    conn.commit()                       #insert offset of found block into db file
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
                                        blocksFound) + '/' + str(bam) + ' Blocks found.',
                                    end=". ")
                                sys.stdout.flush()

                        except (KeyboardInterrupt, BaseException):      #if search gets interrupted by user, try to recover file with found blocks
                            print('Not all Blocks have been found.')
                            print('Start recovering file...')
                            fout = open(fName.decode() + '.ec', "wb")
                            fout.write(data)
                            counter = 0

                            for row in c.execute('SELECT * FROM file_offsets ORDER BY ind;'):       #write sorted blocks to a new file
                                index = row[2]
                                if index != counter:
                                    fout.write('C'.encode() * 512 * (index - counter))

                                offset = row[1]
                                f.seek(offset, 0)
                                buffer = f.read(512)
                                fout.write(buffer)
                                counter = index + 1
                            print('\nFile created!')
                            alreadySorted = True

                        if not alreadySorted:       #if all blocks been found, enter this section
                            print('All Blocks have been found.')
                            print('Start recovering file...')

                            for row in c.execute('SELECT * FROM file_offsets ORDER BY ind;'):
                                offset = row[1]
                                f.seek(offset, 0)
                                buffer = f.read(512)
                                fout.write(buffer)

                        fout.close()

                        #start recovering file with sorted blocks
                        recovered_file = open('recovered_' + fName.decode(), 'wb')
                        source_file = open(fName.decode() + '.ec', 'rb')
                        blockCollectionEncoded = []
                        bam = int(bam / 100)
                        byte_amount = filesize % 43600  # get Byteamount of Data in the last 100 Blocks
                        total_data_blocks = str((bam-1) * 100 + math.ceil(byte_amount/436))

                        counter_blocks_recovered = 0
                        recovered_block = b''
                        counter = 0

                        offset = 512
                        source_file.seek(offset, 0)

                        for i in range(0, bam):
                            for y in range(0, 100):
                                buffer = source_file.read(512)
                                blockCollectionEncoded.append(buffer)       #fill array with first 100 blocks

                            for block in range(0, 100):
                                if i == bam - 1:  # check if its last 100 Blocks
                                    for byte_sequence in range(0, 100):
                                        recovered_block += blockCollectionEncoded[byte_sequence][
                                                           12 + block * 5:12 + (block + 1) * 5]     #get origin blocks back, not combined ones

                                    if byte_amount - counter <= 436:        #check if its last block
                                        if byte_amount - counter <= 212:
                                            recovered_file.write(rsc.decode(recovered_block[0:245])[0][0:byte_amount - counter])
                                        elif 436 >= byte_amount - counter > 212:
                                            recovered_file.write(rsc.decode(recovered_block[0:245])[0])
                                            counter += 213
                                            recovered_file.write(rsc.decode(recovered_block[245:500])[0][0:byte_amount - counter])

                                        counter_blocks_recovered += 1
                                        print(
                                            f'\r{counter_blocks_recovered}/' + total_data_blocks + ' Blocks recovered',
                                            end=". ")
                                        sys.stdout.flush()
                                        print('File has been successfully recovered - recovered_' + fName.decode())
                                        exit()
                                    try:
                                        recovered_file.write(rsc.decode(recovered_block[0:245])[0])     #write origin content to recovered file
                                        recovered_file.write(rsc.decode(recovered_block[245:500])[0])
                                    except:     #if block cannot get decoded, enter this section
                                        print('Too many errors found. File could not be recovered.')
                                        source_file.close()
                                        recovered_file.close()
                                        exit()
                                    counter += 436
                                    recovered_block = b''

                                    counter_blocks_recovered += 1
                                    print(
                                        f'\r{counter_blocks_recovered}/'+total_data_blocks+' Blocks recovered',
                                        end=". ")
                                    sys.stdout.flush()
                                else:       #if its not the last 100 blocks
                                    for byte_sequence in range(0, 100):
                                        recovered_block += blockCollectionEncoded[byte_sequence][
                                                           12 + block * 5:12 + (block + 1) * 5]     #get origin blocks back, not combined ones
                                    try:
                                        recovered_file.write(rsc.decode(recovered_block[0:245])[0])      #write origin content to recovered file
                                        recovered_file.write(rsc.decode(recovered_block[245:500])[0])    #write origin content to recovered file
                                    except:     #if block cannot get decoded, enter this section
                                        print('Too many errors found. File could not be recovered.')
                                        recovered_file.close()
                                        source_file.close()
                                        exit()
                                    recovered_block = b''

                                    counter_blocks_recovered += 1
                                    print(
                                        f'\r{counter_blocks_recovered}/'+total_data_blocks+' Blocks recovered',
                                        end=". ")
                                    sys.stdout.flush()

                            blockCollectionEncoded.clear()  #clear array to get next 100 blocks
                        exit()
                    if option == '3':
                        exit()

            except Exception as e:
                pass


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
        dec()
