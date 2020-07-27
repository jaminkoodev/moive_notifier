import requests
import threading
import time
from datetime import datetime
from datetime import timedelta
import telepot
import logging
import pickle

# 메가박스
# post방식으로 통신
# JSON
#   brchNm : 상영관 brch
#   detailType : 영화별 | 지역별 | 특별관 (movie | area | spcl)
#   theabKindCd : 특별관 분류 돌비시네마 | 더 부티크 | MX관 | 컴포트 | 메가박스 키즈 | 더 퍼스트 클럽 (DBC | TB | MX | CFT | MKB | TFC)
#   firstAt : 첫 화면인지 여부 Y | N (Y일경우 오늘 날짜만 검색 가능)
#   brchNo : 상영관번호 (1581=목동, 1351=코엑스)
#   playDe : 확인할 상영날짜
#   crtDe : 현재날짜
def get_megabox_movie_list(date, brch, shall):
    brch_dic = {'코엑스':'1351', '목동':'1581', '상암':'1211'}
    crtde = datetime.today().strftime("%Y%m%d")

    URL = "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"
    parameters = {"masterType": "brch", # 상영관
                  "detailType": "spcl", # 분류 기준 : 영화별 | 지역별 | 특별관 (movie | area | spcl)
                  "theabKindCd": shall, # 돌비시네마 | 더 부티크 | MX관 | 컴포트 | 메가박스 키즈 | 더 퍼스트 클럽 (DBC | TB | MX | CFT | MKB | TFC)
                  "brchNo": brch_dic[brch], # 상영관번호 : 코엑스 | 목동 | 상암 | (1351 | 1581 | 1211) 주요 상영관만 표기하였음
                  "firstAt": "N", #  **** Y일경우 오늘 날짜만 검색가능하니 반드시 N으로 설정!! ****
                  "brchNo1": brch_dic[brch], # 상영관번호 : 코엑스 | 목동 | 상암 | (1351 | 1581 | 1211) 주요 상영관만 표기하였음
                  "spclbYn1": "Y", # Y | N
                  "theabKindCd1": shall, # 특별관 분류 : 돌비시네마 | 더 부티크 | MX관 | 컴포트 | 메가박스 키즈 | 더 퍼스트 클럽 (DBC | TB | MX | CFT | MKB | TFC)
                  "crtDe": crtde, # 접속한 날짜
                  "playDe": date} # 찾고있는 날짜
    response = requests.post(URL, data=parameters).json()
    return response['megaMap']['movieFormList']

# 현재 날짜에 상영중인 영화 제목의 고유번호를 반환함
def get_megabox_movie_no_list(response):
    movielst = []
    for item in response:
        if item['movieNo'] not in movielst:
            movielst.append(item['movieNo'])

    return movielst

def megabox_crawling(date, brch, shall):
    shall_dic = {'DBC': 'Dolby Cinema', 'TB': 'The Boutique', 'MX': 'MX관',
                 'CFT': '컴포트관', 'MKB': 'MEGA KIDS', 'TFC': 'The First Class'}
    filename = 'megabox' + brch + shall + '.pickle'

    try:
        with open(filename, 'rb') as f:
            sdate = pickle.load(f)

    except (EOFError, FileNotFoundError):
        sdate = date
    logger.info('메가박스 검색 시작 날짜 : {}'.format(sdate))
    while True:
        movie_list = get_megabox_movie_list(sdate, brch, shall)
        movie_no_list = get_megabox_movie_no_list(movie_list)
        movie_split_list = []
        try:
            if not movie_list:
                logger.info("메가박스 {} {} Not Found ({})".format(brch, shall, sdate))
                raise ValueError

            logger.info("메가박스 {} {} Found ({})".format(brch, shall, sdate))
            for i in range(len(movie_no_list)):
                line = []
                for mvlst in movie_list:
                    if movie_no_list[i] == mvlst['movieNo']:
                        if mvlst['movieNm'] not in line:
                            line.append(mvlst['movieNm'])
                        line.append(mvlst['playStartTime'])
                        line.append("(" + str(mvlst['restSeatCnt']) + "/" + str(mvlst['totSeatCnt']) + ")")
                movie_split_list.append(line)

            sendmsg = "*메가박스 " + brch + " " + shall_dic[shall] + "*\n"
            week = t[datetime.strptime(sdate, "%Y%m%d").weekday()]
            sendmsg += sdate + " (" + week + ") 예매 오픈\n"
            for i in range(len(movie_split_list)):
                sendmsg = sendmsg + "*" + movie_split_list[i][0] + "*\n"
                for j in range(1, len(movie_split_list[i]), 2):
                    sendmsg = sendmsg + "[" + movie_split_list[i][j] + "](https://www.megabox.co.kr/booking) "
                    sendmsg = sendmsg + movie_split_list[i][j + 1] + "\n"
                sendmsg += "\n"
            bot.sendMessage(mc, sendmsg, parse_mode="Markdown", disable_web_page_preview=True)
            # 결과를 찾았으니 다음날로 넘어간다
            sdate = datetime.strptime(sdate, "%Y%m%d")
            sdate += timedelta(days=1)
            sdate = sdate.strftime("%Y%m%d")

            with open(filename, 'wb') as f:
                pickle.dump(sdate, f)
        except ValueError:  # 리스트가 비어있을경우(예매오픈하기 전) 30초마다 재탐색
            time.sleep(30)

if __name__ == "__main__":
    latest_date = "20200727" # 프로그램을 실행시킨 시간부터 탐색
    t = ['월', '화', '수', '목', '금', '토', '일']
    # 텔레그램 봇 연결 파트
    mytoken = ""  # 텔레그램 봇 토큰
    mc = ""  # My Channel
    bot = telepot.Bot(mytoken)

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s|%(lineno)s] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    sh = logging.StreamHandler()
    fh = logging.FileHandler('./log.log')

    sh.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.setLevel(level=logging.INFO)

    logger.info('서버가 정상적으로 시작되었습니다.')
    logger.info('검색 디폴트 날짜 : {}'.format(latest_date))

    # 영화 리스트 불러오기

    megabox = threading.Thread(target=megabox_crawling, args=(latest_date, '코엑스', 'DBC',))
    megabox.start()
    megabox.join()
    logger.info("Server Exit")