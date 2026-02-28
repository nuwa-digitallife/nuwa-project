// 设置文章简介
// __DESCRIPTION__ 会被 Python 替换为实际内容
(function() {
    var desc = "__DESCRIPTION__";
    var textarea = document.querySelector("#js_description");
    if (!textarea) return "description textarea not found";

    // 用 native setter 触发 React/Vue 变更检测
    var nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
    ).set;
    nativeSetter.call(textarea, desc);
    textarea.dispatchEvent(new Event('input', {bubbles: true}));
    return "description set: " + desc.substring(0, 30) + "...";
})();
