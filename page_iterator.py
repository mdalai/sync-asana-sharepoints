
class PageIterator(object):
    def __init__(self, api, target):
        self.api = api
        self.target = target
        self.limit = 100

        self.continuation = False

    def __iter__(self):
        """Iterator interface, self is an iterator"""
        return self

    def __next__(self):
        """Iterator interface, returns the next 'page'"""
        if self.continuation == None:
            raise StopIteration
        # first call to __next__
        elif self.continuation == False:
            result = self.get_initial()
        # Subsequent calls to __next__
        else:
            result = self.get_next()
        # Extract the continuation from the response
        self.continuation = result[self.CONTINUATION_KEY]  # json part: "next_page"
        # Get the data, update the count, return the data
        data = result["data"]  # json part: "data"
        return data

    def next(self):
        """Alias for __next__"""
        return self.__next__()

    def items(self):
        for page in self:
            yield page
            #for item in page:
            #    yield item 
        raise StopIteration


class Pagination(PageIterator):
    CONTINUATION_KEY = 'next_page'    

    def get_initial(self):
        self.target = self.target + "&limit={}".format(self.limit)
        print("URI1={}".format(self.target))
        return self.api._get_asana(self.target)

    def get_next(self):
        print(">>>>>>>>>>>>>>>OFFSET:{}".format(self.continuation['offset']))
        target = self.target + "&offset={}".format(self.continuation['offset'])
        return self.api._get_asana(target)


