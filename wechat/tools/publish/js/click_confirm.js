// 点击对话框的「确定」按钮
(function() {
    var selectors = [
        ".weui-desktop-btn_primary",
        ".btn_primary",
        "button",
        "a[role=button]",
        "div[role=button]"
    ];
    for (var s = 0; s < selectors.length; s++) {
        var els = document.querySelectorAll(selectors[s]);
        for (var i = 0; i < els.length; i++) {
            if (els[i].textContent.trim() === "\u786E\u5B9A") {
                els[i].click();
                return "clicked 确定";
            }
        }
    }
    return "确定 not found";
})();
