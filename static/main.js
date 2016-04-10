var metadata = [
    // {
    //      'filename': filename
    //      'id': file#,
    //      'dom_id': DOM id,
    // }
];


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
    $('#btn_upload').click(start_upload);

});


function show_qr_code (text) {
    qrcode.clear();
    qrcode.makeCode(decodeURIComponent(text));
}


function add_metadata (file) {
    for (var i = 0; i < metadata.length; i++) {
        if (file.name == metadata[i].filename) {
            return false;
        }
    }
    var obj = {};
    obj.file = file;
    obj.id = 'file'+ metadata.length;

    metadata.push(obj);
    return true;
}


function add_progress_bar (metadata_obj) {
    var curdir = $('#curdir').val();
    console.log(curdir);

    var form = $('<form method="POST" action="/'+ curdir +'" enctype="multipart/form-data">');
    var li = $('<li id="'+ metadata_obj.id +'"></li>');
    var progress_bar = $('<div class="progress-bar">');
    var progress = $('<div class="progress">');
    var filesize = $('<div class="file-size">'+ metadata_obj.file.size +'</div>')
    var file = $('<input type="file" name="upload" class="hidden">');

    console.log(form);

    li.append(form);
    form.append(file);
    form.append(progress_bar);
    progress_bar.append(progress);
    progress_bar.append('<div class="file-name">'+ metadata_obj.file.name +'</div>');
    progress_bar.append(filesize);
    $('#pending_files').append(li);

    metadata_obj.form = form;
    metadata_obj.li = li;
    metadata_obj.progress_bar = progress_bar;
    metadata_obj.progress = progress;
    metadata_obj.filesize = filesize;
}


function file_selected () {
    var files = $('#file')[0].files;
    for (var i = 0; i < files.length; i++) {
        if (!add_metadata(files[i])) {
            continue;
        }
        add_progress_bar(metadata[metadata.length-1]);
    }
    console.log(metadata);
}


function start_upload () {
    if (metadata.length == 0) {
        return;
    }

    file_upload(0);
}


function file_upload (index) {
    var metadata_obj = metadata[index];
    var req = new XMLHttpRequest();
    var form = new FormData();
    var method = metadata_obj.form.attr('method');
    var url = metadata_obj.form.attr('action');

    form.append('upload', metadata_obj.file);

    function show_upload_progress (evt) {
        if (evt.lengthComputable) {
            var percent = Math.round(evt.loaded * 100 / evt.total);
            metadata_obj.progress.css('width', percent +'%');
            metadata_obj.filesize.text(evt.loaded +'/'+ evt.total);
        } else {
            metadata_obj.progress.css({
                'width': '100%',
                'background': 'yellow',
            });
            metadata_obj.filesize.text('N/A');
        }
    }


    function show_upload_complete_message () {
        $('#message').text('Upload succeed.');
        if (index == metadata.length - 1) {
            window.location.reload();
        } else {
            file_upload(index + 1);
        }
    }


    function show_upload_fail_message () {
        $('#message').text('Upload failed.');
    }


    function show_upload_cancel_message () {
        $('#message').text('Upload canceled.');
    }

    req.upload.addEventListener('progress', show_upload_progress, false);
    req.addEventListener('load', show_upload_complete_message, false);
    req.addEventListener('error', show_upload_fail_message, false);
    // req.addEventListener('abort', show_upload_cancel_message, false);
    req.open(method, url, true);
    req.send(form);
}
