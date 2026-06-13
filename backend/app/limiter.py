from slowapi import Limiter
from slowapi.util import get_remote_address

# 요청자 IP를 기준으로 호출 횟수를 센다 (로그인 brute-force 방어)
limiter = Limiter(key_func=get_remote_address)
