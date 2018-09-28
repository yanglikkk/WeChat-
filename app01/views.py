from django.shortcuts import render,HttpResponse
import requests
import time
import re
import json


CTIME = None
QCODE = None
TIP = 1
ticket_dict ={}
ALL_COOKIE_DICT = {}


def login(request):
    global CTIME
    CTIME = time.time()
    response = requests.get(
        url ='https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&fun=new&lang=zh_CN&_=%s' % CTIME
    )
    v = re.findall('uuid = "(.*)";',response.text)
    global QCODE
    QCODE = v[0]
    return render(request,'login.html',{'qcode':QCODE})

def check_login(request):
    global TIP
    ret = {'code': 408,'data': None}
    r1 = requests.get(
        url="https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid=%s&tip=%s&r=95982085&_=%s" %(QCODE,TIP,CTIME,)
    )
    if 'window.code=408' in  r1.text:
        print('无人扫码')
        return HttpResponse(json.dumps(ret))
    elif 'window.code=201' in  r1.text:
        ret['code'] = 201
        avatar = re.findall("window.userAvatar = '(.*)';", r1.text)[0]
        ret['data'] = avatar
        TIP = 0
        return HttpResponse(json.dumps(ret))
    elif 'window.code=200' in  r1.text:
        ALL_COOKIE_DICT.update(r1.cookies.get_dict())
        # 用户点击确认登录，
        """
        window.code=200;
        window.redirect_uri="https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=AYKeKS9YQnNcteZCfLeTlzv7@qrticket_0&uuid=QZA2_kDzdw==&lang=zh_CN&scan=1494553432";
        window.redirect_uri="https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=AYKeKS9YQnNcteZCfLeTlzv7@qrticket_0&uuid=QZA2_kDzdw==&lang=zh_CN&scan=1494553432";
        """

        redirect_uri = re.findall('window.redirect_uri="(.*)";', r1.text)[0]
        redirect_uri = redirect_uri + "&fun=new&version=v2"

        # 获取凭证
        r2 = requests.get(url=redirect_uri)
        ALL_COOKIE_DICT.update(r2.cookies.get_dict())
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r2.text,'html.parser')
        for tag in soup.find('error').children:
            ticket_dict[tag.name] = tag.get_text()
        print(ticket_dict)


        # 获取用户信息
        # https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=88828930&lang=zh_CN&pass_ticket=uBfBw5um5Zor97ihMqdFprf4kqjecz8q0VRdevL%252BMg7Ozij4NvnpZCevYQX5jhO0
        get_user_info_data = {
            'BaseRequest': {
                'DeviceID': "e037211446009402",
                'Sid':ticket_dict['wxsid'],
                'Uin':ticket_dict['wxuin'],
                'Skey':ticket_dict['skey'],
            }
        }
        get_user_info_url = "https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=88828930&lang=zh_CN&pass_ticket=" +ticket_dict['pass_ticket']
        r3 = requests.post(
            url=get_user_info_url,
            json=get_user_info_data
        )
        r3.encoding = 'utf-8'
        user_init_dict = json.loads(r3.text)
        print(user_init_dict)
        ret['code'] = 200
        ALL_COOKIE_DICT.update(r3.cookies.get_dict())

        """
            获取所有联系人,并在页面中显示
            :param request:
            :return:
            """
        # https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?pass_ticket=J6GLa%252FBobIDCebI4llpykyMrbHPm86KGMDqE4jUS20OCwWhkK%252BF6uiJpLM%252BO5PoU&r=1494811126614&seq=0&skey=@crypt_d83b5b90_eb1965b01a3bc3f4d7a4bdc846b77a19
        ctime = str(time.time())
        base_url = "https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?pass_ticket=%s&r=%s&seq=0&skey=%s"
        url = base_url % (ticket_dict['pass_ticket'], ctime, ticket_dict['skey'])
        response = requests.get(url=url, cookies=ALL_COOKIE_DICT)
        ALL_COOKIE_DICT.update(response.cookies.get_dict())
        response.encoding = 'utf-8'
        contact_list_dict = json.loads(response.text)
        # print(contact_list_dict['MemberList'])
        # for item in contact_list_dict['MemberList']:
        #     print(item['NickName'], item['UserName'])
        for item in contact_list_dict['MemberList']:
            # print(item['NickName'])
            # if(item['NickName'] == 'Germany'):
            #     to_user = item['UserName']
            if ('Mamba' in item['NickName']):
                to_user = item['UserName']
        url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?lang=zh_CN&pass_ticket=%s' % (
        ticket_dict['pass_ticket'],)
        p = 0
        while True:
            msg = '你好,我系第' + str(p) + '个发消息比你噶微信小爬虫'
            ctime = str(int(time.time() * 1000))
            post_dict = {
                'BaseRequest': {
                    'DeviceID': "e037211446009402",
                    'Sid': ticket_dict['wxsid'],
                    'Uin': ticket_dict['wxuin'],
                    'Skey': ticket_dict['skey'],
                },
                "Msg": {
                    'ClientMsgId': ctime,
                    'Content': msg,
                    'FromUserName': user_init_dict['User']['UserName'],
                    'LocalID': ctime,
                    'ToUserName': to_user.strip(),
                    'Type': 1
                },
                'Scene': 0
            }
            # print(post_dict)
            # print(url)
            # response = requests.post(url=url,json=post_dict,cookies=ALL_COOKIE_DICT)
            response = requests.post(url=url, data=bytes(json.dumps(post_dict, ensure_ascii=False), encoding='utf-8'))
            p += 1
            # print(response.text)
            if(p > 20):
                break

        return HttpResponse(json.dumps(ret))