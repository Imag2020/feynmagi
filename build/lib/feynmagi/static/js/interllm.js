$(document).ready(function() {

     $('#stop-button').hide();
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
        socket.emit('get_agents'); // Demander les infos système à la connexion
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
     $(this).hide(); // Cache le bouton send
     $('#stop-button').show(); // Montre le bouton stop
    var msg = $("#message-textarea").val();
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
         $(this).hide(); // Cache le bouton send
     $('#stop-button').show(); // Montre le bouton stop
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
        $(this).hide(); // Cache le bouton send
     $('#stop-button').show(); // Montre le bouton stop
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
    // Accumuler le contenu dans un div spécifique
    var ftout = data.token.replace(/\n/g, "<br>");
    $("#output").append(ftout);

    // S'assurer que le contenu est traité après un bref délai
    setTimeout(function() {
        processContent();
    }, 0);

    var divHeight = $('#output').prop('scrollHeight');
    $('#output').scrollTop(divHeight);
});

    socket.on('end_message', function(data) {
     $('#send-button').show(); // Montre le bouton send
     $('#stop-button').hide(); // Montre le bouton stop
});


function processContent() {
    // Parcourir le contenu de #output
    var html = $("#output").html();

    // Traiter les équations Markdown avec KaTeX
  html = html.replace(/```(\w+)\n([\s\S]*?)```/g, function(match, lang, code) {
    // Clean up `<br>` tags inside the code
    var cleanedCode = code.replace(/<br>/g, '\n');

    // Check if the block is meant for code or just Markdown
    if (lang.toLowerCase() === 'markdown') {
        // Render using a Markdown renderer if it's meant to be Markdown
        return new marked.Marked().parse(cleanedCode);
    } else {
        // Otherwise render as code block
        try {
            var markedInstance = new marked.Marked();
            var renderedCode = markedInstance.parse('```' + lang + '\n' + cleanedCode.trim() + '\n```');
             console.error('rendering markdown');
            return `
                <div class="code-container" style="background-color: black; padding: 20px; border-radius: 5px; margin-top: 20px;">
                    <div class="code-header" style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 5px; border-bottom: 1px solid grey; margin-bottom: 10px;">
                        <span class="code-type" style="color: yellow;">${lang.toUpperCase()} Code</span>
                        <button class="copy-button" style="background-color: white; color: black; border: none; padding: 10px; cursor: pointer;">Copy</button>
                    </div>
                    <pre class="code-block" style="background-color: #333; color: white; overflow-x: auto;">${renderedCode}</pre>
                </div>`;
        } catch (e) {
            console.error('Markdown rendering error:', e);
            return match;  // Return original text in case of an error
        }
    }
});

    // Traiter tous les blocs de code indiqués par les triple backticks
    html = html.replace(/```([\w\W]*?)```/g, function(match, code) {
        try {
            // Clean up `<br>` tags inside the code
            var cleanedCode = code.replace(/<br>/g, '\n');
            
            // Determine the language from the first line (if specified)
            var firstNewLine = cleanedCode.indexOf('\n');
            var firstLine = cleanedCode.substr(0, firstNewLine);
            var language = firstLine.match(/^[a-z]+$/i) ? firstLine : 'plaintext';
            cleanedCode = firstNewLine > -1 ? cleanedCode.substr(firstNewLine + 1) : cleanedCode;

            // Create a Marked instance to parse the code
            var markedInstance = new marked.Marked();
            var renderedCode = markedInstance.parse('```' + language + '\n' + cleanedCode.trim() + '\n```');
             console.error('rendering code');
            // Returning the enhanced HTML structure
            return `
                <div class="code-container" style="background-color: black; padding: 20px; border-radius: 5px; margin-top: 20px;">
                    <div class="code-header" style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 5px; border-bottom: 1px solid grey; margin-bottom: 10px;">
                        <span class="code-type" style="color: yellow;">${language.toUpperCase()} Code</span>
                        <button class="copy-button" style="background-color: white; color: black; border: none; padding: 10px; cursor: pointer;">Copy</button>
                    </div>
                    <pre class="code-block" style="background-color: #333; color: white; overflow-x: auto;">${renderedCode}</pre>
                </div>`;
        } catch (e) {
            console.error('Markdown rendering error:', e);
            return match;  // Return original text in case of an error
        }
    });

    // Mettre à jour le HTML de #output avec le contenu traité
    $("#output").html(html);

  $(document).on('click', '.copy-button', function() {
    var codeBlock = $(this).closest('.code-container').find('.code-block').text();

    if (navigator.clipboard && window.isSecureContext) {
        // If the Clipboard API is available and the context is secure, use it
        navigator.clipboard.writeText(codeBlock).then(function() {
            console.log('Copying to clipboard was successful!');
        }, function(err) {
            console.error('Could not copy text:', err);
        });
    } else {
        // Fallback: Copy text using a temporary textarea
        var textArea = document.createElement("textarea");
        textArea.value = codeBlock;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            var successful = document.execCommand('copy');
            var msg = successful ? 'successful' : 'unsuccessful';
            console.log('Fallback: Copying text command was ' + msg);
        } catch (err) {
            console.error('Fallback: Could not copy text:', err);
        }
        document.body.removeChild(textArea);
    }
});


    
}




    

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
        $(this).hide(); // Cache le bouton stop
        $('#send-button').show(); // Montre le bouton send
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

    // --------------------------------    Video
    
        let isRecording = false;
        const video = document.getElementById('videoStream');
        const captureCanvas = document.getElementById('captureCanvas');
        const contextCapture = captureCanvas.getContext('2d');
       
        let popupWindow = null;

        function openPopup() {
            popupWindow = window.open("", "Popup", "width=640,height=480");
            if (popupWindow) {
                popupWindow.document.write('<html><head><title>Processed Video</title></head><body><canvas id="popupCanvas" width="640" height="480"></canvas></body></html>');
                popupWindow.document.close();
            }
        }

        function captureFrame() {
            if (!isRecording) return;
            contextCapture.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
            captureCanvas.toBlob(blob => {
                const reader = new FileReader();
                reader.onload = function() {
                    const arrayBuffer = reader.result;
                    socket.emit('video', arrayBuffer);
                };
                reader.readAsArrayBuffer(blob);
            }, 'image/jpeg');
            requestAnimationFrame(captureFrame); // Capture frame at every animation frame
        }

        if (navigator.mediaDevices === undefined) {
            navigator.mediaDevices = {};
        }

        if (navigator.mediaDevices.getUserMedia === undefined) {
            navigator.mediaDevices.getUserMedia = function(constraints) {
                var getUserMedia = navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
                if (!getUserMedia) {
                    return Promise.reject(new Error('getUserMedia is not implemented in this browser'));
                }
                return new Promise(function(resolve, reject) {
                    getUserMedia.call(navigator, constraints, resolve, reject);
                });
            };
        }

        $("#startCamera").on('click', function() {
            var $iconSpan = $(this).find('span');
            if (!isRecording) {
                 
                $iconSpan.removeClass('bi-camera-video-off-fill').addClass('bi-camera-video-fill');
                navigator.mediaDevices.getUserMedia({ video: true, audio: true })
                .then(stream => {
                    openPopup();
                    video.srcObject = stream;
                    isRecording = true;
                    captureFrame();
                    socket.emit('startrecord');
                })
                .catch(error => console.log(error));
            } else {
                
                $iconSpan.removeClass('bi-camera-video-fill').addClass('bi-camera-video-off-fill');
                isRecording = true;
                if (video.srcObject) {
                    const tracks = video.srcObject.getTracks();
                    tracks.forEach(track => track.stop());
                    video.srcObject = null;
                }
                if (popupWindow) {
                    popupWindow.close();
                    popupWindow = null;
                }
            }
        });

        socket.on('processed_frame', function(data) {
            if (popupWindow) {
                const popupCanvas = popupWindow.document.getElementById('popupCanvas');
                if (popupCanvas) {
                    const contextPopup = popupCanvas.getContext('2d');
                    const image = new Image();
                    image.onload = function() {
                        contextPopup.drawImage(image, 0, 0, popupCanvas.width, popupCanvas.height);
                    };
                    image.src = 'data:image/jpeg;base64,' + data.frame;
                }
            }
        });

    // Gestionnaire d'événements pour le retour de l'agent
socket.on('output_agent', function(data) {
    // Convertit Markdown en HTML si nécessaire
    var converter = new showdown.Converter();
    var htmlContent = converter.makeHtml(data.token);

    // Vérifie si la fenêtre popup est déjà ouverte
    if (popupWindow && !popupWindow.closed) {
        // La fenêtre popup existe déjà, affiche le contenu reçu
        popupWindow.document.body.insertAdjacentHTML('beforeend', "<p>" + htmlContent + "</p>");
    } else {
        // La fenêtre popup n'existe pas, il faut la créer
        popupWindow = window.open("", "Popup", "width=800,height=600");
        popupWindow.document.write("<html><head><title>Agent Output</title></head><body><p>" + htmlContent + "</p></body></html>");
        popupWindow.document.close(); // Termine l'écriture dans le document
    }
});




    // -----------------------------------------------------------------

   var mediaRecorder;
   var audioChunks = [];
   let isAudioRecording = false;

function startRecording(stream) {
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    isAudioRecording = true;

    mediaRecorder.ondataavailable = function(event) {
        if (event.data.size > 0) {
            event.data.arrayBuffer().then(arrayBuffer => {
                socket.emit('audio', arrayBuffer);
            });
        }
    };

    // Arrête l'enregistrement après 1 seconde, puis le redémarre
    setTimeout(function() {
        if (isAudioRecording) {
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
    if (!isAudioRecording) {
            
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
            isAudioRecording = false; // Met à jour le contrôle d'état pour arrêter la boucle d'enregistrement
        } 
    
    
});




    // 

    
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



    // modal agents

   
     $('#agentManager').modal({
        show: false,
        backdrop: 'static',  // empêche la fermeture en cliquant en dehors du modal
        keyboard: false  // empêche la fermeture avec la touche ESC
    });

    $('#agentConfigModal').modal({
        show: false,
        backdrop: 'static',
        keyboard: false
    });

    // Initialisations des modaux
    $('#agentManager, #agentConfigModal').modal({
        show: false
    });

    // Gestionnaires pour ouvrir le modal principal
    $('#agentManager').modal({
        backdrop: 'static', // empêche de fermer en cliquant à l'extérieur
        keyboard: false, // empêche la fermeture avec la touche ESC
        show: false // n'affiche pas le modal automatiquement
    });
    
    $("#openModal").click(function() {
       
        $("#agentManager").modal('show');
    });

    // Gestionnaires pour fermer les modaux
    $(".close").click(function() {
        // Assurez-vous que c'est le bon modal qui est fermé
        var modalId = $(this).closest('.modal').attr('id');
        $("#" + modalId).modal('hide');
    });

    $("#newAgent").click(function(event) {
        

    // Générer un nouvel ID pour le nouvel agent, basé sur le nombre actuel d'agents
    var newAgentId = $(".card").length ; // Cela suppose que chaque carte ajoutée représente un nouvel agent
    let new_agent={'name': 'Agent '+newAgentId, 'schedule': ['Daily'], 'when': '22:15', 'system': "", 'prompt': '', 'tools': ['calculate']}
    agentsData.push(new_agent);
    // alert(JSON.stringify(agentsData, null, 2));
    // Créer la structure HTML de la carte pour le nouvel agent
    var newCardHtml = `
                    <div class="card" style="width: 18rem;" data-toggle="modal" data-target="#agentConfigModal" data-index="${newAgentId}">
                        <div class="card-body">
                        <span><button class="btn-close float-right" title="Del" data-index="${newAgentId}"><span class="bi bi-trash"></span></button></span>
                        <h5 class="card-title">Agent ${newAgentId}</h5>
                        <p class="card-text">Description de l'agent ${newAgentId}.</p>
                        </div>
                        </div>
                            `;
       // Ajouter la nouvelle carte au modal-body
       $("#agentManager .modal-body").append(newCardHtml);
      
});

 
    // Lorsque l'on revient au modal principal après fermeture du modal enfant
    $('#agentConfigModal').on('hidden.bs.modal', function() {
    
        $('#agentManager').modal('show');
    });
    

    $("#saveAgent").click(function() {
   
    var agentData = {
        name: $("#agentName").val(),
        schedule: $("input[name='scheduler']:checked").map(function() { return $(this).val(); }).get(),
        when: $("#timeExecution").val(),
        system: $("#systemPrompt").val(),
        prompt: $("#mainPrompt").val(),
        tools: $("input[name='tools']:checked").map(function() { return $(this).val(); }).get()
    };

    socket.emit('add_agent', agentData);
   });

    // Annuler et fermer le modal
    $("#cancelBtn").click(function(){
        $("#agentConfigModal").hide();
    });


   // -----------------------------
     var agentsData = [];  // Store the agents data here

     socket.on('update_agents', function(data) {
        agentsData = data;  // Update the global variable with new data
         // alert(JSON.stringify(agentsData, null, 2));
        $('#agentManager .modal-body').empty(); // Clear the existing cards
        data.forEach(function(agent,index) {
            var newCardHtml = `
            <div class="card" style="width: 18rem;" data-toggle="modal" data-target="#agentConfigModal" data-index="${index}">
                <div class="card-body">
                    <span><button class="btn-close float-right" title="Del" data-index="${index}"><span style="width:10px;wigth:10px"class="bi bi-trash"></span></button></span>
                    <h5 class="card-title">Agent ${agent.name}</h5>
                    <p class="card-text">Description de l'agent ${agent.name}.</p>
                </div>
            </div>
        `;

                        // Ajouter la nouvelle carte au modal-body
                        $("#agentManager .modal-body").append(newCardHtml);                 
        });  
    });  
    

   var availableTools = [];

socket.on('update_tools', function(data) {
    availableTools = Object.keys(data); // Stocke seulement les clés
    $('#toolslist').empty(); // Vide la liste existante
    availableTools.forEach(function(tool) {
        var description = data[tool]; // Accède à la description ou autre détail
        var toolLabel = `<label><input type="checkbox" name="tools" value="${tool}"> ${tool} - ${description}</label>`;
        $("#toolslist").append(toolLabel);
    });
});

   
        

       // Déplacer le gestionnaire d'événements hors de la socket.on pour éviter de le réattacher
$("#agentManager .modal-body").on("click", ".card", function() {
    var index = $(this).data('index');
   
    var agent = agentsData[index];
   
    loadAgentDetails(agent);
    $('#agentModal').modal('show');
    });

         $("#agentManager .modal-body").on("click", ".btn-close", function(event) {
    event.stopPropagation();  // Stop propagation to prevent opening the modal
    var index = $(this).data('index');
    agent_to_drop=agentsData[index];
             alert("dropping "+agent_to_drop.name);
    socket.emit('remove_agent', agent_to_drop);
    agentsData.splice(index, 1);  // Remove the agent from the array
    $(this).closest('.card').remove();  // Remove the card from the DOM
    });

        // });
function loadAgentDetails(agent) {
    // Générer les cases à cocher pour les outils en utilisant availableTools
    var toolsHtml = availableTools.map(tool => {
        return `<label><input type="checkbox" name="tools" value="${tool}" ${agent.tools.includes(tool) ? "checked" : ""}> ${tool}</label>`;
    }).join('');

    var detailsHtml = `
        <div id="agentDetails" class="modal-body row">
            <div class="col-md-8">
                <div class="form-group">
                    <label for="agentName">Name</label>
                    <input type="text" id="agentName" name="agentName" class="form-control" value="${agent.name}">
                </div>
                <div class="form-group">
                    <label>Planification:</label>
                    <div class="checkbox">
                        <label><input type="radio" id="daily" name="scheduler" value="Daily" ${agent.schedule.includes("Daily") ? "checked" : ""}> Daily</label>
                        <label><input type="radio" id="weekly" name="scheduler" value="Weekly" ${agent.schedule.includes("Weekly") ? "checked" : ""}> Weekly</label>
                        <label><input type="radio" id="monthly" name="scheduler" value="Monthly" ${agent.schedule.includes("Monthly") ? "checked" : ""}> Monthly</label>
                    </div>
                    <label for="timeExecution">When:</label>
                    <input type="time" id="timeExecution" name="timeExecution" class="form-control" value="${agent.when}">
                </div>
                <div class="form-group">
                    <label>System (optional)</label>
                    <textarea id="systemPrompt" name="systemPrompt" class="form-control">${agent.system}</textarea>
                </div>
                <div class="form-group">
                    <label for="mainPrompt">Prompt</label>
                    <textarea id="mainPrompt" name="mainPrompt" class="form-control">${agent.prompt}</textarea>
                </div>
            </div>
            <div class="col-md-4">
                <label>Tools</label>
                <div class="checkbox">${toolsHtml}</div>
            </div>
        </div>
    `;
    $('#agentDetails').html(detailsHtml);
}


    
    $("#playAgent").click(function(){
    // Récupération des valeurs des champs
    var name = $("#agentName").val();         // Récupère la valeur de l'input du nom de l'agent
    var system = $("#systemPrompt").val();    // Récupère le texte de la zone de texte "System"
    var prompt = $("#mainPrompt").val();      // Récupère le texte de la zone de texte "Prompt"

    // Construction de l'objet data avec les valeurs récupérées
    var data = {
        name: name,
        system: system,
        prompt: prompt
    };

    // Envoi de l'objet data au serveur via socket
    socket.emit('play_agent', data);
   });
        
    

});