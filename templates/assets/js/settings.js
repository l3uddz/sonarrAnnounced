// Settings Page
$(function(){
    $('#sonarr_check').on('click', function() {
        alite({
            url: '/sonarr/check',
            method: 'POST',
            data: {
                url: $("#sonarr_url").val().trim(),
                apikey: $("#sonarr_apikey").val().trim()
            },
        }).then(function (result) {
            console.log('sonarr_check result: ', result);
            if (result == 'ERR') {
                // apikey was invalid
                $("#sonarr_check").removeClass("btn-success").addClass("btn-danger");
            } else {
                // apikey was valid
                $("#sonarr_check").removeClass("btn-danger").addClass("btn-success");
            }
        }).catch(function (err) {
            console.error('sonarr_check error: ', err);
            $("#sonarr_check").removeClass("btn-success").addClass("btn-danger");
        });        
    });
});