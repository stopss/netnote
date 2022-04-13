from flask import Flask, render_template, request, redirect, url_for, jsonify
app = Flask(__name__)

# jwt 연결
import jwt                                                                            #파이썬 인터프리터에서 jwt 추가해주세요!
# 시간 날짜 형태 사용
from datetime import datetime, timedelta
# 비밀번호 암호화
import hashlib

import requests
from bs4 import BeautifulSoup
# 비밀키 설정
SECRET_KEY = 'NetNote'
from bson.objectid import ObjectId                                                    #db에서 object id값 가져올 때 사용.
import certifi                                                                        #파이썬 인터프리터에서 certifi 추가해주세요.
from pymongo import MongoClient

client = MongoClient('',tlsCAFile=certifi.where())
db = client.dbnetnote


@app.route('/')
def home():
    return render_template('home.html')

#로그인 시간이 만료되면 홈으로 이동.
@app.route('/')
def login_over():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('home.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))


@app.route('/login')
def login_template():
    return render_template('login.html')


@app.route("/login", methods=["POST"])
def login():
    # 로그인
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()                             # 비밀번호 암호화를 위한 해쉬값을 만들어 줌.
    result = db.users.find_one({'id': id_receive,
                                'pw': pw_hash})                                                  # 아이디와 패스워드가 매칭되는지 판단을 해줌. 매칭되는 사람이 있다면! 로그인에 성공 한것. 매칭이 안되면 회원가입을 해야함.

    if result is not None:                                                                       # result가 있다면!
        payload = {
            'id2': id_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)                           # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')                               # jwt 토큰을 발행. 놀이공원 자유입장권과 같은 것. 어떤 사람이 언제까지 입장이 유효하다를 적시해줌.
                                                                                                 # 토큰이 제대로 발행되었는지 확인하려면, 오른쪽 마우스 검사 누르고, 개발자 콘솔을 열면 Application탭을 눌러서 cookies가 나와 있음.
        return jsonify({'result': 'success', 'token': token})
                                                                                                 # 찾지 못하면,
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

@app.route('/sign_up')
def sign_up_template():
    return render_template('sign_up.html')

@app.route("/sign_up/save", methods=["POST"])
def sign_up():
    id_receive = request.form['id_give']                                                              # id 받고
    pw_receive = request.form['pw_give']                                                              # pw 받고
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()                                  # 해쉬 함수를 걸어준다
    doc = {
        "id": id_receive,                                                                             # 아이디
        "pw": pw_hash,                                                                                # 비밀번호
        "profile_name": id_receive                                                                    # 프로필 이름 기본값은 아이디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route("/sign_up/chkid", methods=["POST"])
def sign_up_check():
    # 아이디 중복 확인
    id_receive = request.form['id_give']
    exists = bool(db.users.find_one({"id": id_receive}))
    return jsonify({'result': 'success', 'exists': exists})

@app.route("/netnote/write", methods=["GET"])
def write_get():
   print("get")
   # get_url = "https://www.netflix.com/kr/title/81251379"
   # get_url = "https://www.netflix.com/title/81251379"
   get_url = "https://www.justwatch.com/kr/%EC%98%81%ED%99%94/riteul-poreseuteu"
   objId = db.movies.find_one({'url': get_url})['_id']
   print(objId)

   headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
   data = requests.get(get_url, headers=headers)

   soup = BeautifulSoup(data.text, 'html.parser')

   title = soup.select_one('#base > div.jw-info-box > div > div.jw-info-box__container-content > div:nth-child(2) > div.title-block__container > div.title-block > div > h1').text
   director = soup.select_one('#base > div.jw-info-box > div > div.jw-info-box__container-sidebar > div > aside > div.hidden-sm.visible-md.visible-lg.title-sidebar__desktop > div.title-info > div:nth-child(5) > div.detail-infos__value > span > a').text
   image = soup.select_one('meta[property="og:image"]')['content']

   db.movies.update_one({'_id': objId}, {'$set':{'title':title, 'director':director, 'image':image}})

   doc = {
      'objId': objId,
      'title': title,
      'director': director,
      'image': image
   }

   return render_template('write.html', data=doc)
   # return jsonify({'movies':doc})


@app.route("/netnote/write", methods=["POST"])
def write_post():
   print("기록 저장하기")
   objId_receive = request.form['objId']
   date_receive = request.form['date']
   together_receive = request.form['together']
   memo_receive = request.form['memo']
   star_receive = request.form['star']
   print(objId_receive, date_receive, together_receive, memo_receive, star_receive)


   doc = {
      'date': date_receive,
      'together': together_receive,
      'memo': memo_receive,
      'star': star_receive
   }
   db.movies.update_one({'_id': ObjectId(objId_receive)}, {'$set':doc})

   return render_template('home.html')


@app.route("/netnote/view", methods=["GET"])
def view_get():
   print("view")
   objId_receive = "6254557f6626d6d50173d193"

   doc = db.movies.find_one({'_id': ObjectId(objId_receive)})

   return render_template('view.html', data=doc)


# main page -eunjin-
@app.route('/main')
def main():
   return render_template('main.html')


# DB에 저장된 유저 기록 요청
@app.route("/netnote/main", methods=["GET"])
def movie_get():
    movie_list = list(db.movies.find({},{'_id':False}))

    return jsonify({'movies': movie_list})


# URL DB에 저장
@app.route('/netnote/geturl', methods=['POST'])
def url_post():
   url = request.form['url']

   doc = {
      'url': url
   }
   db.movies.insert_one(doc)

   return jsonify({'msg': 'url 주소 저장!'})







if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)