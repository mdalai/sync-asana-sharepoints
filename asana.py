
import base64
import six
import requests
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote
try:
    import simplejson as json
except ImportError:
    import json

class AsanaException(Exception):
    pass


class ASANA_API(object):
    """ wrapper for the Asana api
    """
    def __init__(self, api_key, debug=False):
        self.debug = debug
        self.asana_url = "https://app.asana.com/api"
        self.api_version = "1.0"
        self.aurl = "/".join([self.asana_url,self.api_version])
        self.api_key = api_key
        #self.bauth = self.get_basic_auth()

    def get_basic_auth(self):
        s = six.b(self.api_key + ":")
        return base64.b64encode(s).rstrip()

    def handle_exception(self, r):
        """ Handle exceptions
        :param r: request object
        :returns: 1 if exception was 429 (rate limit exceeded), otherwise, -1
        """
        if self.debug:
            print("-> Got: {0}".format(r.status_code))
            print("-> {0}".format(r.text))
        if (r.status_code == 429):
            self._handle_rate_limit(r)
            return 1
        else:
            raise AsanaException('Received non 2xx or 404 status code on call')


    def _handle_rate_limit(self, r):
        """ Sleep for length of retry time
        :param r: request object
        """
        retry_time = int(r.headers['Retry-After'])
        assert(retry_time > 0)
        if self.debug:
            print("-> Sleeping for {0} seconds".format(retry_time))
        time.sleep(retry_time)


    def _asana(self, api_target):
        target = "/".join([self.aurl, quote(api_target ,safe="/&=?")])
        if self.debug:
            print("-> calling: {}".format(target))
        r = requests.get(target, auth=(self.api_key,""))
        if self._ok_status(r.status_code) and r.status_code is not 404:
            if r.headers['content-type'].split(';')[0] == 'application/json':
                if hasattr(r, 'text'):
                    return json.loads(r.text)['data']
                elif hasattr(r, 'content'):
                    return json.loads(r.content)['data']
                else:
                    raise AsanaException('Unknown format in response from api')
            else:
                raise AsanaException(
                    'Did not receive json from api: %s' % str(r))
        else:
            if (self.handle_exception(r) > 0):
                return self._asana(api_target)


    @classmethod
    def _ok_status(self, status_code):
        """Check whether status_code is a ok status i.e. 2xx or 404"""
        status_code = int(status_code)
        if status_code / 200 == 1:
            return True
        elif status_code / 400 == 1:
            if status_code is 404:
                return True
            else:
                return False
        elif status_code is 500:
            return False


    def list_workspaces(self):
        return self._asana('workspaces')
    def list_projects(self,workspace=None,archived=None):
        target = "projects"
        if archived:
            target = target + "?archived={0}".format(archived)
        if workspace:
            target = "workspaces/{0}/".format(workspace) + target
        return self._asana(target)



        
if '__name__' == '__main__':
    key = '0/b4ce1442dad5e0776aa37d8202f3bffc'
    api = ASANA_API(key, debug=True)
    r = api.list_workspaces()
    r2 = api.list_projects()


    print(r)
    print(r2)
