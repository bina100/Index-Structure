import re
import os
import shutil

import utils


def handleLastMerge(list, bin_file):
    """ This method get a list of numbers and a binary file.
        The method operate calGaps and Encode methods on the list, and write the bytes_arr to the binary file s"""

    diff_list = utils.calGaps(list)
    bytes_arr = utils.buildEncodedMailingList(diff_list)

    start_pointer = bin_file.tell()
    bin_file.write(bytearray(bytes_arr))
    list_size = bin_file.tell() - start_pointer

    return list_size

def mergeDictAndListsFiles(dictFile1, dictFile2, listsFile1, listsFile2, distDir, is_last=False):
    """ This method read the 2 dictionary files and 2 lists files from the disk and build a merge dictionary and lists files on the disk """

    # the dictionary files to merge
    dict_file1 = open(dictFile1, 'r')
    dict_file2 = open(dictFile2, 'r')
    # the lists files to merge
    lists_file1 = open(listsFile1, 'rb')
    lists_file2 = open(listsFile2, 'rb')

    # the distination dir where the merged files will be
    if not os.path.exists(distDir):
        os.makedirs(distDir)
    # the distination files for the merged data
    dict_merged_file = open(distDir + "/dict.txt", 'w')
    lists_merged_file = open(distDir + '/lists.bin', 'wb')

    # read the first dictionary file in an array, while saving the pointers to appropriate review list in the lists file
    content = dict_file1.read()
    items = re.findall(r'([a-z0-9]+).(\d+), (\d+), (\d+).', content)
    tokens_dict1 = []
    for item in items:
        tokens_dict1.append((item[0], int(item[1]), int(item[2]), int(item[3])))

    # read the second dictionary file in an array, while saving the pointers to appropriate review list in the lists file
    content = dict_file2.read()
    items = re.findall(r'([a-z0-9]+).(\d+), (\d+), (\d+).', content)
    tokens_dict2 = []
    for item in items:
        tokens_dict2.append((item[0], int(item[1]), int(item[2]), int(item[3])))

    # start merge the files
    # merged_dict - will keep the merged dictionaries, and the write to the file on disk will be in the end
    # the merge of the lists files will be done while written directly to the merged file on the disk
    merged_dict = []
    idx1 = 0
    idx2 = 0
    while idx1 < len(tokens_dict1) and idx2 < len(tokens_dict2):
        # case 1 - the word appears in the both files
        if tokens_dict1[idx1][0] == tokens_dict2[idx2][0]:
            num_bytes_list1 = tokens_dict1[idx1][3]
            num_bytes_list2 = tokens_dict2[idx2][3]

            # in the last merge we "open" the mailing list, calculate gaps, encode it again and write to the binary lists file
            if is_last:
                mailing_list1 = utils.buildDecodedMailingList(lists_file1, num_bytes_list1)
                mailing_list2 = utils.buildDecodedMailingList(lists_file2, num_bytes_list2)
                list_size = handleLastMerge(mailing_list1 + mailing_list2, lists_merged_file)

                merged_dict.append((tokens_dict1[idx1][0], tokens_dict1[idx1][1] + tokens_dict2[idx2][1],
                                    tokens_dict1[idx1][2] + tokens_dict2[idx2][2],
                                    list_size))
            # in the usual case - write the lists to the file as is
            else:
                lists_merged_file.write(lists_file1.read(num_bytes_list1))
                lists_merged_file.write(lists_file2.read(num_bytes_list2))

                merged_dict.append((tokens_dict1[idx1][0], tokens_dict1[idx1][1] + tokens_dict2[idx2][1],
                                    tokens_dict1[idx1][2] + tokens_dict2[idx2][2],
                                    num_bytes_list1 + num_bytes_list2))

            idx1 += 1
            idx2 += 1

        # case 2 - the word appears just in the first file
        elif tokens_dict1[idx1][0] < tokens_dict2[idx2][0]:
            num_bytes_list1 = tokens_dict1[idx1][3]
            # in the last merge we "open" the mailing list, calculate gaps, encode it again and write to the binary lists file
            if is_last:
                mailing_list = utils.buildDecodedMailingList(lists_file1, num_bytes_list1)
                list_size = handleLastMerge(mailing_list, lists_merged_file)

                merged_dict.append((tokens_dict1[idx1][0], tokens_dict1[idx1][1], tokens_dict1[idx1][2], list_size))
            # in the usual case - write the lists to the file as is
            else:
                lists_merged_file.write(lists_file1.read(num_bytes_list1))
                merged_dict.append((tokens_dict1[idx1][0], tokens_dict1[idx1][1], tokens_dict1[idx1][2],
                                    num_bytes_list1))

            idx1 += 1

        # case 3 - the word appears just in the second file
        else:
            num_bytes_list2 = tokens_dict2[idx2][3]
            # in the last merge we "open" the mailing list, calculate gaps, encode it again and write to the binary lists file
            if is_last:
                mailing_list = utils.buildDecodedMailingList(lists_file2, num_bytes_list2)
                list_size = handleLastMerge(mailing_list, lists_merged_file)

                merged_dict.append((tokens_dict2[idx2][0], tokens_dict2[idx2][1], tokens_dict2[idx2][2], list_size))
            # in the usual case - write the lists to the file as is
            else:
                lists_merged_file.write(lists_file2.read(num_bytes_list2))
                merged_dict.append((tokens_dict2[idx2][0], tokens_dict2[idx2][1], tokens_dict2[idx2][2],
                                    num_bytes_list2))

            idx2 += 1

    while idx1 < len(tokens_dict1):
        num_bytes_list1 = tokens_dict1[idx1][3]
        # in the last merge we "open" the mailing list, calculate gaps, encode it again and write to the binary lists file
        if is_last:
            mailing_list = utils.buildDecodedMailingList(lists_file1, num_bytes_list1)
            list_size = handleLastMerge(mailing_list, lists_merged_file)

            merged_dict.append((tokens_dict1[idx1][0], tokens_dict1[idx1][1], tokens_dict1[idx1][2], list_size))
        # in the usual case - write the lists to the file as is
        else:
            lists_merged_file.write(lists_file1.read(num_bytes_list1))
            merged_dict.append((tokens_dict1[idx1][0], tokens_dict1[idx1][1], tokens_dict1[idx1][2], num_bytes_list1))

        idx1 += 1

    while idx2 < len(tokens_dict2):
        num_bytes_list2 = tokens_dict2[idx2][3]
        # in the last merge we "open" the mailing list, calculate gaps, encode it again and write to the binary lists file
        if is_last:
            mailing_list = utils.buildDecodedMailingList(lists_file2, num_bytes_list2)
            list_size = handleLastMerge(mailing_list, lists_merged_file)

            merged_dict.append((tokens_dict2[idx2][0], tokens_dict2[idx2][1], tokens_dict2[idx2][2], list_size))
        # in the usual case - write the lists to the file as is
        else:
            lists_merged_file.write(lists_file2.read(num_bytes_list2))
            merged_dict.append((tokens_dict2[idx2][0], tokens_dict2[idx2][1], tokens_dict2[idx2][2], num_bytes_list2))

        idx2 += 1

    for item in merged_dict:
        dict_merged_file.write(item[0] + str((item[1], item[2], item[3])))

    dict_file1.close()
    dict_file2.close()
    lists_file1.close()
    lists_file2.close()


def mergeMetaFiles(metaFile1, metaFile2, distDir):
    """ This method read the 2 meta data files from the disk and build a merge meta data file on the disk """
    # the meta data files to merge
    meta_file1 = open(metaFile1, 'r')
    meta_file2 = open(metaFile2, 'r')

    # the distination dir where the merged files will be
    if not os.path.exists(distDir):
        os.makedirs(distDir)
    # the distination file for the merged data
    meta_merged_file = open(distDir + "/meta data.txt", 'w')

    num_reviews = str(int(meta_file1.readline()) + int(meta_file2.readline()))
    num_tokens = str(int(meta_file1.readline()) + int(meta_file2.readline()))
    meta_merged_file.write(f"{num_reviews}\n{num_tokens}\n")

    for line in meta_file1:
        meta_merged_file.write(line)
    for line in meta_file2:
        meta_merged_file.write(line)

    meta_file1.close()
    meta_file2.close()


def deleteDirWithFiles(dir):
    """ This method get a dir and delete it with all its files """
    files = os.listdir(dir)
    for file in files:
        os.remove(dir + '/' + file)
    os.rmdir(dir)


def mergeIndexes(dir):
    """ This method get a dir name for the final index on the disk.
        The method run over all the indexes and calls the merge functions.
        Finally, the method puts the final files to the desired dir"""
    list_dirs = os.listdir(dir)
    print(list_dirs)

    num_merge = 1
    while len(list_dirs) >= 2:
        is_last = True if len(list_dirs) == 2 else False
        print(is_last)
        first_dir = list_dirs[0]
        second_dir = list_dirs[1]
        path_dir1 = f"{dir}/{first_dir}"
        path_dir2 = f"{dir}/{second_dir}"
        merge_dir = f"{dir}/dirMerged{str(num_merge)}"
        mergeDictAndListsFiles(path_dir1 + '/dict.txt', path_dir2 + '/dict.txt', path_dir1 + '/lists.bin',
                               path_dir2 + '/lists.bin', merge_dir, is_last)
        mergeMetaFiles(path_dir1 + '/meta data.txt', path_dir2 + '/meta data.txt', merge_dir)

        deleteDirWithFiles(path_dir1)
        deleteDirWithFiles(path_dir2)
        num_merge += 1

        list_dirs = os.listdir(dir)
        print(list_dirs)

    # extract files from the last dir to the main (final) index dir
    last_dir = f"{dir}/{list_dirs[0]}"
    files = os.listdir(last_dir)
    for file in files:
        shutil.move(last_dir + '/' + file, dir)

    os.rmdir(last_dir)
