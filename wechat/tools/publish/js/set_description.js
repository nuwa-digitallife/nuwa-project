// 设置文章简介
// __DESCRIPTION__ 会被 Python 替换为实际内容
(function() {
    var desc = "__DESCRIPTION__";
    var textarea = document.querySelector("#js_description");
    if (!textarea) {
        textarea = document.querySelector("textarea[placeholder*='简介']")
            || document.querySelector(".weui-desktop-editor__desc textarea");
    }
    if (!textarea) return "description textarea not found";

    textarea.focus();
    textarea.value = desc;
    textarea.dispatchEvent(new Event('input', {bubbles: true}));
    textarea.dispatchEvent(new Event('change', {bubbles: true}));
    textarea.blur();
    return "description set: " + desc.substring(0, 30) + "...";
})();
