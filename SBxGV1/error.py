import math
import os
import random
import sys

fh = open(sys.argv[1], "r+b")
file_size = os.path.getsize(sys.argv[1])  # get files size
block_amount = math.floor(file_size / 512)

if block_amount > 118694:
    block_amount = 118694


def swap_blocks():      #do 100000 block swaps in the file
    for i in range(0, 100000):
        firstBlockOffset = random.randrange(0, block_amount) * 512
        secondBlockOffset = random.randrange(0, block_amount) * 512

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


def addErrors_TwelveByte():         #add 12 defect bytes to beginning of the file with 50% chance
    counter = 0
    for i in range(0, block_amount):
        if random.randrange(0, 100) < 50:
            fh.seek(i * 512, 0)
            fh.write('A'.encode() * 12)
            counter += 1
        print(
            f'\r{counter} Blocks changed.',
            end=". ")
        sys.stdout.flush()


def addErrors_EightByte():          #add random 8 defect bytes to block
    for i in range(0, block_amount):
        fh.seek(i * 512 + random.randrange(0, 504), 0)
        fh.write('A'.encode() * 8)
        print(
            f'\r{i} Blocks changed.',
            end=". ")
        sys.stdout.flush()


if __name__ == '__main__':
    optionList = {1: swap_blocks, 2: addErrors_TwelveByte, 3: addErrors_EightByte}

    option = input('1: Swap Blocks - 2: Change first twelve Bytes - 3: Change eight random Bytes per Block\n')

    try:
        optionList[int(option)]()
    except:
        print('Please enter a valid option.')
