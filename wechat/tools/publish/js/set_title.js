// 设置文章标题
// __TITLE__ 会被 Python 替换为实际内容
(function() {
    var title = "__TITLE__";
    var input = document.querySelector("#title") || document.querySelector("input[placeholder*='标题']");
    if (!input) return "title input not found";

    var nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
    ).set;
    nativeSetter.call(input, title);
    input.dispatchEvent(new Event('input', {bubbles: true}));
    return "title set: " + title;
})();
