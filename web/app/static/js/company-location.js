// find company element
$("#company").change((event) => {
  // if "__None" send 0 instead
  const selectedId = event.target.value === "__None" ? 0 : event.target.value;
  // request for list of tuples where [(location_id, location_name),]

  function actionsWithCompany(){
    const access_jwt = ('; '+document.cookie).split(`; jwt_token=`).pop().split(';')[0];
    $.ajax({
      url: `/locations_company/cid/${selectedId}`,
      beforeSend: (request) => {
        request.setRequestHeader('Authorization', `Bearer ${access_jwt}`);
      },
      success: (data) => {
        let $el = $("#location");
      $el.empty(); // remove old options
      // remove chosen value
      $("#s2id_location").find(".select2-chosen").empty();

      // append __None to have possibility to empty field
      $el.append(
        $("<option></option>")
          .attr("selected", "selected")
          .attr("value", "__None")
          .text("")
      );

      // append locations respectfully to chosen company
      $.each(data, function (_, idLocation) {
        $el.append(
          $("<option></option>").attr("value", idLocation[0]).text(idLocation[1])
        );
      });
      },
      error: (xhr) => {
        if (xhr.status === 401) {
          refreshJWT()
        }
      }
    });
  }

  //function to refresh jwt token
  function refreshJWT() {
    const refresh_jwt = ('; '+document.cookie).split(`; refresh_jwt_token=`).pop().split(';')[0];

    $.ajax({
      url: '/refresh',
      beforeSend: (request) => {
        request.setRequestHeader('Authorization', `Bearer ${refresh_jwt}`);
      },
      success: () => {
        actionsWithCompany()
      },
      error: (xhr)=> {
        console.log("error in refreshJWT", xhr);
      }
    });
  }

  actionsWithCompany()
});

// Insert founded company or location name and id to inputs
function selectSecondaryMergeObject(hintsContainer) {
  const allHintsParagraphs = document.querySelectorAll(".search-object-hint");
  allHintsParagraphs.forEach((hint) => {
    hint.addEventListener("click", (e) => {
      const nameInput = hintsContainer.parentElement.querySelector(
        ".search-object-input"
      );
      const idInput = hintsContainer.parentElement.querySelector(".search-object-id-input");
      nameInput.value = e.target.innerHTML.trim();
      idInput.value = e.target.id.replace("search-object-hint-", "");
      hintsContainer.setAttribute("hidden", "");

      const confirmButton = hintsContainer.parentElement.parentElement.parentElement.querySelector(".confirm-modal-button");
      confirmButton.removeAttribute("disabled");
    });
  });
};

const searchObjectParagraph = document.querySelector(".search-object-hint");
const searchObjectInputs = document.querySelectorAll(".search-object-input");
searchObjectInputs.forEach((searchObjectInput) => {
  searchObjectInput.addEventListener("input", async (e) => {
    objectHintsContainer = searchObjectInput.parentElement.querySelector(".search-object-hints-div");
    confirmButton = searchObjectInput.parentElement.parentElement.parentElement.querySelector(".confirm-modal-button");
    confirmButton.setAttribute("disabled", "disabled");

    searchObject = window.location.pathname.includes("/admin/company/") ? "company" : "location";

    try {
      const response = await fetch(`/search/${searchObject}?q=${e.target.value}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (response.status !== 200) {
        throw new Error(`Error in searching ${response.status}`);
      }

      objectsArray = await response.json();
    } catch (error) {
      alert(`Error in searching ${searchObject} ${error}`);
    }

    if (objectsArray.results.length > 0) {
      objectHintsContainer.removeAttribute("hidden");

      objectHintsContainer.innerHTML = "";
      // Copy paragraph with hints
      objectsArray.results.forEach((foundObj) => {
        const objectHint = searchObjectParagraph.cloneNode(true);
        objectHint.innerHTML = foundObj.name;
        objectHint.id = `search-object-hint-${foundObj.id}`;
        objectHintsContainer.appendChild(objectHint);
      });
    } else {
      objectHintsContainer.setAttribute("hidden", "");
    }

    selectSecondaryMergeObject(objectHintsContainer);
  });
});
