// 通知 ProseMirror 编辑器内容已变更，触发保存
// 直接改 DOM 不触发变更检测，必须 dispatch event
(function() {
    var editor = document.querySelectorAll("[contenteditable=true]")[1];
    if (!editor) return "editor not found";
    editor.dispatchEvent(new Event("input", {bubbles: true}));
    editor.dispatchEvent(new Event("compositionend", {bubbles: true}));
    return "save triggered";
})();
