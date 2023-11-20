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

const selectedActionsWrapper = document.querySelector(".selected-actions-wrapper");
const itemCheckboxes = document.querySelectorAll(".action-checkbox");
itemCheckboxes.forEach((itemCheckbox) => {
  itemCheckbox.addEventListener("change", async (e) => {
    // Uncheck all checkboxes
    itemCheckboxes.forEach((itemCheckbox) => {
      if (itemCheckbox.checked && itemCheckbox !== e.currentTarget) {
        itemCheckbox.checked = false;
      }
    });

    const actionsWrapper = document.querySelector(`.actions-wrapper-${e.target.value}`);
    if (e.currentTarget.checked) {
      selectedActionsWrapper.innerHTML = null;

      const actions = actionsWrapper.childNodes;
      actions.forEach((action) => {
        const actionClone = action.cloneNode(true);
        if (action.className === "icon" && action.tagName === "A") {
          actionClone.style.color = "inherit";
        } else if (action.className === "icon" && action.tagName === "FORM") {
          childNodes = actionClone.childNodes;
          childNodes.forEach((childNode) => {
            if (childNode.tagName === "BUTTON") {
              childNode.style.border = "none";
              childNode.style.background = "inherit";
            }
          });
        } else if (action.className === "modal fade" && action.tagName === "DIV") {
          return;
        }

        selectedActionsWrapper.appendChild(actionClone);
      });
    } else {
      selectedActionsWrapper.innerHTML = null;
    }
  });
});
