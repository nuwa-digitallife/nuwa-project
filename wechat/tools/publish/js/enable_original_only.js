// 仅启用原创声明（不启用赞赏，避免"请选择赞赏账户"阻塞对话框）
// 赞赏需要选择赞赏账户，目前无法自动化，留给用户手动设置
(function() {
    var origSwitch = document.querySelector(".js_original_area .weui-desktop-switch__input, input.js_original_a");
    if (origSwitch) {
        if (!origSwitch.checked) {
            origSwitch.click();
            return "原创: enabled (赞赏: skipped)";
        } else {
            return "原创: already on";
        }
    }
    // 备选方案：通过文本查找
    var divs = document.querySelectorAll("div");
    for (var i = 0; i < divs.length; i++) {
        if (divs[i].textContent.trim() === "\u539F\u521B" && divs[i].getBoundingClientRect().y > 200) {
            divs[i].click();
            return "原创: clicked div (赞赏: skipped)";
        }
    }
    return "原创 switch not found";
})();
