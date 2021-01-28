def enum(**enums):
    return type('Enum', (), enums)

SIZE = enum(ONE_BYTE=2**6, TWQ_BYTES=2**14, THREE_BYTES=2**22, FOUR_BYTES=2**30, MASK_2_BYTES=2**14, MASK_3_BYTES=2**23, MASK_4_BYTES=((2**31)+(2**30)))


def lpVarintEncode(number):
    """ This method get a number and returns the Length-Precoded Varint of this number """
    if number < SIZE.ONE_BYTE:
        return number
    if number < SIZE.TWQ_BYTES:
        return number | SIZE.MASK_2_BYTES
    if number < SIZE.THREE_BYTES:
        return number | SIZE.MASK_3_BYTES
    if number < SIZE.FOUR_BYTES:
        return number | SIZE.MASK_4_BYTES
    return number   # in case of a number that bigger than 30 bits

def lpVarintDecode(number, num_bytes):
    """ This method get a Length-Precoded Varint number and returns the original number """
    if num_bytes == 1:
        return number
    if num_bytes == 2:
        return number ^ SIZE.MASK_2_BYTES
    if num_bytes == 3:
        return number ^ SIZE.MASK_3_BYTES
    if num_bytes == 4:
        return number ^ SIZE.MASK_4_BYTES
    return number

def getBytesArray(number):
    """ This method get a number and returns an array consists of the bytes of this number """
    bytes_arr = []
    while number:
        bytes_arr.insert(0, number & 0xff)
        number >>= 8
    return bytes_arr

def getDiffArray(num_arr):
    """ THis method get an array of numbers and returns an array of the differences (the first number remains the same) """
    diff_arr = [num_arr[0]]  # the first number remains the same
    diff_arr += [num - num_arr[i] for i, num in enumerate(num_arr[1:])]  # Differences between all other numbers
    return diff_arr

def getArrayFromdiff(diff_arr):
    """ THis method get an array of differences and returns an array of the original numbers (the first number remains the same) """
    num_arr = [diff_arr[0]]  # the first number remains the same
    for i, diff in enumerate(diff_arr[1:]):  # Addition between all other numbers
        num_arr += [diff + num_arr[i]]
    return num_arr

def buildEncodedMailingList(mailing_list):
    """ This method get mailing list of numbers and returns sequence of bytes """
    bytes_arr = []
    for num in mailing_list:  # Length-Precoded Varint encoding for any number in the mailing list
        encoded_num = lpVarintEncode(num)
        bytes_arr += getBytesArray(encoded_num)  # get the encoded number in an array of bytes

    return bytes_arr

def buildDecodedMailingList(lists_file, size_in_bytes):
    """ This method get a lists file and num of bytes to read.
    Reading sequence of byte and returns array of numbers """
    mailing_list = []
    while size_in_bytes:  # run over all the bytes of the list - reads one number at a time
        stream = lists_file.read(1)  # read one byte
        stream = ord(stream)
        byte = stream & 0xc0
        num_bytes = byte >> 6  # check how more bytes makes up the number
        stream *= 2 ** (8 * num_bytes)  # start to makes up the number
        num_bytes1 = num_bytes
        while num_bytes1:  # read and build the rest of the number
            byte = ord(lists_file.read(1))
            num_bytes1 -= 1
            byte *= 2 ** (8 * num_bytes1)
            stream += byte

        decode_mun = lpVarintDecode(stream, num_bytes + 1)  # decodes the number
        mailing_list.append(decode_mun)
        size_in_bytes -= num_bytes + 1  # update, for move to the next number

    return mailing_list

def calGaps(mailing_list):
    """ This method get mailing list and calculates the gaps between the review_ids """
    reviews_list = mailing_list[::2]  # get the reviewIDs only
    freq_list = mailing_list[1::2]  # get the freq. only
    reviews_diff_list = getDiffArray(reviews_list)  # calculates the differences between reviewIDs

    mailing_list = []
    for (r_id, freq) in zip(reviews_diff_list, freq_list):  # merge the reviewIDs (in differences) + freq. back together
        mailing_list.extend([r_id, freq])

    return mailing_list
