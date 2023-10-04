//For password change modal on the Users page
const changePasswordForm = document.querySelector("#change-password-form");
changePasswordForm.addEventListener("submit", (e) => {
  const passwordHint = document.querySelector("#passwords-not-equal-hint");
  const newPasswordInput = document.querySelector("#new-password-input");
  const confirmPasswordInput = document.querySelector("#confirm-new-password-input");

  if (!newPasswordInput.value || !confirmPasswordInput.value) {
		e.preventDefault();
		passwordHint.innerHTML = "*Both fields must be filled out";
		passwordHint.removeAttribute("hidden");
	} else if (newPasswordInput.value !== confirmPasswordInput.value) {
		e.preventDefault();
		passwordHint.innerHTML = "*Passwords do not match";
    passwordHint.removeAttribute("hidden");
  }
});

const showPassword = (event, oppositeButton) => {
	const passwordInput = event.target.parentElement.querySelector("input");
	const oppositeButtonElement = document.querySelector(`#${oppositeButton}`);

	event.target.setAttribute("hidden", true);
	oppositeButtonElement.removeAttribute("hidden");
	passwordInput.setAttribute("type", "text");
}

const hidePassword = (event, oppositeButton) => {
	const passwordInput = event.target.parentElement.querySelector("input");
	const oppositeButtonElement = document.querySelector(`#${oppositeButton}`);

	event.target.setAttribute("hidden", true);
	oppositeButtonElement.removeAttribute("hidden");
	passwordInput.setAttribute("type", "password");
}
