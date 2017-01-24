// Index Pgae
function notify_sonarr(announcement_id) {
    console.log("Notifying sonarr again for announcement: " + announcement_id);
    
    alite({
            url: '/sonarr/notify',
            method: 'POST',
            data: {
                id: announcement_id
            },
        }).then(function (result) {
            console.log('sonarr_notify result: ', result);
            if (result == 'ERR') {
                // sonarr rejected the announcement
                toastr.error("Sonarr still declined this torrent...");
            } else {
                // sonarr accepted the announcement
                toastr.success("Sonarr approved the torrent this time!");
            }
        }).catch(function (err) {
            console.error('sonarr_notify error: ', err);
            toastr.error("Error notfying sonarr of this announcement??");
        });  
}