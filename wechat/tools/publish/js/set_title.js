// 设置文章标题
// __TITLE__ 会被 Python 替换为实际内容
(function() {
    var title = "__TITLE__";

    // 微信编辑器标题可能是 input 或 contenteditable
    var input = document.querySelector("#title")
        || document.querySelector("input[placeholder*='标题']")
        || document.querySelector(".weui-desktop-editor__title input")
        || document.querySelector("[class*='title'] input");

    if (input) {
        input.focus();
        input.value = title;
        input.dispatchEvent(new Event('input', {bubbles: true}));
        input.dispatchEvent(new Event('change', {bubbles: true}));
        input.blur();
        return "title set (input): " + title.substring(0, 30);
    }

    // 可能是 contenteditable 的标题区域
    var editable = document.querySelector("[contenteditable='true']");
    if (editable) {
        // 第一个 contenteditable 通常是标题
        editable.focus();
        editable.textContent = title;
        editable.dispatchEvent(new Event('input', {bubbles: true}));
        return "title set (contenteditable): " + title.substring(0, 30);
    }

    return "title input not found";
})();
