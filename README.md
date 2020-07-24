# Moive_Notifier
CGV나 메가박스 예매 사이트가 열릴 경우 텔레그램 채널로 알림 메시지를 보냄.

## index.py
변수 mc에 텔레그램 채널 또는 사용자 아이디를 저장하고
변수 token에 텔레그램 봇의 토큰 값을 저장한 후

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
- 상영관 : 검색할 상영관을 영문으로 저장 ex)돌비시네마 | 더 부티크 | MX관 | 컴포트 | 메가박스 키즈 | 더 퍼스트 클럽 (DBC | TB | MX | CFT | MKB | TFC)
