/**
 * Global JavaScript.
 */

/******************************************************************************
 * General Helpers                                                            *
 ******************************************************************************/

/** Copies the given text to the clipboard. Returns a Promise. */
function copyTextToClipboard(text) {
  return navigator.clipboard.writeText(text);
}

/******************************************************************************
 * jQuery                                                                     *
 ******************************************************************************/

$.fn.forEach = function (func) {
  return this.each((index, element) => func($(element), index));
};

$.fn.onEnterKeyPress = function (func) {
  return this.on("keydown", function (event) {
    if (event.key === "Enter") {
      func(event, $(this));
    }
  });
};

function ajaxRequest(method, url, options = {}) {
  // Super thin wrapper around jQuery's `ajax` method.
  // `options.success` accepts args: (response, status, jqXHR)
  // `options.error` accepts args: (jqXHR, status, errorThrown)
  // https://api.jquery.com/jquery.ajax/
  $.ajax({ method, url, ...options });
}

/******************************************************************************
 * Bootstrap                                                                  *
 ******************************************************************************/

/** Dismisses all the ".alert-success" elements after the given time. */
function dismissSuccessAlerts(seconds = 10) {
  setTimeout(() => {
    // For each success alert, emulate a click on the close button
    $(".alert-success").forEach(($alert) => {
      $alert.find(".btn-close").trigger("click");
    });
  }, seconds * 1000);
}
