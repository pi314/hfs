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

});

function show_qr_code (text) {
    qrcode.clear();
    qrcode.makeCode(decodeURIComponent(text));
}
