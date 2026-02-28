// 删除 mdnice 渲染产生的空表格（ghost tables）
// mdnice 渲染 markdown 表格到微信编辑器时，可能在有内容的表格上方产生空表格
(function() {
    var editor = document.querySelectorAll("[contenteditable=true]")[1];
    if (!editor) return "editor not found";
    var tables = editor.querySelectorAll("table");
    var removed = 0;
    for (var t = tables.length - 1; t >= 0; t--) {
        var cells = tables[t].querySelectorAll("td, th");
        var hasContent = false;
        for (var c = 0; c < cells.length; c++) {
            if (cells[c].textContent.trim().length > 0) {
                hasContent = true;
                break;
            }
        }
        if (!hasContent) {
            tables[t].remove();
            removed++;
        }
    }
    return "removed " + removed + " empty tables";
})();
