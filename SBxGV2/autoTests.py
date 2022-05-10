import random
import sys
from os.path import exists

import codeSBxG_testing
import checkFiles


def swap_blocks():
    for i in range(0, 10000):
        fh = open('newMediaTemp.ec', "r+b")
        firstBlockOffset = random.randrange(1, 195312) * 512
        secondBlockOffset = random.randrange(1, 195312) * 512

        fh.seek(firstBlockOffset, 0)
        firstBlock = fh.read(512)
        fh.seek(secondBlockOffset, 0)
        secondBlock = fh.read(512)

        fh.seek(firstBlockOffset, 0)
        fh.write(secondBlock)
        fh.seek(secondBlockOffset, 0)
        fh.write(firstBlock)

        print(
            f'\r{i} Blocks swapped.',
            end=". ")
        sys.stdout.flush()
    fh.close()
    print('-------------------------')


if __name__ == '__main__':
    try:
        temp = sys.argv[1]
        sys.argv[1] = 'newMediaTemp.ec'
        sys.argv.append(temp)
    except:
        print('\nPlease enter a valid image file.')
        exit()

    if not exists(sys.argv[2]):
        print('\nFile not found. Please make sure to add the correct path.')
        exit()

    counterRecovered = 0
    counterLost = 0

    for x in range(0, 50):

        # ----------------copy first 200MB to a temp file------------------
        f1 = open(sys.argv[2], 'rb')
        f2 = open('newMediaTemp.ec', 'wb')

        buffer = f1.read(200000000)
        f2.write(buffer)

        f1.close()
        f2.close()
        # -----------------------------------------------------------------

        swap_blocks()       #swap blocks
        f1 = open('newMediaTemp.ec', 'r+b')
        for i in range(0, 195312):
            f1.seek(i * 512, 0)
            if random.randrange(0, 100) < 4:
                f1.write('AAA'.encode())
        try:
            codeSBxG_testing.dec()
        except BaseException:
            pass

        if checkFiles.checkFilesWithParam('test.txt', 'recovered_test.txt'):  #hard coded file names to check - needs to be changed to actual file names
            counterRecovered += 1
        else:
            counterLost += 1
        print('\n'+str(counterRecovered)+'/50 files recovered. ' + str(counterLost) + '/50 files lost.')

