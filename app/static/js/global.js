//POST method implementation:
async function postData(url = "", data = {}) {
  // Default options are marked with *
  const response = await fetch(url, {
    method: "POST", // *GET, POST, PUT, DELETE, etc.
    mode: "cors", // no-cors, *cors, same-origin
    cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
    credentials: "same-origin", 
    headers: {
      "Content-Type": "application/json",      
    },
    redirect: "follow", // manual, *follow, error
    referrerPolicy: "no-referrer", // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
    body: JSON.stringify(data), // body data type must match "Content-Type" header
  });
  return response.json(); // parses JSON response into native JavaScript objects
}

// Flash Messages
function flash(message, category) {
  const messagesContainer = document.getElementById("messages-container");
  messagesContainer.innerHTML = `
  <div class="alert alert-${category} alert-dismissible fade show" style="margin-top:5rem;" role="alert">
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  </div>
  `;
}

// Delete Record
// let delRecord = function (obj, event) {
//   if (confirm("Are you sure you want to delete entire row and all entries attached to it?") == true) {
//     $(obj).closest("tr").remove();
//   } else {
//     console.log(event)
//     // event.preventDefault();
//   }  
// };

    
