import re
import utils


def enum(**enums):
    return type('Enum', (), enums)

Fields = enum(REVIEW_ID=0, PRODUCT_ID=1, HELPFUL_NUMERATOR=2, HELPFUL_DENOMINATOR=3, SCORE=4, TXT_LEN=5)
Tuple = enum(COLLECTION_FREQUENCY=0, TOKEN_FREQUENCY=1, REVIEWS_LIST=2, LIST_SIZE=3)


class IndexReader:
    def __init__(self, dir):
        """Creates an IndexReader which will read from
        the given directory"""
        self.dir = dir
        self.lists_file = open(self.dir + '/lists.bin', 'rb')
        self.meta_file = open(self.dir + '/meta data.txt', 'r')
        self.tokens_dict = self._buildTokensDict()

    def _buildTokensDict(self):
        """ This method read the dictionary file from the disk and build a tokens dict in the memory """
        dict_file = open(self.dir + '/dict.txt', 'r')
        content = dict_file.read()
        items = re.findall(r'([a-z0-9]+).(\d+), (\d+), (\d+).', content)
        pointer = 0  # Will keep the pointer to the beginning of the list
        tokens_dict = {}
        for item in items:
            tokens_dict[item[0]] = (int(item[1]), int(item[2]), pointer, int(item[3]))
            pointer += int(item[3])  # Adds the list size in bytes
        dict_file.close()

        return tokens_dict

    def _dataByReviewId(self, reviewId, field):
        """ This method accesses the meta_file on the disk,
        searches for the appropriate line for the requested review
        and returns the requested information """
        self.meta_file.seek(0)
        # Skips the first 2 lines of the file that store other information
        next(self.meta_file)
        next(self.meta_file)
        for line in self.meta_file:
            if line.startswith(str(reviewId)):
                data = line.split()
                return data[field]
        return None if field == Fields.PRODUCT_ID else -1

    def getProductId(self, reviewId):
        """Returns the product identifier for the given
        review
        Returns null if there is no review with the
        given identifier"""
        return self._dataByReviewId(reviewId, Fields.PRODUCT_ID)

    def getReviewScore(self, reviewId):
        """Returns the score for a given review
        Returns -1 if there is no review with the given
        identifier"""
        return int(self._dataByReviewId(reviewId, Fields.SCORE))

    def getReviewHelpfulnessNumerator(self, reviewId):
        """Returns the numerator for the helpfulness of
        a given review
        Returns -1 if there is no review with the given
        identifier"""
        return int(self._dataByReviewId(reviewId, Fields.HELPFUL_NUMERATOR))

    def getReviewHelpfulnessDenominator(self, reviewId):
        """Returns the denominator for the helpfulness
        of a given review
        Returns -1 if there is no review with the given
        identifier"""
        return int(self._dataByReviewId(reviewId, Fields.HELPFUL_DENOMINATOR))

    def getReviewLength(self, reviewId):
        """Returns the number of tokens in a given
        review
        Returns -1 if there is no review with the given
        identifier"""
        return int(self._dataByReviewId(reviewId, Fields.TXT_LEN))

    def getTokenFrequency(self, token):
        """Return the number of reviews containing a
        given token (i.e., word)
        Returns 0 if there are no reviews containing
        this token"""
        return self.tokens_dict[token][Tuple.TOKEN_FREQUENCY] if token in self.tokens_dict else 0

    def getTokenCollectionFrequency(self, token):
        """Return the number of times that a given
        token (i.e., word) appears in
        the reviews indexed
        Returns 0 if there are no reviews containing
        this token"""
        return self.tokens_dict[token][Tuple.COLLECTION_FREQUENCY] if token in self.tokens_dict else 0

    def getReviewsWithToken(self, token):
        """Returns a series of integers of the form id-1, freq-1, id-2, freq-2, ... such
        that id-n is the n-th review containing the
        given token and freq-n is the
        number of times that the token appears in
        review id-n
        Note that the integers should be sorted by id
        Returns an empty Tuple if there are no reviews
        containing this token"""
        pointer = self.tokens_dict[token][Tuple.REVIEWS_LIST] if token in self.tokens_dict else None  # Gets the pointer to the review list of the given token
        if pointer is not None:
            size_in_bytes = self.tokens_dict[token][Tuple.LIST_SIZE]    # Gets the length (in bytes) of the review list
            self.lists_file.seek(pointer)   # Move to the appropriate place in the file, according to the pointer

            mailing_list = utils.buildDecodedMailingList(self.lists_file, size_in_bytes)  # decoded the mailing list of the token

            reviews_diff_list = mailing_list[::2]  # get the reviewIDs (in differences) only
            freq_list = mailing_list[1::2]  # get the freq. only
            reviews_list = utils.getArrayFromdiff(reviews_diff_list)    # get the original reviewIDs

            mailing_list = []
            for (r_id, freq) in zip(reviews_list, freq_list):  # merge the reviewIDs + freq. back together
                mailing_list.extend([r_id, freq])

            return mailing_list

        return ()   # There are no reviews containing this token

    def getNumberOfReviews(self):
        """Return the number of product reviews
        available in the system"""
        self.meta_file.seek(0)
        num_reviews = self.meta_file.readline() # The first line in the meta_file saves the number of reviews
        return int(num_reviews)

    def getTokenSizeOfReviews(self):
        """Return the number of tokens in the system
        (Tokens should be counted as many times as they
        appear)"""
        self.meta_file.seek(0)
        next(self.meta_file)
        num_tokens = self.meta_file.readline()  # The second line in the meta_file saves the number of tokens
        return int(num_tokens)

    def getProductReviews(self, productId):
        """Return the ids of the reviews for a given
        product identifier
        Note that the integers returned should be
        sorted by id
        Returns an empty Tuple if there are no reviews
        for this product"""
        self.meta_file.seek(0)
        # Skips the first 2 lines of the file that store other information
        next(self.meta_file)
        next(self.meta_file)
        review_ids = ()
        for line in self.meta_file:
            res = re.match(r'(\d+) '+productId, line)
            if res:     # If the given productId appears in the line - save the appropriate review id
                review_ids += (int(res.group(1)), )
        return review_ids

    def destructor(self):
        """ This method simulates destructor - handles the files closing"""
        self.lists_file.close()
        self.meta_file.close()
