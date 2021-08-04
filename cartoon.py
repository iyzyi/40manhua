import config
from requests_manage import RequestManager
from file_downloader import FileDownloader
from progress_bar import ProgressBar
import re, os
from textwrap import dedent
from threading import Thread, Lock
#import pdfkit       # 首先去https://wkhtmltopdf.org/downloads.html 下载wkhtmltopdf安装包，并且安装到电脑上。然后pip install pdfkit, pip install wkhtmltopdf



def printf(str):
    if config.no_print:
        pass
    else:
        print(str)


def already_downloaded(book_name):
    with open(r'SAVED.txt')as f:
        ids = f.read()
    return book_name in ids.split('\n')

def already_failed(book_name):          # 确认此漫画书失效，无法下载
    with open(r'FAILED.txt')as f:
        ids = f.read()
    return book_name in ids.split('\n')

def download_success(book_name):
    log_path = r'SAVED.txt'
    with open(log_path, 'a+')as f:
        f.write(book_name+'\n')

def download_failed(book_name):
    log_path = r'FAILED.txt'
    with open(log_path, 'a+')as f:
        f.write(book_name+'\n')



def down_one(book_url):

    book_name = re.search(r'https://www.40manhua.com/(.+?)/', book_url).group(1)
    if already_downloaded(book_name):
        printf('{} 早已下载，跳过'.format(book_url))
        return 2
    if already_failed(book_name):
        print('{} 已确认失效无法下载，跳过'.format(book_url))
        return 3

    if not os.path.exists(config.root_path):
        os.makedirs(config.root_path)

    request = RequestManager(config.headers, config.proxies)
    res = request.get(book_url)
    if not res:
        printf('无法打开{}，任务中止'.format(book_url))
        return 0
    else:
        # 获取基本信息
        book_html = res.text
        cartoon_title = re.search(r'\<h1.+?\>(.+?)\</h1\>', book_html).group(1)
        cartoon_title = re.sub(r'[\/\\\*\?\|/:"<>\.]', '', cartoon_title)
        cartoon_intro = re.search(r'class="desc-content".+?\</span\>(.+?)\</p\>', book_html).group(1)
        cartoon_cover_url = re.search(r'itemprop="image"\s*?content="(.+?)">', book_html).group(1)
        main_view_chapter_titles = re.findall(r'class\="name".+?j_chapter_badge.+?\</i\>(.+?)\</p\>', book_html)            # 该项只是为了确定进度条长度，具体的章节名通过迭代json获取，并保存至chapter_titles
        first_chapter_url = 'https:' + re.search(r'id="j_chapter_list".+?data-chapter.+?title=".+?"\s*?href="(.+?)"', book_html, re.S).group(1)
        book_id = re.search(r'https\://www\.kanman\.com/(\d+?)/.+?\.html', first_chapter_url).group(1)
        printf('书名：{}\n简介：{}\n本漫画共{}回'.format(cartoon_title, cartoon_intro, len(main_view_chapter_titles)))
        chapter_titles = []

        
        # 获取封面
        res = request.get(cartoon_cover_url)
        book_dir_path = os.path.join(config.root_path, cartoon_title)
        if not os.path.exists(book_dir_path):
            os.makedirs(book_dir_path)

        if res:
            file_path = os.path.join(config.root_path, cartoon_title, 'cover.jpg')
            with open(file_path, 'wb')as f:
                f.write(res.content)
        else:
            printf('封面{} 下载失败'.format(cartoon_cover_url))
            #return 0


        # 获取全部图片链接
        print('正在获取 {} 全部章节的图片链接列表......'.format(cartoon_title))
        if not config.no_print:
            progress_bar = ProgressBar(len(main_view_chapter_titles), fmt=ProgressBar.IYZYI)
        first = True
        chapters_imgs_list = []
        while True:
            if first:
                res = request.get(first_chapter_url)
                if res:
                    chapter_newid = re.search(r'current_chapter:{.+?chapter_newid:"(.+?)".+?}', res.text).group(1)
                    next_chapter = {'chapter_newid': chapter_newid}
                else:
                    printf('无法打开{}，任务中止'.format(first_chapter_url))
                    return 0
                    break
                first = False

            if next_chapter != None:
                chapter_newid = next_chapter['chapter_newid']
                chapter_url = 'https://www.kanman.com/api/getchapterinfov2?product_id=1&productname=kmh&platformname=pc&comic_id={}&chapter_newid={}&isWebp=1&quality=middle'.format(book_id, chapter_newid)
                '''
                API
                isWebp: 0为非webp格式，1为webp格式
                quality: low, middle, high
                '''
            else:
                break
            
            res = request.get(chapter_url)
            chapter_img_list = res.json()['data']['current_chapter']['chapter_img_list']
            chapter_name = res.json()['data']['current_chapter']['chapter_name'].strip()
            chapter_name = re.sub(r'[\/\\\*\?\|/:"<>\.]', '', chapter_name)
            chapter_titles.append(chapter_name)
            next_chapter = res.json()['data']['next_chapter']

            for img_url in chapter_img_list:
                img_info = {'title': chapter_name, 'img_url': img_url}
                chapters_imgs_list.append(img_info)

            if not config.no_print:
                progress_bar.current += 1
                progress_bar()

        #if not config.no_print:
        #    progress_bar.done()     
           
        # 下载全部图片
        print('正在下载 {} 全部章节的图片......'.format(cartoon_title))
        if config.no_print:
            ImgDown = FileDownloader(chapters_imgs_list, cartoon_title, False)
            result = ImgDown.success
        else:
            ImgDown = FileDownloader(chapters_imgs_list, cartoon_title, True)
            result = ImgDown.success

        if not result:
            return 0

        # 生成HTML文件
        chapters_html = ''
        for chapter_title in chapter_titles:
            chapter_path = os.path.join(config.root_path, cartoon_title, chapter_title)
            imgs_path = os.listdir(chapter_path)
            imgs_path = sorted(imgs_path, key=lambda x: (int(x.split('.')[0])))
            chapter_html = ''
            for img_path in imgs_path:
                chapter_html += '\n    <p><img src="./{}/{}"></p>'.format(chapter_title, img_path)
            chapters_html += '\n    <h2>{}</h2>{}'.format(chapter_title, chapter_html)


        html_frame = dedent('''\
                            <html>
                             <head>
                              <meta charset="utf-8">
                              <title>{}</title>
                              <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                             </head>
                             <body bgcolor="#00FFFF">
                              <div style="margin:40px ; text-align:center;">
                               <a href="{}" style="color:red;text-decoration:none;">
                                <h1>{}</h1>
                               </a>
                               <div class="intro_and_cover">
                                <p>{}</p>
                                <img src="{}">
                               </div>
                               <div class="chapters">{}
                               </div>
                              </div>
                             </body>
                            </html>
                            ''').format(cartoon_title, book_url, cartoon_title, cartoon_intro, './cover.jpg', chapters_html)

        html_path = os.path.join(book_dir_path, cartoon_title+'.html')                    
        with open(html_path, 'w', encoding='utf-8')as f:
            f.write(html_frame)

        download_success(book_name)
        print('成功保存 {}, URL: {}\n'.format(cartoon_title, book_url))
        return 1

        
        # # HTML转换成PDF
        # pdf_path = os.path.join(book_dir_path, cartoon_title+'.pdf')

        # wkhtmltopdf_config = pdfkit.configuration(wkhtmltopdf = config.wkhtmltopdf_path)
        # options = {
        #     "enable-local-file-access": ''
        # }
        # pdfkit.from_file(html_path, pdf_path, configuration=wkhtmltopdf_config, options = options)



comic_newid_list = []
thread_list = []
lock = Lock()
main_progress_bar = None

def thread_func(null):
    global comic_newid_list
    global thread_list
    global lock
    global main_progress_bar

    while True:
        comic_newid = None
        lock.acquire()
        if len(comic_newid_list) > 0:
            comic_newid = comic_newid_list.pop()
        else:
            lock.release()
            break
        lock.release()

        if comic_newid:
            book_url = 'https://www.40manhua.com/{}/'.format(comic_newid)
            try:
                res = down_one(book_url)
                if res == 1 or res == 2:
                    # 绘制进度条
                    lock.acquire()
                    main_progress_bar.current += 1
                    main_progress_bar()
                    lock.release()
                else:
                    print('下载{} 失败'.format(book_url))
            except Exception as e:
                print('{} 异常: {}'.format(book_url, e))



def down_all():
    config.no_print = False
    global comic_newid_list
    global thread_list
    global main_progress_bar
    
    
    getComicList_url = 'https://www.40manhua.com/api/getComicList/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43', 
        'Referer': 'https://www.40manhua.com/sort/'
    }
    request = RequestManager(headers, config.proxies)
    res = request.get(getComicList_url)

    if res:
        books = res.json()['data']
        for book in books:
            comic_newid_list.append(book['comic_newid'])
        comic_newid_list = comic_newid_list[::-1]
        print('共{}部漫画'.format(len(comic_newid_list)))

        main_progress_bar = ProgressBar(len(comic_newid_list), fmt=ProgressBar.IYZYI)

        # 多线程
        for i in range(config.main_thread_num):
            t = Thread(target = thread_func, args=(1,))
            t.setDaemon(True)               #设置守护进程
            t.start()
            thread_list.append(t)

        for t in thread_list:
            t.join()                        #阻塞主进程，进行完所有线程后再运行主进程
    else:
        print('获取全部漫画列表失败')



if __name__ == '__main__':
    url = 'https://www.40manhua.com/touxingjiuyuetian/'
    #url = 'https://www.40manhua.com/hm/'
    down_one(url)


    #down_all()