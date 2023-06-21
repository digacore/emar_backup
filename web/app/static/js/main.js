// custom javascript
// TODO make more elegant jwt flow to all js scripts

document.querySelectorAll(".single-search-form").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    function refreshJWT() {
      const refresh_jwt = ('; '+document.cookie).split(`; refresh_jwt_token=`).pop().split(';')[0];

      $.ajax({
        url: '/refresh',
        beforeSend: (request) => {
          request.setRequestHeader('Authorization', `Bearer ${refresh_jwt}`);
        },
        success: () => {
          searchColumn()
        },
        error: (xhr)=> {
          console.log("error in refreshJWT", xhr);
        }
      });
    }

    async function searchColumn() {
      const access_jwt = ('; '+document.cookie).split(`; jwt_token=`).pop().split(';')[0];

      const response = await fetch("/search_column", {
        method: "POST",
        body: JSON.stringify({
          col_name: e.target.dataset.search_value,
          current_href: window.location.href,
        }),
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${access_jwt}`
        },
      });

      if (response.status === 401) {
        refreshJWT()
        return
      }
      const globalForm = document.querySelector("#overall-admin-search");
      const globalInput = document.querySelector("#overall-admin-search-input");
      globalInput.value = e.target.elements[0].value;
      globalForm.submit();
    }

    searchColumn();
  })
);

document.querySelectorAll("#overall-admin-search").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    function refreshJWT() {
      const refresh_jwt = ('; '+document.cookie).split(`; refresh_jwt_token=`).pop().split(';')[0];

      $.ajax({
        url: '/refresh',
        beforeSend: (request) => {
          request.setRequestHeader('Authorization', `Bearer ${refresh_jwt}`);
        },
        success: () => {
          searchMain()
        },
        error: (xhr)=> {
          console.log("error in refreshJWT", xhr);
        }
      });
    }

    async function searchMain() {
      const access_jwt = ('; '+document.cookie).split(`; jwt_token=`).pop().split(';')[0];

      const response = await fetch("/search_column", {
        method: "POST",
        body: JSON.stringify({
          col_name: "all",
          current_href: window.location.href,
        }),
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${access_jwt}`
        },
      });

      if (response.status === 401) {
        refreshJWT()
        return
      }
      console.log("test search")
      const globalForm = document.querySelector("#overall-admin-search");
      globalForm.submit();
    }

    searchMain();
  })
);

function startTime() {
  const today = new Date().toLocaleTimeString("en-US", {
    timeZone: "America/New_York",
  });
  document.getElementById("js-clock").innerHTML = today;
  setTimeout(startTime, 1000);
}
