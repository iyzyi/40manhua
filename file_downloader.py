import config
from requests_manage import RequestManager
from progress_bar import ProgressBar
from threading import Thread, Lock
from os import path, makedirs


class FileDownloader:
    
    def __init__(self, urls_list, relative_path, use_progress_bar = False):
        self.urls_list = urls_list
        self.relative_path = relative_path
        self.use_progress_bar = use_progress_bar
        self.thread_list = []
        self.request = RequestManager(config.headers, config.proxies)
        self.lock = Lock()
        self.path = path.join(config.root_path, relative_path)
        if not path.exists(self.path):
            makedirs(self.path)
        # 进度条
        if use_progress_bar:
            self.progress_bar = ProgressBar(len(self.urls_list), fmt=ProgressBar.IYZYI)
        self.success = True
        
        self.save_files()

        


    def save_files(self):
        for i in range(config.thread_num):
            t = Thread(target = FileDownloader.thread_func, args=(self,))
            t.setDaemon(True)               #设置守护进程
            t.start()
            self.thread_list.append(t)

        for t in self.thread_list:
            t.join()                        #阻塞主进程，进行完所有线程后再运行主进程
        #print()


    def thread_func(self):
        while True:
            img_info = None
            self.lock.acquire()

            if len(self.urls_list) > 0:
                img_info = self.urls_list.pop()
                chapter_title = img_info['title']
                dir_path = path.join(self.path, chapter_title)
                if not path.exists(dir_path):
                    makedirs(dir_path)
            else:
                self.lock.release()
                break

            self.lock.release()

            if img_info:
                self.save_file(img_info)

            # 绘制进度条
            self.lock.acquire()
            if self.use_progress_bar:
                self.progress_bar.current += 1
                self.progress_bar()
            self.lock.release()




    def save_file(self, img_info):
        chapter_title = img_info['title']
        img_url = img_info['img_url']

        file_name = img_url.split('/')[-1].split('?')[0] + '.jpg'
        file_path = path.join(self.path, chapter_title, file_name)
        if path.exists(file_path) and path.getsize(file_path) > 256:    #256 Byte
            #print('图片{} 已存在，不再下载'.format(file_path))
            return None

        res = self.request.get(img_url)
        if res:
            with open(file_path, 'wb')as f:
                f.write(res.content)
        else:
            print('图片{} 下载失败'.format(img_url))
            self.success = False
            #with open(file_path, 'wb')as f:
            #    f.write(b'')
        #print('成功下载：{}'.format(file_path))


# if __name__ == '__main__':
#     urls_list = ['http://file.iyzyi.com/test/1.txt', 'http://file.iyzyi.com/test/2.txt', 'http://file.iyzyi.com/test/3.txt', 'http://file.iyzyi.com/test/4.txt', 'http://file.iyzyi.com/test/5.txt', 'http://file.iyzyi.com/test/6.txt', 'http://file.iyzyi.com/test/7.txt', 'http://file.iyzyi.com/test/8.txt', 'http://file.iyzyi.com/test/9.txt', 'http://file.iyzyi.com/test/10.txt', 'http://file.iyzyi.com/test/11.txt', 'http://file.iyzyi.com/test/12.txt', 'http://file.iyzyi.com/test/13.txt', 'http://file.iyzyi.com/test/14.txt', 'http://file.iyzyi.com/test/15.txt', 'http://file.iyzyi.com/test/16.txt', ]
#     file_downloader = FileDownloader(urls_list, r'./file', use_progress_bar=True)
#     #file_downloader = FileDownloader(urls_list, r'./file')