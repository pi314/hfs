var metadata = [
    /* structure: */
    /*
    {
         file: file,
         form: form,
         progress_bar: div_progress_bar;
         progress_ratio: td_fsize;
    }
    */
];


$(function () {
    var qrcode = new QRCode('qrcode', {
        'correctLevel' : QRCode.CorrectLevel.Q
    });
    qrcode.clear();
    qrcode.makeCode(decodeURIComponent(window.location));

    $('.widget-show').click(function () {
        $('#widget-show-hidden-files').addClass('hidden');
        $('#hidden-files').removeClass('hidden');
        console.log('test');
    });

    $('.widget-hide').click(function () {
        $('#widget-show-hidden-files').removeClass('hidden');
        $('#hidden-files').addClass('hidden');
    });

    $('#file').change(on_file_selected);
    $('#btn-upload').click(function () {
        upload_file(0);
    });

});


function add_metadata (file) {
    for (var i = 0; i < metadata.length; i++) {
        if (file.name == metadata[i].file.name) {
            return false;
        }
    }
    var obj = {};
    obj.file = file;

    metadata.push(obj);
    return true;
}


function add_progress_bar (metadata_obj) {
    var curdir = $('#curdir').val();

    var tr = $('<tr>')
    var td_fname = $('<td class="fname">'+ metadata_obj.file.name +'</td>')
    var div_progress_bar = $('<div class="progress-bar">');
    var td_fsize = $('<td class="fsize">'+ metadata_obj.file.size +'</td>')
    var td_form = $('<td>');
    var form = $('<form method="POST" action="/'+ curdir +'" enctype="multipart/form-data">');
    td_fname.append(div_progress_bar);
    tr.append(td_fname);
    tr.append(td_fsize);
    td_form.append(form);
    tr.append(td_form);

    $('#pending-files').append(tr);

    metadata_obj.form = form;
    metadata_obj.progress_bar = div_progress_bar;
    metadata_obj.progress_ratio = td_fsize;
}


function on_file_selected () {
    var files = $('#file')[0].files;
    for (var i = 0; i < files.length; i++) {
        if (!add_metadata(files[i])) {
            continue;
        }
        add_progress_bar(metadata[metadata.length - 1]);
    }
    console.log(metadata);
}


function show_upload_progress (metadata_obj, evt) {
    if (evt.lengthComputable) {
        var percent = Math.round(evt.loaded * 100 / evt.total);
        metadata_obj.progress_bar.css('width', percent +'%');
        metadata_obj.progress_ratio.text(evt.loaded +'/'+ evt.total);
    } else {
        metadata_obj.progress_bar.css({
            'width': '100%',
            'background': 'yellow',
        });
        metadata_obj.progress_ratio.text(evt.loaded +'/?');
    }
}


function show_upload_complete_message (index) {
    $('#message').text('Upload succeed.');
    if (index == metadata.length - 1) {
        window.location.reload();
    } else {
        upload_file(index + 1);
    }
}


function show_upload_fail_message () {
    $('#message').text('Upload failed.');
}


function show_upload_cancel_message () {
    $('#message').text('Upload canceled.');
}


function upload_file (index) {
    if (index >= metadata.length) {
        return;
    }
    var metadata_obj = metadata[index];
    var req = new XMLHttpRequest();
    var form = new FormData();
    var method = metadata_obj.form.attr('method');
    var url = metadata_obj.form.attr('action');

    form.append('upload', metadata_obj.file);


    req.upload.addEventListener('progress', function (evt) {
        show_upload_progress(metadata_obj, evt);
    }, false);
    req.addEventListener('load', function () {
        show_upload_complete_message(index);
    }, false);
    req.addEventListener('error', show_upload_fail_message, false);
    // req.addEventListener('abort', show_upload_cancel_message, false);
    req.open(method, url, true);
    req.send(form);
}

function file_delete (path) {
    var req = new XMLHttpRequest();
    req.open('DELETE', path, true);
    req.addEventListener('load', window.location.reload.bind(window.location), false);
    req.send();
}
