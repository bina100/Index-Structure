import re
import os

import utils
import mergeIndexes


class IndexWriter:
    def write(self, inputFile, dir):
        """ Given product review data, creates an on disk index
            inputFile is the path to the file containing the review data,
            dir is the directory in which all index files will be created.
            if the directory does not exist, it should be created """
        data_file = open(inputFile,'r')
        if not os.path.exists(dir):  # if the directory does not exist - create it
            os.makedirs(dir)
        else:   # if the directory is allready exist and not empty - delete all files
            all_files = os.listdir(dir)
            for file in all_files:
                os.remove(f"{dir}/{file}")
        num_block = 0
        review_i = 0
        eof = False  # save if we arrive to the end_of_file, if not - build more index
        while not eof:
            if review_i == 0:   # every 100,000 reviews
                # open 3 files to create a new index on the disk
                num_block += 1
                # Gives a unique name for each block_dir, maintaining alphabetical order (up to 1000 indexes)
                num_block_str = "00" + str(num_block) if num_block < 10 else ("0" + str(num_block) if num_block < 100 else str(num_block))
                block_dir = f"{dir}/{dir}{num_block_str}"
                os.makedirs(block_dir)
                dict_file = open(block_dir + '/dict.txt', 'w')
                lists_file = open(block_dir + '/lists.bin', 'wb')
                meta_file = open(block_dir + '/meta data.txt', 'w')

                product_id = []
                helpfulness = []
                score = []
                text = []

            """ read and analyze the raw data file """
            flag = False
            for line in data_file:
                if review_i == 100000:
                    review_i = 0
                    flag = True
                    break
                p_id = re.search(r'productId: ([A-Z0-9]{10,})', line)   # search for a product Id
                if p_id:
                    review_i += 1
                    product_id.append(p_id.group(1))
                    continue
                h = re.search(r'helpfulness: (\d+)/(\d+)', line)    # search for a helpfulness
                if h:
                    helpfulness.append((h.group(1), h.group(2)))
                    continue
                s = re.search(r'score: ([1-5]).0', line)    # search for a score
                if s:
                    score.append(s.group(1))
                    continue
                t = re.search(r'text: (.*)', line)  # search for the text
                if t:
                    txt = t.group(1)
                    line = data_file.readline()
                    while line:  # continue reading the text, until an empty line
                        if line != '\n':
                            txt += ' ' + line
                            line = data_file.readline()
                        else:
                            break
                    text.append(txt)

            if not flag:
                eof = True

            """ Divide the text into separate words by alphanumeric character
                and normalize the tokens into small letters """
            for i, review_text in enumerate(text):
                text_words = re.split(r'[^A-Za-z0-9]+', review_text)
                text[i] = [word.lower() for word in text_words if word != '']    # Without the empty string

            """ Build the dictionary """
            tokens_dict = {}
            for i, text_words in enumerate(text):
                review_id = i + 1 + (num_block-1)*100_000   # keep the real review_id - we will need that for the merge stage
                for word in text_words:
                    if not word in tokens_dict:
                        tokens_dict[word] = (1, 1, {review_id: 1})
                    else:
                        if review_id in tokens_dict[word][2]:
                            tokens_dict[word][2][review_id] += 1
                            tokens_dict[word] = (tokens_dict[word][0] + 1, tokens_dict[word][1], tokens_dict[word][2])
                        else:
                            tokens_dict[word][2].update({review_id: 1})
                            tokens_dict[word] = (tokens_dict[word][0] + 1, tokens_dict[word][1] + 1, tokens_dict[word][2])

            """ Write the mailing Lists to lists_file and save the size (in bytes) of each list in the appropriate place in the dictionary """
            sorted_words = sorted(tokens_dict.keys())
            for word in sorted_words:
                mailing_list = tokens_dict[word][2]     # reviewIDs + freq. in a dict object

                mailing_list_arr = []
                for (r_id, freq) in mailing_list.items():
                    mailing_list_arr += [r_id, freq]

                # calculate here the gaps between review_ids, only if there is just one index
                if eof and num_block == 1:
                    mailing_list_arr = utils.calGaps(mailing_list_arr)

                bytes_arr = utils.buildEncodedMailingList(mailing_list_arr)  # build encoded mailing list in array of bytes

                start_pointer = lists_file.tell()   # keep the place on the file where we start writing the list
                lists_file.write(bytearray(bytes_arr))
                list_size = lists_file.tell() - start_pointer   # keep the list size, in bytes
                tokens_dict[word] = (tokens_dict[word][0], tokens_dict[word][1], list_size)     # for every token keep: total_freq, review_freq, list_size (in bytes)

            lists_file.close()

            """ Write the dictionary to dict_file file """
            sorted_words = sorted(tokens_dict.keys())
            for word in sorted_words:
                dict_file.write(word + str(tokens_dict[word]))
            dict_file.close()

            """ Write the other information to meta_data file """
            num_reviews = len(product_id)
            num_tokens = 0
            for text_words in text:
                num_tokens += len(text_words)
            meta_file.write(str(num_reviews) + '\n')
            meta_file.write(str(num_tokens) + '\n')
            for i, (p_id, h, s, t) in enumerate(zip(product_id, helpfulness, score, text)):
                meta_file.write(str(i + 1 + (num_block-1)*100_000) + ' ' + str(p_id) + ' ' + str(h[0]) + ' ' + str(h[1]) + ' ' + str(s) + ' ' + str(len(t)) + '\n')
            meta_file.close()

        data_file.close()

        """ Call merge function - merge all the indexes that created on disk """
        mergeIndexes.mergeIndexes(dir)


    def removeIndex(self, dir):
        """ Delete all index files by removing the given directory """
        if os.path.exists(dir):
            all_files = os.listdir(dir)
            for file in all_files:
                os.remove(f"{dir}/{file}")
            os.rmdir(dir)
        else:
            print("The directory does not exist")
