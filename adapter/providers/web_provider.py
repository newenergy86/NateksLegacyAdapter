from requests import Session

class WebProvider:
    def __init__(self):
        self.session=Session()

    def login(self,host,user,password):
        url=f"http://{host}/goform/SetSigninInfo"
        data={
            "userName":user,
            "password":password,
            "language":"3",
            "result":"1"
        }
        r=self.session.post(url,data=data,timeout=10)
        return r.status_code==200

    def get(self,host,page):
        return self.session.get(f"http://{host}/{page}",timeout=10).text
