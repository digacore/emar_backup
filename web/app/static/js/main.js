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

function selectCompany(hintsContainer) {
  const allHintsParagraphs = document.querySelectorAll(".search-company-hint");
  allHintsParagraphs.forEach((hint) => {
    hint.addEventListener("click", (e) => {
      const input = hintsContainer.parentElement.querySelector(
        ".search-company-input"
      );
      input.value = e.target.innerHTML.trim();
      hintsContainer.setAttribute("hidden", "");

      const confirmButton = hintsContainer.parentElement.parentElement.parentElement.querySelector(".confirm-modal-button");
      console.log("confirmButton", confirmButton);
      confirmButton.removeAttribute("disabled");
    });
  });
};

const searchCompanyParagraph = document.querySelector(".search-company-hint");
const searchComapnyInputs = document.querySelectorAll(".search-company-input");
searchComapnyInputs.forEach((searchComapnyInput) => {
  searchComapnyInput.addEventListener("input", async (e) => {
    try {
      const response = await fetch(`/search/company?q=${e.target.value}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (response.status !== 200) {
        throw new Error(`Error in searching ${response.status}`);
      }

      companiesArray = await response.json();
    } catch (error) {
      alert(`Error in searching company ${error}`);
    }

    companyHintsContainer = searchComapnyInput.parentElement.querySelector(".search-company-hints-div");

    if (companiesArray.results.length > 0) {
      companyHintsContainer.removeAttribute("hidden");

      companyHintsContainer.innerHTML = "";
      // Copy paragraph with hints
      companiesArray.results.forEach((company) => {
        const companyHint = searchCompanyParagraph.cloneNode(true);
        companyHint.innerHTML = company.name;
        companyHintsContainer.appendChild(companyHint);
      });
    } else {
      companyHintsContainer.setAttribute("hidden", "");
    }

    selectCompany(companyHintsContainer);
  });
});


