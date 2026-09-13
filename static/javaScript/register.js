// Correctly select elements by ID
const usernameField = document.querySelector("#usernameField");
const feedBackArea = document.querySelector("#invalid_feedback");
const emailField = document.querySelector("#emailField");
const emailFeedBackArea = document.querySelector(".emailFeedBackArea");
const passwordField = document.querySelector("#passwordField");
const showPasswordToggle = document.querySelector(".showPasswordToggle");
const submitBtn = document.querySelector(".submit-btn");

const handleToggleInput = (e) => {
    if (!showPasswordToggle || !passwordField) return;
    if (showPasswordToggle.textContent === "Show") {
        showPasswordToggle.textContent = "Hide";
        passwordField.setAttribute("type", "text");
    } else {
        showPasswordToggle.textContent = "Show";
        passwordField.setAttribute("type", "password");
    }
};

if (showPasswordToggle) {
    showPasswordToggle.addEventListener("click", handleToggleInput);
}

if (usernameField) {
    usernameField.addEventListener("keyup", (e) => {
        const usernameVal = e.target.value;

        if (usernameVal.length > 0) {
            fetch("/authentication/validate-username", {
                body: JSON.stringify({ username: usernameVal }),
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then((res) => res.json())
            .then((data) => {
                if (data.username_error) {
                    usernameField.classList.add("is-invalid");
                    if (feedBackArea) {
                        feedBackArea.style.display = "block";
                        feedBackArea.innerText = data.username_error;
                    }
                    if (submitBtn) submitBtn.disabled = true;
                } else {
                    usernameField.classList.remove("is-invalid");
                    if (feedBackArea) feedBackArea.style.display = "none";
                    if (submitBtn) submitBtn.removeAttribute("disabled");
                }
            });
        } else {
            usernameField.classList.remove("is-invalid");
            if (feedBackArea) feedBackArea.style.display = "none";
        }
    });
}

if (emailField) {
    emailField.addEventListener("keyup", (e) => {
        const emailVal = e.target.value;

        if (emailVal.length > 0) {
            fetch("/authentication/validate-email", {
                body: JSON.stringify({ email: emailVal }),
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then((res) => res.json())
            .then((data) => {
                if (data.email_error) {
                    if (submitBtn) submitBtn.disabled = true;
                    emailField.classList.add("is-invalid");
                    if (emailFeedBackArea) {
                        emailFeedBackArea.style.display = "block";
                        emailFeedBackArea.innerText = data.email_error;
                    }
                } else {
                    emailField.classList.remove("is-invalid");
                    if (emailFeedBackArea) emailFeedBackArea.style.display = "none";
                    if (submitBtn) submitBtn.removeAttribute("disabled");
                }
            });
        } else {
            emailField.classList.remove("is-invalid");
            if (emailFeedBackArea) emailFeedBackArea.style.display = "none";
        }
    });
}
