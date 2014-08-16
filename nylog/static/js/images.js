/**
 * Bad solution to ensure that the "full-width" images indeed take the
 * full width of the page
 * Tested on firefox, firefox android and chrome android
 */

var resizeFullWidthImages = function() {
    // We expect the document to have a certain structure :
    // body -> div#content -> h1, p(s) and img(s)
    var body = document.getElementsByTagName('body')[0];
    var page_width = body.offsetWidth;
    var width = page_width + "px";
    // the title of the post (h1 element) will be our anchor
    // to determine how many pixels to the left the image should be moved
    var title = document.getElementById('content').getElementsByTagName('h1')[0];
    var margin = getOffset(title).left;
    margin = "-" + margin + "px";

    var images = document.getElementsByClassName('full-width');
    for ( var i = 0; i < images.length; i++) {
        images[i].style.marginLeft = margin;
        images[i].style.width = width;
    }
}

document.onreadystatechange = function() {
    if (document.readyState == "interactive") {
        resizeFullWidthImages();
    }
}

// from http://stackoverflow.com/a/442474
function getOffset( el ) {
    var _x = 0;
    var _y = 0;
    while( el && !isNaN( el.offsetLeft ) && !isNaN( el.offsetTop ) ) {
        _x += el.offsetLeft - el.scrollLeft;
        _y += el.offsetTop - el.scrollTop;
        el = el.offsetParent;
    }
    return { top: _y, left: _x };
}

window.onresize = resizeFullWidthImages;

