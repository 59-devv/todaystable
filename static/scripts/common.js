// 작성후 X분 후 
// 사용 : user.html, detail.html
function time2str(date) {
  let today = new Date()
  let time_ex = today - date
  let time = time_ex / 1000 / 60 // 분

  if (time < 2) {
      return "방금 전"
  }

  if (time < 60) {
      return parseInt(time) + "분 전"
  }
  time = time / 60 // 시간
  if (time < 24) {
      return parseInt(time) + "시간 전"
  }
  time = time / 24 // 일
  if (time < 7) {
      return parseInt(time) + "일 전"
  }
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`
}

// header의 로그아웃버튼
// 사용: user.html, detail.html, main.html
function sign_out() {
  $.removeCookie('mytoken', { path: '/'});
  alert('정상적으로 로그아웃 되었습니다.')
  window.location.href = "/"
}
 
// userpage로 이동
// 사용: detail.html, main.html
function userpage(){
  location.href='/user'
}

// 프로필클릭시 로그아웃버튼 show
// 사용: user.html, detail.html, main.html
$(".user").click(function () {
  if ($(".nav").hasClass("show")) {
    $(".nav").removeClass("show");
  } else {
    $(".nav").addClass("show");
  }
});

//top버튼 클릭시 위로스크롤
//사용: detail.html, main.html
$("#top-btn").click(function () {
  $("html, body").animate({scrollTop: 0}, 400);
  return false;
});
//top버튼 스트롤200부터 보임
//사용: detail.html, main.html
$(window).scroll(function () {
  if ($(this).scrollTop() > 200) {
      $("#top-btn").fadeIn();
  } else {
      $("#top-btn").fadeOut();
  }
});
