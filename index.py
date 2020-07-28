import pickle
import sys
import requests
import re
import threading
import time
import telepot
import logging
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup


# CGV
# GET방식으로 통신
# 파라미터
#   arecode : 지역번호 서울 | 경기 | 대전 | 인천 | 대구 | 강원 [01 | 02 | 03, 205 | 202 | 11 | 12]
#   theatercode : 상영관 번호 용산 | 왕십리 | 대학로 | 강남 [0013 | 0074 | 0063 | 0056]
#   date : 날짜 YYYYMMDD
def get_cgv_movie_list(date, therater, shall):
    theater_dic = {'용산': '0013', '왕십리': '0074', '대학로': '0063'}
    URL = "http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?areacode=01&theatercode="
    try:
        URL += theater_dic[therater] + "&date=" + date
    except KeyError as e:  # therater에 therater_dic에 없는 키값일 경우 키오류 발생
        print("Error Message : {}".format(e))
        URL += "0013&date=" + date
    response = requests.get(URL)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    search_special_hall = shall  # IMAX, 4DX, CINE de CHEF, SCREENX, Laser

    movie_split_list = []
    line = []
    movie_select_list = soup.select('body > div > div.sect-showtimes > ul > li')
    for msl in movie_select_list:
        title = msl.select_one('div > div.info-movie > a > strong').get_text().strip()

        table_select_list = msl.select('div > div.type-hall')
        for tsl in table_select_list:
            special_hall = tsl.select_one('div > ul > li:nth-child(2)').get_text().strip()
            movie_tot_seat = tsl.select_one('div.info-hall > ul > li:nth-child(3)').get_text().strip()
            m = re.search(r"(총)?(\s)*(?P<totcnt>\d*)(석)?", movie_tot_seat)
            if m:
                movie_tot_seat = m['totcnt']
            if search_special_hall in special_hall:
                line.clear()
                line.append(title)
                timetable = tsl.select('div.info-timetable > ul > li')
                for tbl in timetable:
                    movie_link = tbl.find('a', href=True)
                    if movie_link:
                        movie_link = 'http://www.cgv.co.kr' + str(movie_link['href'])
                    else:
                        movie_link = "-1"
                    movie_start_time = tbl.select_one('em').get_text().strip()
                    movie_rest_seat = tbl.select_one('span').get_text().strip()
                    line.append(movie_start_time)
                    m = re.search(r"(잔여좌석)?(?P<seatcnt>((\d)*(마감)?))(석)?", movie_rest_seat)
                    if m:
                        movie_rest_seat = m['seatcnt']
                        if movie_rest_seat == "매진" or movie_rest_seat == "":
                            movie_rest_seat = "매진"
                            line.append(movie_rest_seat)
                        elif movie_rest_seat == "마감":
                            line.append(movie_rest_seat)
                        elif movie_rest_seat == "예매준비중" or movie_rest_seat == "준비중":
                            movie_rest_seat = "에매준비중"
                            line.append(movie_rest_seat)
                        else:
                            movie_rest_seat = "(" + movie_rest_seat + "/" + movie_tot_seat + ")"
                            line.append(movie_rest_seat)
                    line.append(movie_link)
                movie_split_list.append(line)
            else:
                continue
    return movie_split_list


def cgv_crawling(date, therater, shall):
    filename = 'cgv' + therater + shall + '.pickle'

    try:
        with open(filename, 'rb') as f:
            sdate = pickle.load(f)

    except (EOFError, FileNotFoundError):
        sdate = date

    logger.info('CGV 검색 시작 날짜 : {}'.format(sdate))
    while True:
        movie_list = get_cgv_movie_list(sdate, therater, shall)
        try:
            if not movie_list:
                logger.info("CGV {} {} Not Found ({})".format(therater, shall, sdate))
                raise ValueError
            logger.info("CGV {} {} Found ({})".format(therater, shall, sdate))
            sendmsg = "*CGV " + therater + " " + shall + "*\n"
            week = t[datetime.strptime(sdate, "%Y%m%d").weekday()]
            sendmsg += sdate + " (" + week + ") 예매 오픈\n"
            for i in range(len(movie_list)):
                sendmsg = sendmsg + "*" + movie_list[i][0] + "*\n"
                for j in range(1, len(movie_list[i]), 3):
                    if movie_list[i][j + 2] == "-1":
                        if movie_list[i][j + 1] == "예매준비중":
                            logger.info("CGV {} {} 예매준비중 ({})".format(therater, shall, sdate))
                            raise ValueError
                        sendmsg = sendmsg + movie_list[i][j] + " "
                        sendmsg = sendmsg + movie_list[i][j + 1] + "\n"
                    else:
                        sendmsg = sendmsg + "[" + movie_list[i][j] + "](" + movie_list[i][j + 2] + ") "
                        sendmsg = sendmsg + movie_list[i][j + 1] + "\n"
                sendmsg += "\n"

            bot.sendMessage(mc, sendmsg, parse_mode="Markdown", disable_web_page_preview=True)
            # 결과를 찾았으니 다음날로 넘어간다
            sdate = datetime.strptime(sdate, "%Y%m%d")
            sdate += timedelta(days=1)
            sdate = sdate.strftime("%Y%m%d")
            with open(filename, 'wb') as f:
                pickle.dump(sdate, f)
        except ValueError:
            time.sleep(30)


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
    brch_dic = {'코엑스': '1351', '목동': '1581', '상암': '1211'}
    crtde = datetime.today().strftime("%Y%m%d")

    URL = "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"
    parameters = {"masterType": "brch",  # 상영관
                  "detailType": "spcl",  # 분류 기준 : 영화별 | 지역별 | 특별관 (movie | area | spcl)
                  "theabKindCd": shall,
                  # 돌비시네마 | 더 부티크 | MX관 | 컴포트 | 메가박스 키즈 | 더 퍼스트 클럽 (DBC | TB | MX | CFT | MKB | TFC)
                  "brchNo": brch_dic[brch],  # 상영관번호 : 코엑스 | 목동 | 상암 | (1351 | 1581 | 1211) 주요 상영관만 표기하였음
                  "firstAt": "N",  # **** Y일경우 오늘 날짜만 검색가능하니 반드시 N으로 설정!! ****
                  "brchNo1": brch_dic[brch],  # 상영관번호 : 코엑스 | 목동 | 상암 | (1351 | 1581 | 1211) 주요 상영관만 표기하였음
                  "spclbYn1": "Y",  # Y | N
                  "theabKindCd1": shall,
                  # 특별관 분류 : 돌비시네마 | 더 부티크 | MX관 | 컴포트 | 메가박스 키즈 | 더 퍼스트 클럽 (DBC | TB | MX | CFT | MKB | TFC)
                  "crtDe": crtde,  # 접속한 날짜
                  "playDe": date}  # 찾고있는 날짜
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
    shallname = ""
    sdate = ""

    try:
        shallname = shall_dic[shall]
        with open(filename, 'rb') as f:
            sdate = pickle.load(f)

    except (EOFError, FileNotFoundError) as e:
        logger.debug('{}을 찾을 수 없어 {}(기본날짜)부터 검색을 시작합니다. : {}'.format(filename, date, e))
        sdate = date
    except KeyError as e:
        logger.debug('shall_dic에서 {}을 찾을 수 없습니다. : {}'.format(shall, e))
        shall = 'Dolby Cinema'

    logger.info('메가박스 검색 시작 날짜 : {}'.format(sdate))
    while True:
        movie_list = get_megabox_movie_list(sdate, brch, shall)
        movie_no_list = get_megabox_movie_no_list(movie_list)
        movie_split_list = []
        try:
            if not movie_list:
                logger.info("Megabox {} {} Not Found ({})".format(brch, shall, sdate))
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


# 롯데시네마
# post방식으로 통신
# JSON
#   playDate : 확인할 상영날짜
#   cinemaID : 국가 | 지역 | 상영관 ( 1 | area | spcl)
#   - 국가 : 1(한국)
#   - 지역 : 0001(서울), 0002(경기/인천), 0003(충청/대전), 0004(전라/광주), 0005(경북/대구),
#           0101(경남/부산/울산), 0006(강원), 0007(제주)
#   - 상영관 : 1016(월드타워), 1003(노원), 1004(건대입구), 1008(청량리), 1009(김포공항)
def get_lottecinema_movie_list(date, brch, shallcode):
    brch_dic = {'노원':'1003', '건대입구':'1004', '청량리':'1008', '김포공항':'1009', '월드타워':'1016'}
    sdate = date[:4] + "-" + date[4:6] + "-" + date[6:8]


    URL = "https://www.lottecinema.co.kr/LCWS/Ticketing/TicketingData.aspx"
    dic = {"MethodName":"GetPlaySequence",
           "channelType":"HO",
           "osType":"",
           "osVersion":"",
           "playDate":sdate,
           "cinemaID":"1|0001|"+brch_dic[brch],
           "representationMovieCode":""}
    parameters = {"paramList":str(dic)}
    response = requests.post(URL, data=parameters).json()

    line = []
    for mvlst in response['PlaySeqs']['Items']:
        if mvlst['ScreenDivisionCode'] == shallcode:
            line.append(mvlst)
    return line


# 현재 날짜에 상영중인 영화 제목의 고유번호를 반환함
def get_lottecinema_movie_no_list(response):
    movielst = []
    for item in response:
        if item['MovieCode'] not in movielst:
            movielst.append(item['MovieCode'])

    return movielst

def lottecinema_crawling(date, brch, shall):
    shall_dic = {'일반':100, '샤롯데':300, '아르떼 클래식':400, '수퍼플렉스 G':941,
                 '수퍼 4D':930, '씨네패밀리':960, '수퍼 S':980}
    filename = 'lottecinema' + brch + shall + '.pickle'
    shallcode = 0

    try:
        shallcode = shall_dic[shall]
        with open(filename, 'rb') as f:
            sdate = pickle.load(f)

    except (EOFError, FileNotFoundError):
        sdate = date
    except KeyError:
        shallcode = 100

    logger.info('롯데시네마 검색 시작 날짜 : {}'.format(sdate))
    while True:
        movie_list = get_lottecinema_movie_list(sdate, brch, shallcode)
        movie_no_list = get_lottecinema_movie_no_list(movie_list)
        movie_split_list = []
        try:
            if not movie_list:
                logger.info("롯데시네마 {} {} Not Found ({})".format(brch, shall, sdate))
                raise ValueError

            logger.info("롯데시네마 {} {} Found ({})".format(brch, shall, sdate))
            for i in range(len(movie_no_list)):
                line = []
                for mvlst in movie_list:
                    if movie_no_list[i] == mvlst['MovieCode']:
                        if mvlst['MovieNameKR'] not in line:
                            line.append(mvlst['MovieNameKR'])
                        line.append(mvlst['StartTime'])
                        line.append("(" + str(mvlst['BookingSeatCount']) + "/" + str(mvlst['TotalSeatCount']) + ")")
                movie_split_list.append(line)

            sendmsg = "*롯데시네마 " + brch + " " + shall + "*\n"
            week = t[datetime.strptime(sdate, "%Y%m%d").weekday()]
            sendmsg += sdate + " (" + week + ") 예매 오픈\n"
            for i in range(len(movie_split_list)):
                sendmsg = sendmsg + "*" + movie_split_list[i][0] + "*\n"
                for j in range(1, len(movie_split_list[i]), 2):
                    sendmsg = sendmsg + "[" + movie_split_list[i][j] + "](https://www.lottecinema.co.kr/NLCHS/Ticketing/Schedule) "
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
    t = ['월', '화', '수', '목', '금', '토', '일']
    latest_date = "20200730" #datetime.today().strftime("%Y%m%d")  # 프로그램을 실행시킨 시간부터 탐색
    # 텔레그램 봇 연결 파트
    mytoken = ""
    mc = ""
    bot = telepot.Bot(mytoken)

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s|%(lineno)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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
    # CGV : threading.Thread(target=cgv_crawling, args=(검색디폴트날짜, 지점, 상영관,))
    # MEGABOX : threading.Thread(target=megabox_crawling, args=(검색디폴트날짜, 지점, 상영관,))
    cgv = threading.Thread(target=cgv_crawling, args=(latest_date, '용산', 'IMAX',))
    megabox = threading.Thread(target=megabox_crawling, args=(latest_date, '코엑스', 'DBC',))
    lottecindema = threading.Thread(target=megabox_crawling, args=(latest_date, '월드타워', '수퍼플렉스 G',))

    cgv.start()
    megabox.start()
    cgv.join()
    megabox.join()

    logger.info("Server Exit")
