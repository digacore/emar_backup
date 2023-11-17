// custom javascript
// TODO make more elegant jwt flow to all js scripts

document.querySelectorAll(".single-search-form").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    async function searchColumn() {
      const globalForm = document.querySelector("#overall-admin-search");
      const globalInput = document.querySelector("#overall-admin-search-input");
      globalInput.value = `<<${e.target.dataset.search_value}>>:${e.target.elements[0].value}`;

      globalForm.submit();
    }

    searchColumn();
  })
);

document.querySelectorAll("#overall-admin-search").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    async function searchMain() {
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

const sidebarObj = document.querySelector("#accordionSidebar");
if (sidebarObj.className.includes("toggled")) {
  const smallLogo = document.querySelector("#small-logo");
  smallLogo.removeAttribute("style");
} else {
  const bigLogo = document.querySelector("#big-logo");
  bigLogo.removeAttribute("style");
}

const sidebarLogoWrapper = document.querySelector("#sidebar-logo-wrapper");
const sidebarToggleButton = document.querySelector("#sidebarToggle");
sidebarToggleButton.addEventListener("click", () => {
  const smallLogo = document.querySelector("#small-logo");
  const bigLogo = document.querySelector("#big-logo");
  if (sidebarObj.className.includes("toggled")) {
    smallLogo.removeAttribute("style");
    sidebarLogoWrapper.style.padding = "0px 0px";
    bigLogo.style.display = "none";
  } else {
    smallLogo.style.display = "none";
    sidebarLogoWrapper.style.padding = "20px 0px";
    bigLogo.removeAttribute("style");
  }
});
