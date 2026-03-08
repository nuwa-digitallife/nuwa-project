// 点击对话框的「确定」按钮
// 先勾选"我已阅读并同意"checkbox，填写作者名
(function() {
    // 1. 勾选 checkbox（原创声明需要）
    var checkboxes = document.querySelectorAll(
        'input[type="checkbox"], .weui-desktop-icon-checkbox, [class*="checkbox"]'
    );
    for (var i = 0; i < checkboxes.length; i++) {
        var cb = checkboxes[i];
        var nearby = cb.closest('.weui-desktop-dialog__bd, .weui-desktop-dialog, [class*="dialog"]');
        if (nearby && nearby.textContent.indexOf('阅读') >= 0) {
            if (!cb.checked) {
                cb.click();
            }
            break;
        }
    }

    // 2. 填写作者名（原创声明要求，不超过8字）
    var authorInputs = document.querySelectorAll('input[placeholder*="作者"]');
    for (var k = 0; k < authorInputs.length; k++) {
        if (!authorInputs[k].value) {
            authorInputs[k].focus();
            authorInputs[k].value = '降临派手记';
            authorInputs[k].dispatchEvent(new Event('input', {bubbles: true}));
            authorInputs[k].dispatchEvent(new Event('change', {bubbles: true}));
            break;
        }
    }

    // 3. 点确定
    var selectors = [
        ".weui-desktop-btn_primary",
        ".btn_primary",
        "button",
        "a[role=button]",
        "div[role=button]"
    ];
    for (var s = 0; s < selectors.length; s++) {
        var els = document.querySelectorAll(selectors[s]);
        for (var j = 0; j < els.length; j++) {
            if (els[j].textContent.trim() === "\u786E\u5B9A") {
                els[j].click();
                return "checked agreement + clicked 确定";
            }
        }
    }
    return "确定 not found";
})();
