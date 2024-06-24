$(document).ready(function() {
    var socket = io();

   var dropZone = $('#drop_zone');

    dropZone.on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.addClass('dragover');
    });

    dropZone.on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.removeClass('dragover');
    });

    dropZone.on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.removeClass('dragover');

        var files = e.originalEvent.dataTransfer.files;
        handleFiles(files);
    });

    dropZone.on('click', function() {
        $('#fileInput').click();
    });

    $('#fileInput').change(function() {
        var files = this.files;
        handleFiles(files);
    });

    function handleFiles(files) {
        var formData = new FormData();
        formData.append('file', files[0]);

        var uploadUrl = '/fupload';

        if (files[0].type.match('image.*')) {
            uploadUrl = '/iupload';
        }

        $.ajax({
            url: uploadUrl,
            type: 'POST',
            data: formData,
            contentType: false,
            cache: false,
            processData: false,
            success: function(data) {
                if (data.success) {
                    alert(data.success);
                    if (uploadUrl === '/iupload') {
                        var imagePath = '/static/uploads/' + data.filename;
                        var currentContent = $("#output").html();
                        var ftout = '<img src="' + imagePath + '" alt="Uploaded Image" style="max-width: 100%;">';
                        $("#output").html(currentContent + ftout);
                    }
                } else if (data.error) {
                    alert(data.error);
                }
            },
            error: function() {
                alert('Échec du téléchargement du fichier.');
            }
        });
    }
       socket.on('update_select', function(data) {
        var $select = $('#info-select');
        $select.empty();  // Empty all existing options

        // Loop through each received option and add them to the select
        $.each(data.options, function(index, value) {
            $select.append($('<option></option>').attr('value', value).text(value));
        });
    });

       socket.on('set_select', function(data) {
        $('#info-select').val(data.model);  // Set the select element to the specified model
        });

    $('#info-select').change(function() {
        var selectedOption = $(this).val();
        socket.emit('select_change', { option: selectedOption });  // Envoyer l'option sélectionnée au serveur
    });

    
    socket.on('connect', function() {
        socket.emit('maj_info'); // Demander les infos système à la connexion
        socket.emit('get_config'); // Demander les infos système à la connexion
    });

    socket.on('update_system_info', function(data) {
        $('#system-info').html(data.system_info);
    });

   socket.on('history', function(sessions) {
    $('#history').empty();
    for (var i = 0; i < sessions.length; i++) {
        var session = sessions[i];
        console.log(session.data);
        // Assurez-vous que session.data[0] et session.data[0].content existent
        if (session.data.length > 0 && session.data[0].content) {
            var contentPreview = session.data[0].content.substring(0, 10);
            var sessionDiv = $('<div class="session d-flex justify-content-between align-items-center" data-id="' + session.session_id + '">' +
                '<span>' + contentPreview + '</span>' +
                 '<i  title="Drop"><span class="delete-icon bi bi-trash"></span></i>' +
                '</div>');

            // Ajout d'un gestionnaire d'événement pour la suppression
            sessionDiv.find('.delete-icon').on('click', function() {
                var sessionId = $(this).parent().parent().data('id');
                // Émettre un événement pour supprimer la session
                socket.emit('delete_session', { session_id: sessionId });
                // Supprimer la ligne de l'historique
                $(this).parent().parent().remove();
            });

            $('#history').append(sessionDiv);
        }
    }
});

    
  socket.on('session', function(session) {
    // Convertir l'objet de session en une chaîne HTML et l'afficher dans le div
    var sessionHtml = '';
    
    session.forEach(function(entry) {
        out=entry.content.replace(/\n/g, "<br>")
        if (entry.role === "user") {
            sessionHtml += '<BR><span style="color:blue"><b>'+out+'</b></span><BR>'
        } else if (entry.role === "assistant") {
            sessionHtml += '<strong>Assistant:</strong> ' + out  + '<BR>';
        }
    });

    sessionHtml += '';
    console.log(sessionHtml);
    $('#output').html(sessionHtml);
});

    $('#history').on('click', '.session', function() {
        
        var session_id = $(this).data('id');
        socket.emit('load_session', {session_id: session_id});
    });

    $('#delete_session').on('click', function() {
        var session_id = $(this).data('id');//onfigIcon
        socket.emit('delete_session', {session_id: session_id});
    });

     socket.on('session_deleted', function(data) {
        if (data.status === 'success') {
            console.log('Session ' + data.session_id + ' deleted successfully.');
        } else if (data.status === 'file_not_found') {
            console.log('File not found for session ' + data.session_id + '.');
        } else {
            console.log('Error deleting session ' + data.session_id + ': ' + data.message);
        }
    });
    socket.on('error', function(error) {
        alert(error.message);
    });

    socket.on('auto_info', function(data) {
        $('#system-info').html(data.data)
    });

     socket.on('clean_output', function() {
        $('#output').html('')
    });
    
    $('#send-button').click(function() {
        var msg = $("#message-textarea").val();
        var tag=$("#tag").val();
        if(msg=='')
         {
             alert("What?");
             return false;
         }
    socket.emit('send_message', {message: msg, tag: tag});
    var currentContent = $("#output").html();        
    let ftout = msg.replace(/\n/g, "<br>");
    var newContent='<BR><span style="color:blue"><b>'+ftout+'</b></span><BR>';
    $("#output").html(currentContent + newContent);
    $("#message-textarea").val("");
     var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
    });

     $("#send-formatted").on('click', function() {

     var msg = $("#message-textarea").val();
        if(msg=='')
         {
             alert("What?");
             return false;
         }
    socket.emit('send_fmessage', {message: msg});
    var currentContent = $("#output").html();        
    let ftout = msg.replace(/\n/g, "<br>");
    var newContent='<BR><span style="color:blue"><b>'+ftout+'</b></span><BR>';
    $("#output").html(currentContent + newContent);
    $("#message-textarea").val("");
    var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
    });
   
      socket.on('get_tag', function() {
            var tag = document.getElementById('tag').value;
            socket.emit('response_tag', { tag: tag });
        });
    


     $('#interllm').click(function() {
         var msg = $("#message-textarea").val();
         if(msg=='')
         {
             alert("What?");
             return false;
         }
        socket.emit('interllm', {message: msg});  

         var currentContent = $("#output").html();        
    let ftout = msg.replace(/\n/g, "<br>");
    var newContent='<BR><span style="color:blue"><b>'+ftout+'</b></span><BR>';
    $("#output").html(currentContent + newContent);
    $("#message-textarea").val("");
     var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
    });


    $('#imagequestion').click(function() {
         var msg = $("#message-textarea").val();
         if(msg=='')
         {
             alert("What?");
             return false;
         }
        socket.emit('imagequestion', {message: msg});  

         var currentContent = $("#output").html();        
    let ftout = msg.replace(/\n/g, "<br>");
    var newContent='<BR><span style="color:blue"><b>'+ftout+'</b></span><BR>';
    $("#output").html(currentContent + newContent);
    $("#message-textarea").val("");
        var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
         
    });


    socket.on('response_token', function(data) {       
    var currentContent = $("#output").html();
    var tout=data.token;
    let ftout = tout.replace(/\n/g, "<br>");
    $("#output").html(currentContent + ftout);
    var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
   });

    socket.on('audio_token', function(data) {       
    var currentContent = $("#message-textarea").html();
    var tout=data.token;
    let ftout = tout.replace(/\n/g, "<br>");
    $("#message-textarea").html(currentContent + ftout);
    var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
   });


    
    socket.on('typewriter_log', function(data) {
    var tout=data.message;
    var currentContent = $("#output").html();
    let ftout = tout.replace(/\n/g, "<br>");
    if(tout=='\n')
        tout='<br>';
    $("#output").html(currentContent + "<div style='color:red'>"+ ftout +"</div>");
    var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
   });


    
    socket.on('say_text', function(data) { 
      
    var currentContent = $("#output").html();
    var tout=data.message;
    let ftout = tout.replace(/\n/g, "<br>");
    $("#output").html(currentContent + "<div style='color:green'>"+ ftout +"</div>");
    var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
   });

    $('#output').on('click', '#installphi3', function() {
        socket.emit('pull_model')
    });

     $('#output').on('click', '#installffmpeg', function() {
        socket.emit('pull_ffmpeg')
    });
   
    socket.on('display_file', function(data) { 
   var currentContent = $("#output").html();
    var tout=data.message;
    alert(tout);

    $("#output").html(currentContent + tout);
    var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
   });

    socket.on('popup', function(data) {  

    $("#popuptext").html(data.message);
    $("#myModal").show();
     });
    
    socket.on('get_config', function(data) {  
      // Vérifiez la valeur de continuous_mode reçue
    if (data['continuous_mode'] == true) {
        // Si True, cochez le bouton radio True
        $('#continuousmodeTrue').prop('checked', true);
    } else  {
        // Sinon, cochez le bouton radio False
        $('#continuousmodeFalse').prop('checked', true);
    }
    // Vérifiez la valeur de continuous_mode reçue
    if (data['speak_mode'] == true) {
        
        // Si True, cochez le bouton radio True
        $('#speakmodeTrue').prop('checked', true);
    } else {
        // Sinon, cochez le bouton radio False
        $('#speakmodeFalse').prop('checked', true);
    }
   });

    

    $('#stop-button').click(function() {
    socket.emit('stop_generation');
    });

    $('#new_llm').click(function() {
     $('#engine').html('(llm)');
     socket.emit('new_llm');
    });
    $('#new_agent').click(function() {
        $('#engine').html('(agent)');
     socket.emit('new_agent');
    });
    $('#new_image').click(function() {
        $('#engine').html('(image)');
     socket.emit('new_image');
    });
    $('#new_document').click(function() {
        $('#engine').html('(doc)');
     socket.emit('new_document');
    });
        
   // Fermer la modale
  $(".close, #no, #cancel").click(function(){
    $("#myModal").hide();
  });

    

  // Gérer le clic sur "Oui"
  $("#yes").click(function(){
    // Logic for "Yes" goes here
    $("#myModal").hide();
    console.log("L'utilisateur a cliqué sur Oui");
    socket.emit('popup', {message: "yes"}); 
  });

    

  // Gérer le clic sur "Non"
  $("#no").click(function(){
    // Logic for "No" goes here
    $("#myModal").hide();
    console.log("L'utilisateur a cliqué sur Non");
      socket.emit('popup', {message: "no"}); 
  });

    

  // Gérer le clic sur "Annuler"
  $("#feed").click(function(){
    // Logic for "Cancel" goes here
    $("#myModal").hide();
      var feed= $("#feedin").val()
      console.log("L'utilisateur a feed back");
      socket.emit('popup', {message: "feed", feed : feed }); 
  });



    

    // Lorsque l'utilisateur clique sur l'icône de configuration
    $("#configIcon").click(function() {

        $("#configModal").show(); // Affiche le modal
    });

    // Lorsque l'utilisateur clique sur le bouton de fermeture (x)
    $(".closeConfig").click(function() {
        $("#configModal").hide(); // Cache le modal
    });

    // Lorsque l'utilisateur clique en dehors du modal, cela le ferme aussi
    $(window).click(function(event) {
        if ($(event.target).is("#configModal")) {
            $("#configModal").hide();
        }
    });

    // Gestion des boutons OK et Cancel
    $("#okBtn").click(function() {
        // Logique à exécuter lorsque OK est cliqué
        socket.emit('set_config', 
                    {
                        speakmode: $('#speakmodeTrue').prop('checked'), 
                        continuousmode : $('#continuousmodeTrue').prop('checked'),
                        openaikey: $('#openaikey').val(),
                        groqkey: $('#groqkey').val()}); 
        $("#configModal").hide();
    });


    
    $("#cancelBtn").click(function() {
        // Logique à exécuter lorsque Cancel est cliqué
        $("#configModal").hide();
    });

    
    $('#textFileBtn').click(function() {
    window.open('/get-text-file', '_blank');
  });

var mediaRecorder;
var audioChunks = [];
var isRecording = false; // Ajout d'un contrôle d'état pour l'enregistrement

function startRecording(stream) {
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    isRecording = true;

    mediaRecorder.ondataavailable = function(event) {
        if (event.data.size > 0) {
            event.data.arrayBuffer().then(arrayBuffer => {
                socket.emit('audio', arrayBuffer);
            });
        }
    };

    // Arrête l'enregistrement après 1 seconde, puis le redémarre
    setTimeout(function() {
        if (isRecording) {
            mediaRecorder.stop(); // Arrête l'enregistrement
            mediaRecorder.start(); // Redémarre immédiatement l'enregistrement pour la prochaine tranche d'1 seconde
            startRecording(stream); // Appel récursif pour continuer le processus
        }
    }, 3000); // 1000 millisecondes = 1 seconde
}

if (navigator.mediaDevices === undefined) {
  navigator.mediaDevices = {};
  navigator.mediaDevices.getUserMedia = function(constraints) {
    // Use old syntax for older browsers
    var getUserMedia = navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
    if (!getUserMedia) {
      return Promise.reject(new Error('getUserMedia is not implemented in this browser'));
    }
    return new Promise(function(resolve, reject) {
      getUserMedia.call(navigator, constraints, resolve, reject);
    });
  }
}
    
$("#startRecord").on('click', function() {

    var $iconSpan = $(this).find('span');
    if ($iconSpan.hasClass('bi-mic-mute-fill')) {
            $iconSpan.removeClass('bi-mic-mute-fill').addClass('bi-mic-fill');

            navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
            startRecording(stream);
            // send message to app
             socket.emit('startrecord')    
           })
           .catch(error => console.log(error));
            
        } else {
            $iconSpan.removeClass('bi-mic-fill').addClass('bi-mic-mute-fill');

            if (mediaRecorder && mediaRecorder.state !== "inactive") {
             mediaRecorder.stop(); // Arrête l'enregistrement
            }
            isRecording = false; // Met à jour le contrôle d'état pour arrêter la boucle d'enregistrement
        } 
    
    
});


    // Lorsque le bouton est cliqué, déclenchez le clic sur l'input de fichier caché
    $("#imageupload").click(function() {
        $("#imageInput").click();
    });




    $("#uploaddiv").click(function() {
        $("#uploadmodal").show(); // Affiche le modal
    });

    // Fonction pour gérer les fichiers déposés
    function handleFileSelect(evt) {
        evt.stopPropagation();
        evt.preventDefault();
        var files = evt.originalEvent.dataTransfer.files;
       $("#fileInput").prop("files", files);
        console.log("Dropped files:", files);
    }

   
    // Fermer le modal
    $('.close').click(function() {
        $('#uploadmodal').hide();
    });

 // Load configuration data from the server
    $.getJSON('/get_config', function(config) {
        $('input[name="continuousmode"][value="' + config.continuous_mode + '"]').prop('checked', true);
        $('input[name="speakmode"][value="' + config.speak_mode + '"]').prop('checked', true);

        if (config.openaikey) {
            $('#openaikey').val(config.openaikey);
        }
        if (config.groqkey) {
            $('#groqkey').val(config.groqkey);
        }
        if (config.openai_organisation) {
            $('#openaiorganisation').val(config.openai_organisation);
        }
        if (config.openai_project) {
            $('#openaiproject').val(config.openai_project);
        }
        if (config.api_endpoint) {
            $('#apiendpoint').val(config.api_endpoint);
        }
        if (config.api_chat_endpoint) {
            $('#chatapiendpoint').val(config.api_chat_endpoint);
        }
        if (config.embedding_endpoint) {
            $('#embedapiendpoint').val(config.embedding_endpoint);
        }
        if (config.openai_mode) {
            $('#openaimodel').val(config.openai_mode);
        }
        if (config.groq_model) {
            $('#groqmodel').val(config.groq_model);
        }
    });

    $('#okBtn').on('click', function() {
        var data = {
            continuousmode: $('input[name="continuousmode"]:checked').val(),
            speakmode: $('input[name="speakmode"]:checked').val(),
            openaikey: $('#openaikey').val(),
            groqkey: $('#groqkey').val(),
            openaiorganisation: $('#openaiorganisation').val(),
            openaiproject: $('#openaiproject').val(),
            apiendpoint: $('#apiendpoint').val(),
            chatapiendpoint: $('#chatapiendpoint').val(),
            embedapiendpoint: $('#embedapiendpoint').val(),
            openaimodel: $('#openaimodel').val(),
            groqmodel: $('#groqmodel').val()
        };
        socket.emit('set_config', data);
    });

    $('#cancelBtn').on('click', function() {
        // Logic to close the modal
        $('#configModal').hide();
    });
    $('#okBtn2').on('click', function() {
        url=$("#urlid").val()
        scrabbing=$('input[name="Scrabbing"]:checked').val();
        tag=$("#tag").val()
        socket.emit('digest_url', {url: url , scrabbing : scrabbing, tag: tag }); 
    });   
    socket.on('config_updated', function(data) {
        if (data.status === 'success') {
            alert('Configuration updated successfully');
            // Optionally, close the modal or perform other actions
            $('#configModal').hide();
        }
    });

    // Lorsqu'un fichier est sélectionné, effectuez l'upload

    // Lorsqu'un fichier est sélectionné, effectuez l'upload
$("#fileInput").change(function() {
    var file = $('#fileInput')[0].files[0];
    if (!file) {
        alert('Veuillez sélectionner un fichier.');
        return;
    }

    var formData = new FormData();
    formData.append('file', file);

    var uploadUrl = '/fupload'; // URL par défaut pour les fichiers

    // Vérifiez si le fichier est une image
    if (file.type.match('image.*')) {
        uploadUrl = '/iupload'; // URL pour les images
    }

    $.ajax({
        url: uploadUrl,
        type: 'POST',
        data: formData,
        contentType: false,
        cache: false,
        processData: false,
        success: function(data){
            if (data.success) {
                alert(data.success);
                if (uploadUrl === '/iupload') {
                    var imagePath = '/static/uploads/' + data.filename; // Assurez-vous que ce chemin est correct
                    var currentContent = $("#output").html();        
                    var ftout = '<img src="' + imagePath + '" alt="Uploaded Image" style="max-width: 100%;">'
                    $("#output").html(currentContent + ftout);
                }
            } else if (data.error) {
                alert(data.error);
            }
        },
        error: function(){
            alert('Échec du téléchargement du fichier.');
        }
    });
});

   

    $("#imageInput").change(function() {
        var formData = new FormData();
        formData.append('file', $('#imageInput')[0].files[0]);

        $.ajax({
            url: '/iupload',
            type: 'POST',
            data: formData,
            contentType: false,
            cache: false,
            processData: false,
            success: function(data){
                if (data.success) {
                    alert(data.success);
                    var imagePath = '/static/uploads/' + data.filename; // Assurez-vous que ce chemin est correct
                    // $('#imageOutput').html('<img src="' + imagePath + '" alt="Uploaded Image" style="max-width: 100%;">');
                    var currentContent = $("#output").html();        
                    let ftout = '<img src="' + imagePath + '" alt="Uploaded Image" style="max-width: 100%;">'
                    // var newContent='<BR><span style="color:blue"><b>'+ftout+'</b></span><BR>';
                    $("#output").html(currentContent + ftout);
                } else if (data.error) {
                    alert(data.error);
                }
            },
            error: function(){
                alert('Échec du téléchargement du fichier.');
            }
        });
    });


    $('input[type=radio][name=llmconnect]').change(function() {
                var selectedValue = $(this).val();
                console.log('Selected value: ' + selectedValue);

                // Perform actions based on the selected value
                if (selectedValue === 'openai') {
                    // Action for OpenAI
                    // alert('OpenAI selected');

                    socket.emit('connect_llm', {api : "openai" }); 
                } else if (selectedValue === 'groq') {
                    // Action for Groq
                   //  alert('Groq selected');
                    socket.emit('connect_llm', {api : "groq" }); 
                } else if (selectedValue === 'local') {
                    // Action for Local
                   //  alert('Local selected');
                    socket.emit('connect_llm', {api : "local" }); 
                }
            });

});

