import requests
import threading
import time
from datetime import datetime
from datetime import timedelta
import telepot
from bs4 import BeautifulSoup
import re
import logging


# CGV
# GET방식으로 통신
# 파라미터
#   arecode : 지역번호 서울 | 경기 | 대전 | 인천 | 대구 | 강원 [01 | 02 | 03, 205 | 202 | 11 | 12]
#   theatercode : 상영관 번호 용산 | 왕십리 | 대학로 | 강남 [0013 | 0074 | 0063 | 0056]
#   date : 날짜 YYYYMMDD
def get_cgv_movie_list(date, therater, shall):
    theater_dic = {'강남':'0056', '강변':'0001', '건대입구':'0229', '구로':'0010', '대학로':'0063',
                   '동대문':'0252', '등촌':'0230', '명동':'0009', '명동역씨네라이브러리':'0105',
                   '목동':'0011', '미아':'0057', '불광':'0030', '상봉':'0046', '성신여대입구':'0300',
                   '송파':'0088', '수유':'0276', '신촌아트레온':'0150', '압구정':'0040', '여의도':'0112',
                   '영등포':'0059', '왕십리':'0074', '용산아이파크몰':'0013', '중계':'0131', '천호':'0199',
                   '청담씨네시티':'0107', '피카다리1958':'0223', '하계':'0164', '홍대':'0191',
                   'CINEDECHEF압구정':'P001', 'CINEDECHEF용산아이파크몰':'P013'}
    shall_dic = {'IMAX':'07', 'CINE de CHEF':'103', 'GOLD CLASS':'99', '씨네앤포레':'0001',
                 '씨네앤리빙룸':'LM', 'SphereX':'SPX', 'STARIUM':'110', 'PREMIUM':'PRM',
                 'Sweet Box':'09', 'SKYBOX':'SKY', 'CINE KIDS':'CK', 'SOUNDX':'SDX',
                 '4DX':'4D14', 'SCREENX':'SCX', '4DX SCREEN':'4DXSC', }

    try:
        URL = "http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?areacode=01&theatercode=" + theater_dic[therater] + "&date=" + date
    except KeyError as e: # therater에 therater_dic에 없는 키값일 경우 키오류 발생
        print("Error Message : {}".format(e))
        URL = "http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?areacode=01&theatercode=0013&date=" + date
    response = requests.get(URL)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    search_special_hall = shall #IMAX, 4DX, CINE de CHEF, SCREENX, Laser

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
                        if movie_rest_seat == "마감":
                            movie_rest_seat = "(0/" + movie_tot_seat + ")"
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


def set_cgv_shall_reg(shall):
    shall = shall.replace(' ', '')

    #IMAX, 4DX, CINE de CHEF, SCREENX, Laser

    shall = re.sub(r"(IMAX|아이맥스|용아맥|아맥)", "IMAX", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(CINEDECHEF|씨네드셰프|시네드셰프)", "CINE de CHEF", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(GOLDCLASS|골드클래스|골드클레스|GOLD)", "GOLD CLASS", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(SCREENX|스크린엑스|스크린X)", "SCREENX", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(4DX|4D|4디|4디엑스|4D엑스|뽀디|포디|뽀디엑스|포디엑스)", "4DX", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(STARIUM|스타리움|퓨리움)", "STARIUM", shall, flags=re.IGNORECASE)
    shall = re.sub(r"(PREMIUM|프리미엄)", "PREMIUM", shall, flags=re.IGNORECASE)
    shall = re.sub(r"", "", shall, flags=re.IGNORECASE)
    shall = re.sub(r"", "", shall, flags=re.IGNORECASE)
    shall = re.sub(r"", "", shall, flags=re.IGNORECASE)
    shall = re.sub(r"", "", shall, flags=re.IGNORECASE)
    shall = re.sub(r"", "", shall, flags=re.IGNORECASE)





def cgv_crawling(date, therater, shall):
    therater = set_cgv_therater_reg(therater)
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

if __name__ == "__main__":
    latest_date = "20200723"  # datetime.today().strftime("%Y%m%d")
    t = ['월', '화', '수', '목', '금', '토', '일']
    mytoken = ""
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

    # CGV : threading.Thread(target=cgv_crawling, args=(검색시작날짜, 지점, 상영관,))
    cgv = threading.Thread(target=cgv_crawling, args=(latest_date, '종로3가', '9관',))
    cgv.start()
    cgv.join()

    logging.info("Server Exit")