
function setThrText() {
    thr_min_val.innerHTML = thr_min_slider.value;
    thr_max_val.innerHTML = thr_max_slider.value;
    thr_andxor.innerHTML = (thr_max_slider.value > thr_min_slider.value) ? "AND" : "XOR";
}

function setPrVisible() {
    var prs = document.getElementsByClassName("d");
    var i;
    for (i = 0; i < prs.length; i++) {
        if (thr_max_slider.value > thr_min_slider.value) {
            // AND
            if (parseFloat(prs[i].getAttribute("value")) >= thr_min_slider.value &&
                parseFloat(prs[i].getAttribute("value")) <= thr_max_slider.value) {
                prs[i].classList.remove("invisible");
            }
            else {
                prs[i].classList.add("invisible");
            }
        }
        else {
            // XOR
            if (parseFloat(prs[i].getAttribute("value")) >= thr_max_slider.value &&
                parseFloat(prs[i].getAttribute("value")) <= thr_min_slider.value) {
                prs[i].classList.add("invisible");
            }
            else {
                prs[i].classList.remove("invisible");
            }
        }
    }
}

function setPrSignificant() {
    var prs = document.getElementsByClassName("pr");
    var i;
    for (i = 0; i < prs.length; i++) {
        if (parseFloat(prs[i].getAttribute("zscore")) >= thr_sig_slider.value) {
            prs[i].classList.add("significant");
        }
        else {
            prs[i].classList.remove("significant");
        }
    }
}

$(document).ready(function(){
    // Bootstrap popover elements.
    $('[data-toggle="popover"]').popover();

    // Attach to elements by ID.
    var thr_min_slider = document.getElementById("thr_min_slider");
    var thr_max_slider = document.getElementById("thr_max_slider");
    var thr_min_val = document.getElementById("thr_min_val");
    var thr_max_val = document.getElementById("thr_max_val");
    var thr_andxor = document.getElementById("thr_andxor");

    thr_min_slider.oninput = function() {
        setThrText();
        setPrVisible();
    }

    thr_max_slider.oninput = function() {
        setThrText();
        setPrVisible();
    }

    setThrText();
    setPrVisible();
    setPrSignificant();
});
