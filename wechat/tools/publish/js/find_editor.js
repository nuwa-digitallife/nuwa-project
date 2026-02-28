// 检测当前页面是否有微信编辑器
(function() {
    var editors = document.querySelectorAll("[contenteditable=true]");
    if (editors.length < 2) return JSON.stringify({found: false, count: editors.length});
    var editor = editors[1];
    var text = editor.textContent.substring(0, 100);
    return JSON.stringify({found: true, count: editors.length, preview: text});
})();
