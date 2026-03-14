// 启用原创声明（不启用赞赏，避免"请选择赞赏账户"阻塞对话框）
// 2026-03-14 更新：修正 selector，旧 .js_original_area / input.js_original_a 已不存在
(function() {
    // 方案1：找 #js_original 下可见的 .js_edit_ori（DIV 开关）
    var origSection = document.querySelector('#js_original');
    if (origSection) {
        var switches = origSection.querySelectorAll('.js_edit_ori');
        for (var i = 0; i < switches.length; i++) {
            if (switches[i].offsetParent !== null) {
                switches[i].scrollIntoView({block: 'center'});
                switches[i].click();
                return "原创: clicked switch (selector: #js_original .js_edit_ori[" + i + "])";
            }
        }
    }

    // 方案2：通过 setting-group__title 文本找"原创"
    var titles = document.querySelectorAll('.setting-group__title');
    for (var j = 0; j < titles.length; j++) {
        if (titles[j].textContent.trim() === '原创' && titles[j].offsetParent !== null) {
            var group = titles[j].closest('.setting-group__content, .appmsg-editor__setting-group');
            if (group) {
                var sw = group.querySelector('.js_edit_ori, .setting-group__switch');
                if (sw) {
                    sw.scrollIntoView({block: 'center'});
                    sw.click();
                    return "原创: clicked via title text";
                }
            }
        }
    }

    return "原创 switch not found (no #js_original or visible .js_edit_ori)";
})();
