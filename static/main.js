$(function () {
    qrcode = new QRCode('qrcode', {
        'correctLevel' : QRCode.CorrectLevel.Q
    });
    $('.btn-show').click(function () {
        $('#btn-show-hidden-files').addClass('hidden');
        $('#hidden-files').removeClass('hidden');
        console.log('test');
    });

    $('.btn-hide').click(function () {
        $('#btn-show-hidden-files').removeClass('hidden');
        $('#hidden-files').addClass('hidden');
    });

    show_qr_code(window.location);

    $('#file').change(file_selected);
    $('#btn_upload').click(file_upload);

});


function show_qr_code (text) {
    qrcode.clear();
    qrcode.makeCode(decodeURIComponent(text));
}


function file_selected () {
    var file = $('#file')[0].files[0];

    $('#progress-bar-container').css('display', 'block');
    $('#file-size').text(file.size);
}


function file_upload () {
    var req = new XMLHttpRequest();
    var form = document.getElementById('form');
    var data = new FormData(form);
    var url = form.action;

    req.upload.addEventListener('progress', show_upload_progress, false);
    req.addEventListener('load', show_upload_complete_message, false);
    req.addEventListener('error', show_upload_fail_message, false);
    req.addEventListener('abort', show_upload_cancel_message, false);
    req.open('POST', url, true);
    req.send(data);

    return false;
}


function show_upload_progress (evt) {
    if (evt.lengthComputable) {
        var percent = Math.round(evt.loaded * 100 / evt.total);
        $('#progress-bar').css('width', percent +'%');
        $('#progress-bar').text(percent +'%');
        $('#file-size').text(evt.loaded +'/'+ evt.total);
    } else {
        $('#progress-bar').css({
            'width': '100%',
            'background': 'yellow',
        });
        $('#progress-bar').text('Unable to compute');
    }
}


function show_upload_complete_message () {
    $('#message').text('Upload succeed.');
    window.location.reload();
}


function show_upload_fail_message () {
    $('#message').text('Upload failed.');
}


function show_upload_cancel_message () {
    $('#message').text('Upload canceled.');
}
