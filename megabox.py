import requests
import threading
import time
from datetime import datetime
from datetime import timedelta
import telepot
import logging
import pickle
import re
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
    brch_dic = {'강낭':'1372', '강남대로':'1359', '강동':'1341', '군자':'1431', '동대문':'1003',
                '마곡':'1572', '목동':'1581', '상봉':'1311', '상암월드컵경기장':'1211', '성수':'1331',
                '센트럴':'1371', '송파파크하비오':'1381', '신촌':'1202', '은평':'1221', '이수':'1561',
                '창동':'1321', '코엑스':'1351', '홍대':'1212', '화곡':'1571', 'ARTNINE':'1562'}
    shall_dic = {'돌비시네마':'DBC', '더 부티크':'TB', 'MX관':'MX',
                 '컴포트':'CFT', '메가박스 키즈':'MKB', '더 퍼스트 클럽':'TFC'}

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


def set_megabox_brch_reg(brch):
    brch = brch.replace(' ', '')

    if brch[-1] == "점" or brch[-1] == "관" or brch[-1] == "역" or brch[-1] == "동":
        brch = brch[:-2]

    brch = re.sub(r"(상암|상암월드컵경기장|월드컵경기장|월드컵경기장상암)", "상암월드컵경기장", brch)
    brch = re.sub(r"(센트럴|샌트럴|센트랄|샌트랄|고터|고속터미널|고속터미널역|터미널|강남터미널)", "센트럴", brch)
    brch = re.sub(r"(송파|문정|북정|송파파크하비오|파크하비오|송파하비오|송파하비오파크)", "송파파크하비오", brch)
    brch = re.sub(r"(신촌|신촌아트레온|아트레온|연세|연세대|아트레온신촌|신촌기차)", "신촌", brch)
    brch = re.sub(r"(코엑스|코엑스몰|봉은사|삼성|삼성동)", "코엑스", brch)
    brch = re.sub(r"(홍대|홍대입구|홍익대학교)", "홍대", brch)
    brch = re.sub(r"(ARTNINE|artnine|아트나인|아트나인이수|이수아트나인)", "ARTNINE", brch, flags=re.IGNORECASE)

    return brch


def set_megabox_shall_reg(shall):
    shall = shall.replace(' ', '')

    if shall[-1] == "점" or shall[-1] == "관":
        shall = shall[:-2]

    shall = re.sub(r"(DBC|돌비시네마|돌비|시네마|dolbycinema|dollbycinema|dolby)", "DBC", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(TB|thebotique|theboutique|boutique|botique|더부티크|부티크|더부티|부티크|부티)", "TB", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(MX|엠엑스|앰엑스|atmos|dolbyatmos)", "MX", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(CFT|컴포트|COMFORT|CF|CP|CPT)", "CFT", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(MKB|메가박스키즈|키즈|키드|어린이|메가키즈|MEGABOXKIDS|MEGABOXKID|KID|MEGAKID|MEGAKIDS|KIDS)", "MKB", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(TFC|TF|THEFIRSTCLUB|THRFIRSTCLUBS|더퍼스트클럽|더퍼스트|퍼스트클럽|퍼스트클래스|더퍼스트클래스|)", "TFC", shall, flags=re.IGNORECASE)

    return shall

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
    shallname = ""

    try:
        shallname = shall_dic[shall]
        with open(filename, 'rb') as f:
            sdate = pickle.load(f)

    except (EOFError, FileNotFoundError):
        sdate = date
    except KeyError:
        shallname = 'Dolby Cinema'
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

            sendmsg = "*메가박스 " + brch + " " + shallname + "*\n"
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
            time.sleep(60)

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