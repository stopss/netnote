from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# test!!!

# jwt 연결
import jwt  # 파이썬 인터프리터에서 jwt 추가해주세요!
# 시간 날짜 형태 사용
from datetime import datetime, timedelta
# 비밀번호 암호화
import hashlib

import requests
from bs4 import BeautifulSoup

# 비밀키 설정
SECRET_KEY = 'NetNote'
from bson.objectid import ObjectId  # db에서 object id값 가져올 때 사용.
import certifi  # 파이썬 인터프리터에서 certifi 추가해주세요.
from pymongo import MongoClient

client = MongoClient('mongodb+srv://sparta:test@cluster0.gqkk6.mongodb.net/Cluster0?retryWrites=true&w=majority',
                     tlsCAFile=certifi.where())
db = client.dbnetnote


@app.route('/')
def home():
    return render_template('home.html')



# 로그인 시간이 만료되면 홈으로 이동.
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

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()  # 비밀번호 암호화를 위한 해쉬값을 만들어 줌.
    result = db.users.find_one({'id': id_receive,
                                'pw': pw_hash})  # 아이디와 패스워드가 매칭되는지 판단을 해줌. 매칭되는 사람이 있다면! 로그인에 성공 한것. 매칭이 안되면 회원가입을 해야함.

    if result is not None:  # result가 있다면!
        payload = {
            'id2': id_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY,
                           algorithm='HS256')  # jwt 토큰을 발행. 놀이공원 자유입장권과 같은 것. 어떤 사람이 언제까지 입장이 유효하다를 적시해줌.
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
    id_receive = request.form['id_give']  # id 받고
    pw_receive = request.form['pw_give']  # pw 받고
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()  # 해쉬 함수를 걸어준다
    doc = {
        "id": id_receive,  # 아이디
        "pw": pw_hash,  # 비밀번호
        "profile_name": id_receive  # 프로필 이름 기본값은 아이디
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
    get_url = request.args.get('url')
    print("write:" + get_url)
    # url = url
    # print("url:"+url)
    # objId = db.movies.find_one({'url': get_url})['_id']
    # print(objId)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(get_url, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    title = soup.select_one(
        '#base > div.jw-info-box > div > div.jw-info-box__container-content > div:nth-child(2) > div.title-block__container > div.title-block > div > h1').text
    director = soup.select_one('.title-credit-name').text
    print("director:" + director)
    image = soup.select_one('meta[property="og:image"]')['content']

    # db.movies.update_one({'_id': objId}, {'$set':{'title':title, 'director':director, 'image':image}})

    doc = {
        'title': title,
        'director': director,
        'img': image,
        'url': get_url
    }

    return render_template('write.html', data=doc)


@app.route("/netnote/write", methods=["POST"])
def write_post():
    token_receive = request.cookies.get('token')
    user_info = ""

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({'id': payload['id2']})['id']
    except jwt.ExpiredSignatureError:
        # 로그인 시간 만료
        return redirect(url_for("login"))
    except jwt.exceptions.DecodeError:
        # 로그인 정보 존재x
        return redirect(url_for("login"))

    print("기록 저장하기")
    url_receive = request.form['url']

    director_receive = request.form['director']
    title_receive = request.form['title']
    image_receive = request.form['image']
    category_receive = request.form['category']
    date_receive = request.form['date']
    together_receive = request.form['together']
    memo_receive = request.form['memo']
    star_receive = request.form['star']
    print(category_receive)

    doc = {
        'title': title_receive,
        'director': director_receive,
         'img': image_receive,
        'url': url_receive,
        'date': date_receive,
        'together': together_receive,
        'memo': memo_receive,
        'star': star_receive,
        'writer': user_info
    }
    if category_receive == "영화":
        db.movies.insert_one(doc)
    elif category_receive == "드라마":
        db.dramas.insert_one(doc)
    else:
        db.kids.insert_one(doc)

    return redirect(url_for('main'))


@app.route("/netnote/view", methods=["POST"])
def view_get():
    title5 = request.form['title_give']
    print(title5)
    # objId_receive = "6254557f6626d6d50173d193"
    # doc = db.movies.find_one({'_id': ObjectId(objId_receive)})
    return render_template('view.html')


# main page -eunjin-
@app.route("/main", methods=["GET","POST"])
def main():
    token_receive = request.cookies.get('token')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({'id': payload['id2']})
        return render_template('main.html', id=user_info['id'])
    except jwt.ExpiredSignatureError:
        # 로그인 시간 만료
        return redirect(url_for("login"))
    except jwt.exceptions.DecodeError:
        # 로그인 정보 x
        return render_template('main.html', id="")

    # return render_template('main.html')




# DB에 저장된 유저 기록 요청
@app.route("/netnote/main", methods=["GET"])
def movie_get():
    movie_list = list(db.movies.find({}, {'_id': False}))
    dramas_list = list(db.dramas.find({}, {'_id': False}))

    return jsonify({'movies': movie_list, 'dramas': dramas_list })



# URL DB에 저장
@app.route('/netnote/geturl', methods=['POST'])
def url_post():
    print("geturl")
    url_receive = request.form['url']
    print("geturl:" + url_receive)

    doc = {
        'url': url_receive
    }

    return redirect(url_for('write_get', url=url_receive))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
