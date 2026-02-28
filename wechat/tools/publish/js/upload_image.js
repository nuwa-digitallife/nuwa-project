// 上传图片到微信 CDN
// __IMAGE_URL__ = HTTPS 本地服务器上的图片 URL
// __TOKEN__ = 微信后台 token（从 URL 中提取）
// __IMAGE_NAME__ = 图片文件名（用于日志）
(async function() {
    var imageUrl = "__IMAGE_URL__";
    var token = "__TOKEN__";
    var imageName = "__IMAGE_NAME__";

    try {
        // Fetch image from HTTPS local server
        var resp = await fetch(imageUrl);
        var blob = await resp.blob();

        // Build multipart form
        var formData = new FormData();
        formData.append("file", blob, imageName);

        // Upload to WeChat CDN
        var uploadUrl = "/cgi-bin/filetransfer?action=upload_material&f=json&scene=8&writetype=doublewrite&groupid=1&token=" + token + "&type=10";
        var result = await fetch(uploadUrl, {
            method: "POST",
            body: formData
        });
        var data = await result.json();

        if (data.cdn_url) {
            return JSON.stringify({ok: true, cdn_url: data.cdn_url, name: imageName});
        } else {
            return JSON.stringify({ok: false, error: JSON.stringify(data), name: imageName});
        }
    } catch (e) {
        return JSON.stringify({ok: false, error: e.message, name: imageName});
    }
})();
