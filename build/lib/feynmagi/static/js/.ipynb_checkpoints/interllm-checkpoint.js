$(document).ready(function() {
    var socket = io();
    
    socket.on('connect', function() {
        socket.emit('maj_info'); // Demander les infos système à la connexion
    });

    socket.on('update_system_info', function(data) {
        $('#system-info').html(data.system_info);
    });

    // Autres interactions avec SocketIO ici...

    $('#send-button').click(function() {
    var msg = $("#message-textarea").val();
    socket.emit('send_message', {message: msg});
    var currentContent = $("#output").html();
    var newContent='<BR><span style="color:blue"><b>'+msg+'</b></span><BR>';
    $("#output").html(currentContent + newContent);
    $("#message-textarea").val("");
    });

    socket.on('response_token', function(data) {
       
    var currentContent = $("#output").html();
    $("#output").html(currentContent + data.token);
   });

    $('#stop-button').click(function() {
    socket.emit('stop_generation');
    });


   
});

