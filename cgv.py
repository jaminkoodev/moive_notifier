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
    theater_dic = {'용산':'0013', '왕십리':'0074', '대학로':'0063'}
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

if __name__ == "__main__":
    latest_date = "20200723"  # datetime.today().strftime("%Y%m%d")
    t = ['월', '화', '수', '목', '금', '토', '일']
    mytoken = ""
    mc = ""  # My Channel
    bot = telepot.Bot(mytoken)

    logging.basicConfig(filename='./test.log',
                        level=logging.INFO,
                        format='[%(asctime)s][%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('서버가 정상적으로 시작되었습니다.')
    logging.info('검색 시작 날짜 : {}'.format(latest_date))

    # CGV : threading.Thread(target=cgv_crawling, args=(검색시작날짜, 지점, 상영관,))
    cgv = threading.Thread(target=cgv_crawling, args=(latest_date, '용산', '4DX',))
    cgv.start()
    cgv.join()

    logging.info("Server Exit")