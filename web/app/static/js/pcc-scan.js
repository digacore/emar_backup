// Tooltips initialization
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

// Searching input
const searchInput = document.querySelector("#reports-search-input");
if (searchInput) {
  searchInput.addEventListener("keyup", function (e) {
    if (e.key === "Enter") {
      let oldParams = (new URL(window.location)).searchParams;
      let url = new URL(window.location.href);
      url.searchParams.set("q", searchInput.value);
      // reset page to 1
      url.searchParams.set("page", "1");
      url.searchParams.set("per_page", oldParams.get("per_page") || "25");
      url.searchParams.set("approved_page", oldParams.get("approved_page") || "False");
      window.location.href = "".concat(url.href);
    }
  });
}

// X button to clear search input
const clearSearchInput = (e) => {
  searchInput.value = "";
  let oldParams = (new URL(window.location)).searchParams;
  let url = new URL(window.location.href);
  url.searchParams.set("q", "");
  // reset page to 1
  url.searchParams.set("page", "1");
  url.searchParams.set("per_page", oldParams.get("per_page") || "25");
  url.searchParams.set("approved_page", oldParams.get("approved_page") || "False");
  window.location.href = "".concat(url.href);
}

// Function for JWT token refresh
async function refreshJWT(obj_id, changed_data) {
  const refresh_jwt = ('; '+document.cookie).split(`; refresh_jwt_token=`).pop().split(';')[0];

  $.ajax({
    url: '/refresh',
    beforeSend: (request) => {
      request.setRequestHeader('Authorization', `Bearer ${refresh_jwt}`);
    },
    success: async () => {
      await handleChangeData(obj_id, changed_data);
    },
    error: (xhr)=> {
      console.log("error in refreshJWT", xhr);
    }
  });
}

// Function for handling changes in reports (delete action; set downloading type; approve / reject)
const handleChangeData = async (obj_id, changed_data, should_reload) => {
  const url = new URL(`/pcc_api/creation-report/${obj_id}`, window.location.origin).href;
  const access_jwt = ('; '+document.cookie).split(`; jwt_token=`).pop().split(';')[0];

  try {
    response = await fetch(url, {
      method: 'PATCH',
      headers: {
          'Content-type': 'application/json; charset=UTF-8',
          'Authorization': `Bearer ${access_jwt}`
      },
      body: JSON.stringify(changed_data),
    });

    if (response.status === 401) {
      await refreshJWT(obj_id, changed_data)
      window.location.reload();
    } else if (response.status !== 200) {
      throw new Error(`Error deleting action from report: ${response.status}`);
    }

  } catch (error) {
    alert(`Error deleting action from report: ${error}`);
  }

  if (should_reload) {
    window.location.reload();
  }
}
