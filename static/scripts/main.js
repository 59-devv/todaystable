// like 버튼 토글
function toggle_like(food_num, type) {
  // 백엔드로 어떤 음식이 좋아요를 받았는지 보내주어야 하기 때문에
  // food.no 을 전달해준다. type은 빈 하트인지 찬 하트인지(좋아요가 원래 눌려있었는지 아닌지를 판단하기 위함)
  let $a_like = $(`#${food_num} a[aria-label='heart']`);
  let $i_like = $a_like.find("i");
  // 그래서 좋아요를 받은 요리의 하트가 fa-heart (빈하트)이면 좋아요가 안되어 있다는 것
  if ($i_like.hasClass("fa-heart")) {
    $.ajax({
      type: "POST",
      url: "/update_like",
      data: {
        food_num_give: food_num,
        type_give: type,
        action_give: "unlike",
      },
      success: function (response) {
        // 백엔드에서 좋아요 처리한 후 좋아요 개수를 response로 전달해준다.
        // fa-heart(빈 하트)를 지우고 fa-heart-o(찬 하트)로 바꾸어 줌으로써 좋아요 하트를 표시한다.
        // 그러고 a 태그에 count 수 전달
        $i_like.addClass("fa-heart-o").removeClass("fa-heart");
        $a_like.find("span.like-num").text(response["count"]);
      },
    });
  } else {
    // 좋아요가 되어있는 것이면 (찬 하트이면) 이제 unlike 해야함
    $.ajax({
      type: "POST",
      url: "/update_like",
      data: {
        food_num_give: food_num,
        type_give: type,
        action_give: "like",
      },
      success: function (response) {
        // 마찬가지로 찬하트 빼고 빈 하트 추가 바뀐 좋아요 수 적용
        $i_like.addClass("fa-heart").removeClass("fa-heart-o");
        $a_like.find("span.like-num").text(response["count"]);
      },
    });
  }
}

// modal show/hide
function show_modal() {
  $(".modal").addClass("show");
}

function hide_modal() {
  $(".modal").removeClass("show");
}
