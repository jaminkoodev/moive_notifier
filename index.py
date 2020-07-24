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
    while True:
        movie_list = get_cgv_movie_list(date, therater, shall)
        try:
            if not movie_list:
                logging.info("CGV {} {} Not Found ({})".format(therater, shall, date))
                raise ValueError
            logging.info("CGV {} {} Found ({})".format(therater, shall, date))
            sendmsg = "*CGV " + therater + " " + shall + "*\n"
            week = t[datetime.strptime(date, "%Y%m%d").weekday()]
            sendmsg += date + " (" + week + ") 예매 오픈\n"
            for i in range(len(movie_list)):
                sendmsg = sendmsg + "*" + movie_list[i][0] + "*\n"
                for j in range(1, len(movie_list[i]), 3):
                    if movie_list[i][j + 2] == "-1":
                        if movie_list[i][j + 1] == "예매준비중":
                            logging.info("CGV {} {} 예매준비중 ({})".format(therater, shall, date))
                            raise ValueError
                        sendmsg = sendmsg + movie_list[i][j] + " "
                        sendmsg = sendmsg + movie_list[i][j + 1] + "\n"
                    else:
                        sendmsg = sendmsg + "[" + movie_list[i][j] + "](" + movie_list[i][j + 2] + ") "
                        sendmsg = sendmsg + movie_list[i][j + 1] + "\n"
                sendmsg += "\n"

            bot.sendMessage(mc, sendmsg, parse_mode="Markdown", disable_web_page_preview=True)
            # 결과를 찾았으니 다음날로 넘어간다
            date = datetime.strptime(date, "%Y%m%d")
            date += timedelta(days=1)
            date = date.strftime("%Y%m%d")
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
    while True:
        movie_list = get_megabox_movie_list(date, brch, shall)
        movie_no_list = get_megabox_movie_no_list(movie_list)
        movie_split_list = []
        try:
            if not movie_list:
                logging.info("Megabox {} {} Not Found ({})".format(brch, shall, date))
                raise ValueError

            logging.info("메가박스 {} {} Found ({})".format(brch, shall, date))
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
            week = t[datetime.strptime(date, "%Y%m%d").weekday()]
            sendmsg += date + " (" + week + ") 예매 오픈\n"
            for i in range(len(movie_split_list)):
                sendmsg = sendmsg + "*" + movie_split_list[i][0] + "*\n"
                for j in range(1, len(movie_split_list[i]), 2):
                    sendmsg = sendmsg + "[" + movie_split_list[i][j] + "](https://www.megabox.co.kr/booking) "
                    sendmsg = sendmsg + movie_split_list[i][j + 1] + "\n"
                sendmsg += "\n"
            bot.sendMessage(mc, sendmsg, parse_mode="Markdown", disable_web_page_preview=True)
            # 결과를 찾았으니 다음날로 넘어간다
            date = datetime.strptime(date, "%Y%m%d")
            date += timedelta(days=1)
            date = date.strftime("%Y%m%d")

        except ValueError:  # 리스트가 비어있을경우(예매오픈하기 전) 30초마다 재탐색
            time.sleep(30)


if __name__ == "__main__":
    t = ['월', '화', '수', '목', '금', '토', '일']
    latest_date = datetime.today().strftime("%Y%m%d")  # 프로그램을 실행시킨 시간부터 탐색
    # 텔레그램 봇 연결 파트
    mytoken = ""
    mc = ""
    bot = telepot.Bot(mytoken)
    logging.basicConfig(filename='./test.log',
                        level=logging.INFO,
                        format='[%(asctime)s][%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('서버가 정상적으로 시작되었습니다.')
    logging.info('검색 시작 날짜 : {}'.format(latest_date))

    # 영화 리스트 불러오기
    # CGV : threading.Thread(target=cgv_crawling, args=(검색시작날짜, 지점, 상영관,))
    # MEGABOX : threading.Thread(target=megabox_crawling, args=(검색시작날짜, 지점, 상영관,))
    cgv = threading.Thread(target=cgv_crawling, args=(latest_date, '용산', 'IMAX',))
    megabox = threading.Thread(target=megabox_crawling, args=(latest_date, '코엑스', 'DBC',))

    cgv.start()
    megabox.start()
    cgv.join()
    megabox.join()

    logging.info("Server Exit")