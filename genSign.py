import requests
import time
import hmac
import hashlib

appkey = "0627978becc7871dd37e2ced2a593677"
secret = "d0d8b2b51fb9595339a049a1661828df"

def request(method, api_host, path, queryParams):
    def gen_sign(queryParams, timestamp):
        signStr = f"{appkey}{timestamp}"
        sorted_params = sorted(queryParams.items())

        for key, values in sorted_params:
            if values is None:
                continue
            value_str = ",".join(sorted(values, key=lambda x: x.lower())) if isinstance(values, list) else values
            if value_str.strip() == "":
                continue
            signStr += f"&{key}={value_str}"

        sign = hmac.new(secret.encode("utf-8"), signStr.encode("utf-8"), digestmod=hashlib.md5).hexdigest().upper()
        return sign

    timestamp = int(time.time() * 1000)
    sign = gen_sign(queryParams, timestamp)
    url = f"{api_host}{path}"
    headers = {
"x-data365-appkey": appkey,
"x-data365-timestamp": str(timestamp),
"x-data365-sign": sign
    }
    return requests.request(method, url, headers=headers, params=queryParams)

method = "GET"
api_host = "http://37.12.199.20:29993"
path = "/api/base/crosscroad_info"
queryParams = {
}
res = request(method, api_host, path, queryParams)
print(res.json())
