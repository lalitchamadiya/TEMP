// Correctly select elements by ID
const usernameField = document.querySelector("#usernameField");
const feedBackArea = document.querySelector("#invalid_feedback");
const emailField = document.querySelector("#emailField");
const emailFeedBackArea = document.querySelector(".emailFeedBackArea");
const passwordField = document.querySelector("#passwordField");
const showPasswordToggle= document.querySelector(".showPasswordToggle");
const submitBtn = document.querySelector(".submit-btn");


const handleToggleInput = (e) =>{
    if(showPasswordToggle.textContent==="Show"){
        showPasswordToggle.textContent ="Hide";

        passwordField.setAttribute("type" , "text");
    }else{
        showPasswordToggle.textContent= "Show";
        passwordField.setAttribute("type" , "password");
    }
}



showPasswordToggle.addEventListener("click", handleToggleInput);


usernameField.addEventListener("keyup", (e) => {
    console.log('777777', 777777);

    // Use the value from the input field
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
                feedBackArea.style.display = "block";
                feedBackArea.innerText = data.username_error; // Assuming you want to show the error message
                submitBtn.disabled = true;
            } else {
                usernameField.classList.remove("is-invalid");
                feedBackArea.style.display = "none";
                submitBtn.removeAttribute("disabled");
            }
        });
    } else {
        // Optionally handle the case where the input is empty
        usernameField.classList.remove("is-invalid");
        emailFeedBackArea.style.display = "none";
    }
});

emailField.addEventListener("keyup", (e) => {
    console.log('777777', 777777);

    // Use the value from the input field
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
            console.log("data", data);
            if (data.email_error) {
                submitBtn.disabled=true;
                emailField.classList.add("is-invalid");
                emailFeedBackArea.style.display = "block";
                emailFeedBackArea.innerText = data.email_error; // Assuming you want to show the error message
            } else {
                emailField.classList.remove("is-invalid");
                emailFeedBackArea.style.display = "none";
                submitBtn.removeAttribute("disabled");
            }
        });
    } else {
        // Optionally handle the case where the input is empty
        emailField.classList.remove("is-invalid");
        emailFeedBackArea.style.display = "none";
    }
});
