// 启用原创声明 + 赞赏（两个 switch 一起搞定）
// 用法：注入到微信编辑器页面执行
(function() {
    var results = [];

    // 1. 原创
    var origSwitch = document.querySelector(".js_original_area .weui-desktop-switch__input, input.js_original_a");
    if (origSwitch) {
        if (!origSwitch.checked) {
            origSwitch.click();
            results.push("原创: enabled");
        } else {
            results.push("原创: already on");
        }
    } else {
        var divs = document.querySelectorAll("div");
        for (var i = 0; i < divs.length; i++) {
            if (divs[i].textContent.trim() === "\u539F\u521B" && divs[i].getBoundingClientRect().y > 200) {
                divs[i].click();
                results.push("原创: clicked div");
                break;
            }
        }
    }

    // 2. 赞赏
    var rewardSwitch = document.querySelector("input.js_reward_set");
    if (rewardSwitch) {
        if (!rewardSwitch.checked) {
            rewardSwitch.click();
            results.push("赞赏: enabled");
        } else {
            results.push("赞赏: already on");
        }
    } else {
        results.push("赞赏: switch not found");
    }

    return results.join(" | ");
})();
