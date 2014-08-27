var holder = document.getElementById('upload'),
content = document.getElementById('content'),
crop_dialog = document.getElementById('img-crop'),
tests = {
    filereader: typeof FileReader != 'undefined',
    dnd: 'draggable' in document.createElement('span'),
    formdata: !!window.FormData,
    progress: "upload" in new XMLHttpRequest
},
support = {
    filereader: document.getElementById('filereader'),
    formdata: document.getElementById('formdata'),
    progress: document.getElementById('progress')
},
acceptedTypes = {
    'image/png': true,
    'image/jpeg': true,
    'image/gif': true
},
progress = document.getElementById('uploadprogress'),
fileupload = document.getElementById('upload');

"filereader formdata progress".split(' ').forEach(function (api) {
    if (tests[api] === false) {
        support[api].className = 'fail';
    } else {
        // FFS. I could have done el.hidden = true, but IE doesn't support
        // hidden, so I tried to create a polyfill that would extend the
        // Element.prototype, but then IE10 doesn't even give me access
        // to the Element object. Brilliant.
        support[api].className = 'hidden';
    }
});

function previewfile(file) {
    /*if (tests.filereader === true && acceptedTypes[file.type] === true) {
        var reader = new FileReader();
        reader.onload = function (event) {
            var image = new Image();
            image.src = event.target.result;
            $(image).addClass("full-width");
            crop_dialog.appendChild(image);
            $(crop_dialog).removeClass('hidden');
            $(image).Jcrop();
        };

        reader.readAsDataURL(file);
    }  else {
        holder.innerHTML += '<p>Uploaded ' + file.name + ' ' + (file.size ? (file.size/1024|0) + 'K' : '');
        console.log(file);
    }*/
}

function readfiles(files) {
    var formData = tests.formdata ? new FormData() : null;
    for (var i = 0; i < files.length; i++) {
        if (tests.formdata) formData.append('image', files[i]);
    }

    var name = prompt('Image name ?');
    formData.append('name', name);

    // now post a new XHR request
    if (tests.formdata) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/admin/image/upload');
        xhr.setRequestHeader('X-CSRFToken', csrf_token);
        xhr.onload = function(e) {
            progress.value = progress.innerHTML = 0;
        };
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4) {
                if(xhr.status == 200) {
                    var result = JSON.parse(xhr.responseText);

                    // the image may have been resized
                    var path = result.resized ? result.resized : result.original;
                    
                    var line = '\n:image ' + path + '\n'
                    document.getElementById('post-content').value += line;
                }
            }
        };
        xhr.onerror = function(e) {
            alert(e.target.status);
        }

        if (tests.progress) {
            xhr.upload.onprogress = function (event) {
                if (event.lengthComputable) {
                    var complete = (event.loaded / event.total * 100 | 0);
                    progress.value = progress.innerHTML = complete;
                }
            }
        }

        xhr.send(formData);
    }
}

var dnd_hover_classname = 'upload-hover';
if (tests.dnd) {
    holder.ondragover = function () {
        $(this).addClass(dnd_hover_classname);
        return false;
    };
    holder.ondragend = function () {
        $(this).removeClass(dnd_hover_classname);
        return false;
    };
    holder.ondrop = function (e) {
        $(this).removeClass(dnd_hover_classname);
        e.preventDefault();
        readfiles(e.dataTransfer.files);
    }
}
fileupload.querySelector('input').onchange = function () {
    readfiles(this.files);
};
