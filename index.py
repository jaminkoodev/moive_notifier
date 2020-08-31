import pickle
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
    theater_dic = {'강남': '0056', '강변': '0001', '건대입구': '0229', '구로': '0010', '대학로': '0063',
                   '동대문': '0252', '등촌': '0230', '명동': '0009', '명동역 씨네라이브러리': '0105',
                   '목동': '0011', '미아': '0057', '불광': '0030', '상봉': '0046', '성신여대입구': '0300',
                   '송파': '0088', '수유': '0276', '신촌아트레온': '0150', '압구정': '0040', '여의도': '0112',
                   '영등포': '0059', '왕십리': '0074', '용산아이파크몰': '0013', '중계': '0131', '천호': '0199',
                   '청담씨네시티': '0107', '피카다리1958': '0223', '하계': '0164', '홍대': '0191',
                   'CINE DE CHEF 압구정': 'P001', 'CINE DE CHEF 용산아이파크몰': 'P013'}
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


def set_cgv_therater_reg(therater):
    therater = therater.replace(' ', '')

    if therater[-1] == "점" or therater[-1] == "관" or therater[-1] == "역":
        therater = therater[:-1]

    therater = re.sub(r"(강남|신논현|논현|역삼|논현동|역삼동|신논현동)", "강남", therater)
    therater = re.sub(r"(강변|터미널|동서울터미널|동서울|버스터미널|동서울버스터미널|시외버스터미널|동서울시외버스터미널)", "강변", therater)
    therater = re.sub(r"(건대입구|건대|건국대|건국대입구|건국대학교|건국대학교입구)", "건대입구", therater)
    therater = re.sub(r"(대학로|혜화|성균관|성균관대|성대|헤화동)", "대학로", therater)
    therater = re.sub(r"(등촌|가양|증미|등촌동|가양동|증미동)", "등촌", therater)
    therater = re.sub(r"(명동역씨네라이브러리|명동씨네라이브러리|씨네라이브러리|씨네라이브)", "명동역씨네라이브러리", therater)
    therater = re.sub(r"(목동|오목교|양평)", "목동", therater)
    therater = re.sub(r"(미아|미아사거리|미아동)", "미아", therater)
    therater = re.sub(r"(상봉|망우|상봉터미널|망우터미널|상봉시외버스터미널|상봉버스터미널|망우동|상봉동)", "상봉", therater)
    therater = re.sub(r"(성신여대입구|성신여대|성신여자대학교|성신여자대학교입구|성신여자대|성신여자대입구)", "성신여대입구", therater)
    therater = re.sub(r"(송파|장지|문정|북정|송파파크하비오|장지동|문정동|북정동)", "송파", therater)
    therater = re.sub(r"(수유|쌍문|수유동|쌍문동)", "수유", therater)
    therater = re.sub(r"(신촌아트레온|신촌|연대|연세대|연세대학교|신촌동)", "신촌아트레온", therater)
    therater = re.sub(r"(여의도|여의나루)", "여의도", therater)
    therater = re.sub(r"(영등포|타임스퀘어|영등포타임스퀘어)", "영등포", therater)
    therater = re.sub(r"(용산아이파크몰|용산|신용산|아이파크몰|아이파크몰용산)", "용산아이파크몰", therater)
    therater = re.sub(r"(청담씨네시티|씨네시티|청담|씨네시티청담|청담씨네씨티|씨네씨티|씨네씨티청담)", "청담씨네시티", therater)
    therater = re.sub(r"(피카디리1958|피카디리|종로피카디리|종로피카디리1958|종로3가|종로|종로3가피카디리|종로3가피카디리1958|피카다리"
                      r"|피카다리1958|종로피카다리|종로3가피카다리|종로피카다리1958|종로3가피카다리1958)", "피카다리1958", therater)
    therater = re.sub(r"(홍대|홍대입구|홍익대학교)", "홍대", therater)
    therater = re.sub(r"(CINEDECHEF압구정|씨네드셰프압구정)", "CINEDECHEF압구정", therater, flags=re.IGNORECASE)
    therater = re.sub(r"(CINEDECHEF용산아이파크몰|CINEDECHEF용산|CINEDECHEF아이파크몰용산|CINEDECHEF신용산|CINEDECHEF아이파크몰"
                      r"|씨네드셰프용산아이파크몰|씨네드셰프용산|씨네드셰프아이파크몰용산|씨네드셰프신용산|씨네드셰프아이파크몰)",
                      "CINEDECHEF용산아이파크몰", therater, flags=re.IGNORECASE)

    return therater


def cgv_crawling(date, therater, shall):
    therater = set_cgv_therater_reg(therater)
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
            try:
                bot.sendMessage(mc, sendmsg, parse_mode="Markdown", disable_web_page_preview=True)
            except Exception as e:
                logger.debug("CGV {} {} ({})Message Exception : {}".format(therater, shall, sdate, e))
                raise ValueError
                
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
    brch_dic = {'강낭': '1372', '강남대로': '1359', '강동': '1341', '군자': '1431', '동대문': '1003',
                '마곡': '1572', '목동': '1581', '상봉': '1311', '상암월드컵경기장': '1211', '성수': '1331',
                '센트럴': '1371', '송파파크하비오': '1381', '신촌': '1202', '은평': '1221', '이수': '1561',
                '창동': '1321', '코엑스': '1351', '홍대': '1212', '화곡': '1571', 'ARTNINE': '1562'}
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
    except KeyError as e:
        logger.debug('shall_dic에서 {}을 찾을 수 없습니다. : {}'.format(shall, e))
        shallname = "Dolby Cinema"
    try:
        with open(filename, 'rb') as f:
            sdate = pickle.load(f)
    except (EOFError, FileNotFoundError) as e:
        logger.debug('{}을 찾을 수 없어 {}(기본날짜)부터 검색을 시작합니다. : {}'.format(filename, date, e))
        sdate = date

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
            try:
                bot.sendMessage(mc, sendmsg, parse_mode="Markdown", disable_web_page_preview=True)
            except Exception as e:
                logger.debug("Megabox {} {} ({})Message Exception : {}".format(brch, shall, sdate, e))
                raise ValueError
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
    brch_dic = {'가산디지털': '1013', '가양': '1018', '강동': '9010', '건대입구': '1004', '김포공항': '1009',
                '노원': '1003', '도곡': '1023', '독산': '1017', '브로드웨이(신사)': '9056', '서울대입구': '1012',
                '수락산': '1019', '수유': '1022', '신도림': '1015', '신림': '1007', '에비뉴엘(명동)': '1001',
                '영등포': '1002', '용산': '1014', '월드타워': '1016', '은평(롯데몰)': '1021', '장안': '9053',
                '청량리': '1008', '합정': '1010', '홍대입구': '1005', '황학': '1011'}
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
    try:
        for mvlst in response['PlaySeqs']['Items']:
            if mvlst['ScreenDivisionCode'] == shallcode:
                line.append(mvlst)
    except Exception as e:
        logger.debug("롯데시네마 Not Found Exception : {}".format(e))
        line = []
    return line


def set_lottecinema_brch_reg(brch):
    brch = brch.replace(' ', '')

    if brch[-1] == "점" or brch[-1] == "관" or brch[-1] == "역" or brch[-1] == "동":
        brch = brch[:-1]

    brch = re.sub(r"(가산디지털|가산|가디단|가디|가산디지털단지|디지털단지)", "가산디지털", brch)
    brch = re.sub(r"(강동|천호|강동구청)", "강동", brch)
    brch = re.sub(r"(건대입구|건대|건국대|건국대입구|건국대학교|건국대학교입구)", "건대입구", brch)
    brch = re.sub(r"(브로드웨이|신사|신사브로드웨이|브로드웨이신사)", "브로드웨이", brch)
    brch = re.sub(r"(서울대입구|서울대|관악구청|관악구|관악|서울대학교)", "서울대입구", brch)
    brch = re.sub(r"(수유|강북구청|강북구)", "수유", brch)
    brch = re.sub(r"(에비뉴엘|명동|명동에비뉴엘|에비뉴엘명동)", "에비뉴엘", brch)
    brch = re.sub(r"(용산|용산아이파크몰|신용산|아이파크몰|아이파크몰용산)", "용산", brch)
    brch = re.sub(r"(월드타워|잠실|롯데타워|롯데월드타워|롯데월드|잠실월드타워|월드타워잠실|잠실롯데타워|롯데타워잠실|잠실롯데월드타워"
                  r"|롯데월드타워잠실|잠실롯데월드|롯데월드잠실)", "월드타워", brch)
    brch = re.sub(r"(은평|구파발|은평롯데몰|롯데몰은평|구파발롯데몰|롯데몰구파발)", "은평", brch)
    brch = re.sub(r"(홍대입구|홍대|홍익대학교)", "홍대입구", brch)

    return brch


def set_lottecinema_shall_reg(shall):
    shall = shall.replace(' ', '')

    shall = re.sub(r"(샤롯데|CHARLOTTE)", "샤롯데", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(아르떼클래식|클래식아르떼|ARTECLASSIC|CLASSICARTE|ARTE)", "아르떼클래식", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(수퍼플렉스G|슈퍼플렉스G|수퍼플랙스G|슈퍼플랙스G|SUPERPLEXG|SUPERFLEXG)", "수퍼플렉스G", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(수퍼4D|슈퍼4D|SUPER4D|4D|4DX)", "수퍼4D", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(씨네패밀리|CINEFAMILY|시네패밀리|씨내패밀리|씨네페밀리|씨내페밀리)", "씨네패밀리", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(수퍼S|슈퍼S|SUPERS)", "수퍼S", shall, flags=re.IGNORECASE)

    return shall


# 현재 날짜에 상영중인 영화 제목의 고유번호를 반환함
def get_lottecinema_movie_no_list(response):
    movielst = []
    for item in response:
        if item['MovieCode'] not in movielst:
            movielst.append(item['MovieCode'])

    return movielst

def lottecinema_crawling(date, brch, shall):
    shall_dic = {'일반':100, '샤롯데':300, '아르떼 클래식':400, '수퍼플렉스G':941,
                 '수퍼4D':930, '씨네패밀리':960, '수퍼S':980}
    brch = set_lottecinema_brch_reg(brch)
    shall = set_lottecinema_shall_reg(shall)
    filename = 'lottecinema' + brch + shall + '.pickle'
    shallcode = 0
    sdate = ""
    
    try:
        shallcode = shall_dic[shall]
    except KeyError as e:
        logger.debug('shall_dic에서 {}을 찾을 수 없습니다. : {}'.format(shall, e))
        shallcode = 100
    try:
        with open(filename, 'rb') as f:
            sdate = pickle.load(f)
    except (EOFError, FileNotFoundError) as e:
        logger.debug('{}을 찾을 수 없어 {}(기본날짜)부터 검색을 시작합니다. : {}'.format(filename, date, e))
        sdate = date
    

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
            try:
                bot.sendMessage(mc, sendmsg, parse_mode="Markdown", disable_web_page_preview=True)
            except Exception as e:
                logger.debug("롯데시네마 {} {} ({}) Message Exception : {}".format(brch, shall, sdate, e))
                raise ValueError
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
    latest_date = "20200904" #datetime.today().strftime("%Y%m%d")  # 프로그램을 실행시킨 시간부터 탐색
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
    lottecinema = threading.Thread(target=lottecinema_crawling, args=(latest_date, '월드타워', '수퍼플렉스G',))

    cgv.start()
    megabox.start()
    lottecinema.start()

    cgv.join()
    megabox.join()
    lottecinema.join()

    logger.info("Server Exit")
