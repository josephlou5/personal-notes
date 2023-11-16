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

function pad0(value, length) {
  return String(value).padStart(length, "0");
}

/** Formats the given datetime in the "Weekday, YYYY-MM-DD HH:MM:SS" format. */
function strftime(datetime) {
  // JavaScript annoyingly doesn't have a strftime method, so doing this
  // manually...
  const weekday = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][
    datetime.getDay()
  ];
  const year = pad0(datetime.getFullYear(), 4);
  const month = pad0(datetime.getMonth() + 1, 2);
  const day = pad0(datetime.getDate(), 2);
  const hour = pad0(datetime.getHours(), 2);
  const minute = pad0(datetime.getMinutes(), 2);
  const second = pad0(datetime.getSeconds(), 2);
  return `${weekday}, ${year}-${month}-${day} ${hour}:${minute}:${second}`;
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

/** Creates a Bootstrap icon. */
function bsIcon(code, { class: extraClasses = "" } = {}) {
  return $("<i>", { class: `bi bi-${code} ${extraClasses}` });
}

/** Creates a Bootstrap close button. */
function bsCloseBtn({ dismiss }) {
  return $("<button>", {
    "type": "button",
    "class": "btn-close",
    "data-bs-dismiss": dismiss,
    "aria-label": "Close",
  });
}

/** Creates a Bootstrap alert with the given error message. */
function bsErrorAlert(
  message,
  { class: extraClasses = "", dismissible = true } = {}
) {
  const classes = ["alert", "alert-danger"];
  if (dismissible) {
    classes.push("alert-dismissible", "fade", "show");
  }
  if (extraClasses) {
    classes.push(extraClasses);
  }
  return $("<div>", { class: classes.join(" "), role: "alert" }).append(
    $("<span>").text(message),
    bsCloseBtn({ dismiss: "alert" })
  );
}

/** Dismisses all the ".alert-success" elements after the given time. */
function dismissSuccessAlerts(seconds = 10) {
  setTimeout(() => {
    // For each success alert, emulate a click on the close button
    $(".alert-success").forEach(($alert) => {
      $alert.find(".btn-close").trigger("click");
    });
  }, seconds * 1000);
}

/******************************************************************************
 * Markdown                                                                   *
 ******************************************************************************/

/**
 * Initializes the `js-emoji` library.
 *
 * This is pretty hacky.
 */
function initEmoji() {
  // Support interchangeable underscores and hyphens
  for (const emojiData of Object.values(EmojiConvertor.prototype.data)) {
    if (emojiData.length < 3) continue;
    const codes = emojiData[3];
    if (!Array.isArray(codes)) continue;
    const codesSet = new Set();
    for (const code of codes) {
      codesSet.add(code);
      codesSet.add(code.replaceAll("_", "-"));
      codesSet.add(code.replaceAll("-", "_"));
    }
    // Replace the contents with the converted codes
    codes.splice(0, codes.length, ...codesSet);
  }

  // It's possible to convert all typed emojis into colon syntax with the
  // following code. However, it doesn't work well with a max length limit
  // (users' entered text may turn out to be too long, which isn't in their
  // control), and converting emojis as they type would result in their cursor
  // bouncing around, which isn't great either. It will *probably* be fine to
  // leave them as is.
  //   const emoji = new EmojiConvertor();
  //   emoji.colons_mode = true;
  //   const converted = emoji.replace_unified(context);
}

/**
 * Parses the given raw Markdown text, converting emojis and outputting the
 * resulting HTML.
 *
 * Expects the template to have `include_markdown = True` so that `Marked`,
 * `DOMPurify`, and `js-emoji` are loaded in the page.
 * @param {string} content
 * @returns {string}
 */
function parseMarkdown(content) {
  const emoji = new EmojiConvertor();
  emoji.replace_mode = "unified";
  // Replace emojis, remove common zero-width characters from the start, and
  // sanitize
  return DOMPurify.sanitize(
    marked.parse(
      emoji.replace_colons(
        content.replace(/^[\u200B\u200C\u200D\u200E\u200F\uFEFF]/, "")
      )
    ),
    { USE_PROFILES: { html: true } }
  );
}
