import requests
import threading
import time
from datetime import datetime
from datetime import timedelta
import telepot
import logging
import pickle
import re

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
    brch_dic = {'가산디지털':'1013', '가양':'1018', '강동':'9010', '건대입구':'1004', '김포공항':'1009',
                '노원':'1003', '도곡':'1023', '독산':'1017', '브로드웨이':'9056', '서울대입구':'1012',
                '수락산':'1019', '수유':'1022', '신도림':'1015', '신림':'1007', '에비뉴엘':'1001',
                '영등포':'1002', '용산':'1014', '월드타워':'1016', '은평':'1021', '장안':'9053',
                '청량리':'1008', '합정':'1010', '홍대입구':'1005', '황학':'1011'}
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
    # 수퍼플렉스관은 일반으로 분류됨
    shall_dic = {'일반':100, '샤롯데':300, '아르떼클래식':400, '수퍼플렉스 G':941,
                 '수퍼 4D':930, '씨네패밀리':960, '수퍼 S':980}
    brch = set_lottecinema_brch_reg(brch)
    shall = set_lottecinema_shall_reg(shall)
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
    latest_date = "20200801" # 프로그램을 실행시킨 시간부터 탐색
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

    lottecinema = threading.Thread(target=lottecinema_crawling, args=(latest_date, '월드타워', '수퍼플렉스 G',))
    lottecinema.start()
    lottecinema.join()
    logger.info("Server Exit")