import requests
import json

from urllib.parse import urlparse, parse_qs

login = json.load("login.json")
username = login.get("username")
password = login.get("password")

session = requests.Session()

response = session.get("https://accounts.marketwatch.com/login?target=https%3A%2F%2Fwww.marketwatch.com%2F")
parsed_url = urlparse(response.url)
data = parse_qs(parsed_url.query)

cookies = response.cookies.get_dict()

headers = {
    "authority": "sso.accounts.dowjones.com",
    "method": "POST",
    "path": "/usernamepassword/login",
    "scheme": "https",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "auth0-client": "eyJuYW1lIjoiYXV0aDAuanMtdWxwIiwidmVyc2lvbiI6IjkuMTEuMyJ9",
    "cache-control": "no-cache",
    "content-length": "782",
    "content-type": "application/json",
    "cookie": f"_csrf={cookies['_csrf']}; did=s%3Av0%3A93301040-2d35-11ec-8e25-fd39f12f6bef.PS2YCw5rrhTX63hqj66VcP3rLZVAvpy0%2BPs7DxPnWYA; did_compat=s%3Av0%3A93301040-2d35-11ec-8e25-fd39f12f6bef.PS2YCw5rrhTX63hqj66VcP3rLZVAvpy0%2BPs7DxPnWYA; djcs_route=e2cb04d1-f1e0-49ff-9ee9-fb84fc717244; optimizelyEndUserId=oeu1634246870011r0.5430598172338112; s_ecid=MCMID%7C83018043478144002752941604360205704110; ki_r=aHR0cHM6Ly93d3cubWFya2V0d2F0Y2guY29tLw%3D%3D; auth0=s%3ARCLrR4Yf-UUlHfgsO-k2sSAkSmraARa3.IVapYK%2FzG8QuRYyOM0ODtIHZIbF7%2B0opSR6ht%2FkWt3Q; auth0_compat=s%3ARCLrR4Yf-UUlHfgsO-k2sSAkSmraARa3.IVapYK%2FzG8QuRYyOM0ODtIHZIbF7%2B0opSR6ht%2FkWt3Q; AMCVS_CB68E4BA55144CAA0A4C98A5%40AdobeOrg=1; AMCV_CB68E4BA55144CAA0A4C98A5%40AdobeOrg=1585540135%7CMCIDTS%7C18919%7CMCMID%7C83018043478144002752941604360205704110%7CMCAAMLH-1635182823%7C9%7CMCAAMB-1635182823%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1634585223s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.4.0; s_cc=true; ki_t=1634246870913%3B1634578023761%3B1634578378030%3B4%3B22; s_ppvl=MW_Login_Login_Form%2C100%2C100%2C872%2C918%2C872%2C918%2C872%2C2%2CL; sc.ASP.NET_SESSIONID=; sc.Status=2; utag_main=v_id:017c80b44533003dc54d7c4b03f605072024f06a00bd0$_sn:5$_se:3$_ss:0$_st:1634580181758$vapi_domain:dowjones.com$ses_id:1634578023254%3Bexp-session$_pn:2%3Bexp-session$_prevpage:MW_Login_Login_Unknown%3Bexp-1634581981766; gpv_pn=MW_Login_Login_Unknown; s_ppv=MW_Login_Login_Unknown%2C100%2C100%2C872%2C918%2C872%2C918%2C872%2C2%2CL; s_sq=djglobal%3D%2526pid%253DMW_Login_Login_Unknown%2526pidt%253D1%2526oid%253DSIGN%252520IN%2526oidt%253D3%2526ot%253DSUBMIT",
    "origin": "https://sso.accounts.dowjones.com",
    "pragma": "no-cache",
    "sec-ch-ua": '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Mobile Safari/537.36",
    "x-remote-user": username
}

for elem in data:
    data[elem] = data[elem][0]

data["headers"] = {"X-REMOTE-USER": username}
data["username"] = username
data["password"] = password
data["client_id"] = data.pop("client")
data["_csrf"] = cookies["_csrf"]

print(f"Headers: {headers}")
print(f"Data: {data}")

response = session.post("https://sso.accounts.dowjones.com/usernamepassword/login", headers=json.dumps(headers), data=json.dumps(data))
print(response.text)
