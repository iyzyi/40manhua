import requests
import config


class RequestManager:

    def __init__(self, headers = None, proxies = None, timeout = 8, retry_num = 5):
        self.headers = headers 
        self.proxies = proxies
        self.timeout = timeout
        self.retry_num = retry_num

        self.session = requests.Session()


    def get(self, url, headers = None, proxies = None, timeout = None, retry_num = None):  
        kwargs = {}

        if headers:
            kwargs['headers'] = headers
        elif self.headers:
            kwargs['headers'] = self.headers

        if proxies:
            kwargs['proxies'] = proxies
        if self.proxies:
            kwargs['proxies'] = self.proxies

        if timeout:
            kargs['timeout'] = timeout
        elif self.timeout:
            kwargs['timeout'] = self.timeout
        
        if retry_num:
            _retry_num = retry_num
        else:
            _retry_num = self.retry_num


        success = False
        for i in range(_retry_num):
            try:
                #if i != 0:
                #    print('第{}次重连{}'.format(i+1, url))

                res = self.session.get(url, **kwargs)
                
                if res.status_code == 200:
                    success = True
                    #print(kwargs)
                    break
            except Exception as e:
                pass
                #print(e)
        if success:
            return res
        else:
            return False
        

    
# if __name__ == '__main__':
#     # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43'}
#     # proxies = {'http': '127.0.0.1:8889', 'https': '127.0.0.1:8889'} 
#     request = RequestManager(config.headers, config.proxies)
#     r = request.get('http://iyzyi.com')
#     if r:
#         print(r.text)