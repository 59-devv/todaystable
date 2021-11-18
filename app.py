import random
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from pymongo import MongoClient


app = Flask(__name__)

# DB 접속
client = MongoClient('mongodb://3.35.19.169', 27017, username="test", password="test")
db = client.todaystable


# JWT 토큰을 만들 때 필요한 비밀번호와 같은 문자열.
# 내 서버에서만 토큰을 인코딩/디코딩이 가능하다.
SECRET_KEY = 'HANGHAE99'

# PYJWT 패키지 사용
import jwt

# 토큰 만료시간을 지정하기 위해 datetime 모듈 사용
import datetime

# 비밀번호는 암호화하여 DB에 저장해야 함. 그래야 개발자도 비밀번호를 알 수 없음
import hashlib


# 메인페이지 및 로그인/회원가입 페이지
@app.route('/')
def home():
    # 클라이언트로 부터 토큰이 담긴 쿠키를 받는다.
    token_receive = request.cookies.get('mytoken')
    try:  # 토큰이 확인 될 경우 -> 메인페이지로 이동
        # payload 생성
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 로그인 한 User 정보
        user_info = db.users.find_one({"username": payload['id']})
        # 음식 리스트를 좋아요 순으로 정렬 (내림차순)
        dishes = list(db.foodInfo.find({}, {'_id': False}).sort('likeCount', -1))
        # 좋아요 수와, 로그인 한 유저가 좋아요 했는지 여부를 변수로 저장
        for dish in dishes:
            dish["count_like"] = db.likes.count_documents({'foodNum':dish['no'], 'type':'heart'})
            dish["like_by_me"] = bool(db.likes.find_one({'foodNum':dish['no'], 'type':'heart', 'username':payload['id']}))
        # 전체 음식 리스트 중, 3개를 랜덤으로 선택
        recommends = random.sample(dishes, 3)

        return render_template('main.html', nickname=user_info["nickname"], dishes=dishes, recommends=recommends, user_pic=user_info["profile_pic_real"])
    except:  # 토큰이 만료되었거나 정보가 없는 경우, 로그인 페이지로 바로 이동
        return redirect(url_for("index"))


# 로그인 및 회원가입 페이지
@app.route('/index')
def index():
    return render_template('index.html')


# 회원가입 - 아이디 중복 체크 API
@app.route('/api/sign_up/check_dup', methods=['POST'])
def check_dup():
    # 아이디를 입력받고, DB에서 중복이 있는지 검토
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


# 회원가입 - 완료 후 DB에 저장
@app.route('/api/sign_up', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,
        "password": password_hash,
        "nickname": nickname_receive,
        # 회원가입 시 기본 프로필사진을 DB에 지정해줌
        "profile_pic": "default_pic.jpg",
        "profile_pic_real": "profile_pics/default_pic.jpg"
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


# 로그인 기능
@app.route('/api/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    # 비밀번호 암호화
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})
    # ID / PW 가 일치하는 result가 DB에 있을 경우 payload 생성 및 token 발행
    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.datetime.utcnow() + timedelta(seconds=60 * 60 * 24) # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 계정 정보가 일치하지 않는 경우
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 음식 상세 페이지
@app.route('/detail/<keyword>')
def detail(keyword):
    # 토큰이 있을 경우, 페이지로 이동
    token_receive = request.cookies.get('mytoken')
    try:
        # detail/<keyword> 를 통해 keyword 번호에 해당하는 음식의 상세 페이지로 이동
        # 필요한 정보를 DB에서 추출 (음식 상세정보, 해당 음식에 대한 코멘트)
        food = db.foodInfo.find_one({'no' : keyword}, {'_id': False})
        comments = db.comments.find({'num': keyword}, {'_id': False})

        # 토큰을 통해 로그인한 USER 정보 확인
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload['id']})
        user_pic = user_info["profile_pic_real"]

        username = user_info['username']
        nickname = user_info['nickname']

        # 음식의 상세 정보 중 요리방법, 요리 단계별 이미지
        food_recipe = db.foodManual.find({'num': keyword}, {'_id': False, 'num': False})[0]
        food_img = db.foodImg.find({'num': keyword}, {'_id': False, 'num': False})[0]

        return render_template('detail.html', food=food, comments=comments,
                               receipe=food_recipe, foodImg=food_img, username=username, nickname=nickname, user_pic=user_pic)
    except: # 토큰이 만료되었거나 정보가 없는 경우, 로그인 페이지로 바로 이동
        return redirect(url_for("index"))

# 코멘트 저장 기능
@app.route('/api/save_comment', methods=['POST'])
def save_comment():
    # 코멘트 내용, 어떤 음식인지 음식 번호, 업로드 시간
    comment_receive = request.form['comment_give']
    num_receive = request.form['num_give']
    time_receive = request.form['time_give']

    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload['id']})
    username = user_info['username']
    nickname = user_info['nickname']
    user_pic = user_info['profile_pic_real']

    # 추후 코멘트를 이용해서 활용할 항목들을 DB에 저장
    doc = {
        "num": num_receive,
        "username": username,
        "nickname": nickname,
        "comment": comment_receive,
        "time": time_receive,
        "profile_pic_real": user_pic
    }
    db.comments.insert_one(doc)

    return jsonify({'result': 'success', 'msg': 'Comment 저장 성공'})


# 코멘트 불러오기 기능
@app.route('/api/get_comments', methods=['POST'])
def get_comments():
    # 해당 음식에 대한 코멘트를 불러오기 위해, 음식 번호와 코멘트를 불러옴
    # 이 때, 코멘트는 최신순으로 정렬
    num_receive = request.form['num_give']
    comments = list(db.comments.find({'num': num_receive}, {'_id': False}).sort("time", -1))

    return jsonify({'result': 'success', 'comments': comments})


# 코멘트 삭제하기 기능
@app.route('/api/delete_comment', methods=['POST'])
def delete_comment():
    # 작성자(USERNAME)와 코멘트 내용이 일치할 경우, 코멘트를 삭제
    username_receive = request.form['username_give']
    comment_receive = request.form['comment_give']
    db.comments.delete_one({'username': username_receive, 'comment': comment_receive})

    return jsonify({'result': 'success', 'msg': '코멘트가 삭제되었습니다.'})


# 좋아요 기능
@app.route('/update_like', methods=['POST'])
def update_like():
    # 토큰을 통해 USER 정보 확인
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload["id"]})

    # 좋아요/좋아요 취소를 확인하기 위한 변수 설정
    food_num_receive = request.form["food_num_give"]
    type_receive = request.form["type_give"]
    action_receive = request.form["action_give"]
    doc = {
        "foodNum": food_num_receive,
        "username": user_info["username"],
        "type": type_receive
    }
    # 클라이언트쪽의 토글기능을 통해 전달받은 action으로, 좋아요인지 취소인지를 확인 후 저장/삭제
    if action_receive == "like":
        db.likes.insert_one(doc)
    else:
        db.likes.delete_one(doc)
    # 좋아요/취소 후 현재 좋아요 숫자를 세어주고, DB에 UPDATE 진행
    count = db.likes.count_documents({"foodNum": food_num_receive, "type": "heart"})
    db.foodInfo.update({"no": food_num_receive}, {"$set": {"likeCount": count}})
    return jsonify({"result": "success", 'msg': 'updated', "count": count})


# 마이 페이지
@app.route('/user')
def user():
    token_receive = request.cookies.get('mytoken')
    try:  # 토큰이 있을 경우 페이지 오픈
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]}, {"_id": False})
        user_pic = db.users.find_one({"username": payload["id"]}, {"_id": False})["profile_pic_real"]
        comments = list(db.comments.find({"username": payload["id"]}, {"_id": False}))
        food_info = {}
        for comment in comments:
            food_info["num"] = db.foodInfo.find_one({"no":comment["num"]})["no"]
            food_info[comment["num"]] = db.foodInfo.find_one({"no":comment["num"]})["menu_name"]

        return render_template('user.html', user_info=user_info, nickname=user_info["nickname"], food_info=food_info, comments=comments, user_pic=user_pic)
    except: # 토큰이 만료되었거나 정보가 없는 경우, 로그인 페이지로 바로 이동
        return redirect(url_for("index"))


# 마이페이지 코멘트 불러오기
@app.route('/api/get_my_comments', methods=['GET'])
def get_my_comments():
    return jsonify({'result': 'success'})


#음식 추천 기능
@app.route('/api/recommend_food', methods=['POST'])
def recommend_food():
    # 사용자가 제출한 문제의 답변
    answer1 = request.form['answers1']
    answer2 = request.form['answers2']
    answer3 = request.form['answers3']

    # 각 응답값에 따라, 결과를 3단계로 필터링
    main_dish = db.foodInfo.find({'menu_type': '밥'}, {'_id': False})
    dessert = db.foodInfo.find({'menu_type': '후식'}, {'_id': False})
    # 1차 필터링
    r = main_dish if answer1 == "밥" else dessert

    # 2차 필터링
    r2 = []
    for i in r:
        if answer2 == "고단백":
            if float(i['protein']) > 25:
                r2.append(i)
        else:
            if float(i['natrium']) < 100:
                r2.append(i)

    # 3차 필터링
    r3 = []
    for i in r2:
        if answer3 == "다이어트식":
            if float(i['calorie']) < 300:
                r3.append(i)
        else:
            if float(i['calorie']) > 500:
                r3.append(i)

    # 결과값 중, 랜덤으로 1개의 음식을 추천
    result = random.sample(r3, 1)
    return jsonify({'result': 'success', 'recommended': result})


# 프로필 수정 기능
@app.route('/update_profile', methods=['POST'])
def update_profile():
    # 토큰에서 현재 로그인한 사용자 정보 확인
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    username = payload["id"]
    # 사용자가 수정한 닉네임 입력값을 전달받아, 수정 대상(new_doc)에 대입
    nickname_receive = request.form["nickname_give"]
    new_doc = {
        "nickname": nickname_receive,
    }
    # 사용자가 파일을 업로드 했을 때, 수행할 기능
    if 'file_give' in request.files:
        # 사용자가 업로드한 파일 읽기
        file = request.files["file_give"]
        # 파일 이름 읽기
        filename = secure_filename(file.filename)
        # 파일 이름 중, 확장자 분리
        extension = filename.split(".")[-1]
        # 파일 이름을 'username.png' 과 같이 저장하기 위해, 경로 및 파일이름 설정
        file_path = f"profile_pics/{username}.{extension}"
        # 파일 저장
        file.save("./static/"+file_path)
        # db에 파일의 경로(주소)를 저장하기 위해, new_doc에 대입
        new_doc["profile_pic"] = filename
        new_doc["profile_pic_real"] = file_path
    # User정보, Comment정보가 담긴 DB에서 기존 닉네임을 사용자가 수정한 닉네임으로 UPDATE
    db.users.update_one({'username': payload['id']}, {'$set':new_doc})
    db.comments.update_many({'username': payload['id']}, {'$set': {'nickname': nickname_receive}})
    return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
