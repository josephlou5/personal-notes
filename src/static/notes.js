/**
 * Helpers for pages involving fetching notes
 */

function refreshTimestampTooltips() {
  const MS_PER_SEC = 1000;
  const SEC_PER_MIN = 60;
  const MIN_PER_HOUR = 60;
  const HOUR_PER_DAY = 24;
  const DAY_PER_WEEK = 7;

  const DAY_LABEL = "d";
  const HOUR_LABEL = "hr";
  const MIN_LABEL = "min";

  const ISO_ATTR = "iso";

  $(`[${ISO_ATTR}]`).forEach(($element) => {
    const timestamp = $element.attr(ISO_ATTR);
    if (timestamp == null) {
      // Remove attribute so it doesn't get processed again
      $element.removeAttr(ISO_ATTR);
      return;
    }
    const datetime = new Date(timestamp);
    if (isNaN(datetime)) {
      // Invalid date: remove attribute
      $element.removeAttr(ISO_ATTR);
      return;
    }

    // Set the "time ago" text
    // Total time difference in minutes
    const totalDiff = Math.floor(
      (new Date() - datetime) / MS_PER_SEC / SEC_PER_MIN
    );
    let timeAgoStr;
    if (totalDiff === 0) {
      timeAgoStr = "Now";
    } else {
      const minutes = totalDiff % MIN_PER_HOUR;
      const minutesRem = Math.floor(totalDiff / MIN_PER_HOUR);
      const hours = minutesRem % HOUR_PER_DAY;
      const days = Math.floor(minutesRem / HOUR_PER_DAY);

      if (days >= DAY_PER_WEEK) {
        // It's been more than a week, so just show the timestamp and be done
        bootstrap.Tooltip.getInstance($element.get(0))?.dispose();
        $element.text(strftime(datetime));
        $element.removeAttr(ISO_ATTR);
        $element.removeAttr("data-bs-toggle");
        return;
      }

      const timeAgoParts = [];
      if (days > 0) {
        timeAgoParts.push(`${days}${DAY_LABEL}`);
      }
      if (hours > 0) {
        timeAgoParts.push(`${hours}${HOUR_LABEL}`);
      }
      // Don't include minutes if there are days
      if (days === 0 && minutes > 0) {
        timeAgoParts.push(`${minutes}${MIN_LABEL}`);
      }
      timeAgoParts.push("ago");
      timeAgoStr = timeAgoParts.join(" ");
    }
    $element.text(timeAgoStr);

    if (!$element.attr("data-bs-toggle")) {
      // This is the first time we're seeing this tooltip element, so
      // initialize it
      $element.attr("data-bs-toggle", "tooltip");
      new bootstrap.Tooltip($element.get(0), {
        placement: "top",
        title: strftime(datetime),
      });
    }
  });
}

function initNoteCards($element, noNotesText, response, $error = null) {
  if (response.numNotes === 0) {
    $element.html("");
    $element.append(
      $("<div>", { class: "d-flex justify-content-center mt-3" }).append(
        $("<span>", { class: "fst-italic" }).text(noNotesText)
      )
    );
    return;
  }

  $element.html(response.notesHtml);

  // Handle favoriting
  $element.find(".note-favorite-btn").on("click", function (event) {
    const $btn = $(this);
    const noteId = $btn.attr("note-id");
    if (noteId == null) return;
    $error?.html("");
    ajaxRequest("POST", "/api/notes/favorites", {
      contentType: "application/json",
      data: JSON.stringify({ noteId }),
      success: (response, status, jqXHR) => {
        if (!response.success) {
          $error?.append(bsErrorAlert(response.error, { class: "mt-3" }));
          return;
        }
        let iconCode = "heart";
        if (response.isFavorite) {
          iconCode += "-fill";
          $(`#note-${noteId}-card`).attr("is-favorite", "true");
        } else {
          $(`#note-${noteId}-card`).removeAttr("is-favorite");
        }
        $btn.html(bsIcon(iconCode));
      },
    });
  });

  // Convert content
  $element.find(".card-body[not-converted]").forEach(($element) => {
    let content = $element.html();
    if (!content.trim()) {
      content = "_Nothing to see yet :eyes:_";
    }
    $element.html(parseMarkdown(content));
    $element.removeAttr("not-converted");
  });

  refreshTimestampTooltips();
}

function sendAjaxOnClick(
  $elements,
  { method, buildUrlFunc, $error, buildOptionsFunc = null, onError = null }
) {
  $elements.on("click", function (event) {
    $error.html("");
    const $btn = $(this);
    const noteId = $btn.attr("note-id");
    if (!noteId) {
      console.warning("Could not get note ID from button:", $btn);
      // Refresh page to hopefully fix the invalid state
      window.location.reload();
      return;
    }
    ajaxRequest(method, buildUrlFunc(noteId), {
      success: (response, status, jqXHR) => {
        if (!response.success) {
          onError?.();
          $error.append(bsErrorAlert(response.error, { class: "mt-3" }));
          return;
        }
        // Refresh page on success
        window.location.reload();
      },
      ...(buildOptionsFunc?.(noteId) ?? {}),
    });
  });
}

function initModalActionButton(modalId, ajaxOptions) {
  // Set up modal to track note ID
  $(`#${modalId}`).on("show.bs.modal", function (event) {
    const $trigger = $(event.relatedTarget);
    $(`#${modalId}-btn`).attr("note-id", $trigger.attr("note-id"));
  });

  // Set up button handler
  sendAjaxOnClick($(`#${modalId}-btn`), {
    ...ajaxOptions,
    onError: () => {
      // Close the modal before showing error
      $(`#${modalId}-close`).trigger("click");
    },
  });
}
