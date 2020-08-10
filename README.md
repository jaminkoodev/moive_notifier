# Moive_Notifier
CGV나 메가박스 예매 사이트가 열릴 경우 텔레그램 채널로 알림 메시지를 보냄.

## index.py
변수 mc에 텔레그램 채널 또는 사용자 아이디를 저장하고
변수 token에 텔레그램 봇의 토큰 값을 저장한 후 아래 세부사항을 설정

### CGV
```
cgv = threading.Thread(target=cgv_crawling, args=(검색할 날짜, 지점, 상영관,))
```
- 검색할 날짜 : YYYYMMDD 형식으로 과거의 날짜가 아닌 미래의 날짜로 저장
- 지점 : 지역명만 저장 ex) 용산, 영등포, 대학로, 강남, ...
- 상영관 : 검색할 상영관 ex) IMAX, SKYBOX, 4DX, SCREEN X, ...

### MEGABOX
```
megabox = threading.Thread(target=megabox_crawling, args=(검색할 날짜, 지점, 상영관,))
```
- 검색할 날짜 : YYYYMMDD 형식으로 과거의 날짜가 아닌 미래의 날짜로 저장
- 지점 : 지역명만 저장 ex) 코엑스, 목동, 동대문, ...
- 상영관 : 검색할 상영관 ex)돌비시네마, 더 부티크, MX관, 컴포트, 메가박스 키즈, 더 퍼스트 클럽

### LOTTECINEMA
```
lottecinema = threading.Thread(target=lottecinema_crawling, args=(검색할 날짜, 지점, 상영관,))
```
- 검색할 날짜 : YYYYMMDD 형식으로 과거의 날짜가 아닌 미래의 날짜로 저장
- 지점 : 지역명만 저장 ex) 월드타워, 청량리, 노원, ...
- 상영관 : 검색할 상영관 ex) SUPER PLEX G, , SUPER 4D, SUPER S, ...


## cgv.py
변수 mc에 텔레그램 채널 또는 사용자 아이디를 저장하고
변수 token에 텔레그램 봇의 토큰 값을 저장한 후 위에 CGV 세부사항을 따라 설정

## megabox.py
변수 mc에 텔레그램 채널 또는 사용자 아이디를 저장하고
변수 token에 텔레그램 봇의 토큰 값을 저장한 후 위에 megabox 세부사항을 따라 설정

## lottecinema.py
변수 mc에 텔레그램 채널 또는 사용자 아이디를 저장하고
변수 token에 텔레그램 봇의 토큰 값을 저장한 후 위에 lottecinema 세부사항을 따라 설정
